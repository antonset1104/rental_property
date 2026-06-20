# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

REC = 'asset_receivable'


class PropertyKpiDashboard(models.TransientModel):
    _name = 'property.kpi.dashboard'
    _description = 'Property KPI Dashboard'

    property_id = fields.Many2one('property.details', string='Property')
    date_from = fields.Date(default=lambda s: date.today().replace(month=1, day=1))
    date_to = fields.Date(default=fields.Date.today)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    total_properties = fields.Integer(compute='_compute_kpis')
    active_contracts = fields.Integer(compute='_compute_kpis')
    total_income = fields.Monetary(compute='_compute_kpis')
    total_expense = fields.Monetary(compute='_compute_kpis')
    noi = fields.Monetary(string='Net Operating Income', compute='_compute_kpis')
    arrears_total = fields.Monetary(compute='_compute_kpis')
    collection_rate = fields.Float(string='Collection Rate %', compute='_compute_kpis')
    lease_expiring_12m = fields.Integer(string='Leases Expiring (12m)',
                                        compute='_compute_kpis')

    def _move_domain(self, move_types):
        dom = [('move_type', 'in', move_types), ('state', '=', 'posted'),
               ('company_id', '=', self.company_id.id),
               ('invoice_date', '>=', self.date_from),
               ('invoice_date', '<=', self.date_to)]
        if self.property_id and 'property_financial_id' in self.env['account.move']._fields:
            dom.append(('property_financial_id', '=', self.property_id.id))
        return dom

    @api.depends('property_id', 'date_from', 'date_to')
    def _compute_kpis(self):
        Move = self.env['account.move']
        MoveLine = self.env['account.move.line']
        Tenancy = self.env['tenancy.details']
        Property = self.env['property.details']
        for rec in self:
            rec.total_properties = Property.search_count([])
            # contracts
            tdom = [('property_id', '=', rec.property_id.id)] if rec.property_id else []
            try:
                rec.active_contracts = Tenancy.search_count(tdom)
            except Exception:
                rec.active_contracts = 0
            # income / expense (accrual, untaxed)
            inc = sum(Move.search(rec._move_domain(('out_invoice',))).mapped('amount_untaxed')) \
                - sum(Move.search(rec._move_domain(('out_refund',))).mapped('amount_untaxed'))
            exp = sum(Move.search(rec._move_domain(('in_invoice',))).mapped('amount_untaxed')) \
                - sum(Move.search(rec._move_domain(('in_refund',))).mapped('amount_untaxed'))
            rec.total_income = inc
            rec.total_expense = exp
            rec.noi = inc - exp
            # arrears (receivable residual)
            ar_dom = [('parent_state', '=', 'posted'),
                      ('company_id', '=', rec.company_id.id),
                      ('account_id.account_type', '=', REC)]
            if rec.property_id and 'property_financial_id' in self.env['account.move']._fields:
                ar_dom.append(('move_id.property_financial_id', '=', rec.property_id.id))
            try:
                arrears = sum(MoveLine.search(ar_dom).mapped('amount_residual'))
            except Exception:
                arrears = 0.0
            rec.arrears_total = arrears
            # collection rate = received / invoiced (period)
            invoiced_total = sum(Move.search(rec._move_domain(('out_invoice',))).mapped('amount_total'))
            rec.collection_rate = ((invoiced_total - max(arrears, 0.0)) / invoiced_total * 100.0) \
                if invoiced_total else 0.0
            # leases expiring within 12 months
            try:
                horizon = fields.Date.context_today(rec) + relativedelta(months=12)
                edom = [('end_date', '>=', fields.Date.context_today(rec)),
                        ('end_date', '<=', horizon)]
                if rec.property_id:
                    edom.append(('property_id', '=', rec.property_id.id))
                rec.lease_expiring_12m = Tenancy.search_count(edom)
            except Exception:
                rec.lease_expiring_12m = 0
