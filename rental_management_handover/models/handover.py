# -*- coding: utf-8 -*-
from odoo import api, fields, models

DEFAULT_CHECKLISTS = {
    'move_in': [
        'Condition report completed & signed',
        'Keys / access cards issued',
        'Tenant insurance certificate received',
        'Opening meter readings recorded',
        'Handover / welcome pack provided',
    ],
    'fit_out': [
        'Fit-out drawings submitted & approved',
        'Contractor public-liability insurance verified',
        'Fit-out bond / deposit received',
        'Permits & landlord approvals obtained',
        'Works completed & inspected',
        'Compliance / occupancy certificates received',
    ],
    'move_out': [
        'Vacating notice received',
        'Final joint inspection completed',
        'Make-good / reinstatement completed',
        'Keys / access cards returned',
        'Final meter readings recorded',
        'Bond / security deposit reconciled',
    ],
}


class PropertyHandover(models.Model):
    _name = 'property.handover'
    _description = 'Tenant Handover (Move-in / Fit-out / Move-out)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda s: s.env._('New'))
    handover_type = fields.Selection([
        ('move_in', 'Move-in'),
        ('fit_out', 'Fit-out'),
        ('move_out', 'Move-out'),
    ], string='Type', required=True, default='move_in', tracking=True)
    tenancy_id = fields.Many2one('tenancy.details', string='Contract',
                                 required=True, tracking=True)
    property_id = fields.Many2one(related='tenancy_id.property_id', store=True)
    tenant_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Tenant',
                                store=True)
    scheduled_date = fields.Date(string='Scheduled Date', default=fields.Date.today,
                                 tracking=True)
    actual_date = fields.Date(string='Actual Date', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible',
                                     default=lambda s: s.env.user)
    state = fields.Selection([('draft', 'Draft'),
                              ('progress', 'In Progress'),
                              ('done', 'Completed'),
                              ('cancel', 'Cancelled')],
                             default='draft', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    # Fit-out specific
    contractor_id = fields.Many2one('res.partner', string='Fit-out Contractor')
    fitout_start = fields.Date(string='Fit-out Start')
    fitout_end = fields.Date(string='Fit-out End')
    bond_amount = fields.Monetary(string='Fit-out Bond')

    # Condition / move-out specific
    condition_notes = fields.Text(string='Condition Report')
    make_good_required = fields.Boolean(string='Make-good Required')
    make_good_notes = fields.Text(string='Make-good Notes')
    keys_issued = fields.Integer(string='Keys / Cards Issued')
    keys_returned = fields.Integer(string='Keys / Cards Returned')

    checklist_ids = fields.One2many('property.handover.checklist', 'handover_id',
                                    string='Checklist')
    progress = fields.Float(string='Progress', compute='_compute_progress')

    @api.depends('checklist_ids.is_done')
    def _compute_progress(self):
        for rec in self:
            total = len(rec.checklist_ids)
            done = len(rec.checklist_ids.filtered('is_done'))
            rec.progress = (done / total * 100.0) if total else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') in ('New', self.env._('New')):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.handover') or '/'
        return super().create(vals_list)

    def action_generate_checklist(self):
        for rec in self:
            items = DEFAULT_CHECKLISTS.get(rec.handover_type, [])
            lines = [(5, 0, 0)]
            for idx, item in enumerate(items):
                lines.append((0, 0, {'sequence': (idx + 1) * 10, 'name': item}))
            rec.checklist_ids = lines
        return True

    def action_start(self):
        self.write({'state': 'progress'})

    def action_complete(self):
        for rec in self:
            rec.state = 'done'
            if not rec.actual_date:
                rec.actual_date = fields.Date.today()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})


class PropertyHandoverChecklist(models.Model):
    _name = 'property.handover.checklist'
    _description = 'Handover Checklist Item'
    _order = 'sequence, id'

    handover_id = fields.Many2one('property.handover', required=True,
                                  ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Task', required=True)
    is_done = fields.Boolean(string='Done')
    note = fields.Char(string='Note')


class TenancyDetailsHandover(models.Model):
    _inherit = 'tenancy.details'

    handover_ids = fields.One2many('property.handover', 'tenancy_id',
                                   string='Handovers')
    handover_count = fields.Integer(compute='_compute_handover_count')

    def _compute_handover_count(self):
        for rec in self:
            rec.handover_count = len(rec.handover_ids)

    def action_view_handovers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Handovers',
            'res_model': 'property.handover',
            'view_mode': 'list,form',
            'domain': [('tenancy_id', '=', self.id)],
            'context': {'default_tenancy_id': self.id},
        }
