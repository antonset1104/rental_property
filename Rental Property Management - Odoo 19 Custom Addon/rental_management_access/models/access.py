# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyAccessCard(models.Model):
    _name = 'property.access.card'
    _description = 'Access / Parking Card'
    _order = 'card_no'

    card_no = fields.Char(string='Card No.', required=True)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract')
    holder_id = fields.Many2one('res.partner', string='Holder')
    card_type = fields.Selection([('access', 'Access'), ('parking', 'Parking'),
                                  ('lift', 'Lift'), ('other', 'Other')],
                                 default='access')
    issue_date = fields.Date(default=fields.Date.today)
    return_date = fields.Date()
    status = fields.Selection([('active', 'Active'), ('lost', 'Lost'),
                               ('returned', 'Returned'), ('expired', 'Expired')],
                              default='active', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    def action_return(self):
        self.write({'status': 'returned', 'return_date': fields.Date.today()})

    def action_lost(self):
        self.write({'status': 'lost'})


class PropertyVisitor(models.Model):
    _name = 'property.visitor'
    _description = 'Visitor Log'
    _order = 'check_in desc, id desc'

    name = fields.Char(string='Visitor Name', required=True)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    host_id = fields.Many2one('res.partner', string='Host (Tenant)')
    purpose = fields.Char()
    id_card_no = fields.Char(string='ID / Plate No.')
    card_id = fields.Many2one('property.access.card', string='Visitor Card')
    check_in = fields.Datetime(default=fields.Datetime.now)
    check_out = fields.Datetime()
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    def action_check_out(self):
        self.write({'check_out': fields.Datetime.now()})
