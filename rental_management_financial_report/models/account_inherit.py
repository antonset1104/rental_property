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

    # Resolve the related property from the links stamped by rental_management
    # (tenancy_id / sold_id / maintenance_request_id) so financial reports can
    # filter every journal entry that belongs to a property.
    property_financial_id = fields.Many2one(
        'property.details', string='Property (Financial)',
        compute='_compute_property_financial', store=True, index=True)

    @api.depends('tenancy_id', 'sold_id', 'maintenance_request_id')
    def _compute_property_financial(self):
        for move in self:
            prop = False
            if move.tenancy_id and move.tenancy_id.property_id:
                prop = move.tenancy_id.property_id
            elif move.sold_id and move.sold_id.property_id:
                prop = move.sold_id.property_id
            elif move.maintenance_request_id and move.maintenance_request_id.property_id:
                prop = move.maintenance_request_id.property_id
            move.property_financial_id = prop and prop.id or False
