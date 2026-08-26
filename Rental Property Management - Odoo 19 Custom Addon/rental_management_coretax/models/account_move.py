# -*- coding: utf-8 -*-
from odoo import fields, models

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

    coretax_trx_code = fields.Selection(TRX_CODES, string='CORETAX Trx Code',
                                        default='04')
    coretax_invoice_opt = fields.Selection([('Normal', 'Normal'),
                                            ('Replacement', 'Replacement')],
                                           string='Tax Invoice Option',
                                           default='Normal')
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

    # --- Retur Faktur PM (input tax invoice return / vendor credit note) ---
    coretax_origin_invoice_number = fields.Char(
        string='Original Faktur No.',
        help="Seller's original tax-invoice number being returned (Retur PM).")
    coretax_seller_tin = fields.Char(
        string="Seller TIN (Return)",
        help="Supplier TIN for the returned input invoice; defaults to the "
             "vendor's CORETAX TIN when empty.")

    # --- Lampiran C (VAT/STLG collected by other collector) ---
    coretax_collector_type = fields.Selection([
        ('001', '001'), ('002', '002'), ('003', '003'), ('100', '100'),
    ], string='Type of VAT Collected')
    coretax_billing_number = fields.Char(string='Billing Document No.')
    coretax_billing_date = fields.Date(string='Billing Document Date')
    coretax_invoice_replaced = fields.Char(string='Invoice Number Replaced')
    coretax_lampc_info = fields.Char(string='Lampiran C Information', default='Ok')

    # --- PPh Final Pasal 4 ayat (2) Sewa Tanah/Bangunan (10%) & e-Bupot ---
    is_pph42_applicable = fields.Boolean(
        string='Objek PPh Final 4(2) 10%', default=True,
        help="Centang jika transaksi ini merupakan sewa tanah/bangunan objek PPh Final 4(2).")
    pph42_rate = fields.Float(string='Tarif PPh 4(2) (%)', default=10.0)
    pph42_withholding_amount = fields.Monetary(
        string='Estimasi PPh 4(2) Dipotong (10%)',
        compute='_compute_pph42_amount', store=True,
        help="Nilai 10% dari DPP sewa yang dipotong oleh tenant badan.")
    pph42_bupot_status = fields.Selection([
        ('not_applicable', 'Bukan Objek PPh 4(2)'),
        ('pending', 'Menunggu Bukti Potong (Pending)'),
        ('received', 'Bukti Potong Diterima'),
    ], default='pending', string='Status Bukti Potong (e-Bupot)', tracking=True)
    pph42_bupot_number = fields.Char(string='Nomor Bukti Potong (e-Bupot Unifikasi)')
    pph42_bupot_date = fields.Date(string='Tanggal Bukti Potong')
    pph42_bupot_file = fields.Binary(string='File Bukti Potong (PDF)')
    pph42_bupot_filename = fields.Char(string='Nama File Bukti Potong')

    def _compute_pph42_amount(self):
        for rec in self:
            if rec.is_pph42_applicable:
                rec.pph42_withholding_amount = (rec.amount_untaxed or 0.0) * ((rec.pph42_rate or 10.0) / 100.0)
            else:
                rec.pph42_withholding_amount = 0.0

