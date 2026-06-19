# -*- coding: utf-8 -*-
import base64
from xml.etree.ElementTree import Element, SubElement, tostring

from odoo import api, fields, models
from odoo.exceptions import UserError


def _se(parent, tag, value=''):
    el = SubElement(parent, tag)
    el.text = '' if value is None else str(value)
    return el


def _money(value):
    """CORETAX monetary values are whole Rupiah (no decimals)."""
    return str(int(round(value or 0.0)))


def _qty(value):
    value = value or 0.0
    return str(int(value)) if float(value).is_integer() else str(value)


class CoretaxEfakturWizard(models.TransientModel):
    _name = 'coretax.efaktur.wizard'
    _description = 'CORETAX e-Faktur (Faktur PK) Export'

    export_type = fields.Selection([
        ('pk', 'Faktur Keluaran (Output)'),
        ('pm_return', 'Retur Faktur Masukan (Input Return)'),
        ('lampiran_c', 'Lampiran C (VAT collected by other collector)'),
    ], string='Export Type', default='pk', required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company,
                                 required=True)
    date_from = fields.Date(required=True,
                            default=lambda s: fields.Date.today().replace(day=1))
    date_to = fields.Date(required=True, default=fields.Date.today)
    only_unexported = fields.Boolean(string='Only not-yet-exported', default=True)
    only_property = fields.Boolean(
        string='Only property-linked invoices', default=False,
        help="Restrict to invoices attributed to a property (requires the "
             "financial-report module).")
    state = fields.Selection([('choose', 'Choose'), ('done', 'Done')],
                             default='choose')
    file_data = fields.Binary(string='File', readonly=True, attachment=False)
    file_name = fields.Char(string='File Name', readonly=True)
    invoice_count = fields.Integer(string='Invoices Exported', readonly=True)

    # ----- selection ------------------------------------------------------
    def _move_types(self):
        if self.export_type == 'pm_return':
            return ('in_refund',)
        return ('out_invoice', 'out_refund')

    def _get_invoices(self):
        self.ensure_one()
        move_types = self._move_types()
        ctx_ids = self.env.context.get('active_ids')
        if ctx_ids and self.env.context.get('active_model') == 'account.move':
            moves = self.env['account.move'].browse(ctx_ids).filtered(
                lambda m: m.move_type in move_types and m.state == 'posted')
        else:
            domain = [('move_type', 'in', move_types),
                      ('state', '=', 'posted'),
                      ('company_id', '=', self.company_id.id),
                      ('invoice_date', '>=', self.date_from),
                      ('invoice_date', '<=', self.date_to)]
            moves = self.env['account.move'].search(domain)
        if self.export_type == 'lampiran_c':
            moves = moves.filtered(lambda m: m.coretax_collector_type)
        if self.only_unexported:
            moves = moves.filtered(lambda m: not m.coretax_exported)
        if self.only_property and 'property_financial_id' in self.env['account.move']._fields:
            moves = moves.filtered(lambda m: m.property_financial_id)
        return moves

    # ----- XML build ------------------------------------------------------
    def _vat_rate(self, line):
        percents = line.tax_ids.filtered(lambda t: t.amount_type == 'percent')
        return percents[0].amount if percents else 0.0

    def _build_xml(self, moves):
        company_partner = self.company_id.partner_id
        seller_tin = company_partner.coretax_tin or (company_partner.vat or '')
        root = Element('TaxInvoiceBulk')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation', 'TaxInvoice.xsd')
        _se(root, 'TIN', seller_tin)
        lst = SubElement(root, 'ListOfTaxInvoice')
        for mv in moves:
            buyer = mv.partner_id
            ti = SubElement(lst, 'TaxInvoice')
            _se(ti, 'TaxInvoiceDate',
                fields.Date.to_string(mv.invoice_date or mv.date))
            _se(ti, 'TaxInvoiceOpt', mv.coretax_invoice_opt or 'Normal')
            _se(ti, 'TrxCode', mv.coretax_trx_code or '04')
            _se(ti, 'AddInfo', mv.coretax_add_info or '')
            _se(ti, 'CustomDoc', mv.coretax_custom_doc or '')
            _se(ti, 'CustomDocMonthYear', mv.coretax_custom_doc_my or '')
            _se(ti, 'RefDesc', mv.coretax_ref_desc or mv.name or '')
            _se(ti, 'FacilityStamp', mv.coretax_facility_stamp or '')
            _se(ti, 'SellerIDTKU',
                mv.coretax_seller_idtku or company_partner.coretax_idtku or '')
            _se(ti, 'BuyerTin', buyer.coretax_tin or buyer.vat or '')
            _se(ti, 'BuyerDocument', buyer.coretax_doc_type or 'TIN')
            _se(ti, 'BuyerCountry', buyer.coretax_country or 'IND')
            _se(ti, 'BuyerDocumentNumber', buyer.coretax_doc_number or '')
            _se(ti, 'BuyerName', buyer.name or '')
            _se(ti, 'BuyerAdress', buyer.contact_address or buyer.street or '')
            _se(ti, 'BuyerEmail', buyer.email or '')
            _se(ti, 'BuyerIDTKU', mv.coretax_buyer_idtku or buyer.coretax_idtku or '')
            gs_list = SubElement(ti, 'ListOfGoodService')
            for line in mv.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                if not line.product_id and not line.name:
                    continue
                product = line.product_id
                opt = (product.coretax_opt
                       or ('B' if product.type == 'service' else 'A'))
                rate = self._vat_rate(line)
                tax_base = line.price_subtotal
                other_base = tax_base
                vat = round(other_base * rate / 100.0)
                discount = (line.price_unit or 0.0) * (line.quantity or 0.0) \
                    * (line.discount or 0.0) / 100.0
                gs = SubElement(gs_list, 'GoodService')
                _se(gs, 'Opt', opt)
                _se(gs, 'Code', product.coretax_code or '000000')
                _se(gs, 'Name', line.name or (product.name or ''))
                _se(gs, 'Unit', product.coretax_unit_code or 'UM.0001')
                _se(gs, 'Price', _money(line.price_unit))
                _se(gs, 'Qty', _qty(line.quantity))
                _se(gs, 'TotalDiscount', _money(discount))
                _se(gs, 'TaxBase', _money(tax_base))
                _se(gs, 'OtherTaxBase', _money(other_base))
                _se(gs, 'VATRate', str(int(round(rate))))
                _se(gs, 'VAT', _money(vat))
                _se(gs, 'STLGRate', '0')
                _se(gs, 'STLG', '0')
        xml_bytes = b'<?xml version="1.0" encoding="utf-8"?>\n' + \
            tostring(root, encoding='utf-8')
        return xml_bytes

    def _build_pm_return(self, moves):
        """Retur Faktur Masukan — from vendor credit notes (in_refund)."""
        company_partner = self.company_id.partner_id
        root = Element('InputTaxInvoiceReturn')
        _se(root, 'TIN', company_partner.coretax_tin or company_partner.vat or '')
        data_list = SubElement(root, 'InputReturnDataList')
        for mv in moves:
            seller = mv.partner_id
            ird = SubElement(data_list, 'InputReturnData')
            doc = SubElement(ird, 'TransactionDocumentData')
            _se(doc, 'InvoiceNumber',
                mv.coretax_origin_invoice_number or mv.ref or mv.name or '')
            _se(doc, 'SellerTIN',
                mv.coretax_seller_tin or seller.coretax_tin or seller.vat or '')
            _se(doc, 'ReturnDate',
                (mv.invoice_date or mv.date).strftime('%d-%m-%Y'))
            _se(doc, 'ReturnTaxBase', _money(mv.amount_untaxed))
            _se(doc, 'ReturnOtherTaxBase', _money(mv.amount_untaxed))
            _se(doc, 'ReturnVAT', _money(mv.amount_tax))
            _se(doc, 'ReturnSTLG', '0')
            details = SubElement(ird, 'TransactionDetailsData')
            tb_tot = vat_tot = 0.0
            for line in mv.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                if not line.product_id and not line.name:
                    continue
                product = line.product_id
                opt = (product.coretax_opt
                       or ('B' if product.type == 'service' else 'A'))
                rate = self._vat_rate(line)
                tax_base = line.price_subtotal
                vat = round(tax_base * rate / 100.0)
                discount = (line.price_unit or 0.0) * (line.quantity or 0.0) \
                    * (line.discount or 0.0) / 100.0
                tb_tot += tax_base
                vat_tot += vat
                rows = SubElement(details, 'Rows')
                _se(rows, 'Type', opt)
                _se(rows, 'Name', line.name or (product.name or ''))
                _se(rows, 'Code', product.coretax_code or '000000')
                _se(rows, 'Quantity', _qty(line.quantity))
                _se(rows, 'Unit', product.coretax_unit_code or 'UM.0001')
                _se(rows, 'UnitPrice', _money(line.price_unit))
                _se(rows, 'STLGRate', '0')
                _se(rows, 'ReturnQuantity', _qty(line.quantity))
                _se(rows, 'ReturnDiscount', _money(discount))
                _se(rows, 'ReturnTaxBase', _money(tax_base))
                _se(rows, 'ReturnOtherTaxBase', _money(tax_base))
                _se(rows, 'ReturnOtherTaxBaseCheck', 'false')
                _se(rows, 'ReturnVAT', _money(vat))
                _se(rows, 'ReturnSTLG', '0')
            footer = SubElement(details, 'FooterRow')
            _se(footer, 'ReturnTaxBaseTotal', _money(tb_tot))
            _se(footer, 'ReturnOtherTaxBaseTotal', _money(tb_tot))
            _se(footer, 'ReturnVATTotal', _money(vat_tot))
            _se(footer, 'ReturnSTLGTotal', '0')
        return b'<?xml version="1.0" encoding="UTF-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _build_lampiran_c(self, moves):
        """Lampiran C — VAT/STLG collected by other collector."""
        company_partner = self.company_id.partner_id
        seller_tin = company_partner.coretax_tin or company_partner.vat or ''
        root = Element('VATandSTLGCollectedByOtherCollector')
        root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        _se(root, 'NameOfTE', company_partner.name or '')
        _se(root, 'TIN', seller_tin)
        _se(root, 'Period', '%02d' % (self.date_from.month))
        _se(root, 'Model', str(self.date_from.year))
        lst = SubElement(root, 'ListOfVATandSTLG')
        tot_sell = tot_base = tot_vat = tot_stlg = 0.0
        for mv in moves:
            buyer = mv.partner_id
            sell = mv.amount_untaxed
            vat = mv.amount_tax
            tot_sell += sell
            tot_base += sell
            tot_vat += vat
            item = SubElement(lst, 'VATandSTLG')
            _se(item, 'TINofSeller', seller_tin)
            _se(item, 'NameofSeller', company_partner.name or '')
            _se(item, 'TINofBuyer', buyer.coretax_tin or buyer.vat or '')
            _se(item, 'NameofBuyer', buyer.name or '')
            _se(item, 'TypeOfVATCollected', mv.coretax_collector_type or '001')
            billing = SubElement(item, 'BillingDocument')
            _se(billing, 'Number', mv.coretax_billing_number or mv.name or '')
            _se(billing, 'Date', fields.Date.to_string(
                mv.coretax_billing_date or mv.invoice_date or mv.date))
            _se(item, 'InvoiceNumberReplaced', mv.coretax_invoice_replaced or '')
            _se(item, 'SellingPrice', _money(sell))
            _se(item, 'OtherTaxBase', _money(sell))
            _se(item, 'VAT', _money(vat))
            _se(item, 'STLG', '0')
            _se(item, 'Information', mv.coretax_lampc_info or 'Ok')
        _se(root, 'TotalSellingPrice', _money(tot_sell))
        _se(root, 'TotalOtherTaxBase', _money(tot_base))
        _se(root, 'TotalVAT', _money(tot_vat))
        _se(root, 'TotalSTLG', _money(tot_stlg))
        return b'<?xml version="1.0" encoding="utf-8"?>\n' + \
            tostring(root, encoding='utf-8')

    # ----- action ---------------------------------------------------------
    def action_export(self):
        self.ensure_one()
        moves = self._get_invoices()
        if not moves:
            raise UserError(self.env._(
                "No posted documents found for the selected criteria."))
        company_partner = self.company_id.partner_id
        if not (company_partner.coretax_tin or company_partner.vat):
            raise UserError(self.env._(
                "Set the CORETAX TIN / NPWP on company '%s'.") % self.company_id.name)
        if self.export_type == 'pm_return':
            xml_bytes = self._build_pm_return(moves)
            prefix = 'ReturFakturPM'
        elif self.export_type == 'lampiran_c':
            xml_bytes = self._build_lampiran_c(moves)
            prefix = 'LampiranC'
        else:
            xml_bytes = self._build_xml(moves)
            prefix = 'FakturPK'
        fname = '%s_%s_%s.xml' % (
            prefix, fields.Date.to_string(self.date_from),
            fields.Date.to_string(self.date_to))
        moves.write({'coretax_exported': True,
                     'coretax_export_date': fields.Datetime.now()})
        self.write({
            'file_data': base64.b64encode(xml_bytes),
            'file_name': fname,
            'invoice_count': len(moves),
            'state': 'done',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'coretax.efaktur.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
