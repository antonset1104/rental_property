# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyParkingBay(models.Model):
    _name = 'property.parking.bay'
    _description = 'Parking Bay'
    _order = 'property_id, code'

    code = fields.Char(string='Bay No.', required=True)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    zone = fields.Char(string='Zone / Level')
    bay_type = fields.Selection([('car', 'Car'), ('motorcycle', 'Motorcycle'),
                                 ('truck', 'Truck'), ('disabled', 'Disabled')],
                                default='car')
    status = fields.Selection([('available', 'Available'), ('allocated', 'Allocated'),
                               ('maintenance', 'Maintenance')], default='available',
                              tracking=True)
    partner_id = fields.Many2one('res.partner', string='Holder')
    tenancy_id = fields.Many2one('tenancy.details', string='Contract')
    monthly_rate = fields.Monetary(string='Monthly Rate')
    product_id = fields.Many2one('product.product', string='Parking Product',
                                 default=lambda s: s.env.ref(
                                     'rental_management_parking.product_parking',
                                     raise_if_not_found=False))
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    _sql_constraints = [('code_property_uniq', 'unique(code, property_id)',
                         'Bay number must be unique per property.')]

    def action_allocate(self):
        for bay in self:
            if not bay.partner_id:
                raise UserError(self.env._("Set a Holder before allocating bay %s.") % bay.code)
            bay.status = 'allocated'

    def action_release(self):
        self.write({'status': 'available', 'partner_id': False, 'tenancy_id': False})

    def action_create_invoice(self):
        moves = self.env['account.move']
        for bay in self.filtered(lambda b: b.partner_id and b.monthly_rate):
            product = bay.product_id or self.env.ref(
                'rental_management_parking.product_parking', raise_if_not_found=False)
            if not product:
                raise UserError(self.env._("Set a Parking Product."))
            vals = {
                'move_type': 'out_invoice',
                'partner_id': bay.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': self.env._('Parking %s - %s') % (bay.code, bay.property_id.name or ''),
                    'quantity': 1.0,
                    'price_unit': bay.monthly_rate,
                })],
            }
            if bay.tenancy_id and 'tenancy_id' in moves._fields:
                vals['tenancy_id'] = bay.tenancy_id.id
            elif 'property_manual_id' in moves._fields:
                vals['property_manual_id'] = bay.property_id.id
            moves |= moves.create(vals)
        if moves:
            return {'type': 'ir.actions.act_window', 'res_model': 'account.move',
                    'view_mode': 'list,form', 'domain': [('id', 'in', moves.ids)]}
        return True
