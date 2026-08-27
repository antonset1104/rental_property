# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyFacility(models.Model):
    _name = 'property.facility'
    _description = 'Fasilitas Bersama Gedung (Function Room & Facilities)'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nama Fasilitas', required=True, tracking=True)
    code = fields.Char(string='Kode Fasilitas', required=True)
    property_id = fields.Many2one('property.details', string='Gedung / Properti', required=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)
    facility_type = fields.Selection([
        ('meeting', 'Ruang Rapat (Meeting Room)'),
        ('ballroom', 'Ballroom / Function Hall'),
        ('atrium', 'Area Promosi Atrium Mall'),
        ('rooftop', 'Rooftop Lounge / Garden'),
        ('loading_bay', 'Loading Dock Khusus'),
    ], string='Kategori Fasilitas', default='meeting', required=True)

    capacity = fields.Integer(string='Kapasitas (Orang)')
    hourly_rate = fields.Float(string='Tarif Sewa per Jam (IDR)', default=0.0)
    daily_rate = fields.Float(string='Tarif Sewa per Hari (IDR)', default=0.0)
    cleaning_deposit = fields.Float(string='Deposit Kebersihan (IDR)', default=0.0)
    description = fields.Text(string='Fasilitas & Kelengkapan (Proyektor, Sound, Wi-Fi)')


class PropertyFacilityBooking(models.Model):
    _name = 'property.facility.booking'
    _description = 'Pemesanan Ruang Rapat & Fasilitas Gedung'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'booking_date desc, id desc'

    name = fields.Char(string='Kode Booking', required=True, readonly=True, default='Baru', copy=False)
    facility_id = fields.Many2one('property.facility', string='Fasilitas', required=True, tracking=True)
    property_id = fields.Many2one('property.details', related='facility_id.property_id', store=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)

    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa Tenant (Opsional)')
    partner_id = fields.Many2one('res.partner', string='Nama Pemesan (Tenant / Umum)', required=True, tracking=True)

    booking_date = fields.Date(string='Tanggal Pemakaian', required=True, tracking=True)
    time_slot = fields.Selection([
        ('morning', 'Pagi Hari (08:00 - 12:00)'),
        ('afternoon', 'Siang Hari (13:00 - 17:00)'),
        ('evening', 'Malam Hari (18:00 - 22:00)'),
        ('full_day', 'Seharian Penuh (08:00 - 22:00)'),
    ], string='Sesi Waktu', default='morning', required=True, tracking=True)

    rental_price = fields.Float(string='Biaya Sewa Fasilitas (IDR)', required=True)
    cleaning_deposit = fields.Float(string='Deposit Kebersihan (IDR)', default=0.0)
    total_amount = fields.Float(string='Total Tagihan (IDR)', compute='_compute_total_amount', store=True)

    state = fields.Selection([
        ('draft', 'Pengajuan (Draft)'),
        ('confirmed', 'Dikonfirmasi'),
        ('invoiced', 'Ditagihkan (Invoice Terbit)'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status Booking', default='draft', tracking=True)

    invoice_id = fields.Many2one('account.move', string='Faktur Tagihan', readonly=True)

    @api.depends('rental_price', 'cleaning_deposit')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.rental_price + rec.cleaning_deposit

    @api.onchange('facility_id', 'time_slot')
    def _onchange_facility_slot(self):
        if self.facility_id:
            if self.time_slot == 'full_day':
                self.rental_price = self.facility_id.daily_rate
            else:
                self.rental_price = self.facility_id.hourly_rate * 4.0
            self.cleaning_deposit = self.facility_id.cleaning_deposit

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.facility.booking') or 'BKG/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            # Check double booking
            conflict = self.search([
                ('id', '!=', rec.id),
                ('facility_id', '=', rec.facility_id.id),
                ('booking_date', '=', rec.booking_date),
                ('time_slot', 'in', (rec.time_slot, 'full_day') if rec.time_slot != 'full_day' else ('morning', 'afternoon', 'evening', 'full_day')),
                ('state', 'in', ('confirmed', 'invoiced', 'completed')),
            ], limit=1)
            if conflict:
                raise UserError(_("Jadwal bentrok! Fasilitas '%s' pada tanggal %s sesi %s sudah dipesan (%s).") % (
                    rec.facility_id.name, rec.booking_date, rec.time_slot, conflict.name))
            rec.state = 'confirmed'
            rec.message_post(body=_("Pemesanan fasilitas telah dikonfirmasi."))

    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                raise UserError(_("Invoice sudah pernah dibuat."))
            inv_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [
                    (0, 0, {
                        'name': f"Sewa Fasilitas: {rec.facility_id.name} ({rec.booking_date} {rec.time_slot})",
                        'quantity': 1.0,
                        'price_unit': rec.rental_price,
                    }),
                ]
            }
            if rec.cleaning_deposit > 0:
                inv_vals['invoice_line_ids'].append((0, 0, {
                    'name': f"Deposit Kebersihan Fasilitas ({rec.facility_id.name})",
                    'quantity': 1.0,
                    'price_unit': rec.cleaning_deposit,
                }))
            inv = self.env['account.move'].create(inv_vals)
            rec.write({'invoice_id': inv.id, 'state': 'invoiced'})
            rec.message_post(body=_("Invoice tagihan fasilitas %s telah dibuat.") % inv.name)

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            rec.message_post(body=_("Pemakaian fasilitas telah selesai."))
