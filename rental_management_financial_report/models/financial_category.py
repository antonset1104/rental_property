# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Report sections used to group income/expense accounts on the Owners Statement.
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
