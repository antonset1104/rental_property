# -*- coding: utf-8 -*-
from odoo import fields, models

METHOD_CODES = [
    ('GL', 'GL - Straight Line (Garis Lurus)'),
    ('SM', 'SM - Declining Balance (Saldo Menurun)'),
    ('JAT', 'JAT'),
    ('JSP', 'JSP'),
    ('SMG', 'SMG'),
    ('JJJ', 'JJJ'),
    ('ML', 'ML'),
]


class CoretaxAssetDepreciation(models.Model):
    """L9 - Depreciation & Amortization register (SPT Tahunan)."""
    _name = 'coretax.asset.depreciation'
    _description = 'CORETAX Depreciation / Amortization Entry'
    _order = 'tax_year desc, kind, id'

    kind = fields.Selection([('depreciation', 'Depreciation'),
                             ('amortization', 'Amortization')],
                            string='Kind', default='depreciation', required=True)
    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    code_of_asset = fields.Char(string='Code of Asset')
    group_of_asset = fields.Char(string='Group of Asset')
    month_of_acquisition = fields.Integer(string='Month of Acquisition')
    year_of_acquisition = fields.Integer(string='Year of Acquisition')
    acquisition_price = fields.Float(string='Acquisition Price', digits=(16, 4))
    remaining_value = fields.Float(string='Remaining Value', digits=(16, 4))
    commercial_method = fields.Selection(METHOD_CODES, string='Commercial Method')
    fiscal_method = fields.Selection(METHOD_CODES, string='Fiscal Method')
    fiscal_depreciation_this_year = fields.Float(
        string='Fiscal Depreciation This Year', digits=(16, 4))
    notes = fields.Char(string='Notes')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class CoretaxWithholdingOther(models.Model):
    """L3B - Income tax withheld/collected by other parties."""
    _name = 'coretax.withholding.other'
    _description = 'CORETAX PPh Withheld by Other Parties'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    partner_tin = fields.Char(string='TIN of Other Party')
    tax_type = fields.Char(string='Tax Type')
    tax_base = fields.Float(string='Tax Base', digits=(16, 2))
    income_tax = fields.Float(string='Income Tax', digits=(16, 2))
    income_tax_usd = fields.Float(string='Income Tax (USD)', digits=(16, 2))
    slip_number = fields.Char(string='Withholding Slip Number')
    slip_date = fields.Date(string='Withholding Slip Date')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class CoretaxUncollectibleDebt(models.Model):
    """L11A - Uncollectible (bad) debt list."""
    _name = 'coretax.uncollectible.debt'
    _description = 'CORETAX Uncollectible Debt'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    identity_number = fields.Char(string='Identity Number')
    name_of_recipient = fields.Char(string='Name of Recipient')
    address = fields.Char(string='Address')
    debt_ceiling = fields.Float(string='Debt Ceiling', digits=(16, 2))
    uncollectible_amount = fields.Float(string='Uncollectible Amount', digits=(16, 2))
    deduction_method = fields.Char(string='Deduction Method', default='01')
    proving_document_type = fields.Char(string='Proving Document Type', default='01')
    remarks = fields.Char(string='Remarks')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class CoretaxNonPerforming(models.Model):
    """L11A - Non-performing credit list."""
    _name = 'coretax.nonperforming.credit'
    _description = 'CORETAX Non-Performing Credit'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    identity_number = fields.Char(string='Identity Number')
    debtor_name = fields.Char(string='Debtor Name')
    address = fields.Char(string='Address')
    amount_beginning = fields.Float(string='Amount Beginning', digits=(16, 2))
    amount_end_of_year = fields.Float(string='Amount End of Year', digits=(16, 2))
    amount_of_interest = fields.Float(string='Amount of Interest', digits=(16, 2))
    category = fields.Selection([('01', '01'), ('02', '02'), ('03', '03')],
                                string='Category', default='01')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
