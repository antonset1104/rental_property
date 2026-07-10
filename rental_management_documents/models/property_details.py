# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    documents_folder_id = fields.Many2one('documents.document',
                                          string='Documents Folder', copy=False,
                                          domain="[('type', '=', 'folder')]")
    documents_count = fields.Integer(compute='_compute_documents_count')

    @api.depends('documents_folder_id')
    def _compute_documents_count(self):
        Document = self.env['documents.document']
        for rec in self:
            rec.documents_count = Document.search_count(
                [('folder_id', '=', rec.documents_folder_id.id)]
            ) if rec.documents_folder_id else 0

    def _ensure_documents_folder(self):
        self.ensure_one()
        if self.documents_folder_id:
            return self.documents_folder_id
        folder = self.env['documents.document'].create({
            'name': self.name or self.env._('Property'),
            'type': 'folder',
        })
        self.documents_folder_id = folder.id
        return folder

    def action_open_documents(self):
        """Create the folder if needed, push the property's own attachments into
        Documents, and open the folder's documents."""
        self.ensure_one()
        folder = self._ensure_documents_folder()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'property.details'),
            ('res_id', '=', self.id)])
        Document = self.env['documents.document']
        for att in attachments:
            exists = Document.search_count([('attachment_id', '=', att.id)])
            if not exists:
                Document.create({
                    'name': att.name,
                    'attachment_id': att.id,
                    'folder_id': folder.id,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Documents'),
            'res_model': 'documents.document',
            'view_mode': 'kanban,list,form',
            'domain': [('folder_id', '=', folder.id)],
            'context': {'default_folder_id': folder.id},
        }
