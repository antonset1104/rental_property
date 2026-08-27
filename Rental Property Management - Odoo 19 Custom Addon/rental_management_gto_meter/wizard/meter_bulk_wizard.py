# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PropertyMeterReadingBulkWizard(models.TransientModel):
    _name = 'property.meter.reading.bulk.wizard'
    _description = 'Input Catatan Meter Massal'

    date = fields.Date(string='Tanggal Pencatatan', required=True, default=fields.Date.today)
    property_id = fields.Many2one('property.details', string='Properti / Gedung (Filter)')
    meter_type = fields.Selection([
        ('electricity', 'Listrik'),
        ('water', 'Air'),
        ('gas', 'Gas'),
        ('other', 'Lainnya')
    ], string='Tipe Meter (Filter)')
    auto_create_invoice = fields.Boolean(string='Langsung Terbitkan Tagihan Customer (Draft Invoice)', default=True)
    line_ids = fields.One2many('property.meter.reading.bulk.line', 'wizard_id', string='Daftar Meter')

    @api.onchange('property_id', 'meter_type')
    def onchange_filters(self):
        self.action_load_meters()

    def action_load_meters(self):
        domain = [('active', '=', True)]
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.meter_type:
            domain.append(('meter_type', '=', self.meter_type))

        meters = self.env['property.meter'].search(domain, order='property_id, name')
        lines = []
        for m in meters:
            lines.append((0, 0, {
                'meter_id': m.id,
                'meter_type': m.meter_type,
                'property_id': m.property_id.id,
                'tenancy_id': m.tenancy_id.id if m.tenancy_id else False,
                'tenant_id': m.tenant_id.id if m.tenant_id else False,
                'previous_reading': m.last_reading or 0.0,
                'current_reading': m.last_reading or 0.0,
                'tariff': m.tariff or 0.0,
                'uom_name': m.uom_name or '',
            }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_process_readings(self):
        valid_lines = self.line_ids.filtered(lambda l: l.current_reading > l.previous_reading)
        if not valid_lines:
            raise UserError(self.env._("Tidak ada pembacaan meter dengan angka stand baru (Current Reading > Previous Reading)."))

        created_readings = self.env['property.meter.reading']
        for line in valid_lines:
            reading = self.env['property.meter.reading'].create({
                'meter_id': line.meter_id.id,
                'tenancy_id': line.tenancy_id.id if line.tenancy_id else False,
                'date': self.date or fields.Date.today(),
                'previous_reading': line.previous_reading,
                'current_reading': line.current_reading,
                'tariff': line.tariff,
            })
            created_readings |= reading
            if self.auto_create_invoice and reading.consumption > 0 and (reading.tenant_id or reading.tenancy_id):
                try:
                    reading.action_create_invoice()
                except Exception as e:
                    _logger.warning(
                        "Auto-invoice failed for meter reading %s: %s",
                        reading.name, e)

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Hasil Pembacaan Meter'),
            'res_model': 'property.meter.reading',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_readings.ids)],
        }


class PropertyMeterReadingBulkLine(models.TransientModel):
    _name = 'property.meter.reading.bulk.line'
    _description = 'Bulk Meter Reading Line'

    wizard_id = fields.Many2one('property.meter.reading.bulk.wizard', required=True, ondelete='cascade')
    meter_id = fields.Many2one('property.meter', string='No. Meter', required=True)
    meter_type = fields.Selection(related='meter_id.meter_type', string='Tipe')
    property_id = fields.Many2one('property.details', string='Properti')
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa')
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    uom_name = fields.Char(string='Satuan')
    previous_reading = fields.Float(string='Stand Lalu', readonly=True)
    current_reading = fields.Float(string='Stand Baru / Kini')
    tariff = fields.Float(string='Tarif / Unit')
    consumption = fields.Float(string='Pemakaian', compute='_compute_consumption')
    estimated_amount = fields.Float(string='Est. Tagihan', compute='_compute_consumption')

    @api.depends('current_reading', 'previous_reading', 'tariff')
    def _compute_consumption(self):
        for rec in self:
            cons = (rec.current_reading or 0.0) - (rec.previous_reading or 0.0)
            rec.consumption = cons if cons > 0 else 0.0
            rec.estimated_amount = rec.consumption * (rec.tariff or 0.0)
