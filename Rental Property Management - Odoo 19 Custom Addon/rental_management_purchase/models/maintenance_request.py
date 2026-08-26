# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    purchase_order_ids = fields.One2many('purchase.order', 'maintenance_request_id',
                                         string='Purchase Orders')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    def action_create_purchase_order(self):
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(self.env._(
                "Set a Vendor on the maintenance request first."))
        if not self.maintenance_product_ids:
            raise UserError(self.env._(
                "Add at least one product line to create a purchase order."))
        order_lines = [(0, 0, {
            'product_id': line.product_id.id,
            'name': line.description or (line.product_id.display_name or ''),
            'product_qty': line.quantity or 1,
            'price_unit': line.price_unit,
        }) for line in self.maintenance_product_ids if line.product_id]
        if not order_lines:
            raise UserError(self.env._("Product lines must reference a product."))
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'maintenance_request_id': self.id,
            'property_id': self.property_id.id if self.property_id else False,
            'order_line': order_lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('maintenance_request_id', '=', self.id)],
            'context': {'default_maintenance_request_id': self.id,
                        'default_property_id': self.property_id.id if self.property_id else False},
        }
