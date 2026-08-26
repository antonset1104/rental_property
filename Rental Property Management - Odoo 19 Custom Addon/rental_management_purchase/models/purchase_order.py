# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    property_id = fields.Many2one('property.details', string='Property')
    tenancy_id = fields.Many2one('tenancy.details', string='Lease Contract',
                                 domain="[('property_id', '=', property_id)]")
    maintenance_request_id = fields.Many2one('maintenance.request',
                                             string='Maintenance Request')

    @api.onchange('tenancy_id')
    def _onchange_tenancy_id(self):
        if self.tenancy_id and self.tenancy_id.property_id:
            self.property_id = self.tenancy_id.property_id

    @api.onchange('maintenance_request_id')
    def _onchange_maintenance_request_id(self):
        if self.maintenance_request_id and self.maintenance_request_id.property_id:
            self.property_id = self.maintenance_request_id.property_id

    def _prepare_invoice(self):
        """Propagate the property links onto the generated vendor bill so the
        spend is attributed to the property in the financial reports."""
        vals = super()._prepare_invoice()
        move_fields = self.env['account.move']._fields
        if self.tenancy_id and 'tenancy_id' in move_fields:
            vals['tenancy_id'] = self.tenancy_id.id
        if self.maintenance_request_id and 'maintenance_request_id' in move_fields:
            vals['maintenance_request_id'] = self.maintenance_request_id.id
        if self.property_id and 'property_manual_id' in move_fields:
            vals['property_manual_id'] = self.property_id.id
        return vals
