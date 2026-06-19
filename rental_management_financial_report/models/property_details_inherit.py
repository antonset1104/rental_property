# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    # Multi-owner support (IFCA / CBRE owners statement can have several owners)
    owner_line_ids = fields.One2many('property.ownership.line', 'property_id',
                                     string='Owners')
    owner_count = fields.Integer(compute='_compute_owner_count')

    # Owners Statement header information
    property_manager_id = fields.Many2one('res.users', string='Property Manager')
    manager_phone = fields.Char(string='Telephone')
    manager_fax = fields.Char(string='Facsimile')

    # Per-property analytic account (for future cost allocation / per-property GL)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account', copy=False)

    budget_ids = fields.One2many('property.budget', 'property_id', string='Budgets')

    @api.depends('owner_line_ids')
    def _compute_owner_count(self):
        for rec in self:
            rec.owner_count = len(rec.owner_line_ids)

    def action_create_analytic_account(self):
        """Create (once) a dedicated analytic account for the property."""
        Analytic = self.env['account.analytic.account']
        Plan = self.env['account.analytic.plan']
        plan = Plan.search([], limit=1)
        if not plan:
            plan = Plan.create({'name': 'Properties'})
        for rec in self:
            if rec.analytic_account_id:
                continue
            vals = {'name': rec.name or 'Property', 'plan_id': plan.id}
            if rec.company_id:
                vals['company_id'] = rec.company_id.id
            rec.analytic_account_id = Analytic.create(vals).id
        return True


class PropertyOwnershipLine(models.Model):
    _name = 'property.ownership.line'
    _description = 'Property Ownership Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, ondelete='cascade')
    owner_id = fields.Many2one('res.partner', string='Owner', required=True)
    ownership_percentage = fields.Float(string='Ownership %', default=100.0)
    owner_street = fields.Char(related='owner_id.street', string='Street')
    owner_city = fields.Char(related='owner_id.city', string='City')
    company_id = fields.Many2one(related='property_id.company_id', store=True)

    @api.constrains('ownership_percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.ownership_percentage < 0 or rec.ownership_percentage > 100:
                raise ValidationError(self.env._(
                    "Ownership % must be between 0 and 100."))
