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
        """Post GL entries for any deduction/refund line not yet posted
        (only if the relevant accounts are configured)."""
        for rec in self:
            prop = rec.property_id
            liab = prop.deposit_liability_account_id
            for line in rec.line_ids.filtered(lambda l: not l.move_id and l.amount):
                if not liab:
                    continue
                if line.line_type == 'refund' and prop.trust_account_id:
                    # Dr Deposit Liability / Cr Trust Bank
                    line.move_id = rec._deposit_move(
                        liab, prop.trust_account_id, line.amount,
                        self.env._('Deposit refund %s') % rec.name,
                        partner=rec.tenant_id)
                elif line.line_type == 'deduction' and prop.deposit_income_account_id:
                    # Dr Deposit Liability / Cr Forfeiture Income
                    line.move_id = rec._deposit_move(
                        liab, prop.deposit_income_account_id, line.amount,
                        self.env._('Deposit deduction %s') % rec.name,
                        partner=rec.tenant_id)
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
