# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyAsset(models.Model):
    _name = 'property.asset'
    _description = 'Property Fixed Asset'
    _inherit = ['mail.thread']
    _order = 'acquisition_date desc, id desc'

    name = fields.Char(string='Asset', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Vendor')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running'),
                              ('closed', 'Closed')], default='draft', tracking=True)

    acquisition_date = fields.Date(string='Acquisition Date',
                                   default=fields.Date.today, required=True)
    acquisition_value = fields.Monetary(string='Acquisition Value', tracking=True)
    salvage_value = fields.Monetary(string='Salvage Value')
    method = fields.Selection([('linear', 'Straight Line'),
                               ('declining', 'Declining Balance')],
                              string='Method', default='linear', required=True)
    method_number = fields.Integer(string='Number of Depreciations', default=5)
    method_period = fields.Integer(string='Period Length (months)', default=12)
    declining_factor = fields.Float(string='Declining Factor', default=2.0)

    # CORETAX L9 metadata
    asset_code = fields.Char(string='Asset Code (L9)')
    asset_group = fields.Char(string='Asset Group (L9)')

    # Accounts
    account_asset_id = fields.Many2one('account.account', string='Asset Account')
    account_depreciation_id = fields.Many2one(
        'account.account', string='Accumulated Depreciation Account')
    account_expense_id = fields.Many2one(
        'account.account', string='Depreciation Expense Account')
    account_revaluation_id = fields.Many2one(
        'account.account', string='Revaluation Reserve Account')
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', '=', 'general')]")

    depreciation_line_ids = fields.One2many('property.asset.depreciation.line',
                                            'asset_id', string='Depreciation Board')
    revaluation_line_ids = fields.One2many('property.asset.revaluation.line',
                                           'asset_id', string='Revaluations')

    revaluation_total = fields.Monetary(compute='_compute_values', store=True)
    depreciated_total = fields.Monetary(compute='_compute_values', store=True)
    gross_value = fields.Monetary(compute='_compute_values', store=True)
    book_value = fields.Monetary(compute='_compute_values', store=True)

    @api.depends('acquisition_value', 'revaluation_line_ids.amount',
                 'revaluation_line_ids.posted',
                 'depreciation_line_ids.depreciation_amount',
                 'depreciation_line_ids.state')
    def _compute_values(self):
        for asset in self:
            rev = sum(r.amount for r in asset.revaluation_line_ids if r.posted)
            dep = sum(l.depreciation_amount for l in asset.depreciation_line_ids
                      if l.state == 'posted')
            asset.revaluation_total = rev
            asset.depreciated_total = dep
            asset.gross_value = (asset.acquisition_value or 0.0) + rev
            asset.book_value = asset.gross_value - dep

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.asset') or '/'
        return super().create(vals_list)

    # ---- board generation -------------------------------------------------
    def action_generate_board(self):
        for asset in self:
            posted = asset.depreciation_line_ids.filtered(
                lambda l: l.state == 'posted').sorted('date')
            asset.depreciation_line_ids.filtered(
                lambda l: l.state != 'posted').unlink()
            if asset.method_number <= 0:
                continue
            posted_count = len(posted)
            accumulated = sum(posted.mapped('depreciation_amount'))
            remaining_periods = asset.method_number - posted_count
            depreciable_left = (asset.gross_value - asset.salvage_value) - accumulated
            if remaining_periods <= 0 or depreciable_left <= 0:
                continue
            last_date = posted[-1].date if posted else asset.acquisition_date
            new_lines = []
            for i in range(1, remaining_periods + 1):
                if asset.method == 'linear':
                    amt = round(depreciable_left / remaining_periods, 2)
                else:
                    rate = (asset.declining_factor / asset.method_number) \
                        if asset.method_number else 0.0
                    book_remaining = asset.gross_value - accumulated
                    amt = round(max(book_remaining - asset.salvage_value, 0.0) * rate, 2)
                if i == remaining_periods:  # final line absorbs rounding
                    amt = round((asset.gross_value - asset.salvage_value) - accumulated, 2)
                accumulated += amt
                new_lines.append((0, 0, {
                    'sequence': posted_count + i,
                    'date': last_date + relativedelta(months=asset.method_period * i),
                    'depreciation_amount': amt,
                    'accumulated_value': accumulated,
                    'remaining_value': asset.gross_value - accumulated,
                    'state': 'draft',
                }))
            asset.depreciation_line_ids = new_lines
        return True

    def action_confirm(self):
        for asset in self:
            if not asset.depreciation_line_ids:
                asset.action_generate_board()
            asset.state = 'running'

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    # ---- posting ----------------------------------------------------------
    def _check_accounts(self):
        self.ensure_one()
        if not (self.account_expense_id and self.account_depreciation_id
                and self.journal_id):
            raise UserError(self.env._(
                "Set Depreciation Expense, Accumulated Depreciation accounts and "
                "a Journal on asset '%s'.") % self.name)

    def _move_property_vals(self):
        vals = {}
        if 'property_manual_id' in self.env['account.move']._fields and self.property_id:
            vals['property_manual_id'] = self.property_id.id
        return vals

    def _post_depreciation_line(self, line):
        self.ensure_one()
        self._check_accounts()
        move_vals = {
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': line.date,
            'ref': self.env._('Depreciation %s') % self.name,
            'line_ids': [
                (0, 0, {'account_id': self.account_expense_id.id,
                        'name': self.env._('Depreciation %s') % self.name,
                        'debit': line.depreciation_amount, 'credit': 0.0}),
                (0, 0, {'account_id': self.account_depreciation_id.id,
                        'name': self.env._('Depreciation %s') % self.name,
                        'debit': 0.0, 'credit': line.depreciation_amount}),
            ],
        }
        move_vals.update(self._move_property_vals())
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        line.move_id = move.id
        line.state = 'posted'

    def action_post_depreciation(self):
        """Post all due (date <= today) draft depreciation lines."""
        today = fields.Date.context_today(self)
        for asset in self.filtered(lambda a: a.state == 'running'):
            for line in asset.depreciation_line_ids.filtered(
                    lambda l: l.state == 'draft' and l.date and l.date <= today):
                asset._post_depreciation_line(line)
        return True

    @api.model
    def _cron_post_depreciation(self):
        assets = self.search([('state', '=', 'running')])
        assets.action_post_depreciation()
        return True

    # ---- revaluation ------------------------------------------------------
    def action_post_revaluations(self):
        for asset in self:
            if not (asset.account_asset_id and asset.account_revaluation_id
                    and asset.journal_id):
                raise UserError(asset.env._(
                    "Set Asset Account, Revaluation Reserve Account and a Journal "
                    "on asset '%s'.") % asset.name)
            posted_any = False
            for rev in asset.revaluation_line_ids.filtered(
                    lambda r: not r.posted and r.amount):
                amt = rev.amount
                if amt > 0:  # upward: Dr Asset / Cr Revaluation Reserve
                    lines = [
                        (0, 0, {'account_id': asset.account_asset_id.id,
                                'name': rev.reason or 'Revaluation',
                                'debit': amt, 'credit': 0.0}),
                        (0, 0, {'account_id': asset.account_revaluation_id.id,
                                'name': rev.reason or 'Revaluation',
                                'debit': 0.0, 'credit': amt}),
                    ]
                else:  # downward
                    lines = [
                        (0, 0, {'account_id': asset.account_revaluation_id.id,
                                'name': rev.reason or 'Revaluation',
                                'debit': -amt, 'credit': 0.0}),
                        (0, 0, {'account_id': asset.account_asset_id.id,
                                'name': rev.reason or 'Revaluation',
                                'debit': 0.0, 'credit': -amt}),
                    ]
                move_vals = {
                    'move_type': 'entry', 'journal_id': asset.journal_id.id,
                    'date': rev.date or fields.Date.today(),
                    'ref': asset.env._('Revaluation %s') % asset.name,
                    'line_ids': lines,
                }
                move_vals.update(asset._move_property_vals())
                move = asset.env['account.move'].create(move_vals)
                move.action_post()
                rev.move_id = move.id
                rev.posted = True
                posted_any = True
            if posted_any:
                # prospective: spread the new book value over remaining periods
                asset.action_generate_board()
        return True

    # ---- CORETAX L9 sync --------------------------------------------------
    def action_sync_coretax_l9(self):
        if 'coretax.asset.depreciation' not in self.env:
            raise UserError(self.env._("The CORETAX module is not installed."))
        Reg = self.env['coretax.asset.depreciation']
        today = fields.Date.context_today(self)
        for asset in self:
            year = today.year
            dep_this_year = sum(
                l.depreciation_amount for l in asset.depreciation_line_ids
                if l.state == 'posted' and l.date and l.date.year == year)
            Reg.create({
                'kind': 'depreciation',
                'tax_year': year,
                'code_of_asset': asset.asset_code or '',
                'group_of_asset': asset.asset_group or '',
                'month_of_acquisition': asset.acquisition_date.month if asset.acquisition_date else 0,
                'year_of_acquisition': asset.acquisition_date.year if asset.acquisition_date else 0,
                'acquisition_price': asset.gross_value,
                'remaining_value': asset.book_value,
                'commercial_method': 'GL' if asset.method == 'linear' else 'SM',
                'fiscal_method': 'GL' if asset.method == 'linear' else 'SM',
                'fiscal_depreciation_this_year': dep_this_year,
                'notes': asset.name,
                'company_id': asset.company_id.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('CORETAX L9'),
            'res_model': 'coretax.asset.depreciation',
            'view_mode': 'list,form',
        }


class PropertyAssetDepreciationLine(models.Model):
    _name = 'property.asset.depreciation.line'
    _description = 'Asset Depreciation Line'
    _order = 'sequence, date, id'

    asset_id = fields.Many2one('property.asset', required=True, ondelete='cascade')
    sequence = fields.Integer(default=1)
    date = fields.Date(string='Date')
    depreciation_amount = fields.Monetary(string='Depreciation')
    accumulated_value = fields.Monetary(string='Accumulated')
    remaining_value = fields.Monetary(string='Remaining')
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')],
                             default='draft')
    currency_id = fields.Many2one(related='asset_id.currency_id')
    company_id = fields.Many2one(related='asset_id.company_id', store=True)


class PropertyAssetRevaluationLine(models.Model):
    _name = 'property.asset.revaluation.line'
    _description = 'Asset Revaluation Line'
    _order = 'date, id'

    asset_id = fields.Many2one('property.asset', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.today)
    amount = fields.Monetary(string='Adjustment (+/-)',
                             help="Positive for upward revaluation, negative for "
                                  "downward.")
    reason = fields.Char(string='Reason')
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    posted = fields.Boolean(string='Posted')
    currency_id = fields.Many2one(related='asset_id.currency_id')
    company_id = fields.Many2one(related='asset_id.company_id', store=True)
