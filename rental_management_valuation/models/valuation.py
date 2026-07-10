# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyValuation(models.Model):
    _name = 'property.valuation'
    _description = 'Property Market Valuation'
    _order = 'date desc, id desc'

    property_id = fields.Many2one('property.details', string='Property', required=True)
    date = fields.Date(required=True, default=fields.Date.today)
    valuer_id = fields.Many2one('res.partner', string='Valuer')
    method = fields.Selection([('market', 'Market Comparison'),
                               ('income', 'Income / Cap Rate'),
                               ('cost', 'Cost / DRC'), ('other', 'Other')],
                              default='market')
    market_value = fields.Monetary(string='Market Value')
    cap_rate = fields.Float(string='Cap Rate %')
    note = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')


class PropertyDetailsValuation(models.Model):
    _inherit = 'property.details'

    valuation_ids = fields.One2many('property.valuation', 'property_id',
                                    string='Valuations')
    latest_market_value = fields.Monetary(compute='_compute_latest_valuation',
                                          string='Latest Market Value')
    latest_valuation_date = fields.Date(compute='_compute_latest_valuation')
    valuation_count = fields.Integer(compute='_compute_latest_valuation')

    @api.depends('valuation_ids.market_value', 'valuation_ids.date')
    def _compute_latest_valuation(self):
        for rec in self:
            vals = rec.valuation_ids.sorted(lambda v: (v.date or fields.Date.today(), v.id))
            rec.valuation_count = len(vals)
            rec.latest_market_value = vals[-1].market_value if vals else 0.0
            rec.latest_valuation_date = vals[-1].date if vals else False

    def action_view_valuations(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Valuations',
                'res_model': 'property.valuation', 'view_mode': 'list,form',
                'domain': [('property_id', '=', self.id)],
                'context': {'default_property_id': self.id}}
