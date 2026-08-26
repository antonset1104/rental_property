# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    expected_move_in = fields.Date(string='Expected Move-in')
    expected_rent = fields.Monetary(string='Expected Rent',
                                    currency_field='company_currency')
    lease_months = fields.Integer(string='Lease Duration (months)')
    tenancy_count = fields.Integer(compute='_compute_tenancy_count')

    @api.depends('partner_id')
    def _compute_tenancy_count(self):
        Tenancy = self.env['tenancy.details']
        for lead in self:
            lead.tenancy_count = Tenancy.search_count(
                [('tenancy_id', '=', lead.partner_id.id)]
            ) if lead.partner_id else 0

    def action_create_lease_contract(self):
        self.ensure_one()
        ctx = {'default_tenancy_id': self.partner_id.id if self.partner_id else False}
        if self.property_id:
            ctx['default_property_id'] = self.property_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('New Lease Contract'),
            'res_model': 'tenancy.details',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }

    def action_view_tenancies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Lease Contracts'),
            'res_model': 'tenancy.details',
            'view_mode': 'list,form',
            'domain': [('tenancy_id', '=', self.partner_id.id)],
            'context': {'default_tenancy_id': self.partner_id.id},
        }
