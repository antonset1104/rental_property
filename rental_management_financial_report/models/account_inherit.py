# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    property_fin_category_id = fields.Many2one(
        'property.financial.category',
        string='Property Report Category',
        help="Owners Statement section/group this account is reported under.")


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Manually set property link, used by owner-remittance / manual trust entries
    # that have no tenancy / sale / maintenance link.
    property_manual_id = fields.Many2one('property.details', string='Property (Manual)')

    # Resolve the related property from the links stamped by rental_management
    # (tenancy_id / sold_id / maintenance_request_id) or the manual link, so
    # financial reports can filter every journal entry that belongs to a property.
    property_financial_id = fields.Many2one(
        'property.details', string='Property (Financial)',
        compute='_compute_property_financial', store=True, index=True)

    @api.depends('tenancy_id', 'sold_id', 'maintenance_request_id', 'property_manual_id')
    def _compute_property_financial(self):
        for move in self:
            prop = False
            if move.property_manual_id:
                prop = move.property_manual_id
            elif move.tenancy_id and move.tenancy_id.property_id:
                prop = move.tenancy_id.property_id
            elif move.sold_id and move.sold_id.property_id:
                prop = move.sold_id.property_id
            elif move.maintenance_request_id and move.maintenance_request_id.property_id:
                prop = move.maintenance_request_id.property_id
            move.property_financial_id = prop and prop.id or False

    # ---- Integration with standard Odoo Analytic Accounting --------------
    _PL_TYPES = ('income', 'income_other', 'expense',
                 'expense_depreciation', 'expense_direct_cost')

    def _apply_property_analytic(self):
        """Tag the property's analytic account on income/expense journal items
        that have no analytic distribution yet, so property spend & income flow
        into Odoo's native Analytic Accounting (analytic items, plans, budgets,
        P&L by analytic)."""
        for move in self:
            prop = move.property_financial_id
            analytic = prop.analytic_account_id if prop else False
            if not analytic:
                continue
            for line in move.line_ids:
                if line.display_type:
                    continue
                if line.account_id.account_type not in self._PL_TYPES:
                    continue
                if line.analytic_distribution:
                    continue
                try:
                    line.analytic_distribution = {str(analytic.id): 100.0}
                except Exception:
                    continue

    def _post(self, soft=True):
        self._apply_property_analytic()
        return super()._post(soft=soft)
