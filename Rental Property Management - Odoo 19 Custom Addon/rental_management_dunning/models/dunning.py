import urllib.parse
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyDunningLevel(models.Model):
    _name = 'property.dunning.level'
    _description = 'Dunning Level'
    _order = 'days_overdue, id'

    name = fields.Char(required=True)
    level = fields.Integer(string='Level', required=True, default=1)
    days_overdue = fields.Integer(string='Days Overdue', required=True)
    send_email = fields.Boolean(string='Send Email', default=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template',
                                       domain="[('model', '=', 'account.move')]")
    late_fee_type = fields.Selection([
        ('none', 'No Late Fee'),
        ('fixed', 'Fixed Amount'),
        ('percent', 'Flat % on Residual'),
        ('weekly_percent', 'Weekly % (e.g. 2%/week)'),
        ('daily_permil', 'Daily ‰ (e.g. 1‰/day)'),
    ], string='Late Fee Type', default='weekly_percent', required=True)
    late_fee_percent = fields.Float(string='Late Fee Rate (% or ‰)', default=2.0,
                                    help="For % types: 2.0 = 2%. For daily ‰ type: 1.0 = 1‰ (0.1% per day).")
    late_fee_fixed = fields.Monetary(string='Late Fee (Fixed)')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    active = fields.Boolean(default=True)


class AccountMoveDunning(models.Model):
    _inherit = 'account.move'

    dunning_level = fields.Integer(string='Dunning Level', default=0, copy=False)
    dunning_date = fields.Date(string='Last Dunning Date', copy=False)

    def action_send_whatsapp(self):
        self.ensure_one()
        raw_phone = self.partner_id.mobile or self.partner_id.phone
        if not raw_phone:
            raise UserError(self.env._("Nomor telepon/WhatsApp tenant (%s) belum terisi pada master partner.") % self.partner_id.name)
        
        # Clean phone number (e.g. 0812... -> 62812...)
        phone = "".join(filter(str.isdigit, raw_phone))
        if phone.startswith('0'):
            phone = '62' + phone[1:]

        partner_name = self.partner_id.name or 'Bapak/Ibu'
        inv_name = self.name or '-'
        due_date = self.invoice_date_due.strftime('%d/%m/%Y') if self.invoice_date_due else '-'
        currency_symbol = self.currency_id.symbol or 'Rp'
        residual = f"{currency_symbol} {self.amount_residual:,.2f}"
        company_name = self.company_id.name or 'Building Management'

        msg = (
            f"Halo {partner_name},\n\n"
            f"Kami dari *{company_name}* menginformasikan tagihan sewa/utilitas Anda:\n"
            f"📄 *No. Invoice:* {inv_name}\n"
            f"📅 *Jatuh Tempo:* {due_date}\n"
            f"💰 *Sisa Tagihan:* {residual}\n"
        )
        if self.dunning_level > 0:
            msg += f"⚠️ *Status:* Surat Peringatan (SP-{self.dunning_level})\n"
        
        msg += (
            f"\nMohon dapat segera melakukan pembayaran untuk menghindari denda keterlambatan atau penghentian fasilitas layanan.\n"
            f"Terima kasih atas kerja samanya."
        )

        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_msg}"

        return {
            'type': 'ir.actions.act_url',
            'url': wa_url,
            'target': 'new',
        }


    def _apply_dunning_level(self, level):
        self.ensure_one()
        if level.send_email and level.mail_template_id:
            level.mail_template_id.send_mail(self.id, force_send=False)
        # Calculate late fee based on selected type
        days = (fields.Date.today() - self.invoice_date_due).days if self.invoice_date_due else level.days_overdue
        days = max(1, days)
        residual = self.amount_residual or 0.0
        fee = level.late_fee_fixed or 0.0

        if level.late_fee_type == 'weekly_percent':
            weeks = max(1, days // 7)
            fee += residual * (level.late_fee_percent or 2.0) / 100.0 * weeks
        elif level.late_fee_type == 'daily_permil':
            fee += residual * ((level.late_fee_percent or 1.0) / 1000.0) * days
        elif level.late_fee_type == 'percent':
            fee += residual * (level.late_fee_percent or 0.0) / 100.0
        elif level.late_fee_type == 'fixed':
            fee += 0.0  # already added fixed amount

        if fee > 0:
            product = self.env.ref('rental_management_dunning.product_late_fee',
                                   raise_if_not_found=False)
            if product:
                vals = {
                    'move_type': 'out_invoice',
                    'partner_id': self.partner_id.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': self.env._('Late payment fee for %s (Level %s - %s days)') % (
                            self.name, level.level, days),
                        'quantity': 1.0,
                        'price_unit': round(fee, 2),
                    })],
                }
                if self.tenancy_id and 'tenancy_id' in self._fields:
                    vals['tenancy_id'] = self.tenancy_id.id
                elif 'property_manual_id' in self._fields and self.property_financial_id:
                    vals['property_manual_id'] = self.property_financial_id.id
                self.env['account.move'].create(vals)
        self.dunning_level = level.level
        self.dunning_date = fields.Date.today()
        self.message_post(body=self.env._("Dunning level %s (%s) applied.") % (level.level, level.name))

        # PDF 2 item 75: Auto-flag or notify for unit sealing on SP3 (level >= 3)
        if level.level >= 3 and self.tenancy_id:
            self.tenancy_id.message_post(body=self.env._(
                "🚨 SP 3 / Peringatan Terakhir aktif untuk invoice %s. Unit direkomendasikan untuk DISEGEL / DIBLOKIR LAYANAN.") % self.name)

    @api.model
    def _cron_run_dunning(self):
        today = fields.Date.context_today(self)
        levels = self.env['property.dunning.level'].search([])
        if not levels:
            return True
        overdue = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '!=', False),
            ('invoice_date_due', '<', today),
        ])
        for move in overdue:
            days = (today - move.invoice_date_due).days
            matched = levels.filtered(lambda l: days >= l.days_overdue)
            if not matched:
                continue
            top = max(matched, key=lambda l: l.level)
            if top.level > (move.dunning_level or 0):
                move._apply_dunning_level(top)
        return True


class TenancyDetailsDunning(models.Model):
    _inherit = 'tenancy.details'

    is_sealed = fields.Boolean(string='Unit Disegel / Layanan Diblokir', default=False, tracking=True, copy=False)
    sealed_date = fields.Date(string='Tanggal Penyegelan', copy=False)
    sealed_reason = fields.Char(string='Alasan Penyegelan', copy=False)
    sealed_by_id = fields.Many2one('res.users', string='Petugas Penyegelan', copy=False)

    def action_seal_unit(self):
        for rec in self:
            rec.write({
                'is_sealed': True,
                'sealed_date': fields.Date.today(),
                'sealed_reason': rec.sealed_reason or self.env._('Tunggakan pembayaran sewa / SP 3 Dunning'),
                'sealed_by_id': self.env.user.id,
            })
            if rec.property_id and 'is_sealed' in rec.property_id._fields:
                rec.property_id.is_sealed = True
            rec.message_post(body=self.env._(
                "🚨 <b>UNIT DISEGEL / LAYANAN DIBLOKIR</b><br/>"
                "Alasan: %s<br/>Petugas: %s<br/>Tanggal: %s") % (
                    rec.sealed_reason or 'Tunggakan sewa', self.env.user.name, fields.Date.today()))
        return True

    def action_unseal_unit(self):
        for rec in self:
            rec.write({
                'is_sealed': False,
                'sealed_date': False,
                'sealed_reason': False,
                'sealed_by_id': False,
            })
            if rec.property_id and 'is_sealed' in rec.property_id._fields:
                rec.property_id.is_sealed = False
            rec.message_post(body=self.env._(
                "✅ <b>SEGEL UNIT DIBUKA / LAYANAN DIAKTIFKAN KEMBALI</b> oleh %s.") % self.env.user.name)
        return True


class PropertyDetailsDunning(models.Model):
    _inherit = 'property.details'

    is_sealed = fields.Boolean(string='Unit Disegel', default=False, tracking=True, copy=False)

