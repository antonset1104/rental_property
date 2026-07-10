# -*- coding: utf-8 -*-
from odoo import fields, models


class TenancyDetailsPortal(models.Model):
    _name = 'tenancy.details'
    _inherit = ['tenancy.details', 'portal.mixin']

    # Stored related so the portal can show the property name without granting
    # portal users ORM read access to property.details.
    portal_property_name = fields.Char(related='property_id.name', store=True,
                                        string='Property Name')

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/contracts/%s' % rec.id
