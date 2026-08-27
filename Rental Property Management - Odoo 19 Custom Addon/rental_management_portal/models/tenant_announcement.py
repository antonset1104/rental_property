# -*- coding: utf-8 -*-
import urllib.parse
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyTenantAnnouncement(models.Model):
    _name = 'property.tenant.announcement'
    _description = 'Pengumuman Gedung untuk Tenant (Building Broadcast)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'publish_date desc, id desc'

    title = fields.Char(string='Judul Pengumuman', required=True, tracking=True)
    announcement_type = fields.Selection([
        ('general', 'Pengumuman Umum'),
        ('maintenance', 'Pemeliharaan Gedung / MEP / Lift / Genset'),
        ('fire_drill', 'Simulasi Kebakaran & Keselamatan (Fire Drill)'),
        ('pest_control', 'Pest Control & Fogging Nyamuk'),
        ('holiday', 'Penyesuaian Jam Operasional Libur'),
        ('emergency', 'Pemberitahuan Darurat (Emergency)'),
    ], string='Kategori Pengumuman', default='general', required=True, tracking=True)

    publish_date = fields.Date(string='Tanggal Tayang', default=fields.Date.today,
                               required=True, tracking=True)
    expiry_date = fields.Date(string='Tanggal Berakhir', required=True, tracking=True)
    content = fields.Text(string='Isi Lengkap Pengumuman', required=True)
    target_property_ids = fields.Many2many('property.details', string='Gedung / Properti Target',
                                           help="Pilih gedung tujuan. Kosongkan untuk broadcast ke seluruh gedung.")
    company_id = fields.Many2one('res.company', string='Perusahaan / PT',
                                 default=lambda s: s.env.company)
    is_published = fields.Boolean(string='Tayang di Portal Tenant', default=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Dipublikasikan'),
        ('archived', 'Diarsipkan / Kedaluwarsa'),
    ], string='Status Pengumuman', default='draft', tracking=True)

    def action_publish(self):
        for rec in self:
            rec.state = 'published'
            rec.is_published = True
            rec.message_post(body=self.env._("Pengumuman telah dipublikasikan ke Portal Mandiri Tenant."))

    def action_archive(self):
        for rec in self:
            rec.state = 'archived'
            rec.is_published = False
            rec.message_post(body=self.env._("Pengumuman telah diarsipkan."))

    def action_send_whatsapp_broadcast(self):
        self.ensure_one()
        type_labels = {
            'general': '📢 PENGUMUMAN PENGELOLA GEDUNG',
            'maintenance': '⚡ PEMBERITAHUAN PEMELIHARAAN GEDUNG (MEP)',
            'fire_drill': '🚨 SIMULASI EVAKUASI KEBAKARAN (FIRE DRILL)',
            'pest_control': '🌿 PEMBERITAHUAN PEST CONTROL & FOGGING',
            'holiday': '🏖️ PEMBERITAHUAN OPERASIONAL HARI LIBUR',
            'emergency': '⚠️ PEMBERITAHUAN DARURAT (EMERGENCY)',
        }
        header_txt = type_labels.get(self.announcement_type, '📢 PENGUMUMAN RESMI')
        msg = f"""*{header_txt}*
*Gedung:* {self.env.company.name}
*Judul:* {self.title}
*Tanggal:* {self.publish_date}

{self.content}

_Building Management Division - {self.env.company.name}_"""

        encoded_msg = urllib.parse.quote(msg)
        return {
            'type': 'ir.actions.act_url',
            'url': f'https://wa.me/?text={encoded_msg}',
            'target': 'new',
        }
