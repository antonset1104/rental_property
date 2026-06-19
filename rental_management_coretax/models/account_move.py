# -*- coding: utf-8 -*-
from odoo import fields, models

TRX_CODES = [
    ('01', '01 - To non-collector party'),
    ('02', '02 - To Treasurer collector'),
    ('03', '03 - To collector other than Treasurer'),
    ('04', '04 - Other Tax Base (DPP Nilai Lain)'),
    ('05', '05 - Specific amount (Besaran Tertentu)'),
    ('06', '06 - Other deliveries / to foreign passport holders'),
    ('07', '07 - VAT not collected'),
    ('08', '08 - VAT exempt'),
    ('09', '09 - Delivery of assets (Art. 16D)'),
]


class AccountMove(models.Model):
    _inherit = 'account.move'

    coretax_trx_code = fields.Selection(TRX_CODES, string='CORETAX Trx Code',
                                        default='04')
    coretax_invoice_opt = fields.Selection([('Normal', 'Normal'),
                                            ('Replacement', 'Replacement')],
                                           string='Tax Invoice Option',
                                           default='Normal')
    coretax_add_info = fields.Char(string='Additional Info Code')
    coretax_custom_doc = fields.Char(string='Customs Document No.')
    coretax_custom_doc_my = fields.Char(string='Customs Doc Month/Year (MMYYYY)')
    coretax_ref_desc = fields.Char(string='Reference Description')
    coretax_facility_stamp = fields.Char(string='Facility Stamp')
    coretax_seller_idtku = fields.Char(string='Seller ID TKU')
    coretax_buyer_idtku = fields.Char(string='Buyer ID TKU')
    coretax_exported = fields.Boolean(string='e-Faktur Exported', copy=False)
    coretax_export_date = fields.Datetime(string='Exported On', copy=False)
