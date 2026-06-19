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
    def _get_invoices(self):
        self.ensure_one()
        ctx_ids = self.env.context.get('active_ids')
        if ctx_ids and self.env.context.get('active_model') == 'account.move':
            moves = self.env['account.move'].browse(ctx_ids).filtered(
                lambda m: m.move_type in ('out_invoice', 'out_refund')
                and m.state == 'posted')
        else:
            domain = [('move_type', 'in', ('out_invoice', 'out_refund')),
                      ('state', '=', 'posted'),
                      ('company_id', '=', self.company_id.id),
                      ('invoice_date', '>=', self.date_from),
                      ('invoice_date', '<=', self.date_to)]
            moves = self.env['account.move'].search(domain)
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

    # ----- action ---------------------------------------------------------
    def action_export(self):
        self.ensure_one()
        moves = self._get_invoices()
        if not moves:
            raise UserError(self.env._(
                "No posted customer invoices found for the selected criteria."))
        company_partner = self.company_id.partner_id
        if not (company_partner.coretax_tin or company_partner.vat):
            raise UserError(self.env._(
                "Set the CORETAX TIN / NPWP on company '%s'.") % self.company_id.name)
        xml_bytes = self._build_xml(moves)
        fname = 'FakturPK_%s_%s.xml' % (
            fields.Date.to_string(self.date_from),
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
