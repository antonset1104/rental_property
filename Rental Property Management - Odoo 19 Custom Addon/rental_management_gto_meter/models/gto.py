# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class TenancyDetailsGto(models.Model):
    _inherit = 'tenancy.details'

    is_gto = fields.Boolean(string='GTO / Revenue Sharing')
    gto_type = fields.Selection([
        ('higher_of', 'Higher of Base Rent or % Turnover'),
        ('base_plus', 'Base Rent + Overage'),
        ('pure', 'Pure % of Turnover'),
    ], string='GTO Type', default='higher_of')
    gto_percentage = fields.Float(string='Turnover %', help="Percentage of gross "
                                  "turnover used to compute percentage rent.")
    gto_breakpoint = fields.Monetary(
        string='Artificial Breakpoint',
        help="For 'Base Rent + Overage': turnover threshold above which the "
             "percentage applies. Leave 0 to use the natural breakpoint "
             "(base rent ÷ turnover %).")
    gto_product_id = fields.Many2one(
        'product.product', string='GTO Rent Product',
        default=lambda self: self.env.ref(
            'rental_management_gto_meter.product_gto_rent', raise_if_not_found=False))
    turnover_ids = fields.One2many('property.gto.turnover', 'tenancy_id',
                                   string='Turnover Declarations')
    turnover_count = fields.Integer(compute='_compute_turnover_count')

    def _compute_turnover_count(self):
        for rec in self:
            rec.turnover_count = len(rec.turnover_ids)

    def action_view_turnovers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Turnover Declarations',
            'res_model': 'property.gto.turnover',
            'view_mode': 'list,form',
            'domain': [('tenancy_id', '=', self.id)],
            'context': {'default_tenancy_id': self.id},
        }


class PropertyGtoTurnover(models.Model):
    _name = 'property.gto.turnover'
    _description = 'Tenant Gross Turnover Declaration'
    _inherit = ['mail.thread']
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    tenancy_id = fields.Many2one('tenancy.details', string='Contract',
                                 required=True, tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    company_id = fields.Many2one(related='tenancy_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    date_from = fields.Date(string='Period From', required=True)
    date_to = fields.Date(string='Period To', required=True)
    gross_turnover = fields.Monetary(string='Gross Turnover', tracking=True)
    base_rent = fields.Monetary(string='Base Rent (Period)')
    gto_type = fields.Selection([
        ('higher_of', 'Higher of Base Rent or % Turnover'),
        ('base_plus', 'Base Rent + Overage'),
        ('pure', 'Pure % of Turnover'),
    ], string='GTO Type', default='higher_of')
    percentage = fields.Float(string='Turnover %')
    breakpoint = fields.Monetary(string='Breakpoint')
    percentage_rent = fields.Monetary(compute='_compute_amounts', store=True)
    billable_amount = fields.Monetary(string='Billable (Percentage/Overage) Rent',
                                      compute='_compute_amounts', store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('invoiced', 'Invoiced')], default='draft', tracking=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True,
                                 copy=False)

    @api.onchange('tenancy_id')
    def _onchange_tenancy(self):
        if self.tenancy_id:
            self.percentage = self.tenancy_id.gto_percentage
            self.breakpoint = self.tenancy_id.gto_breakpoint
            self.base_rent = self.tenancy_id.total_rent
            self.gto_type = self.tenancy_id.gto_type

    @api.depends('gross_turnover', 'base_rent', 'percentage', 'breakpoint', 'gto_type')
    def _compute_amounts(self):
        for rec in self:
            pct = (rec.percentage or 0.0) / 100.0
            pr = (rec.gross_turnover or 0.0) * pct
            rec.percentage_rent = pr
            if rec.gto_type == 'higher_of':
                rec.billable_amount = max(0.0, pr - (rec.base_rent or 0.0))
            elif rec.gto_type == 'base_plus':
                bp = rec.breakpoint
                if not bp and pct:
                    bp = (rec.base_rent or 0.0) / pct  # natural breakpoint
                rec.billable_amount = max(0.0, (rec.gross_turnover or 0.0) - bp) * pct
            else:  # pure
                rec.billable_amount = pr

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.gto.turnover') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_invoice(self):
        last_rec = self.env['property.gto.turnover']
        for rec in self:
            if rec.invoice_id:
                continue
            if rec.billable_amount <= 0.0:
                raise UserError(self.env._(
                    "Billable percentage/overage rent is zero for %s.") % rec.name)
            product = rec.tenancy_id.gto_product_id or self.env.ref(
                'rental_management_gto_meter.product_gto_rent', raise_if_not_found=False)
            if not product:
                raise UserError(self.env._("Set a GTO Rent Product on the contract."))
            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': rec.tenant_id.id,
                'invoice_date': rec.date_to or fields.Date.today(),
                'tenancy_id': rec.tenancy_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': self.env._('Percentage Rent %s (%s - %s)') % (
                        rec.name, rec.date_from, rec.date_to),
                    'quantity': 1.0,
                    'price_unit': rec.billable_amount,
                })],
            })
            rec.invoice_id = move.id
            rec.state = 'invoiced'
            last_rec = rec
        if len(self) == 1 and last_rec:
            return last_rec._open_invoice()
        return True

    def _open_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
        }
