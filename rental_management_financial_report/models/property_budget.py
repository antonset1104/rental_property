# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyBudget(models.Model):
    """Per-property budget used for Actual vs Budget vs Variance on the
    Owners Statement. Budget is captured per account per month."""
    _name = 'property.budget'
    _description = 'Property Budget'
    _order = 'date_from desc, id desc'

    name = fields.Char(string='Reference', required=True, default='New', copy=False)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('cancel', 'Cancelled')],
                             default='draft', string='Status')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    line_ids = fields.One2many('property.budget.line', 'budget_id', string='Lines')

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_generate_monthly_lines(self):
        """Optional helper: explode each existing annual line into 12 monthly
        lines (annual amount / 12) for finer Actual vs Budget tracking."""
        from dateutil.relativedelta import relativedelta
        for budget in self:
            new_lines = []
            for line in budget.line_ids.filtered(lambda l: l.amount and not l.date):
                monthly = line.amount / 12.0
                cur = budget.date_from
                while cur and budget.date_to and cur <= budget.date_to:
                    new_lines.append((0, 0, {
                        'account_id': line.account_id.id,
                        'category_id': line.category_id.id,
                        'date': cur,
                        'amount': monthly,
                    }))
                    cur = cur + relativedelta(months=1)
            if new_lines:
                budget.write({'line_ids': new_lines})
        return True


class PropertyBudgetLine(models.Model):
    _name = 'property.budget.line'
    _description = 'Property Budget Line'
    _order = 'date, id'

    budget_id = fields.Many2one('property.budget', string='Budget',
                                required=True, ondelete='cascade')
    property_id = fields.Many2one(related='budget_id.property_id', store=True)
    account_id = fields.Many2one('account.account', string='Account')
    category_id = fields.Many2one('property.financial.category', string='Report Category')
    date = fields.Date(string='Month',
                       help="First day of the budgeted month. Leave empty for an "
                            "annual amount (use 'Generate Monthly Lines').")
    amount = fields.Monetary(string='Budget Amount')
    currency_id = fields.Many2one(related='budget_id.currency_id')
    company_id = fields.Many2one(related='budget_id.company_id', store=True)
