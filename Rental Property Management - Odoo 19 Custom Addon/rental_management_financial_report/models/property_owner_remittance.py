# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyOwnerRemittance(models.Model):
    """A remittance of trust funds to the property owner(s). Posting creates a
    journal entry: Dr Owners Remittance / Cr Trust Bank, reducing the trust
    balance (the 'Less Remittances' line on the Owners Statement)."""
    _name = 'property.owner.remittance'
    _description = 'Owner Remittance'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, tracking=True)
    date = fields.Date(string='Remittance Date', required=True,
                       default=fields.Date.today, tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda s: s.env.company)
    currency_id = fields.Many2one(
        'res.currency', string='Remittance Currency',
        default=lambda s: s.env.company.currency_id,
        help="Currency the owners are remitted in. If different from the company "
             "currency, journal entries are converted at the remittance date rate.")
    state = fields.Selection([('draft', 'Draft'),
                              ('posted', 'Posted'),
                              ('cancel', 'Cancelled')],
                             default='draft', tracking=True)
    line_ids = fields.One2many('property.owner.remittance.line', 'remittance_id',
                               string='Owner Allocations')
    total_amount = fields.Monetary(string='Total Remittance',
                                   compute='_compute_total', store=True)
    available_for_remittance = fields.Monetary(
        string='Available (Trust Balance)', compute='_compute_available')
    move_id = fields.Many2one('account.move', string='Journal Entry',
                              readonly=True, copy=False)

    @api.depends('line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('amount'))

    @api.depends('property_id', 'date')
    def _compute_available(self):
        for rec in self:
            if rec.property_id and rec.date:
                rec.available_for_remittance = rec.property_id.trust_balance(rec.date)
            else:
                rec.available_for_remittance = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.owner.remittance') or '/'
        return super().create(vals_list)

    def action_compute_owners(self):
        """Populate allocations dari ownership yang berlaku di tanggal remittance."""
        for rec in self:
            available = rec.property_id.trust_balance(rec.date)
            rdate = rec.date or fields.Date.today()
            lines = [(5, 0, 0)]
            for owner in rec.property_id.owner_line_ids:
                if owner.date_from and owner.date_from > rdate:
                    continue
                if owner.date_to and owner.date_to < rdate:
                    continue
                pct = owner.ownership_percentage or 0.0
                lines.append((0, 0, {
                    'owner_id': owner.owner_id.id,
                    'percentage': pct,
                    'amount': round(available * pct / 100.0, 2),
                }))
            rec.line_ids = lines
        return True

    def action_post(self):
        for rec in self:
            if rec.state == 'posted':
                continue
            prop = rec.property_id
            if not (prop.trust_account_id and prop.remittance_account_id
                    and prop.remittance_journal_id):
                raise UserError(self.env._(
                    "Configure Trust Bank Account, Owners Remittance Account and "
                    "Remittance Journal on the property '%s' first.") % prop.name)
            if not rec.line_ids:
                raise UserError(self.env._("Add at least one owner allocation."))
            company = rec.company_id or self.env.company
            comp_cur = company.currency_id
            cur = rec.currency_id or comp_cur
            rdate = rec.date or fields.Date.today()
            foreign = cur != comp_cur
            move_lines = []
            total_comp = 0.0
            for line in rec.line_ids:
                if not line.amount:
                    continue
                comp_amt = cur._convert(line.amount, comp_cur, company, rdate) \
                    if foreign else line.amount
                total_comp += comp_amt
                vals = {
                    'account_id': prop.remittance_account_id.id,
                    'partner_id': line.owner_id.id,
                    'name': self.env._('Remittance to %s') % line.owner_id.display_name,
                    'debit': comp_amt, 'credit': 0.0,
                }
                if foreign:
                    vals.update(currency_id=cur.id, amount_currency=line.amount)
                move_lines.append((0, 0, vals))
            # Cr Trust Bank (total, company currency)
            trust_vals = {
                'account_id': prop.trust_account_id.id,
                'name': self.env._('Owner remittance %s') % rec.name,
                'debit': 0.0, 'credit': total_comp,
            }
            if foreign:
                trust_vals.update(currency_id=cur.id, amount_currency=-rec.total_amount)
            move_lines.append((0, 0, trust_vals))
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': prop.remittance_journal_id.id,
                'date': rec.date,
                'ref': rec.name,
                'property_manual_id': prop.id,
                'line_ids': move_lines,
            })
            move.action_post()
            rec.move_id = move.id
            rec.state = 'posted'
        return True

    def action_cancel(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.state == 'posted':
                    rec.move_id.button_draft()
                rec.move_id.unlink()
            rec.state = 'cancel'
        return True

    def action_draft(self):
        self.write({'state': 'draft'})


class PropertyOwnerRemittanceLine(models.Model):
    _name = 'property.owner.remittance.line'
    _description = 'Owner Remittance Allocation'

    remittance_id = fields.Many2one('property.owner.remittance', required=True,
                                    ondelete='cascade')
    owner_id = fields.Many2one('res.partner', string='Owner', required=True)
    percentage = fields.Float(string='Ownership %')
    amount = fields.Monetary(string='Amount')
    currency_id = fields.Many2one(related='remittance_id.currency_id')
    company_id = fields.Many2one(related='remittance_id.company_id', store=True)
