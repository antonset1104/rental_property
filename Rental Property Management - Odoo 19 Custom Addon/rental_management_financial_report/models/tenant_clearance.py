# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyTenantClearance(models.Model):
    _name = 'property.tenant.clearance'
    _description = 'Surat Bebas Kewajiban & Serah Terima Pengakhiran Sewa (Tenant Clearance)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='No. Clearance', required=True, readonly=True, default='Baru', copy=False, tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa', required=True, tracking=True)
    tenant_id = fields.Many2one('res.partner', related='tenancy_id.tenancy_id', store=True)
    property_id = fields.Many2one('property.details', related='tenancy_id.property_id', store=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)

    move_out_date = fields.Date(string='Tanggal Serah Terima Unit (Move-Out)', default=fields.Date.today, required=True, tracking=True)

    # 4 Divisional Sign-offs
    finance_status = fields.Selection([('pending', 'Tertunggak'), ('cleared', 'Lunas')], string='Persetujuan Finance (Tagihan Sewa & Utilitas)', default='pending', tracking=True)
    engineering_status = fields.Selection([('pending', 'Perlu Inspeksi'), ('cleared', 'Unit Restorasi Sesuai / Bare Condition')], string='Persetujuan Engineering (Fisik Unit & MEP)', default='pending', tracking=True)
    housekeeping_status = fields.Selection([('pending', 'Perlu Pembersihan'), ('cleared', 'Unit Bersih & Bebas Sampah')], string='Persetujuan Housekeeping', default='pending', tracking=True)
    security_status = fields.Selection([('pending', 'Belum Lengkap'), ('cleared', 'Kunci & Kartu RFID Dikembalikan')], string='Persetujuan Security & Access', default='pending', tracking=True)

    # Financial Settlement
    deposit_held = fields.Float(string='Total Jaminan Deposit Tersedia (IDR)', required=True)
    repair_deduction = fields.Float(string='Potongan Biaya Perbaikan / Kerusakan (IDR)', default=0.0)
    utility_deduction = fields.Float(string='Potongan Tunggakan Utilitas Terakhir (IDR)', default=0.0)
    deposit_refund_amount = fields.Float(string='Sisa Deposit yang Dikembalikan (IDR)', compute='_compute_deposit_refund', store=True)

    state = fields.Selection([
        ('draft', 'Dalam Proses Pemeriksaan'),
        ('approved', 'Disetujui Seluruh Divisi (Cleared)'),
        ('refunded', 'Deposit Selesai Dicairkan'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status Clearance', default='draft', tracking=True)

    @api.depends('deposit_held', 'repair_deduction', 'utility_deduction')
    def _compute_deposit_refund(self):
        for rec in self:
            rec.deposit_refund_amount = max(rec.deposit_held - (rec.repair_deduction + rec.utility_deduction), 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Baru') == 'Baru':
                seq = self.env['ir.sequence'].next_by_code('property.tenant.clearance') or 'CLR/' + fields.Date.today().strftime('%Y/%m/') + '001'
                vals['name'] = seq
        return super().create(vals_list)

    def action_clear_finance(self):
        for rec in self:
            rec.finance_status = 'cleared'
            rec.message_post(body=self.env._("✅ Divisi Finance menyetujui: Seluruh tagihan sewa & utilitas LUNAS."))
            rec._check_all_cleared()

    def action_clear_engineering(self):
        for rec in self:
            rec.engineering_status = 'cleared'
            rec.message_post(body=self.env._("✅ Divisi Engineering menyetujui: Unit telah dikembalikan ke kondisi bare/restorasi."))
            rec._check_all_cleared()

    def action_clear_housekeeping(self):
        for rec in self:
            rec.housekeeping_status = 'cleared'
            rec.message_post(body=self.env._("✅ Divisi Housekeeping menyetujui: Unit bersih & bebas sampah."))
            rec._check_all_cleared()

    def action_clear_security(self):
        for rec in self:
            rec.security_status = 'cleared'
            rec.message_post(body=self.env._("✅ Divisi Security menyetujui: Kunci & kartu RFID telah dikembalikan."))
            rec._check_all_cleared()

    def _check_all_cleared(self):
        """Automatically approve clearance once all 4 divisions have signed off."""
        self.ensure_one()
        if all([
            self.finance_status == 'cleared',
            self.engineering_status == 'cleared',
            self.housekeeping_status == 'cleared',
            self.security_status == 'cleared',
        ]):
            self.state = 'approved'
            self.message_post(body=self.env._(
                "Seluruh divisi telah menyetujui pengakhiran sewa dan "
                "Surat Bebas Kewajiban (Clearance) telah terbit."))

    def action_approve_all(self):
        """Shortcut: mark all divisions cleared at once (manager override)."""
        for rec in self:
            rec.write({
                'finance_status': 'cleared',
                'engineering_status': 'cleared',
                'housekeeping_status': 'cleared',
                'security_status': 'cleared',
                'state': 'approved',
            })
            rec.message_post(body=self.env._(
                "Seluruh divisi telah menyetujui pengakhiran sewa dan "
                "Surat Bebas Kewajiban (Clearance) telah terbit "
                "(Override oleh Manager)."))

    def action_mark_refunded(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(self.env._(
                    "Deposit hanya bisa dicairkan setelah status clearance disetujui seluruh divisi."))
            rec.state = 'refunded'
            rec.message_post(body=self.env._(
                "Pengembalian deposit sebesar Rp {:,.2f} telah selesai diproses "
                "ke rekening tenant.").format(rec.deposit_refund_amount))
