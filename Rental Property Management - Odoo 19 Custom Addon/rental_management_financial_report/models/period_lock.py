# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyPeriodLock(models.Model):
    """Lock a reporting period for a specific property once the Owners Statement
    has been issued. Locked periods prevent new journal entries from being
    posted against that property in the locked date range."""
    _name = 'property.period.lock'
    _description = 'Property Period Lock'
    _order = 'date_to desc, id desc'

    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, ondelete='cascade')
    date_from = fields.Date(string='Locked From', required=True)
    date_to = fields.Date(string='Locked To', required=True)
    reason = fields.Char(string='Reason', default='Owners Statement issued')
    locked_by = fields.Many2one('res.users', string='Locked By',
                                default=lambda s: s.env.user, readonly=True)
    locked_on = fields.Datetime(string='Locked On', default=fields.Datetime.now,
                                readonly=True)
    active = fields.Boolean(default=True,
                            help="Uncheck to unlock this period.")
    company_id = fields.Many2one(related='property_id.company_id', store=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise UserError(self.env._("'Locked From' must be before 'Locked To'."))

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s: %s – %s' % (
                rec.property_id.name or '', rec.date_from, rec.date_to)))
        return res

    def action_unlock(self):
        self.write({'active': False})
