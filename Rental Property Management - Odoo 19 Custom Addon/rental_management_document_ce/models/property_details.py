# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyLegalDocument(models.Model):
    _name = 'property.legal.document'
    _description = 'Property Legal Document & Permit'
    _order = 'document_type, expiry_date desc, id desc'

    name = fields.Char(string='Nama / Judul Dokumen', required=True)
    property_id = fields.Many2one('property.details', string='Properti', required=True, ondelete='cascade')
    document_type = fields.Selection([
        ('sertipikat', 'Sertipikat Kepemilikan (SHM / HGB)'),
        ('imb', 'IMB / PBG (Persetujuan Bangunan Gedung)'),
        ('slf', 'SLF (Sertifikat Laik Fungsi)'),
        ('pbb', 'PBB (Pajak Bumi & Bangunan)'),
        ('pks', 'PKS / Dokumen Perjanjian'),
        ('tax', 'Pajak (NPWP / SPPKP / NITKU)'),
        ('izin_lingkungan', 'Izin Lingkungan / AMDAL / UKL-UPL'),
        ('izin_damkar', 'Sertifikasi Proteksi Kebakaran (Damkar)'),
        ('izin_operasional', 'Perizinan Operasional Lainnya'),
    ], string='Kategori Dokumen', required=True, default='sertipikat')
    document_number = fields.Char(string='Nomor Dokumen / Sertipikat')
    issuer = fields.Char(string='Instansi Penerbit / Notaris')
    issue_date = fields.Date(string='Tanggal Terbit')
    expiry_date = fields.Date(string='Masa Berlaku / Expiry')
    is_expired = fields.Boolean(string='Kedaluwarsa', compute='_compute_is_expired', store=True)
    attachment_file = fields.Binary(string='File Dokumen (PDF/Scan)', required=True)
    file_name = fields.Char(string='Nama File')
    notes = fields.Text(string='Catatan / Keterangan')
    company_id = fields.Many2one(related='property_id.company_id', store=True)

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = bool(rec.expiry_date and rec.expiry_date < today)


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    attachment_count = fields.Integer(compute='_compute_attachment_count')
    legal_document_ids = fields.One2many('property.legal.document', 'property_id',
                                         string='Dokumen Legal & Perizinan')
    legal_document_count = fields.Integer(compute='_compute_legal_document_count')

    def _compute_attachment_count(self):
        Att = self.env['ir.attachment']
        for rec in self:
            rec.attachment_count = Att.search_count([
                ('res_model', '=', 'property.details'), ('res_id', '=', rec.id)])

    @api.depends('legal_document_ids')
    def _compute_legal_document_count(self):
        for rec in self:
            rec.legal_document_count = len(rec.legal_document_ids)

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Property Files'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', 'property.details'),
                       ('res_id', '=', self.id)],
            'context': {'default_res_model': 'property.details',
                        'default_res_id': self.id},
        }

