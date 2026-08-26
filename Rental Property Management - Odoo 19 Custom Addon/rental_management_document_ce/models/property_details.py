# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _


class PropertyLegalDocument(models.Model):
    _name = 'property.legal.document'
    _description = 'Property Legal Document & Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_type, expiry_date desc, id desc'

    name = fields.Char(string='Nama / Judul Dokumen', required=True, tracking=True)
    property_id = fields.Many2one('property.details', string='Properti', required=True,
                                  ondelete='cascade', tracking=True)
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
    ], string='Kategori Dokumen', required=True, default='sertipikat', tracking=True)
    document_number = fields.Char(string='Nomor Dokumen / Sertipikat', tracking=True)
    issuer = fields.Char(string='Instansi Penerbit / Notaris')
    issue_date = fields.Date(string='Tanggal Terbit')
    expiry_date = fields.Date(string='Masa Berlaku / Expiry', tracking=True)
    days_to_expiry = fields.Integer(string='Sisa Hari Berlaku', compute='_compute_days_to_expiry')
    is_expired = fields.Boolean(string='Kedaluwarsa', compute='_compute_is_expired', store=True)
    attachment_file = fields.Binary(string='File Dokumen (PDF/Scan)', required=True)
    file_name = fields.Char(string='Nama File')
    notes = fields.Text(string='Catatan / Keterangan')
    company_id = fields.Many2one(related='property_id.company_id', store=True)

    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for rec in self:
            if rec.expiry_date:
                rec.days_to_expiry = (rec.expiry_date - today).days
            else:
                rec.days_to_expiry = 99999

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = bool(rec.expiry_date and rec.expiry_date < today)

    @api.model
    def _cron_check_document_expiry(self):
        today = fields.Date.today()
        docs = self.search([('expiry_date', '!=', False)])
        activity_type = self.env.ref('mail.mail_activity_data_warning', raise_if_not_found=False) or                         self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)

        for doc in docs:
            days = (doc.expiry_date - today).days
            if days in (90, 60, 30, 14, 7, 0) or (days < 0 and days > -30):
                msg = _(
                    "⚠️ <b>PERINGATAN JATUH TEMPO PERIZINAN GEDUNG:</b><br/>"
                    "Dokumen: <b>%s</b> (%s)<br/>"
                    "Nomor: %s<br/>"
                    "Gedung: %s<br/>"
                    "Masa Berlaku s.d.: <b>%s</b> (%d hari lagi).<br/>"
                    "Harap segera memproses perpanjangan perizinan ke instansi terkait."
                ) % (doc.name, dict(doc._fields['document_type'].selection).get(doc.document_type),
                     doc.document_number or '-', doc.property_id.name, doc.expiry_date, days)

                doc.message_post(body=msg)
                if doc.property_id:
                    doc.property_id.message_post(body=msg)

                user_to_assign = doc.property_id.property_manager_id or self.env.user
                if activity_type and user_to_assign:
                    existing_act = self.env['mail.activity'].search([
                        ('res_model', '=', 'property.legal.document'),
                        ('res_id', '=', doc.id),
                        ('user_id', '=', user_to_assign.id),
                        ('date_deadline', '=', doc.expiry_date),
                    ], limit=1)
                    if not existing_act:
                        self.env['mail.activity'].create({
                            'activity_type_id': activity_type.id,
                            'summary': f"Perpanjangan Izin: {doc.name} (H-{days})",
                            'note': msg,
                            'date_deadline': doc.expiry_date,
                            'res_model_id': self.env['ir.model']._get_id('property.legal.document'),
                            'res_id': doc.id,
                            'user_id': user_to_assign.id,
                        })


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
