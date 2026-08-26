# -*- coding: utf-8 -*-
from odoo import fields, models


class TenancyDetailsPortal(models.Model):
    _name = 'tenancy.details'
    _inherit = ['tenancy.details', 'portal.mixin']

    # Stored related so the portal can show the property name without granting
    # portal users ORM read access to property.details.
    portal_property_name = fields.Char(related='property_id.name', store=True,
                                        string='Property Name')

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/contracts/%s' % rec.id


class AccountMovePortal(models.Model):
    _inherit = 'account.move'

    portal_payment_proof = fields.Binary(string='Bukti Transfer (Portal)')
    portal_payment_proof_filename = fields.Char(string='Nama File Bukti Bayar')
    portal_payment_proof_date = fields.Datetime(string='Waktu Upload Bukti Bayar')
    portal_payment_notes = fields.Text(string='Catatan Pembayaran dari Tenant')
    portal_payment_proof_status = fields.Selection([
        ('none', 'Belum Ada Bukti Bayar'),
        ('submitted', 'Bukti Bayar Diunggah (Menunggu Verifikasi)'),
        ('verified', 'Terverifikasi'),
    ], default='none', string='Status Bukti Bayar Portal', tracking=True)

