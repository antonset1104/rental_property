# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyManagementFee(models.Model):
    """Periodic management fee charged by the property manager.
    User inputs manually; posting creates a vendor bill (fee payable to manager)
    and optionally a customer invoice (recharge to owner/tenant)."""
    _name = 'property.management.fee'
    _description = 'Property Management Fee'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, tracking=True)
    date = fields.Date(string='Fee Date', required=True,
                       default=fields.Date.today, tracking=True)
    period_from = fields.Date(string='Period From', required=True)
    period_to = fields.Date(string='Period To', required=True)
    fee_type = fields.Selection([
        ('management', 'Management Fee'),
        ('commission', 'Broker Commission'),
        ('other', 'Other Fee'),
    ], string='Fee Type', default='management', required=True)
    amount = fields.Monetary(string='Fee Amount', tracking=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes (PPh/PPN)')
    fee_account_id = fields.Many2one('account.account', string='Expense Account',
                                     help="Account to debit the management fee expense.")
    manager_id = fields.Many2one('res.partner', string='Manager / Agent',
                                 help="Vendor to whom the fee is payable.")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', 'in', ('purchase', 'general'))]")
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'),
                               ('cancel', 'Cancelled')],
                             default='draft', tracking=True)
    bill_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.management.fee') or '/'
        return super().create(vals_list)

    def action_post(self):
        for rec in self:
            if rec.state == 'posted':
                continue
            if not rec.fee_account_id:
                raise UserError(self.env._("Set an Expense Account on the management fee."))
            if not rec.manager_id:
                raise UserError(self.env._("Set a Manager/Agent (vendor) on the management fee."))
            journal = rec.journal_id or self.env['account.journal'].search(
                [('type', '=', 'purchase'), ('company_id', '=', rec.company_id.id)], limit=1)
            if not journal:
                raise UserError(self.env._("No purchase journal found."))
            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': rec.manager_id.id,
                'journal_id': journal.id,
                'invoice_date': rec.date,
                'ref': rec.name,
                'property_manual_id': rec.property_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': '%s – %s' % (rec.fee_type.replace('_', ' ').title(), rec.name),
                    'account_id': rec.fee_account_id.id,
                    'price_unit': rec.amount,
                    'tax_ids': [(6, 0, rec.tax_ids.ids)],
                })],
            })
            bill.action_post()
            rec.bill_id = bill.id
            rec.state = 'posted'

    def action_cancel(self):
        for rec in self:
            if rec.bill_id and rec.bill_id.state == 'posted':
                rec.bill_id.button_draft()
                rec.bill_id.button_cancel()
            rec.state = 'cancel'

    def action_draft(self):
        self.write({'state': 'draft'})


class PropertyTenantRecharge(models.Model):
    """Tenant recharge: actual cost incurred vs amount charged to tenant.
    Profit = charged_amount - actual_cost. Posting creates both the
    expense entry (actual cost) and the customer invoice (charged amount)."""
    _name = 'property.tenant.recharge'
    _description = 'Tenant Recharge'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Lease / Tenant',
                                 domain="[('property_id', '=', property_id)]")
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant', store=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    recharge_type = fields.Char(string='Recharge Type',
                                help="e.g. Common Area Electricity, Water, etc.")
    actual_cost = fields.Monetary(string='Actual Cost',
                                  help="Actual expense incurred (from vendor bill).")
    charged_amount = fields.Monetary(string='Charged to Tenant',
                                     help="Amount invoiced to the tenant.")
    profit = fields.Monetary(string='Profit / (Loss)', compute='_compute_profit', store=True)
    cost_account_id = fields.Many2one('account.account', string='Cost Account')
    income_account_id = fields.Many2one('account.account', string='Income Account',
                                        help="Account for the recharge income (Tenant Recharge Income).")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', 'in', ('sale', 'general'))]")
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'),
                               ('cancel', 'Cancelled')],
                             default='draft', tracking=True)
    invoice_id = fields.Many2one('account.move', string='Customer Invoice',
                                 readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    notes = fields.Text(string='Notes')

    @api.depends('actual_cost', 'charged_amount')
    def _compute_profit(self):
        for rec in self:
            rec.profit = (rec.charged_amount or 0.0) - (rec.actual_cost or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.tenant.recharge') or '/'
        return super().create(vals_list)

    def action_post(self):
        for rec in self:
            if rec.state == 'posted':
                continue
            if not rec.income_account_id:
                raise UserError(self.env._("Set an Income Account on the recharge."))
            if not rec.tenant_id:
                raise UserError(self.env._("Set a Tenant (via Lease) on the recharge."))
            journal = rec.journal_id or self.env['account.journal'].search(
                [('type', '=', 'sale'), ('company_id', '=', rec.company_id.id)], limit=1)
            if not journal:
                raise UserError(self.env._("No sales journal found."))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': rec.tenant_id.id,
                'journal_id': journal.id,
                'invoice_date': rec.date,
                'ref': rec.name,
                'property_manual_id': rec.property_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': rec.recharge_type or rec.name,
                    'account_id': rec.income_account_id.id,
                    'price_unit': rec.charged_amount,
                })],
            })
            invoice.action_post()
            rec.invoice_id = invoice.id
            rec.state = 'posted'

    def action_cancel(self):
        for rec in self:
            if rec.invoice_id and rec.invoice_id.state == 'posted':
                rec.invoice_id.button_draft()
                rec.invoice_id.button_cancel()
            rec.state = 'cancel'

    def action_draft(self):
        self.write({'state': 'draft'})
