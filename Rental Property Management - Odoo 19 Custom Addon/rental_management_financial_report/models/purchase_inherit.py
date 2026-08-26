# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    property_financial_id = fields.Many2one(
        'property.details', string='Property',
        help="Link this PO to a property so that vendor bills generated from "
             "this PO are automatically tagged with the property for financial reporting.")

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.property_financial_id:
            vals['property_manual_id'] = self.property_financial_id.id
        return vals
