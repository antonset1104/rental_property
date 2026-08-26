# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models
from odoo.exceptions import UserError


class CoretaxBatchFakturWizard(models.TransientModel):
    _name = 'coretax.batch.faktur.wizard'
    _description = 'Batch Set Nomor Faktur Pajak CORETAX'

    date_from = fields.Date(string='Dari Tanggal', required=True,
                            default=lambda s: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='Sampai Tanggal', required=True,
                          default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string='Tenant / Customer (Filter)')
    only_without_faktur = fields.Boolean(string='Hanya Faktur Belum Ada Nomor Pajak', default=True)
    start_faktur_number = fields.Char(string='Nomor Faktur Awal (Berurutan)',
                                      placeholder='Contoh: 040.001-26.00000101',
                                      help="Jika diisi, sistem dapat mengisi nomor berurutan secara otomatis.")
    faktur_date = fields.Date(string='Tanggal Faktur Pajak', default=fields.Date.today)
    line_ids = fields.One2many('coretax.batch.faktur.line', 'wizard_id', string='Daftar Tagihan')

    @api.onchange('date_from', 'date_to', 'partner_id', 'only_without_faktur')
    def onchange_filter_invoices(self):
        self.action_fetch_invoices()

    def action_fetch_invoices(self):
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.only_without_faktur:
            domain.append(('coretax_faktur_number', '=', False))

        moves = self.env['account.move'].search(domain, order='invoice_date, name')
        lines = []
        for m in moves:
            lines.append((0, 0, {
                'move_id': m.id,
                'invoice_date': m.invoice_date,
                'partner_id': m.partner_id.id,
                'amount_untaxed': m.amount_untaxed,
                'amount_tax': m.amount_tax,
                'amount_total': m.amount_total,
                'faktur_number': m.coretax_faktur_number or '',
                'faktur_date': m.coretax_faktur_date or self.faktur_date or fields.Date.today(),
            }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_generate_sequential(self):
        """Auto generate sequential tax invoice numbers based on start_faktur_number."""
        if not self.start_faktur_number:
            raise UserError(self.env._("Masukkan Nomor Faktur Awal terlebih dahulu."))
        # extract prefix and numeric suffix
        match = re.match(r'^(.*?)(\d+)$', self.start_faktur_number)
        if not match:
            raise UserError(self.env._("Format nomor faktur awal harus berakhiran angka, contoh: 040.001-26.00000101"))
        prefix, num_str = match.group(1), match.group(2)
        num_len = len(num_str)
        curr_num = int(num_str)

        for line in self.line_ids:
            formatted_no = f"{prefix}{str(curr_num).zfill(num_len)}"
            line.faktur_number = formatted_no
            if not line.faktur_date:
                line.faktur_date = self.faktur_date or fields.Date.today()
            curr_num += 1
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_apply(self):
        applied_count = 0
        for line in self.line_ids:
            if line.faktur_number and line.move_id:
                line.move_id.write({
                    'coretax_faktur_number': line.faktur_number,
                    'coretax_faktur_date': line.faktur_date or fields.Date.today(),
                    'coretax_exported': True,
                    'coretax_export_date': fields.Datetime.now(),
                })
                applied_count += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Berhasil Update Faktur Pajak'),
                'message': self.env._('Sebanyak %s faktur pajak berhasil diperbarui.') % applied_count,
                'type': 'success',
                'sticky': False,
            }
        }


class CoretaxBatchFakturLine(models.TransientModel):
    _name = 'coretax.batch.faktur.line'
    _description = 'Batch Set Faktur Pajak Line'

    wizard_id = fields.Many2one('coretax.batch.faktur.wizard', required=True, ondelete='cascade')
    move_id = fields.Many2one('account.move', string='Invoice', required=True)
    invoice_date = fields.Date(string='Tgl Invoice')
    partner_id = fields.Many2one('res.partner', string='Tenant / Customer')
    amount_untaxed = fields.Monetary(string='DPP (Untaxed)')
    amount_tax = fields.Monetary(string='PPN')
    amount_total = fields.Monetary(string='Total')
    currency_id = fields.Many2one(related='move_id.currency_id')
    faktur_number = fields.Char(string='Nomor Faktur Pajak (e-Faktur)')
    faktur_date = fields.Date(string='Tanggal Faktur Pajak')
