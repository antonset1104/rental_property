# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class OwnerPortal(CustomerPortal):

    def _owner_property_domain(self, partner):
        return [('owner_line_ids.owner_id', 'child_of',
                 partner.commercial_partner_id.id)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'property_count' in counters:
            cnt = 0
            try:
                cnt = request.env['property.details'].search_count(
                    self._owner_property_domain(request.env.user.partner_id))
            except AccessError:
                cnt = 0
            values['property_count'] = cnt
        return values

    @http.route(['/my/properties', '/my/properties/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_properties(self, page=1, **kw):
        partner = request.env.user.partner_id
        Property = request.env['property.details']
        domain = self._owner_property_domain(partner)
        total = Property.search_count(domain)
        pager = portal_pager(url='/my/properties', total=total, page=page,
                             step=self._items_per_page)
        properties = Property.search(domain, limit=self._items_per_page,
                                     offset=pager['offset'])
        return request.render('rental_management_owner_portal.portal_my_properties', {
            'properties': properties, 'page_name': 'owner_property',
            'pager': pager, 'default_url': '/my/properties',
        })

    @http.route(['/my/properties/<int:property_id>'], type='http',
                auth='user', website=True)
    def portal_my_property(self, property_id, access_token=None, **kw):
        try:
            prop = self._document_check_access('property.details', property_id,
                                               access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        remittances = request.env['property.owner.remittance'].sudo().search([
            ('property_id', '=', prop.id), ('state', '=', 'posted')])
        partner = request.env.user.partner_id.commercial_partner_id
        rows = []
        for rem in remittances:
            amt = sum(l.amount for l in rem.line_ids
                      if l.owner_id.commercial_partner_id == partner)
            if amt:
                rows.append({'name': rem.name, 'date': rem.date, 'amount': amt})
        return request.render('rental_management_owner_portal.portal_property_page', {
            'property': prop, 'remittances': rows, 'page_name': 'owner_property',
        })
