# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

TRX_CODES = [
    ('01', '01 - To non-collector party'),
    ('02', '02 - To Treasurer collector'),
    ('03', '03 - To collector other than Treasurer'),
    ('04', '04 - Other Tax Base (DPP Nilai Lain)'),
    ('05', '05 - Specific amount (Besaran Tertentu)'),
    ('06', '06 - Other deliveries / to foreign passport holders'),
    ('07', '07 - VAT not collected'),
    ('08', '08 - VAT exempt'),
    ('09', '09 - Delivery of assets (Art. 16D)'),
]


class AccountMove(models.Model):
    _inherit = 'account.move'

    coretax_trx_code = fields.Selection(TRX_CODES, string='CORETAX Trx Code', default='04')
    coretax_invoice_opt = fields.Selection([('Normal', 'Normal'), ('Replacement', 'Replacement')],
                                           string='Tax Invoice Option', default='Normal')
    coretax_add_info = fields.Char(string='Additional Info Code')
    coretax_custom_doc = fields.Char(string='Customs Document No.')
    coretax_custom_doc_my = fields.Char(string='Customs Doc Month/Year (MMYYYY)')
    coretax_ref_desc = fields.Char(string='Reference Description')
    coretax_facility_stamp = fields.Char(string='Facility Stamp')
    coretax_seller_idtku = fields.Char(string='Seller ID TKU')
    coretax_buyer_idtku = fields.Char(string='Buyer ID TKU')
    coretax_faktur_number = fields.Char(string='Nomor Faktur Pajak (e-Faktur)',
                                        help="Nomor Faktur Pajak resmi dari CORETAX DJP, mis. 040.001-26.00000100")
    coretax_faktur_date = fields.Date(string='Tanggal Faktur Pajak')
    coretax_exported = fields.Boolean(string='e-Faktur Exported', copy=False)
    coretax_export_date = fields.Datetime(string='Exported On', copy=False)

    # Retur Faktur PM
    coretax_origin_invoice_number = fields.Char(string='Original Faktur No.')
    coretax_seller_tin = fields.Char(string="Seller TIN (Return)")

    # Lampiran C
    coretax_collector_type = fields.Selection([
        ('001', '001'), ('002', '002'), ('003', '003'), ('100', '100'),
    ], string='Type of VAT Collected')
    coretax_billing_number = fields.Char(string='Billing Document No.')
    coretax_billing_date = fields.Date(string='Billing Document Date')
    coretax_invoice_replaced = fields.Char(string='Invoice Number Replaced')
    coretax_lampc_info = fields.Char(string='Lampiran C Information', default='Ok')

    # PPh Final 4(2) 10%
    is_pph42_applicable = fields.Boolean(string='Objek PPh Final 4(2) 10%', default=True)
    pph42_amount = fields.Monetary(string='PPh Final 4(2) 10%', compute='_compute_pph42_amount', store=True)
    pph42_ebupot_number = fields.Char(string='Nomor Bukti Potong (e-Bupot)')
    pph42_ebupot_date = fields.Date(string='Tanggal Bukti Potong')
    pph42_ebupot_status = fields.Selection([
        ('none', 'Belum Ada'),
        ('pending', 'Menunggu Bukti Potong'),
        ('received', 'Sudah Diterima'),
    ], string='Status e-Bupot', default='none')
    pph42_ebupot_attachment = fields.Binary(string='File e-Bupot (PDF)')

    # Multi-Currency Valas Lease & Kurs Pajak KMK / BI
    is_foreign_currency_lease = fields.Boolean(string='Kontrak Sewa Valas (USD/SGD)')
    lease_foreign_currency_id = fields.Many2one('res.currency', string='Mata Uang Kontrak Valas')
    lease_foreign_amount = fields.Monetary(string='Nominal Tagihan Valas', currency_field='lease_foreign_currency_id')
    tax_exchange_rate_kmk = fields.Float(string='Kurs Pajak KMK (IDR)', digits=(12, 4),
                                        help="Kurs Menteri Keuangan resmi untuk penentuan DPP e-Faktur.")
    bi_transaction_rate = fields.Float(string='Kurs Transaksi BI (IDR)', digits=(12, 4),
                                      help="Kurs tengah Bank Indonesia untuk konversi nilai piutang sewa.")
    exchange_rate_date = fields.Date(string='Tanggal Penetapan Kurs', default=fields.Date.today)

    @api.depends('is_pph42_applicable', 'amount_untaxed', 'move_type')
    def _compute_pph42_amount(self):
        for rec in self:
            if rec.is_pph42_applicable and rec.move_type in ('out_invoice', 'out_refund'):
                rec.pph42_amount = rec.amount_untaxed * 0.10
            else:
                rec.pph42_amount = 0.0

    @api.onchange('is_foreign_currency_lease', 'lease_foreign_amount', 'tax_exchange_rate_kmk', 'bi_transaction_rate')
    def _onchange_foreign_lease_values(self):
        if self.is_foreign_currency_lease and self.lease_foreign_amount:
            curr_symbol = self.lease_foreign_currency_id.symbol or self.lease_foreign_currency_id.name or 'Valas'
            kmk_rate = self.tax_exchange_rate_kmk or 1.0
            bi_rate = self.bi_transaction_rate or kmk_rate
            dpp_kmk = self.lease_foreign_amount * kmk_rate
            piutang_bi = self.lease_foreign_amount * bi_rate
            if not self.coretax_ref_desc:
                self.coretax_ref_desc = (
                    f"Tagihan Valas {curr_symbol} {self.lease_foreign_amount:,.2f} "
                    f"@ Kurs KMK Rp {kmk_rate:,.2f} (DPP Rp {dpp_kmk:,.0f}) | "
                    f"Kurs BI Rp {bi_rate:,.2f} (Est Rp {piutang_bi:,.0f})"
                )
