# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyAccrualTemplate(models.Model):
    """Master data: defines how a recurring expense is accrued over N months.
    User creates one template per expense type (e.g. Insurance 12 months).
    When applied to a vendor bill line, the system generates N equal accrual
    journal entries spread across the accrual period."""
    _name = 'property.accrual.template'
    _description = 'Property Expense Accrual Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    account_id = fields.Many2one('account.account', string='Accrual Account',
                                 help="Prepaid/accrual balance sheet account (e.g. Prepaid Insurance).")
    expense_account_id = fields.Many2one('account.account', string='Expense Account',
                                         help="P&L account to recognise the expense each month.")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', '=', 'general')]")
    months = fields.Integer(string='Accrual Months', default=12,
                            help="Number of months to spread the expense over.")
    category_id = fields.Many2one('property.financial.category', string='Report Category')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes = fields.Text(string='Notes')


class AccountMoveLineAccrual(models.Model):
    """Extend vendor bill lines with an optional accrual template.
    When the bill is posted, accrual journal entries are auto-generated."""
    _inherit = 'account.move.line'

    accrual_template_id = fields.Many2one(
        'property.accrual.template', string='Accrual Template',
        help="If set, posting this bill will generate monthly accrual entries "
             "spreading this line's amount over the template's accrual period.")
    accrual_start_date = fields.Date(string='Accrual Start',
                                     help="First month of the accrual period.")
    accrual_move_ids = fields.Many2many(
        'account.move', 'accrual_source_line_move_rel',
        'line_id', 'move_id', string='Accrual Entries', copy=False)

    def _generate_accrual_entries(self):
        """Generate N monthly accrual journal entries for this bill line."""
        from dateutil.relativedelta import relativedelta
        for line in self:
            tmpl = line.accrual_template_id
            if not tmpl or not line.accrual_start_date:
                continue
            if line.accrual_move_ids:
                continue  # already generated
            prop = line.move_id.property_financial_id
            journal = tmpl.journal_id or line.move_id.journal_id
            accrual_acc = tmpl.account_id
            expense_acc = tmpl.expense_account_id or line.account_id
            if not accrual_acc:
                raise UserError(
                    "Accrual template '%s' has no Accrual Account set." % tmpl.name)
            months = tmpl.months or 12
            monthly_amt = abs(line.price_subtotal) / months
            start = line.accrual_start_date
            created = self.env['account.move']
            for i in range(months):
                period_date = start + relativedelta(months=i)
                label = "%s – %s/%s" % (tmpl.name, period_date.month, period_date.year)
                move = self.env['account.move'].create({
                    'move_type': 'entry',
                    'journal_id': journal.id,
                    'date': period_date,
                    'ref': label,
                    'property_manual_id': prop.id if prop else False,
                    'line_ids': [
                        (0, 0, {'account_id': expense_acc.id,
                                'name': label, 'debit': monthly_amt, 'credit': 0.0}),
                        (0, 0, {'account_id': accrual_acc.id,
                                'name': label, 'debit': 0.0, 'credit': monthly_amt}),
                    ],
                })
                move.action_post()
                created |= move
            line.accrual_move_ids = [(6, 0, created.ids)]


class AccountMoveAccrual(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        # Call super first so lines are in posted state before generating accruals
        res = super()._post(soft=soft)
        # Only trigger on vendor bills that are now posted, not on the
        # accrual entries themselves (which are also 'entry' type, not in_invoice)
        for move in self.filtered(
                lambda m: m.move_type in ('in_invoice', 'in_refund')
                and m.state == 'posted'):
            move.line_ids.filtered(
                lambda l: l.accrual_template_id and l.accrual_start_date
                and not l.accrual_move_ids
            )._generate_accrual_entries()
        return res
