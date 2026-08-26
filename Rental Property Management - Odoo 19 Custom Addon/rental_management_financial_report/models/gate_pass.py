# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyGatePass(models.Model):
    _name = 'property.gate.pass'
    _description = 'Surat Izin Keluar/Masuk Barang (Gate Pass / Loading Dock Permit)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='No. Gate Pass', required=True, copy=False,
                       readonly=True, default='Baru', tracking=True)
    pass_type = fields.Selection([
        ('in', 'Izin Masuk Barang (Loading In)'),
        ('out', 'Izin Keluar Barang (Loading Out)'),
        ('both', 'Masuk & Keluar (Pameran / Display Sementara)'),
    ], string='Jenis Izin Barang', default='in', required=True, tracking=True)

    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa', required=True, tracking=True)
    property_id = fields.Many2one('property.details', string='Unit Properti',
                                  related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one('res.partner', string='Penyewa (Tenant)',
                                related='tenancy_id.tenancy_id', store=True)
    company_id = fields.Many2one('res.company', string='Perusahaan / PT',
                                 related='property_id.company_id', store=True)

    carrier_name = fields.Char(string='Nama Supir / Kurir / Pembawa Barang', required=True, tracking=True)
    carrier_phone = fields.Char(string='No. HP / WhatsApp Kurir')
    vehicle_plate = fields.Char(string='No. Polisi / Plat Kendaraan', required=True, tracking=True)

    pass_date = fields.Date(string='Tanggal Izin Akses', required=True,
                            default=fields.Date.today, tracking=True)
    time_window = fields.Selection([
        ('morning', 'Pagi Hari (08:00 - 12:00 WIB)'),
        ('afternoon', 'Siang Hari (13:00 - 17:00 WIB)'),
        ('night', 'Malam Hari (21:00 - 05:00 WIB) - Khusus Barang Besar / Furniture'),
    ], string='Jendela Waktu Loading Dock', default='morning', required=True)

    line_ids = fields.One2many('property.gate.pass.line', 'pass_id', string='Daftar Barang / Muatan')
    item_count = fields.Integer(string='Jumlah Item', compute='_compute_item_count')

    state = fields.Selection([
        ('draft', 'Draft Pengajuan'),
        ('approved', 'Disetujui Building Management'),
        ('checked', 'Diverifikasi Security & Loading Dock'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status Gate Pass', default='draft', tracking=True)

    security_notes = fields.Text(string='Catatan Pos Security / Pemeriksaan Lapangan')

    @api.depends('line_ids')
    def _compute_item_count(self):
        for rec in self:
            rec.item_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.gate.pass') or 'GP/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.message_post(body=_("Surat Izin Masuk/Keluar Barang (Gate Pass) telah disetujui Building Management."))

    def action_verify_security(self):
        for rec in self:
            rec.state = 'checked'
            rec.message_post(body=_("Pemeriksaan fisik barang di Pos Security & Loading Dock telah diverifikasi."))

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            rec.message_post(body=_("Proses muat/bongkar barang di Loading Dock telah selesai."))

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec.message_post(body=_("Surat Izin Gate Pass telah dibatalkan."))


class PropertyGatePassLine(models.Model):
    _name = 'property.gate.pass.line'
    _description = 'Rincian Barang Gate Pass'

    pass_id = fields.Many2one('property.gate.pass', string='Gate Pass', required=True, ondelete='cascade')
    item_name = fields.Char(string='Nama Barang / Peralatan', required=True)
    quantity = fields.Float(string='Jumlah / Qty', default=1.0)
    uom_name = fields.Char(string='Satuan', default='Unit / Pcs')
    serial_number = fields.Char(string='No. Seri / Keterangan Spesifik')
    condition = fields.Selection([
        ('good', 'Kondisi Baik'),
        ('damaged', 'Rusak / Perlu Perbaikan'),
        ('material', 'Bahan Bangunan / Material'),
    ], string='Kondisi Barang', default='good', required=True)
