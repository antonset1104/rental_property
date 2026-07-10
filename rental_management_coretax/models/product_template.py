# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    coretax_opt = fields.Selection([('A', 'A - Goods (Barang)'),
                                    ('B', 'B - Service (Jasa)')],
                                   string='CORETAX Type')
    coretax_code = fields.Char(string='CORETAX Goods/Service Code', default='000000')
    coretax_unit_code = fields.Char(string='CORETAX Unit Code', default='UM.0001')
