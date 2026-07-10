# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyDunningLevel(models.Model):
    _name = 'property.dunning.level'
    _description = 'Dunning Level'
    _order = 'days_overdue, id'

    name = fields.Char(required=True)
    level = fields.Integer(string='Level', required=True, default=1)
    days_overdue = fields.Integer(string='Days Overdue', required=True)
    send_email = fields.Boolean(string='Send Email', default=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template',
                                       domain="[('model', '=', 'account.move')]")
    late_fee_percent = fields.Float(string='Late Fee %')
    late_fee_fixed = fields.Monetary(string='Late Fee (Fixed)')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    active = fields.Boolean(default=True)


class AccountMoveDunning(models.Model):
    _inherit = 'account.move'

    dunning_level = fields.Integer(string='Dunning Level', default=0, copy=False)
    dunning_date = fields.Date(string='Last Dunning Date', copy=False)

    def _apply_dunning_level(self, level):
        self.ensure_one()
        if level.send_email and level.mail_template_id:
            level.mail_template_id.send_mail(self.id, force_send=False)
        # optional late fee
        fee = (level.late_fee_fixed or 0.0) + \
            (self.amount_residual or 0.0) * (level.late_fee_percent or 0.0) / 100.0
        if fee > 0:
            product = self.env.ref('rental_management_dunning.product_late_fee',
                                   raise_if_not_found=False)
            if product:
                vals = {
                    'move_type': 'out_invoice',
                    'partner_id': self.partner_id.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': self.env._('Late payment fee for %s') % self.name,
                        'quantity': 1.0,
                        'price_unit': round(fee, 2),
                    })],
                }
                if self.tenancy_id and 'tenancy_id' in self._fields:
                    vals['tenancy_id'] = self.tenancy_id.id
                self.env['account.move'].create(vals)
        self.dunning_level = level.level
        self.dunning_date = fields.Date.today()
        self.message_post(body=self.env._("Dunning level %s applied.") % level.level)

    @api.model
    def _cron_run_dunning(self):
        today = fields.Date.context_today(self)
        levels = self.env['property.dunning.level'].search([])
        if not levels:
            return True
        overdue = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '!=', False),
            ('invoice_date_due', '<', today),
        ])
        for move in overdue:
            days = (today - move.invoice_date_due).days
            matched = levels.filtered(lambda l: days >= l.days_overdue)
            if not matched:
                continue
            top = max(matched, key=lambda l: l.level)
            if top.level > (move.dunning_level or 0):
                move._apply_dunning_level(top)
        return True
