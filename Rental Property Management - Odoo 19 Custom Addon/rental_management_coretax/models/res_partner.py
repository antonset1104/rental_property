# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    coretax_tin = fields.Char(string='CORETAX TIN / NPWP',
                              help="16-digit Taxpayer Identification Number used on "
                                   "CORETAX tax invoices.")
    coretax_idtku = fields.Char(string='ID TKU',
                                help="Place-of-business identifier (NPWP + branch), "
                                     "usually 22 digits.")
    coretax_doc_type = fields.Selection([
        ('TIN', 'TIN'),
        ('Passport', 'Passport'),
        ('NationalID', 'National ID'),
        ('Other', 'Other'),
    ], string='Buyer Document Type', default='TIN')
    coretax_doc_number = fields.Char(string='Buyer Document Number')
    coretax_country = fields.Char(string='Buyer Country (ISO3)', default='IND')
