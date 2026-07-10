# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class PropertyPpmPlan(models.Model):
    _name = 'property.ppm.plan'
    _description = 'Preventive Maintenance Plan'
    _order = 'next_date, id'

    name = fields.Char(required=True)
    property_id = fields.Many2one('property.details', string='Property', required=True)
    category_id = fields.Many2one('maintenance.equipment.category', string='Category')
    frequency_months = fields.Integer(string='Frequency (months)', default=3, required=True)
    next_date = fields.Date(string='Next Service Date', required=True,
                            default=fields.Date.today)
    sla_days = fields.Integer(string='SLA (days)', default=7)
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda s: s.env.user)
    active = fields.Boolean(default=True)
    request_ids = fields.One2many('maintenance.request', 'ppm_plan_id',
                                  string='Generated Requests')
    request_count = fields.Integer(compute='_compute_request_count')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('request_ids')
    def _compute_request_count(self):
        for r in self:
            r.request_count = len(r.request_ids)

    def _generate_request(self):
        self.ensure_one()
        vals = {
            'name': self.env._('PPM: %s') % self.name,
            'property_id': self.property_id.id,
            'maintenance_type': 'preventive',
            'ppm_plan_id': self.id,
        }
        if 'schedule_date' in self.env['maintenance.request']._fields:
            vals['schedule_date'] = fields.Datetime.now()
        return self.env['maintenance.request'].create(vals)

    def action_generate_now(self):
        for plan in self:
            plan._generate_request()
        return True

    @api.model
    def _cron_generate_ppm(self):
        today = fields.Date.context_today(self)
        for plan in self.search([('next_date', '<=', today)]):
            plan._generate_request()
            plan.next_date = today + relativedelta(months=plan.frequency_months or 1)
        return True

    def action_view_requests(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Maintenance Requests',
                'res_model': 'maintenance.request', 'view_mode': 'list,form',
                'domain': [('ppm_plan_id', '=', self.id)]}


class MaintenanceRequestPpm(models.Model):
    _inherit = 'maintenance.request'

    ppm_plan_id = fields.Many2one('property.ppm.plan', string='PPM Plan')
