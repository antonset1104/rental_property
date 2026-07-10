# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class TenantPortal(CustomerPortal):

    def _tenant_contract_domain(self, partner):
        return [('tenancy_id', 'child_of', partner.commercial_partner_id.id)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'contract_count' in counters:
            count = 0
            try:
                partner = request.env.user.partner_id
                count = request.env['tenancy.details'].search_count(
                    self._tenant_contract_domain(partner))
            except AccessError:
                count = 0
            values['contract_count'] = count
        return values

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, sortby=None, **kw):
        partner = request.env.user.partner_id
        Contract = request.env['tenancy.details']
        domain = self._tenant_contract_domain(partner)
        total = Contract.search_count(domain)
        pager = portal_pager(
            url='/my/contracts', total=total, page=page,
            step=self._items_per_page)
        contracts = Contract.search(
            domain, limit=self._items_per_page, offset=pager['offset'],
            order='start_date desc')
        values = {
            'contracts': contracts,
            'page_name': 'contract',
            'pager': pager,
            'default_url': '/my/contracts',
        }
        return request.render('rental_management_portal.portal_my_contracts', values)

    @http.route(['/my/contracts/<int:contract_id>'],
                type='http', auth='user', website=True)
    def portal_my_contract_detail(self, contract_id, access_token=None, **kw):
        try:
            contract_sudo = self._document_check_access(
                'tenancy.details', contract_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = {
            'contract': contract_sudo,
            'page_name': 'contract',
        }
        return request.render('rental_management_portal.portal_contract_page', values)
