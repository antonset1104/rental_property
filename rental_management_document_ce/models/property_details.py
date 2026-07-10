# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    attachment_count = fields.Integer(compute='_compute_attachment_count')

    def _compute_attachment_count(self):
        Att = self.env['ir.attachment']
        for rec in self:
            rec.attachment_count = Att.search_count([
                ('res_model', '=', 'property.details'), ('res_id', '=', rec.id)])

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Property Files'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', 'property.details'),
                       ('res_id', '=', self.id)],
            'context': {'default_res_model': 'property.details',
                        'default_res_id': self.id},
        }
