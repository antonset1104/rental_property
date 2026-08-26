# -*- coding: utf-8 -*-
from odoo import api, fields, models

SECTION_SELECTION = [
    ('income', 'Income'),
    ('statutory', 'Statutory Outgoings'),
    ('variable', 'Variable Outgoings'),
    ('direct_recharge', 'Direct Recharge'),
    ('tenant_recharge', 'Tenant Recharge Expenditure'),
    ('non_recoverable', 'Non-Recoverable Expenditure'),
    ('capital', 'Capital Expenditure'),
    ('gst', 'GST'),
    ('other', 'Other'),
    ('equity_contribution', "Owners' Contribution"),
    ('equity_retained', "Owners' Equity / Retained"),
]


class PropertyFinancialCategory(models.Model):
    """Classifies GL accounts into Owners Statement report lines/groups
    (equivalent to the MRxxxx structured account codes in the CBRE/MRI report)."""
    _name = 'property.financial.category'
    _description = 'Property Financial Report Category'
    _order = 'sequence, code, id'

    name = fields.Char(string='Category', required=True, translate=True)
    code = fields.Char(string='Code', help="Optional MR-style code, e.g. MR01010.")
    sequence = fields.Integer(string='Sequence', default=10)
    section = fields.Selection(SECTION_SELECTION, string='Report Section',
                               required=True, default='other')
    group_name = fields.Char(
        string='Sub-Group',
        help="Sub-header shown above the lines, e.g. 'Rental Income', 'Cleaning'.")
    # D4: optional per-category analytic account
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account (Category)',
        help="If set, journal entries classified under this category will also be "
             "tagged with this analytic account (in addition to the property-level "
             "and dimension-level accounts).")
    account_ids = fields.One2many('account.account', 'property_fin_category_id',
                                  string='GL Accounts')
    account_count = fields.Integer(compute='_compute_account_count')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.depends('account_ids')
    def _compute_account_count(self):
        for rec in self:
            rec.account_count = len(rec.account_ids)


class ProductTemplatePropertyCategory(models.Model):
    """D3: Link product.template to a property financial category so that
    invoices using this product are automatically classified correctly."""
    _inherit = 'product.template'

    property_fin_account_id = fields.Many2one(
        'account.account', string='Property Income/Expense Account',
        help="GL account used for property-related invoices with this product. "
             "The account's Property Report Category determines the Owners Statement "
             "classification. Leave empty to use the product's standard income/expense account.")
    property_fin_category_id = fields.Many2one(
        'property.financial.category',
        string='Property Report Category',
        compute='_compute_property_fin_category',
        store=True,
        help="Derived from the Property Income/Expense Account's report category.")

    @api.depends('property_fin_account_id',
                 'property_fin_account_id.property_fin_category_id')
    def _compute_property_fin_category(self):
        for rec in self:
            rec.property_fin_category_id = (
                rec.property_fin_account_id.property_fin_category_id
                if rec.property_fin_account_id else False
            )
