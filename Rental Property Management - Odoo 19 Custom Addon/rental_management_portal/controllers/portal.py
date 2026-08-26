# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class TenantPortal(CustomerPortal):

    def _tenant_contract_domain(self, partner):
        return [('tenancy_id', 'child_of', partner.commercial_partner_id.id)]

    def _tenant_maintenance_domain(self, partner):
        cid = partner.commercial_partner_id.id
        return [
            '|',
            ('customer_id', 'child_of', cid),
            ('tenancy_id.tenancy_id', 'child_of', cid),
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'contract_count' in counters:
            try:
                values['contract_count'] = request.env['tenancy.details'].search_count(
                    self._tenant_contract_domain(partner))
            except AccessError:
                values['contract_count'] = 0
        if 'maintenance_count' in counters:
            try:
                values['maintenance_count'] = request.env['maintenance.request'].search_count(
                    self._tenant_maintenance_domain(partner))
            except (AccessError, KeyError):
                values['maintenance_count'] = 0
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

    @http.route(['/my/maintenance', '/my/maintenance/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_maintenance(self, page=1, **kw):
        partner = request.env.user.partner_id
        Maintenance = request.env['maintenance.request']
        domain = self._tenant_maintenance_domain(partner)
        total = Maintenance.search_count(domain)
        pager = portal_pager(
            url='/my/maintenance', total=total, page=page,
            step=self._items_per_page)
        requests = Maintenance.search(
            domain, limit=self._items_per_page, offset=pager['offset'],
            order='create_date desc')
        values = {
            'requests': requests,
            'page_name': 'maintenance',
            'pager': pager,
            'default_url': '/my/maintenance',
        }
        return request.render('rental_management_portal.portal_my_maintenance_requests', values)

    @http.route(['/my/maintenance/new'], type='http', auth='user', methods=['GET', 'POST'], website=True)
    def portal_maintenance_new(self, **post):
        partner = request.env.user.partner_id
        contracts = request.env['tenancy.details'].search(self._tenant_contract_domain(partner))
        if request.httprequest.method == 'POST':
            name = post.get('name')
            tenancy_id = int(post.get('tenancy_id', 0)) or False
            description = post.get('description')
            priority = post.get('priority', '1')

            contract = request.env['tenancy.details'].browse(tenancy_id) if tenancy_id else False
            prop = contract.property_id if contract else False

            vals = {
                'name': name or 'Maintenance / Komplain',
                'description': description or '',
                'customer_id': partner.id,
                'tenancy_id': contract.id if contract else False,
                'property_id': prop.id if prop else False,
                'priority': priority,
                'request_date': request.env.cr.now().date(),
            }
            req = request.env['maintenance.request'].sudo().create(vals)

            # Handle attachment upload if any
            if 'attachment' in request.params and request.params['attachment']:
                file = request.params['attachment']
                if hasattr(file, 'read'):
                    attachment_data = file.read()
                    if attachment_data:
                        import base64
                        request.env['ir.attachment'].sudo().create({
                            'name': file.filename or 'Lampiran_Komplain',
                            'type': 'binary',
                            'datas': base64.b64encode(attachment_data),
                            'res_model': 'maintenance.request',
                            'res_id': req.id,
                        })
            return request.redirect('/my/maintenance/%s' % req.id)

        values = {
            'contracts': contracts,
            'page_name': 'maintenance_new',
        }
        return request.render('rental_management_portal.portal_maintenance_new', values)

    @http.route(['/my/maintenance/<int:request_id>'], type='http', auth='user', website=True)
    def portal_my_maintenance_detail(self, request_id, access_token=None, **kw):
        try:
            req_sudo = self._document_check_access(
                'maintenance.request', request_id, access_token)
        except (AccessError, MissingError):
            # fallback sudo search check
            partner = request.env.user.partner_id
            req_sudo = request.env['maintenance.request'].sudo().search([
                ('id', '=', request_id),
                '|',
                ('customer_id', 'child_of', partner.commercial_partner_id.id),
                ('tenancy_id.tenancy_id', 'child_of', partner.commercial_partner_id.id),
            ], limit=1)
            if not req_sudo:
                return request.redirect('/my/maintenance')
        values = {
            'req': req_sudo,
            'page_name': 'maintenance',
        }
        return request.render('rental_management_portal.portal_maintenance_page', values)

    @http.route(['/my/maintenance/<int:request_id>/rate'],
                type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_my_maintenance_rate(self, request_id, **post):
        partner = request.env.user.partner_id
        req_sudo = request.env['maintenance.request'].sudo().search([
            ('id', '=', request_id),
            '|',
            ('customer_id', 'child_of', partner.commercial_partner_id.id),
            ('tenancy_id.tenancy_id', 'child_of', partner.commercial_partner_id.id),
        ], limit=1)
        if req_sudo:
            rating = post.get('rating')
            feedback = post.get('feedback')
            if rating:
                req_sudo.write({
                    'portal_rating': rating,
                    'portal_feedback': feedback or '',
                    'portal_rating_date': fields.Datetime.now(),
                })
                req_sudo.message_post(
                    body=f"⭐ <b>Ulasan Kepuasan Tenant (CSAT):</b> Rating {rating}/5 Bintang.<br/><b>Masukan:</b> {feedback or '-'}"
                )
        return request.redirect('/my/maintenance/%s?rated=1' % request_id)

    @http.route(['/my/invoices/<int:invoice_id>/upload_proof'],
                type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_invoice_upload_proof(self, invoice_id, **kw):
        partner = request.env.user.partner_id
        move = request.env['account.move'].sudo().search([
            ('id', '=', invoice_id),
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
        ], limit=1)
        if not move:
            return request.redirect('/my/invoices')

        payment_notes = kw.get('payment_notes', '')
        payment_date = kw.get('payment_date') or fields.Date.today()
        file = kw.get('proof_file')

        attachment_id = False
        if file and hasattr(file, 'read'):
            attachment_data = file.read()
            if attachment_data:
                import base64
                filename = file.filename or 'Bukti_Transfer.pdf'
                att = request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'type': 'binary',
                    'datas': base64.b64encode(attachment_data),
                    'res_model': 'account.move',
                    'res_id': move.id,
                })
                attachment_id = att.id
                move.write({
                    'portal_payment_proof': base64.b64encode(attachment_data),
                    'portal_payment_proof_filename': filename,
                    'portal_payment_proof_date': fields.Datetime.now(),
                    'portal_payment_notes': payment_notes,
                    'portal_payment_proof_status': 'submitted',
                })

        move.message_post(
            body=f"""
            💳 <b>BUKTI TRANSFER PEMBAYARAN DIUNGGAH VIA PORTAL TENANT</b><br/>
            <b>Pengunggah:</b> {partner.name}<br/>
            <b>Tanggal Bayar:</b> {payment_date}<br/>
            <b>Catatan Tenant:</b> {payment_notes or '-'}<br/>
            <i>Harap tim Keuangan/AR memeriksa mutasi bank dan melakukan rekonsiliasi pembayaran.</i>
            """,
            attachment_ids=[attachment_id] if attachment_id else []
        )

        return request.redirect(f'/my/invoices/{move.id}?success=payment_proof_uploaded')


