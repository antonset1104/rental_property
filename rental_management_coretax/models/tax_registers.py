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


class CoretaxPromotionExpense(models.Model):
    """L11A - Promotion expense list."""
    _name = 'coretax.promotion.expense'
    _description = 'CORETAX Promotion Expense'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    identity_number = fields.Char(string='Identity Number')
    name = fields.Char(string='Name')
    address = fields.Char(string='Address')
    date_of_promotion = fields.Date(string='Date of Promotion')
    form_and_type = fields.Char(string='Form and Type')
    amount_of_promotion = fields.Float(string='Amount of Promotion', digits=(16, 2))
    amount_of_witholding = fields.Float(string='Amount of Withholding', digits=(16, 2))
    witholding_slip_number = fields.Char(string='Withholding Slip Number')
    description = fields.Char(string='Description')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class CoretaxEntertainmentExpense(models.Model):
    """L11A - Entertainment expense list."""
    _name = 'coretax.entertainment.expense'
    _description = 'CORETAX Entertainment Expense'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    date_of_entertainment = fields.Date(string='Date of Entertainment')
    place = fields.Char(string='Place')
    address = fields.Char(string='Address')
    type_of_entertainment = fields.Char(string='Type of Entertainment')
    amount_of_entertainment = fields.Float(string='Amount', digits=(16, 2))
    name_of_business_partner = fields.Char(string='Business Partner Name')
    position = fields.Char(string='Position')
    company_name = fields.Char(string='Company Name')
    business_type = fields.Char(string='Business Type')
    notes = fields.Char(string='Notes')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class CoretaxRelatedParty(models.Model):
    """L10A - Related-party transactions declaration."""
    _name = 'coretax.related.party'
    _description = 'CORETAX Related Party Transaction'
    _order = 'tax_year desc, id'

    tax_year = fields.Integer(string='Tax Year', required=True,
                              default=lambda s: fields.Date.today().year)
    name = fields.Char(string='Name')
    partner_tin = fields.Char(string='TIN')
    country_code = fields.Char(string='Country Code (ISO3)')
    type_of_relation_code = fields.Char(string='Type of Relation Code')
    business_activity = fields.Char(string='Business Activity')
    type_of_transaction_code = fields.Char(string='Type of Transaction Code')
    transaction_value = fields.Float(string='Transaction Value', digits=(16, 2))
    pricing_method_code = fields.Char(string='Pricing Method Applied Code')
    reason_pricing = fields.Char(string='Reason of Pricing Method')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
