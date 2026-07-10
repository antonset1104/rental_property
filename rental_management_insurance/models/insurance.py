# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyInsurancePolicy(models.Model):
    _name = 'property.insurance.policy'
    _description = 'Property Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date, id'

    name = fields.Char(required=True, copy=False, readonly=True,
                       default=lambda s: s.env._('New'))
    property_id = fields.Many2one('property.details', string='Property', tracking=True)
    coverage_type = fields.Selection([
        ('property', 'Property / Building'), ('liability', 'Public Liability'),
        ('fire', 'Fire / ISR'), ('other', 'Other')], default='property')
    insurer = fields.Char(string='Insurer', tracking=True)
    policy_number = fields.Char(string='Policy No.', tracking=True)
    sum_insured = fields.Monetary(string='Sum Insured')
    premium = fields.Monetary(string='Premium')
    start_date = fields.Date()
    expiry_date = fields.Date(tracking=True)
    reminder_days = fields.Integer(string='Reminder Lead (days)', default=30)
    responsible_id = fields.Many2one('res.users', default=lambda s: s.env.user)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'),
                              ('expired', 'Expired'), ('cancelled', 'Cancelled')],
                             default='draft', tracking=True)
    reminder_done = fields.Boolean(copy=False)
    days_to_expiry = fields.Integer(compute='_compute_dte')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    @api.depends('expiry_date')
    def _compute_dte(self):
        today = fields.Date.context_today(self)
        for r in self:
            r.days_to_expiry = (r.expiry_date - today).days if r.expiry_date else 0

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if v.get('name', 'New') in ('New', self.env._('New')):
                v['name'] = self.env['ir.sequence'].next_by_code('property.insurance.policy') or '/'
        return super().create(vals_list)

    def action_activate(self): self.write({'state': 'active'})
    def action_cancel(self): self.write({'state': 'cancelled'})
    def action_draft(self): self.write({'state': 'draft', 'reminder_done': False})

    @api.model
    def _cron_check_expiry(self):
        today = fields.Date.context_today(self)
        for r in self.search([('state', '=', 'active'), ('expiry_date', '!=', False)]):
            delta = (r.expiry_date - today).days
            if delta < 0:
                r.state = 'expired'
                r.message_post(body=self.env._("Insurance policy %s expired.") % r.name)
            elif delta <= (r.reminder_days or 0) and not r.reminder_done:
                if r.responsible_id:
                    r.activity_schedule('mail.mail_activity_data_todo',
                                        date_deadline=r.expiry_date,
                                        summary=self.env._('Insurance expiring: %s') % r.name,
                                        user_id=r.responsible_id.id)
                r.reminder_done = True
        return True
