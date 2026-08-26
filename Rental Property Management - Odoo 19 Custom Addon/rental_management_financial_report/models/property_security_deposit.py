# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertySecurityDeposit(models.Model):
    """Tracks a tenant security deposit as a HELD LIABILITY (not income),
    with deductions and refunds, and surfaces the running balance as the
    'Sec Dep Bal' column on the Owners Statement Tenant Balances."""
    _name = 'property.security.deposit'
    _description = 'Tenant Security Deposit'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    tenancy_id = fields.Many2one('tenancy.details', string='Contract',
                                 required=True, tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    company_id = fields.Many2one(related='tenancy_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    date = fields.Date(string='Received Date', default=fields.Date.today,
                       required=True, tracking=True)
    deposit_type = fields.Selection([
        ('security', 'Security Deposit (Sewa Unit)'),
        ('fitout', 'Fit-Out / Renovation Deposit'),
        ('utility', 'Utility Deposit (Listrik/Air)'),
        ('access_card', 'Access Card Deposit'),
        ('other', 'Deposit Lainnya'),
    ], string='Tipe Deposit', default='security', required=True, tracking=True)
    amount = fields.Monetary(string='Deposit Held', tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('held', 'Held'),
                              ('closed', 'Closed')], default='draft', tracking=True)
    line_ids = fields.One2many('property.security.deposit.line', 'deposit_id',
                               string='Deductions / Refunds')
    receipt_move_id = fields.Many2one('account.move', string='Receipt Entry',
                                      readonly=True, copy=False)
    deducted_amount = fields.Monetary(compute='_compute_balance', store=True)
    refunded_amount = fields.Monetary(compute='_compute_balance', store=True)
    balance = fields.Monetary(string='Deposit Balance', compute='_compute_balance',
                              store=True)

    # PDF 2 item 32 & 66: Fit-Out / Renovation Deposit Inspection Checklist
    fitout_completion_date = fields.Date(string='Tgl Selesai Renovasi')
    fitout_inspection_passed = fields.Boolean(string='Inspeksi Akhir Fit-Out Lolos', tracking=True)
    fitout_damage_notes = fields.Text(string='Catatan Kerusakan Struktur / MEP')

    # PDF 2 item 66: BAST & 30-Day SLA Settlement Tracking
    bast_date = fields.Date(string='Tanggal BAST Selesai (Move-out)', tracking=True,
                            help="Tanggal BAST pengosongan unit & kelengkapan dokumen move-out ditandatangani.")
    bast_attachment = fields.Binary(string='Dokumen BAST / Checklist')
    bast_filename = fields.Char(string='Nama File BAST')
    sla_deadline = fields.Date(string='Tenggat SLA Refund (30 Hari)', compute='_compute_sla', store=True,
                               help="Batas maksimal 30 hari kalender setelah BAST ditandatangani.")
    sla_days_left = fields.Integer(string='Sisa Hari SLA', compute='_compute_sla')
    sla_status = fields.Selection([
        ('no_bast', 'Menunggu BAST'),
        ('on_track', 'SLA Berjalan (Aman)'),
        ('warning', 'Mendekati Batas (≤ 7 Hari)'),
        ('overdue', 'Melewati Batas SLA 30 Hari'),
    ], string='Status SLA Refund', compute='_compute_sla', store=True, tracking=True)

    @api.depends('bast_date', 'state', 'balance')
    def _compute_sla(self):
        from datetime import timedelta
        today = fields.Date.today()
        for rec in self:
            if not rec.bast_date:
                rec.sla_deadline = False
                rec.sla_days_left = 0
                rec.sla_status = 'no_bast'
            else:
                deadline = rec.bast_date + timedelta(days=30)
                rec.sla_deadline = deadline
                days_left = (deadline - today).days
                rec.sla_days_left = days_left
                if rec.state == 'closed' or (rec.balance or 0.0) <= 0.0:
                    rec.sla_status = 'on_track'
                elif days_left < 0:
                    rec.sla_status = 'overdue'
                elif days_left <= 7:
                    rec.sla_status = 'warning'
                else:
                    rec.sla_status = 'on_track'

    def action_confirm_bast(self):
        for rec in self:
            if not rec.bast_date:
                rec.bast_date = fields.Date.today()
            rec.message_post(body=self.env._(
                "📋 <b>BAST Move-out Selesai & Ditandatangani</b> pada %s.<br/>"
                "⏳ Tenggat waktu SLA pengembalian security deposit (30 hari): <b>%s</b>.") % (
                    rec.bast_date, rec.sla_deadline))
        return True

    @api.depends('amount', 'line_ids.amount', 'line_ids.line_type')
    def _compute_balance(self):
        for rec in self:
            ded = sum(l.amount for l in rec.line_ids if l.line_type == 'deduction')
            ref = sum(l.amount for l in rec.line_ids if l.line_type == 'refund')
            rec.deducted_amount = ded
            rec.refunded_amount = ref
            rec.balance = (rec.amount or 0.0) - ded - ref

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.security.deposit') or '/'
        return super().create(vals_list)

    def _deposit_move(self, debit_account, credit_account, amount, label, partner=False):
        prop = self.property_id
        journal = prop.deposit_journal_id or prop.remittance_journal_id
        if not journal:
            raise UserError(self.env._(
                "Set a Deposit/Remittance Journal on property '%s'.") % prop.name)
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'ref': label,
            'property_manual_id': prop.id,
            'line_ids': [
                (0, 0, {'account_id': debit_account.id, 'partner_id': partner and partner.id or False,
                        'name': label, 'debit': amount, 'credit': 0.0}),
                (0, 0, {'account_id': credit_account.id, 'partner_id': partner and partner.id or False,
                        'name': label, 'debit': 0.0, 'credit': amount}),
            ],
        })
        move.action_post()
        return move

    def action_hold(self):
        for rec in self:
            rec.state = 'held'
            prop = rec.property_id
            # Optional GL posting: Dr Trust Bank / Cr Deposit Liability
            if (rec.amount and not rec.receipt_move_id and prop.trust_account_id
                    and prop.deposit_liability_account_id):
                rec.receipt_move_id = rec._deposit_move(
                    prop.trust_account_id, prop.deposit_liability_account_id,
                    rec.amount, self.env._('Security deposit received %s') % rec.name,
                    partner=rec.tenant_id)
        return True

    def action_post_lines(self):
        """Post GL entries for any deduction/refund line not yet posted."""
        for rec in self:
            prop = rec.property_id
            liab = prop.deposit_liability_account_id
            if not liab:
                # Try finding a current liability account as fallback
                liab = self.env['account.account'].search([
                    ('company_id', '=', rec.company_id.id),
                    ('account_type', 'in', ('liability_current', 'liability_non_current')),
                ], limit=1)
                if not liab:
                    raise UserError(self.env._(
                        "Harap konfigurasikan 'Deposit Liability Account' pada master properti '%s' atau Chart of Accounts.") % prop.name)

            posted_count = 0
            for line in rec.line_ids.filtered(lambda l: not l.move_id and l.amount):
                if line.line_type == 'refund':
                    bank_acc = prop.trust_account_id
                    if not bank_acc:
                        bank_acc = self.env['account.account'].search([
                            ('company_id', '=', rec.company_id.id),
                            ('account_type', '=', 'asset_cash'),
                        ], limit=1)
                    if not bank_acc:
                        raise UserError(self.env._(
                            "Harap konfigurasikan 'Trust Bank Account' pada properti '%s' untuk jurnal pengembalian refund.") % prop.name)
                    # Dr Deposit Liability / Cr Trust Bank
                    line.move_id = rec._deposit_move(
                        liab, bank_acc, line.amount,
                        self.env._('Deposit refund %s - %s') % (rec.name, line.name or 'Pengembalian Deposit'),
                        partner=rec.tenant_id)
                    posted_count += 1
                elif line.line_type == 'deduction':
                    income_acc = prop.deposit_income_account_id
                    if not income_acc:
                        income_acc = self.env['account.account'].search([
                            ('company_id', '=', rec.company_id.id),
                            ('account_type', 'in', ('income', 'income_other')),
                        ], limit=1)
                    if not income_acc:
                        raise UserError(self.env._(
                            "Harap konfigurasikan 'Deposit Income / Forfeiture Account' pada properti '%s' untuk jurnal pemotongan deposit.") % prop.name)
                    # Dr Deposit Liability / Cr Forfeiture Income
                    line.move_id = rec._deposit_move(
                        liab, income_acc, line.amount,
                        self.env._('Deposit deduction %s - %s') % (rec.name, line.name or 'Pemotongan Kerusakan/Tunggakan'),
                        partner=rec.tenant_id)
                    posted_count += 1

            if posted_count > 0:
                rec.message_post(body=self.env._("✅ <b>%s Jurnal Settlement Deposit Berhasil Diposting</b>.") % posted_count)
        return True

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})


class PropertySecurityDepositLine(models.Model):
    _name = 'property.security.deposit.line'
    _description = 'Security Deposit Deduction / Refund'
    _order = 'date, id'

    deposit_id = fields.Many2one('property.security.deposit', required=True,
                                 ondelete='cascade')
    line_type = fields.Selection([('deduction', 'Deduction'),
                                  ('refund', 'Refund')],
                                 string='Type', required=True, default='deduction')
    date = fields.Date(string='Date', default=fields.Date.today)
    amount = fields.Monetary(string='Amount')
    reason = fields.Char(string='Reason')
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    currency_id = fields.Many2one(related='deposit_id.currency_id')
    company_id = fields.Many2one(related='deposit_id.company_id', store=True)
