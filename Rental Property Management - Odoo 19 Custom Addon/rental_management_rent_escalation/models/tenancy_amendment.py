# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyTenancyAmendment(models.Model):
    _name = 'property.tenancy.amendment'
    _description = 'Adendum & Perubahan Klausul Kontrak Sewa (Lease Amendment)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'amendment_date desc, id desc'

    name = fields.Char(string='No. Adendum', required=True, readonly=True, default='Baru', copy=False, tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa Induk', required=True, tracking=True)
    tenant_id = fields.Many2one('res.partner', related='tenancy_id.tenancy_id', store=True)
    property_id = fields.Many2one('property.details', related='tenancy_id.property_id', store=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)

    amendment_date = fields.Date(string='Tanggal Adendum', default=fields.Date.today, required=True, tracking=True)
    effective_date = fields.Date(string='Tanggal Efektif Berlaku', default=fields.Date.today, required=True, tracking=True)

    amendment_type = fields.Selection([
        ('rate', 'Penyesuaian Tarif Sewa / Service Charge'),
        ('term', 'Perubahan / Perpanjangan Masa Sewa'),
        ('area', 'Perubahan Luasan Sewa Unit (m²)'),
        ('discount', 'Pemberian Diskon / Grace Period Tambahan'),
        ('clause', 'Perubahan Klausul Khusus Perjanjian'),
    ], string='Jenis Adendum', default='rate', required=True, tracking=True)

    reason = fields.Selection([
        ('negotiation', 'Negosiasi Ulang / Relaksasi Bisnis'),
        ('expansion', 'Ekspansi / Pengurangan Luas Unit'),
        ('renewal', 'Perpanjangan Masa Sewa (Lease Renewal)'),
        ('escalation', 'Kenaikan Berkala Terjadwal'),
        ('other', 'Alasan Lainnya'),
    ], string='Latar Belakang Adendum', default='negotiation', required=True)

    description = fields.Text(string='Ringkasan Perubahan Klausul & Dasar Pertimbangan', required=True)

    # Financial & Terms Comparison
    previous_rent = fields.Float(string='Tarif Sewa Lama (IDR)')
    new_rent = fields.Float(string='Tarif Sewa Baru (IDR)')
    previous_end_date = fields.Date(string='Tanggal Berakhir Lama')
    new_end_date = fields.Date(string='Tanggal Berakhir Baru')

    state = fields.Selection([
        ('draft', 'Draft Usulan'),
        ('approved', 'Disetujui Building Management & Owner'),
        ('applied', 'Telah Diterapkan ke Kontrak'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status Adendum', default='draft', tracking=True)

    @api.onchange('tenancy_id')
    def _onchange_tenancy_id(self):
        if self.tenancy_id:
            self.previous_rent = self.tenancy_id.total_rent
            self.new_rent = self.tenancy_id.total_rent
            self.previous_end_date = self.tenancy_id.end_date
            self.new_end_date = self.tenancy_id.end_date

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.tenancy.amendment') or 'ADD/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.message_post(body=_("Adendum kontrak telah disetujui Management."))

    def action_apply_to_tenancy(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_("Adendum harus disetujui terlebih dahulu."))
            vals = {}
            if rec.new_rent and rec.new_rent != rec.previous_rent:
                vals['total_rent'] = rec.new_rent
            if rec.new_end_date and rec.new_end_date != rec.previous_end_date:
                vals['end_date'] = rec.new_end_date
            if vals:
                rec.tenancy_id.write(vals)
            rec.state = 'applied'
            rec.message_post(body=_("Perubahan adendum telah berhasil diterapkan ke Kontrak Sewa (%s).") % rec.tenancy_id.name)
