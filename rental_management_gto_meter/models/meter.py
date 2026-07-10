# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyMeter(models.Model):
    _name = 'property.meter'
    _description = 'Utility Meter'
    _order = 'property_id, name'

    name = fields.Char(string='Meter No.', required=True, copy=False)
    active = fields.Boolean(default=True)
    meter_type = fields.Selection([('electricity', 'Electricity'),
                                   ('water', 'Water'),
                                   ('gas', 'Gas'),
                                   ('other', 'Other')],
                                  string='Type', default='electricity', required=True)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Current Contract',
                                 domain="[('property_id', '=', property_id)]")
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    uom_name = fields.Char(string='Unit', default='kWh')
    tariff = fields.Float(string='Tariff (per unit)', digits='Product Price')
    product_id = fields.Many2one(
        'product.product', string='Recharge Product',
        default=lambda self: self.env.ref(
            'rental_management_gto_meter.product_utility_recharge',
            raise_if_not_found=False))
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    reading_ids = fields.One2many('property.meter.reading', 'meter_id',
                                  string='Readings')
    last_reading = fields.Float(compute='_compute_last_reading')

    @api.depends('reading_ids.current_reading', 'reading_ids.date')
    def _compute_last_reading(self):
        for rec in self:
            readings = rec.reading_ids.sorted(lambda r: (r.date or fields.Date.today(),
                                                         r.id))
            rec.last_reading = readings[-1].current_reading if readings else 0.0


class PropertyMeterReading(models.Model):
    _name = 'property.meter.reading'
    _description = 'Meter Reading'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    meter_id = fields.Many2one('property.meter', string='Meter', required=True)
    meter_type = fields.Selection(related='meter_id.meter_type', store=True)
    property_id = fields.Many2one(related='meter_id.property_id', store=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract')
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    date = fields.Date(string='Reading Date', required=True, default=fields.Date.today)
    previous_reading = fields.Float(string='Previous Reading')
    current_reading = fields.Float(string='Current Reading')
    consumption = fields.Float(string='Consumption', compute='_compute_consumption',
                               store=True)
    tariff = fields.Float(string='Tariff', digits='Product Price')
    amount = fields.Monetary(string='Amount', compute='_compute_consumption', store=True)
    company_id = fields.Many2one(related='meter_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('billed', 'Billed')],
                             default='draft')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True,
                                 copy=False)

    @api.depends('current_reading', 'previous_reading', 'tariff')
    def _compute_consumption(self):
        for rec in self:
            cons = (rec.current_reading or 0.0) - (rec.previous_reading or 0.0)
            rec.consumption = cons if cons > 0 else 0.0
            rec.amount = rec.consumption * (rec.tariff or 0.0)

    @api.onchange('meter_id')
    def _onchange_meter(self):
        for rec in self:
            if rec.meter_id:
                rec.previous_reading = rec.meter_id.last_reading
                rec.tariff = rec.meter_id.tariff
                rec.tenancy_id = rec.meter_id.tenancy_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.meter.reading') or '/'
        return super().create(vals_list)

    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                continue
            if rec.consumption <= 0.0:
                raise UserError(self.env._(
                    "Consumption is zero for reading %s.") % rec.name)
            tenant = rec.tenant_id or rec.tenancy_id.tenancy_id
            if not tenant:
                raise UserError(self.env._(
                    "Set a contract/tenant on reading %s to recharge.") % rec.name)
            product = rec.meter_id.product_id or self.env.ref(
                'rental_management_gto_meter.product_utility_recharge',
                raise_if_not_found=False)
            if not product:
                raise UserError(self.env._("Set a Recharge Product on the meter."))
            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': tenant.id,
                'invoice_date': rec.date or fields.Date.today(),
                'tenancy_id': rec.tenancy_id.id if rec.tenancy_id else False,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': self.env._('%s recharge - meter %s (%s %s)') % (
                        dict(rec._fields['meter_type'].selection).get(
                            rec.meter_type, ''),
                        rec.meter_id.name, rec.consumption, rec.meter_id.uom_name or ''),
                    'quantity': rec.consumption,
                    'price_unit': rec.tariff,
                })],
            })
            rec.invoice_id = move.id
            rec.state = 'billed'
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
