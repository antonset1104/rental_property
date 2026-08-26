# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class TenancyDetailsEscalation(models.Model):
    _inherit = 'tenancy.details'

    is_escalation = fields.Boolean(string='Rent Escalation')
    escalation_type = fields.Selection([('percent', 'Percentage'),
                                        ('fixed_amount', 'Fixed Amount')],
                                       string='Escalation Type', default='percent')
    escalation_value = fields.Float(string='Escalation Value',
                                    help="Percentage (e.g. 5 = +5%) or fixed amount "
                                         "added to the rent each cycle.")
    escalation_frequency_months = fields.Integer(string='Frequency (months)',
                                                 default=12)
    escalation_next_date = fields.Date(string='Next Escalation Date')
    escalation_proposal_state = fields.Selection([
        ('none', 'Belum Ada Penawaran'),
        ('proposed', 'Surat Penawaran Terkirim ke Tenant'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak / Negosiasi'),
    ], string='Status Penawaran', default='none', tracking=True)
    proposed_new_rent = fields.Monetary(string='Estimasi Sewa Baru', compute='_compute_proposed_rent')
    escalation_log_ids = fields.One2many('property.rent.escalation.log',
                                         'tenancy_id', string='Escalation Log')

    @api.depends('total_rent', 'escalation_type', 'escalation_value')
    def _compute_proposed_rent(self):
        for rec in self:
            old = rec.total_rent or 0.0
            if rec.escalation_type == 'percent':
                new = old * (1.0 + (rec.escalation_value or 0.0) / 100.0)
            else:
                new = old + (rec.escalation_value or 0.0)
            rec.proposed_new_rent = round(new, 2)

    def action_send_escalation_proposal(self):
        for rec in self:
            rec.escalation_proposal_state = 'proposed'
            rec.message_post(body=self.env._(
                "✉️ <b>Surat Penawaran Kenaikan Sewa</b> dikirimkan ke tenant %s.<br/>"
                "Sewa saat ini: %s %s -> Penawaran Sewa Baru: %s %s (%s).") % (
                    rec.tenancy_id.name if rec.tenancy_id else '',
                    rec.currency_id.symbol or '', rec.total_rent,
                    rec.currency_id.symbol or '', rec.proposed_new_rent,
                    f"+{rec.escalation_value}%" if rec.escalation_type == 'percent' else f"+{rec.escalation_value}"))
        return True

    def action_approve_escalation(self):
        for rec in self:
            rec.escalation_proposal_state = 'approved'
            rec._apply_one_escalation()
            rec.escalation_proposal_state = 'none'
        return True

    def action_reject_escalation(self):
        for rec in self:
            rec.escalation_proposal_state = 'rejected'
            rec.message_post(body=self.env._("❌ Penawaran kenaikan sewa ditolak / masuk tahap negosiasi ulang."))
        return True

    def _apply_one_escalation(self):
        self.ensure_one()
        old = self.total_rent or 0.0
        if self.escalation_type == 'percent':
            new = old * (1.0 + (self.escalation_value or 0.0) / 100.0)
        else:
            new = old + (self.escalation_value or 0.0)
        new = round(new, 2)
        self.env['property.rent.escalation.log'].create({
            'tenancy_id': self.id,
            'date': self.escalation_next_date or fields.Date.today(),
            'old_rent': old,
            'new_rent': new,
            'note': '%s %s' % (self.escalation_type, self.escalation_value),
        })
        self.total_rent = new
        if self.escalation_next_date:
            self.escalation_next_date = self.escalation_next_date + relativedelta(
                months=self.escalation_frequency_months or 12)
        self.message_post(body=self.env._(
            "Rent escalated from %(old)s to %(new)s.", old=old, new=new))

    def action_apply_escalation_now(self):
        for rec in self.filtered(lambda r: r.is_escalation):
            rec._apply_one_escalation()
        return True

    @api.model
    def _cron_apply_rent_escalation(self):
        today = fields.Date.context_today(self)
        due = self.search([('is_escalation', '=', True),
                           ('escalation_next_date', '!=', False),
                           ('escalation_next_date', '<=', today)])
        for rec in due:
            rec._apply_one_escalation()
        return True


class PropertyRentEscalationLog(models.Model):
    _name = 'property.rent.escalation.log'
    _description = 'Rent Escalation Log'
    _order = 'date desc, id desc'

    tenancy_id = fields.Many2one('tenancy.details', required=True, ondelete='cascade')
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    date = fields.Date(string='Date')
    old_rent = fields.Monetary(string='Old Rent')
    new_rent = fields.Monetary(string='New Rent')
    note = fields.Char()
    currency_id = fields.Many2one(related='tenancy_id.currency_id')
    company_id = fields.Many2one(related='tenancy_id.company_id', store=True)
