# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyMEPAsset(models.Model):
    _name = 'property.mep.asset'
    _description = 'Aset Mekanikal & Elektrikal Gedung (MEP Asset)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Nama Peralatan / Aset MEP', required=True, tracking=True)
    asset_code = fields.Char(string='Kode Aset / Tag ID', required=True, copy=False,
                             default='Baru', tracking=True)
    property_id = fields.Many2one('property.details', string='Gedung / Properti', required=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)
    location_detail = fields.Char(string='Lokasi Spesifik (Ruang Pompa / Ruang Genset / Lantai)', required=True)

    asset_category = fields.Selection([
        ('genset', 'Genset & Tangki Solar'),
        ('chiller', 'Chiller AC & AHU'),
        ('lift', 'Lift Penumpang & Lift Barang'),
        ('hydrant', 'Pompa Hydrant & Sprinkler Damkar'),
        ('panel_lvmd', 'Panel Utama Listrik (LVMDP) & Trafo'),
        ('stp', 'Sewage Treatment Plant (STP) / WTP'),
        ('cctv', 'Sistem Keamanan CCTV & Access Door'),
    ], string='Kategori Aset', default='genset', required=True, tracking=True)

    brand = fields.Char(string='Merk / Brand Peralatan')
    model_number = fields.Char(string='Model / Tipe')
    serial_number = fields.Char(string='Nomor Seri (Serial Number)')
    installation_date = fields.Date(string='Tanggal Pemasangan / Operasional')
    warranty_expiry = fields.Date(string='Masa Garansi / Servis Berkala')

    inspection_interval = fields.Selection([
        ('daily', 'Harian (Daily Checklist)'),
        ('weekly', 'Mingguan (Weekly)'),
        ('monthly', 'Bulanan (Monthly)'),
    ], string='Interval Inspeksi Rutin', default='daily', required=True)

    log_ids = fields.One2many('property.mep.inspection.log', 'asset_id', string='Riwayat Log Inspeksi')
    last_inspection_date = fields.Date(string='Inspeksi Terakhir', compute='_compute_last_inspection', store=True)
    last_status = fields.Selection([
        ('normal', 'Normal & Prima'),
        ('warning', 'Perlu Perhatian (Warning)'),
        ('critical', 'Kritis / Rusak (Critical)'),
    ], string='Kondisi Terakhir', compute='_compute_last_inspection', store=True)

    @api.depends('log_ids.inspection_date', 'log_ids.operating_status')
    def _compute_last_inspection(self):
        for rec in self:
            logs = rec.log_ids.sorted(key=lambda l: l.inspection_date or fields.Date.today(), reverse=True)
            if logs:
                rec.last_inspection_date = logs[0].inspection_date
                rec.last_status = logs[0].operating_status
            else:
                rec.last_inspection_date = False
                rec.last_status = 'normal'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('asset_code', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.mep.asset') or 'MEP/' + fields.Date.today().strftime('%Y/') + '001'
                vals['asset_code'] = seq
        return super().create(vals_list)


class PropertyMEPInspectionLog(models.Model):
    _name = 'property.mep.inspection.log'
    _description = 'Log Checklist Inspeksi Lapangan Teknisi MEP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, id desc'

    asset_id = fields.Many2one('property.mep.asset', string='Peralatan MEP', required=True, ondelete='cascade')
    inspection_date = fields.Date(string='Tanggal Inspeksi', default=fields.Date.today, required=True)
    technician_id = fields.Many2one('res.users', string='Teknisi Pemeriksa',
                                    default=lambda s: s.env.user, required=True)

    operating_status = fields.Selection([
        ('normal', 'Normal & Prima'),
        ('warning', 'Perlu Perhatian (Warning)'),
        ('critical', 'Kritis / Rusak (Critical)'),
    ], string='Status Kondisi Alat', default='normal', required=True, tracking=True)

    voltage_volt = fields.Float(string='Tegangan Listrik (Volt)')
    current_ampere = fields.Float(string='Arus Listrik (Ampere)')
    temperature_celsius = fields.Float(string='Suhu Operasional (°C)')
    pressure_bar = fields.Float(string='Tekanan (Bar / PSI)')

    notes = fields.Text(string='Catatan Temuan Lapangan', required=True)
    photo_attachment = fields.Binary(string='Foto Temuan Lapangan (Kamera HP)')
    photo_name = fields.Char(string='Nama File Foto')

    maintenance_request_created = fields.Boolean(string='Tiket Maintenance Dibuat', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.operating_status in ('warning', 'critical'):
                rec.asset_id.message_post(body=self.env._(
                    "⚠️ <b>PERINGATAN INSPEKSI TEKNISI MEP:</b><br/>"
                    "Status: <b>%s</b><br/>"
                    "Teknisi: %s<br/>"
                    "Suhu: %s °C | Tekanan: %s Bar | Voltase: %s V<br/>"
                    "Catatan: %s"
                ) % (dict(rec._fields['operating_status'].selection).get(rec.operating_status),
                     rec.technician_id.name, rec.temperature_celsius, rec.pressure_bar,
                     rec.voltage_volt, rec.notes))
        return records
