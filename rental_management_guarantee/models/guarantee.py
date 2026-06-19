# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyTenantGuarantee(models.Model):
    _name = 'property.tenant.guarantee'
    _description = 'Tenant Bank / Insurance Guarantee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date, id'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    guarantee_type = fields.Selection([
        ('bank', 'Bank Guarantee'),
        ('insurance', 'Insurance Bond'),
        ('security', 'Security Guarantee'),
        ('other', 'Other'),
    ], string='Type', default='bank', required=True, tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract',
                                 required=True, tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    reference = fields.Char(string='Guarantee / Bond No.', tracking=True)
    issuer = fields.Char(string='Issuing Bank / Insurer', tracking=True)
    amount = fields.Monetary(string='Guaranteed Amount', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    reminder_days = fields.Integer(string='Reminder Lead (days)', default=30)
    responsible_id = fields.Many2one('res.users', string='Responsible',
                                     default=lambda s: s.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('released', 'Released'),
        ('claimed', 'Claimed'),
    ], string='Status', default='draft', tracking=True)
    days_to_expiry = fields.Integer(string='Days to Expiry',
                                    compute='_compute_days_to_expiry')
    is_expiring = fields.Boolean(string='Expiring Soon',
                                 compute='_compute_days_to_expiry',
                                 search='_search_is_expiring')
    reminder_done = fields.Boolean(string='Reminder Scheduled', copy=False)
    note = fields.Text(string='Notes')
    active = fields.Boolean(default=True)

    @api.depends('expiry_date', 'reminder_days', 'state')
    def _compute_days_to_expiry(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.expiry_date:
                rec.days_to_expiry = (rec.expiry_date - today).days
                rec.is_expiring = (rec.state == 'active'
                                   and 0 <= rec.days_to_expiry <= (rec.reminder_days or 0))
            else:
                rec.days_to_expiry = 0
                rec.is_expiring = False

    def _search_is_expiring(self, operator, value):
        if operator not in ('=', '!='):
            return []
        today = fields.Date.context_today(self)
        candidates = self.search([('state', '=', 'active'),
                                  ('expiry_date', '!=', False)])
        ids = [r.id for r in candidates
               if 0 <= (r.expiry_date - today).days <= (r.reminder_days or 0)]
        want_expiring = bool(value) if operator == '=' else not bool(value)
        return [('id', 'in' if want_expiring else 'not in', ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.tenant.guarantee') or '/'
        return super().create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_release(self):
        self.write({'state': 'released'})

    def action_claim(self):
        self.write({'state': 'claimed'})

    def action_draft(self):
        self.write({'state': 'draft', 'reminder_done': False})

    @api.model
    def _cron_check_guarantee_expiry(self):
        """Daily: expire lapsed guarantees and schedule reminder activities
        for guarantees approaching expiry."""
        today = fields.Date.context_today(self)
        guarantees = self.search([('state', '=', 'active'),
                                   ('expiry_date', '!=', False)])
        todo = self.env.ref('mail.mail_activity_data_todo',
                            raise_if_not_found=False)
        for rec in guarantees:
            delta = (rec.expiry_date - today).days
            if delta < 0:
                rec.state = 'expired'
                rec.message_post(body=self.env._(
                    "Guarantee %s expired on %s.") % (rec.name, rec.expiry_date))
            elif delta <= (rec.reminder_days or 0) and not rec.reminder_done:
                if todo and rec.responsible_id:
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo',
                        date_deadline=rec.expiry_date,
                        summary=self.env._('Guarantee expiring: %s') % rec.name,
                        note=self.env._(
                            'Guarantee %s (%s) for tenant %s expires on %s.') % (
                            rec.name, rec.reference or '',
                            rec.tenant_id.display_name or '', rec.expiry_date),
                        user_id=rec.responsible_id.id)
                rec.reminder_done = True
        return True


class TenancyDetailsGuarantee(models.Model):
    _inherit = 'tenancy.details'

    guarantee_ids = fields.One2many('property.tenant.guarantee', 'tenancy_id',
                                    string='Guarantees')
    guarantee_count = fields.Integer(compute='_compute_guarantee_count')

    def _compute_guarantee_count(self):
        for rec in self:
            rec.guarantee_count = len(rec.guarantee_ids)

    def action_view_guarantees(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guarantees',
            'res_model': 'property.tenant.guarantee',
            'view_mode': 'list,form',
            'domain': [('tenancy_id', '=', self.id)],
            'context': {'default_tenancy_id': self.id},
        }
