# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyHandover(models.Model):
    _inherit = 'property.handover'

    project_id = fields.Many2one('project.project', string='Fit-out Project',
                                 copy=False)
    task_count = fields.Integer(compute='_compute_task_count')

    @api.depends('project_id')
    def _compute_task_count(self):
        Task = self.env['project.task']
        for rec in self:
            rec.task_count = Task.search_count(
                [('project_id', '=', rec.project_id.id)]) if rec.project_id else 0

    def action_create_fitout_project(self):
        self.ensure_one()
        if self.project_id:
            return self.action_view_tasks()
        project = self.env['project.project'].create({
            'name': self.env._('Fit-out %s - %s') % (
                self.name, self.property_id.name or ''),
            'company_id': self.company_id.id if self.company_id else False,
        })
        tasks = []
        for item in self.checklist_ids:
            tasks.append({
                'name': item.name,
                'project_id': project.id,
                'company_id': self.company_id.id if self.company_id else False,
            })
        if tasks:
            self.env['project.task'].create(tasks)
        self.project_id = project.id
        return self.action_view_tasks()

    def action_view_tasks(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(self.env._("No fit-out project yet."))
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Fit-out Tasks'),
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.project_id.id)],
            'context': {'default_project_id': self.project_id.id},
        }
