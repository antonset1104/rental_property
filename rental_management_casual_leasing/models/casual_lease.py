# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyCasualLease(models.Model):
    _name = 'property.casual.lease'
    _description = 'Casual / Short-term Lease'
    _inherit = ['mail.thread']
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, tracking=True)
    space_name = fields.Char(string='Space / Location',
                             help="Booth, kiosk, atrium or area being let.")
    partner_id = fields.Many2one('res.partner', string='Customer', required=True,
                                 tracking=True)
    date_from = fields.Date(string='From', required=True, default=fields.Date.today)
    date_to = fields.Date(string='To', required=True, default=fields.Date.today)
    duration_days = fields.Integer(string='Days', compute='_compute_duration',
                                   store=True)
    rate_type = fields.Selection([('per_day', 'Per Day'),
                                  ('per_week', 'Per Week'),
                                  ('fixed', 'Fixed')],
                                 string='Rate Type', default='per_day', required=True)
    rate = fields.Monetary(string='Rate')
    quantity = fields.Float(string='Billed Quantity', compute='_compute_amount',
                            store=True)
    amount_total = fields.Monetary(string='Total', compute='_compute_amount',
                                   store=True)
    deposit = fields.Monetary(string='Deposit')
    product_id = fields.Many2one(
        'product.product', string='Lease Product',
        default=lambda self: self.env.ref(
            'rental_management_casual_leasing.product_casual_lease',
            raise_if_not_found=False))
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('active', 'Active'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')],
                             default='draft', tracking=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True,
                                 copy=False)

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to >= rec.date_from:
                rec.duration_days = (rec.date_to - rec.date_from).days + 1
            else:
                rec.duration_days = 0

    @api.depends('duration_days', 'rate', 'rate_type')
    def _compute_amount(self):
        for rec in self:
            if rec.rate_type == 'per_day':
                qty = rec.duration_days
            elif rec.rate_type == 'per_week':
                qty = math.ceil(rec.duration_days / 7.0) if rec.duration_days else 0
            else:  # fixed
                qty = 1
            rec.quantity = qty
            rec.amount_total = qty * (rec.rate or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.casual.lease') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_activate(self):
        self.write({'state': 'active'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                continue
            if rec.amount_total <= 0.0:
                raise UserError(self.env._(
                    "Nothing to invoice for %s (total is zero).") % rec.name)
            product = rec.product_id or self.env.ref(
                'rental_management_casual_leasing.product_casual_lease',
                raise_if_not_found=False)
            if not product:
                raise UserError(self.env._("Set a Lease Product on %s.") % rec.name)
            label = self.env._('Casual lease %s - %s (%s to %s)') % (
                rec.name, rec.space_name or rec.property_id.name,
                rec.date_from, rec.date_to)
            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'invoice_date': rec.date_from or fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': label,
                    'quantity': rec.quantity or 1.0,
                    'price_unit': rec.rate,
                })],
            }
            # Attribute to the property for the Owners Statement when the
            # financial-report module is installed (field added there).
            if 'property_manual_id' in self.env['account.move']._fields:
                move_vals['property_manual_id'] = rec.property_id.id
            move = self.env['account.move'].create(move_vals)
            rec.invoice_id = move.id
            if rec.state in ('draft', 'confirm'):
                rec.state = 'active'
        return self._open_invoice()

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
