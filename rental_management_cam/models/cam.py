# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyCamPeriod(models.Model):
    _name = 'property.cam.period'
    _description = 'CAM / Service Charge Period'
    _inherit = ['mail.thread']
    _order = 'date_from desc, id desc'

    name = fields.Char(required=True, copy=False, readonly=True,
                       default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, tracking=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    total_area = fields.Float(string='Total Lettable Area', digits=(16, 2))
    charge_basis = fields.Selection([('budget', 'Budget'), ('actual', 'Actual')],
                                    default='actual', required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('invoiced', 'Invoiced')], default='draft', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    product_id = fields.Many2one(
        'product.product', string='Service Charge Product',
        default=lambda s: s.env.ref('rental_management_cam.product_cam',
                                    raise_if_not_found=False))
    expense_line_ids = fields.One2many('property.cam.expense.line', 'cam_id')
    tenant_line_ids = fields.One2many('property.cam.tenant.line', 'cam_id')
    total_budget = fields.Monetary(compute='_compute_totals', store=True)
    total_actual = fields.Monetary(compute='_compute_totals', store=True)
    total_charge = fields.Monetary(compute='_compute_totals', store=True)

    @api.depends('expense_line_ids.budget_amount', 'expense_line_ids.actual_amount',
                 'charge_basis')
    def _compute_totals(self):
        for rec in self:
            rec.total_budget = sum(rec.expense_line_ids.mapped('budget_amount'))
            rec.total_actual = sum(rec.expense_line_ids.mapped('actual_amount'))
            rec.total_charge = rec.total_actual if rec.charge_basis == 'actual' \
                else rec.total_budget

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.cam.period') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_invoices(self):
        for cam in self:
            product = cam.product_id or self.env.ref(
                'rental_management_cam.product_cam', raise_if_not_found=False)
            if not product:
                raise UserError(self.env._("Set a Service Charge Product."))
            for line in cam.tenant_line_ids.filtered(
                    lambda l: l.partner_id and l.amount and not l.invoice_id):
                move_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': line.partner_id.id,
                    'invoice_date': cam.date_to or fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': self.env._('Service Charge %s (%s)') % (
                            cam.name, cam.property_id.name or ''),
                        'quantity': 1.0,
                        'price_unit': line.amount,
                    })],
                }
                if line.tenancy_id and 'tenancy_id' in self.env['account.move']._fields:
                    move_vals['tenancy_id'] = line.tenancy_id.id
                elif 'property_manual_id' in self.env['account.move']._fields:
                    move_vals['property_manual_id'] = cam.property_id.id
                line.invoice_id = self.env['account.move'].create(move_vals).id
            cam.state = 'invoiced'
        return True


class PropertyCamExpenseLine(models.Model):
    _name = 'property.cam.expense.line'
    _description = 'CAM Expense Line'

    cam_id = fields.Many2one('property.cam.period', required=True, ondelete='cascade')
    name = fields.Char(string='Expense Category', required=True)
    budget_amount = fields.Monetary(string='Budget')
    actual_amount = fields.Monetary(string='Actual')
    variance = fields.Monetary(compute='_compute_variance')
    currency_id = fields.Many2one(related='cam_id.currency_id')
    company_id = fields.Many2one(related='cam_id.company_id', store=True)

    @api.depends('budget_amount', 'actual_amount')
    def _compute_variance(self):
        for l in self:
            l.variance = l.budget_amount - l.actual_amount


class PropertyCamTenantLine(models.Model):
    _name = 'property.cam.tenant.line'
    _description = 'CAM Tenant Apportionment Line'

    cam_id = fields.Many2one('property.cam.period', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Tenant', required=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract')
    area = fields.Float(string='Area', digits=(16, 2))
    share = fields.Float(string='Share %', compute='_compute_amount', store=True)
    amount = fields.Monetary(string='Charge', compute='_compute_amount', store=True)
    invoice_id = fields.Many2one('account.move', readonly=True)
    currency_id = fields.Many2one(related='cam_id.currency_id')
    company_id = fields.Many2one(related='cam_id.company_id', store=True)

    @api.depends('area', 'cam_id.total_area', 'cam_id.total_charge')
    def _compute_amount(self):
        for l in self:
            total_area = l.cam_id.total_area or 0.0
            l.share = (l.area / total_area * 100.0) if total_area else 0.0
            l.amount = (l.cam_id.total_charge or 0.0) * (l.share / 100.0)
