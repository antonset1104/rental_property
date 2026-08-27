# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyFitoutPermit(models.Model):
    _name = 'property.fitout.permit'
    _description = 'Surat Izin Kerja (SIK) / Fit-Out Work Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='No. Surat Izin Kerja (SIK)', required=True, copy=False,
                       readonly=True, default='Baru', tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa', required=True, tracking=True)
    property_id = fields.Many2one('property.details', string='Unit Properti',
                                  related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one('res.partner', string='Penyewa (Tenant)',
                                related='tenancy_id.tenancy_id', store=True)
    company_id = fields.Many2one('res.company', string='Perusahaan / PT',
                                 related='property_id.company_id', store=True)

    contractor_name = fields.Char(string='Nama Kontraktor / Vendor', required=True, tracking=True)
    contractor_pic = fields.Char(string='Penanggung Jawab (PIC)', required=True, tracking=True)
    contractor_phone = fields.Char(string='No. Telepon / WhatsApp PIC', required=True)
    contractor_worker_count = fields.Integer(string='Jumlah Pekerja', default=1)

    work_type = fields.Selection([
        ('minor_fitout', 'Minor Fit-Out / Partisi & Pengecatan'),
        ('major_renovation', 'Renovasi Mayor / Perubahan Struktur Ruangan'),
        ('mep_work', 'Instalasi MEP / Kelistrikan / AC / Plumbing'),
        ('dismantling', 'Pembongkaran / Pengosongan (Dismantling)'),
    ], string='Kategori Pekerjaan', default='minor_fitout', required=True, tracking=True)

    start_date = fields.Date(string='Tanggal Mulai Kerja', required=True,
                             default=fields.Date.today, tracking=True)
    end_date = fields.Date(string='Tanggal Selesai Kerja', required=True, tracking=True)

    working_hours_type = fields.Selection([
        ('daytime', 'Siang Hari (08:00 - 17:00 WIB)'),
        ('night_shift', 'Malam Hari (21:00 - 05:00 WIB) - Khusus Mall/Kantor'),
        ('weekend_only', 'Akhir Pekan (Sabtu - Minggu)'),
        ('24_hours', '24 Jam (Izin Khusus)'),
    ], string='Jam Kerja yang Diizinkan', default='night_shift', required=True)

    is_hot_work_permitted = fields.Boolean(string='Izin Pengelasan / Hot Work',
                                           help="Centang jika pekerjaan melibatkan pengelasan, pemotongan besi, atau api terbuka.")
    has_fire_extinguisher = fields.Boolean(string='APAR Tersedia di Lokasi Kerja', default=True)
    safety_briefing_done = fields.Boolean(string='Safety Induction & K3 Dilakukan', default=True)

    deposit_id = fields.Many2one('property.security.deposit', string='Deposit Fit-Out Terkait',
                                 domain="[('deposit_type', '=', 'fitout'), ('property_id', '=', property_id)]")

    state = fields.Selection([
        ('draft', 'Draft Pengajuan'),
        ('approved', 'Disetujui Building Management'),
        ('active', 'Pekerjaan Berjalan'),
        ('completed', 'Selesai & Inspeksi Akhir'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status SIK', default='draft', tracking=True)

    notes = fields.Text(string='Ketentuan Khusus & Peraturan K3',
                        default="1. Wajib mengenakan APD lengkap (Helm Proyek, Rompi, Sepatu Safety).\n"
                                "2. Dilarang merokok di area kerja dan lorong gedung.\n"
                                "3. Pekerjaan bising/berdebu hanya diizinkan pada malam hari (21:00 - 05:00).\n"
                                "4. Sampah puing wajib dibersihkan setiap hari sebelum shift kerja berakhir.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.fitout.permit') or 'SIK/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.message_post(body=self.env._("Surat Izin Kerja (SIK) telah disetujui oleh Building Management."))

    def action_start(self):
        for rec in self:
            rec.state = 'active'
            rec.message_post(body=self.env._("Pekerjaan fit-out kontraktor resmi dimulai."))

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            rec.message_post(body=self.env._("Pekerjaan fit-out telah selesai dan siap diinspeksi akhir."))

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec.message_post(body=self.env._("Surat Izin Kerja telah dibatalkan."))
