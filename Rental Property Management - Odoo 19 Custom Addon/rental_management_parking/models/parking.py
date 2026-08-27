# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyParkingPass(models.Model):
    _name = 'property.parking.pass'
    _description = 'Kartu & Izin Parkir Langganan Tenant (Parking Pass)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='No. Pass Parkir', required=True, copy=False,
                       readonly=True, default='Baru', tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa', required=True, tracking=True)
    tenant_id = fields.Many2one('res.partner', string='Penyewa (Tenant)',
                                related='tenancy_id.tenancy_id', store=True)
    property_id = fields.Many2one('property.details', string='Gedung / Properti',
                                  related='tenancy_id.property_id', store=True)
    company_id = fields.Many2one('res.company', string='Perusahaan / PT',
                                 related='property_id.company_id', store=True)

    vehicle_type = fields.Selection([
        ('car', 'Mobil (Roda 4)'),
        ('motorcycle', 'Sepeda Motor (Roda 2)'),
        ('vip', 'Slot Khusus VIP Reserved'),
    ], string='Jenis Kendaraan', default='car', required=True, tracking=True)

    plate_number = fields.Char(string='Nomor Polisi (Plat Nomor)', required=True, tracking=True)
    vehicle_brand = fields.Char(string='Merk / Model Kendaraan', placeholder='Contoh: Toyota Kijang Innova')
    driver_name = fields.Char(string='Nama Pengemudi / Pemegang Kartu', required=True, tracking=True)
    driver_phone = fields.Char(string='No. HP / WhatsApp Pengemudi')
    rfid_card_number = fields.Char(string='Nomor Kartu RFID Parkir', tracking=True)

    parking_quota_type = fields.Selection([
        ('free', 'Jatah Kuota Gratis (Allotted Quota)'),
        ('paid', 'Langganan Berbayar Bulanan'),
    ], string='Kategori Kuota', default='free', required=True, tracking=True)

    monthly_fee = fields.Float(string='Tarif Bulanan (IDR)', default=0.0, tracking=True)
    date_start = fields.Date(string='Tanggal Mulai', default=fields.Date.today, required=True)
    date_end = fields.Date(string='Tanggal Berakhir', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Aktif'),
        ('expired', 'Kedaluwarsa'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status Pass Parkir', default='draft', tracking=True)

    notes = fields.Text(string='Catatan Khusus')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.parking.pass') or 'PRK/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_activate(self):
        for rec in self:
            rec.state = 'active'
            rec.message_post(body=self.env._("Kartu Pass Parkir Kendaraan telah diaktifkan."))

    def action_expire(self):
        for rec in self:
            rec.state = 'expired'
            rec.message_post(body=self.env._("Masa berlaku pass parkir telah habis / kedaluwarsa."))

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec.message_post(body=self.env._("Kartu pass parkir telah dibatalkan."))
