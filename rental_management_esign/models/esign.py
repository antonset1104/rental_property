# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertySignatureRequest(models.Model):
    _name = 'property.signature.request'
    _description = 'Contract Signature Request'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True, copy=False, readonly=True,
                       default=lambda s: s.env._('New'))
    tenancy_id = fields.Many2one('tenancy.details', string='Contract', tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    signer_id = fields.Many2one('res.partner', string='Signer', required=True)
    document = fields.Binary(string='Document', attachment=True)
    document_filename = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'),
                              ('signed', 'Signed'), ('declined', 'Declined')],
                             default='draft', tracking=True)
    sent_date = fields.Datetime(readonly=True)
    signed_date = fields.Datetime(readonly=True)
    note = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if v.get('name', 'New') in ('New', self.env._('New')):
                v['name'] = self.env['ir.sequence'].next_by_code(
                    'property.signature.request') or '/'
        return super().create(vals_list)

    def action_send(self):
        self.write({'state': 'sent', 'sent_date': fields.Datetime.now()})
        for rec in self:
            rec.message_post(body=self.env._("Signature requested from %s.")
                             % rec.signer_id.display_name)

    def action_mark_signed(self):
        self.write({'state': 'signed', 'signed_date': fields.Datetime.now()})

    def action_decline(self):
        self.write({'state': 'declined'})

    def action_draft(self):
        self.write({'state': 'draft'})
