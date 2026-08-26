# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyUnitInspection(models.Model):
    _name = 'property.unit.inspection'
    _description = 'Unit Inspection & BAST Digital'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='No. Dokumen BAST / Inspeksi', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    inspection_type = fields.Selection([
        ('move_in', 'Serah Terima Awal (Move-In)'),
        ('move_out', 'Pengosongan / Pengembalian (Move-Out)'),
        ('periodic', 'Inspeksi Berkala (Maintenance Audit)'),
    ], string='Jenis BAST / Inspeksi', default='move_in', required=True, tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa', required=True, tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', string='Unit Properti', store=True)
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant', store=True)
    date = fields.Date(string='Tanggal BAST / Inspeksi', required=True, default=fields.Date.today, tracking=True)
    inspector_id = fields.Many2one('res.users', string='Petugas Pemeriksa (BM/TR)',
                                   default=lambda s: s.env.user, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft Pemeriksaan Lapangan'),
        ('confirmed', 'Diverifikasi & Sah (BAST Final)'),
    ], string='Status', default='draft', tracking=True)

    # Stand Angka Meter Serah Terima
    meter_electricity = fields.Float(string='Stand Meter Listrik Serah Terima')
    meter_water = fields.Float(string='Stand Meter Air Serah Terima')
    notes = fields.Text(string='Catatan Kesimpulan / Hasil Pemeriksaan')

    line_ids = fields.One2many('property.unit.inspection.line', 'inspection_id', string='Checklist Kondisi Fisik')
    company_id = fields.Many2one(related='tenancy_id.company_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                prefix = 'BAST-IN' if vals.get('inspection_type') == 'move_in' else 'BAST-OUT'
                vals['name'] = f"{prefix}/{fields.Date.today().strftime('%Y%m')}/{self.env['ir.sequence'].next_by_code('property.unit.inspection') or '001'}"
        return super().create(vals_list)

    def action_load_default_checklist(self):
        default_items = [
            "Pintu Utama & Kunci Handle",
            "Dinding Ruangan & Cat Finishing",
            "Lantai (Keramik / Homogeneous / Vinyl)",
            "Plafon & Lampu Penerangan",
            "Unit AC & Thermostat / Remote",
            "Fire Sprinkler & Smoke Detector",
            "Sanitair & Saluran Pembuangan Air (STP)",
            "Panel MCB & Instalasi Stop Kontak Listrik",
            "Kaca Jendela & Kusen Aluminium",
            "Meteran Listrik & Air (Fisik Segel)",
        ]
        lines = []
        for item in default_items:
            lines.append((0, 0, {
                'item_name': item,
                'condition': 'good',
                'notes': 'Kondisi baik dan berfungsi normal',
            }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        self.write({'state': 'confirmed'})
        for rec in self:
            rec.message_post(body=self.env._(
                "📋 <b>BAST %s (%s) TELAH DISAHKAN</b>.<br/>"
                "Unit: %s | Tenant: %s<br/>"
                "Listrik: %s kWh | Air: %s m³") % (
                    dict(rec._fields['inspection_type'].selection).get(rec.inspection_type, ''),
                    rec.name, rec.property_id.name or '', rec.tenant_id.name or '',
                    rec.meter_electricity, rec.meter_water))
            # Auto update BAST date on security deposit if move-out
            if rec.inspection_type == 'move_out':
                deposits = self.env['property.security.deposit'].search([
                    ('tenancy_id', '=', rec.tenancy_id.id),
                    ('state', '=', 'held'),
                ])
                for dep in deposits:
                    if not dep.bast_date:
                        dep.write({'bast_date': rec.date})
                        dep.action_confirm_bast()
        return True


class PropertyUnitInspectionLine(models.Model):
    _name = 'property.unit.inspection.line'
    _description = 'Unit Inspection Checklist Line'

    inspection_id = fields.Many2one('property.unit.inspection', required=True, ondelete='cascade')
    item_name = fields.Char(string='Komponen / Bagian Fisik', required=True)
    condition = fields.Selection([
        ('good', 'Baik / Normal'),
        ('damaged', 'Cacat / Rusak'),
        ('missing', 'Hilang / Tidak Ada'),
        ('na', 'Tidak Berlaku (N/A)'),
    ], string='Kondisi Fisik', default='good', required=True)
    notes = fields.Char(string='Catatan / Keterangan')
    photo = fields.Binary(string='Foto Bukti Fisik')
    photo_name = fields.Char(string='Nama File Foto')
