# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    property_fin_category_id = fields.Many2one(
        'property.financial.category',
        string='Property Report Category',
        help="Owners Statement section/group this account is reported under.")

    # D3: link product → financial category via default account
    property_fin_product_ids = fields.One2many(
        'product.template', 'property_fin_account_id',
        string='Linked Products')


class AccountMove(models.Model):
    _inherit = 'account.move'

    property_manual_id = fields.Many2one('property.details', string='Property (Manual)')

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

    _PL_TYPES = ('income', 'income_other', 'expense',
                 'expense_depreciation', 'expense_direct_cost')

    def _build_analytic_distribution(self, prop, account):
        """Build analytic_distribution dict covering all configured dimensions
        for the property.  Each active analytic account gets 100% weight so
        Odoo's multi-plan engine records the full amount on every dimension."""
        dist = {}
        # Property-level (Plan: Properties)
        if prop.analytic_account_id:
            dist[str(prop.analytic_account_id.id)] = 100.0
        # Division
        if prop.analytic_division_id:
            dist[str(prop.analytic_division_id.id)] = 100.0
        # Sub Division
        if prop.analytic_subdivision_id:
            dist[str(prop.analytic_subdivision_id.id)] = 100.0
        # Department
        if prop.analytic_dept_id:
            dist[str(prop.analytic_dept_id.id)] = 100.0
        # Location
        if prop.analytic_location_id:
            dist[str(prop.analytic_location_id.id)] = 100.0
        # D4: per-category analytic (if the financial category has one)
        cat = account.property_fin_category_id if account else False
        if cat and cat.analytic_account_id:
            dist[str(cat.analytic_account_id.id)] = 100.0
        return dist or False

    def _apply_property_analytic(self):
        """Tag all income/expense journal items with the full multi-dimension
        analytic distribution for the linked property + category."""
        for move in self:
            prop = move.property_financial_id
            if not prop:
                continue
            for line in move.line_ids:
                if line.display_type:
                    continue
                if line.account_id.account_type not in self._PL_TYPES:
                    continue
                if line.analytic_distribution:
                    continue
                dist = self._build_analytic_distribution(prop, line.account_id)
                if not dist:
                    continue
                try:
                    line.analytic_distribution = dist
                except Exception:
                    continue

    def _post(self, soft=True):
        self._apply_property_analytic()
        return super()._post(soft=soft)
