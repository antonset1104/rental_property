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
    is_peak_off_peak = fields.Boolean(string='Tarif Beban Puncak PLN (WBP / LWBP)', default=False,
                                      help="Aktifkan untuk tarif listrik komersial B3/I3 dengan pemisahan Waktu Beban Puncak (WBP) dan Luar Waktu Beban Puncak (LWBP).")
    tariff_wbp = fields.Float(string='Tarif WBP (Beban Puncak)', digits='Product Price')
    tariff_lwbp = fields.Float(string='Tarif LWBP (Luar Beban Puncak)', digits='Product Price')

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

    @api.depends('reading_ids.current_reading', 'reading_ids.current_reading_lwbp', 'reading_ids.date')
    def _compute_last_reading(self):
        for rec in self:
            readings = rec.reading_ids.sorted(lambda r: (r.date or fields.Date.today(),
                                                         r.id))
            if readings:
                if rec.is_peak_off_peak:
                    rec.last_reading = (readings[-1].current_reading_wbp or 0.0) + (readings[-1].current_reading_lwbp or 0.0)
                else:
                    rec.last_reading = readings[-1].current_reading or 0.0
            else:
                rec.last_reading = 0.0

    @api.model
    def _cron_meter_reading_reminder(self):
        """Pengingat terjadwal bulanan untuk tim Engineering mencatat meteran utilitas."""
        today = fields.Date.today()
        meters = self.search([('active', '=', True)])
        for m in meters:
            # Check last reading date
            last_date = m.reading_ids and max(m.reading_ids.mapped('date'))
            if not last_date or (today - last_date).days >= 28:
                if m.tenancy_id:
                    m.tenancy_id.message_post(body=self.env._(
                        "⚡ <b>JADWAL PENCATATAN METERAN UTILITAS (%s)</b><br/>"
                        "Unit: %s | Tipe: %s (Stand Terakhir: %s %s).<br/>"
                        "Harap lakukan pencatatan meteran bulanan periode berjalan.") % (
                            m.name, m.property_id.name or '', m.meter_type, m.last_reading, m.uom_name))
        return True



class PropertyMeterReading(models.Model):
    _name = 'property.meter.reading'
    _description = 'Meter Reading'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    meter_id = fields.Many2one('property.meter', string='Meter', required=True)
    meter_type = fields.Selection(related='meter_id.meter_type', store=True)
    is_peak_off_peak = fields.Boolean(related='meter_id.is_peak_off_peak', store=True)
    property_id = fields.Many2one(related='meter_id.property_id', store=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract')
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    date = fields.Date(string='Reading Date', required=True, default=fields.Date.today)
    previous_reading = fields.Float(string='Previous Reading')
    current_reading = fields.Float(string='Current Reading')

    # WBP (Peak) & LWBP (Off-Peak) fields
    previous_reading_wbp = fields.Float(string='Stand Lalu WBP')
    current_reading_wbp = fields.Float(string='Stand Kini WBP')
    consumption_wbp = fields.Float(string='Pemakaian WBP', compute='_compute_consumption', store=True)
    tariff_wbp = fields.Float(string='Tarif WBP', digits='Product Price')
    amount_wbp = fields.Monetary(string='Biaya WBP', compute='_compute_consumption', store=True)

    previous_reading_lwbp = fields.Float(string='Stand Lalu LWBP')
    current_reading_lwbp = fields.Float(string='Stand Kini LWBP')
    consumption_lwbp = fields.Float(string='Pemakaian LWBP', compute='_compute_consumption', store=True)
    tariff_lwbp = fields.Float(string='Tarif LWBP', digits='Product Price')
    amount_lwbp = fields.Monetary(string='Biaya LWBP', compute='_compute_consumption', store=True)

    consumption = fields.Float(string='Total Consumption', compute='_compute_consumption',
                               store=True)
    tariff = fields.Float(string='Tariff', digits='Product Price')
    amount = fields.Monetary(string='Total Amount', compute='_compute_consumption', store=True)
    company_id = fields.Many2one(related='meter_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('billed', 'Billed')],
                             default='draft')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True,
                                 copy=False)

    @api.depends('current_reading', 'previous_reading', 'tariff',
                 'current_reading_wbp', 'previous_reading_wbp', 'tariff_wbp',
                 'current_reading_lwbp', 'previous_reading_lwbp', 'tariff_lwbp', 'is_peak_off_peak')
    def _compute_consumption(self):
        for rec in self:
            if rec.is_peak_off_peak:
                # WBP
                cons_wbp = (rec.current_reading_wbp or 0.0) - (rec.previous_reading_wbp or 0.0)
                rec.consumption_wbp = cons_wbp if cons_wbp > 0 else 0.0
                rec.amount_wbp = rec.consumption_wbp * (rec.tariff_wbp or 0.0)
                # LWBP
                cons_lwbp = (rec.current_reading_lwbp or 0.0) - (rec.previous_reading_lwbp or 0.0)
                rec.consumption_lwbp = cons_lwbp if cons_lwbp > 0 else 0.0
                rec.amount_lwbp = rec.consumption_lwbp * (rec.tariff_lwbp or 0.0)
                # Total
                rec.consumption = rec.consumption_wbp + rec.consumption_lwbp
                rec.amount = rec.amount_wbp + rec.amount_lwbp
            else:
                cons = (rec.current_reading or 0.0) - (rec.previous_reading or 0.0)
                rec.consumption = cons if cons > 0 else 0.0
                rec.amount = rec.consumption * (rec.tariff or 0.0)
                rec.consumption_wbp = 0.0
                rec.amount_wbp = 0.0
                rec.consumption_lwbp = 0.0
                rec.amount_lwbp = 0.0

    @api.onchange('meter_id')
    def _onchange_meter(self):
        for rec in self:
            if rec.meter_id:
                rec.previous_reading = rec.meter_id.last_reading
                rec.tariff = rec.meter_id.tariff
                rec.tariff_wbp = rec.meter_id.tariff_wbp
                rec.tariff_lwbp = rec.meter_id.tariff_lwbp
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
