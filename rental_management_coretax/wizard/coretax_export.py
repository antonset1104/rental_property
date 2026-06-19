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


def _num(value):
    """Numeric output preserving decimals, but integers without a trailing .0."""
    value = value or 0.0
    return str(int(value)) if float(value).is_integer() else repr(float(value))


class CoretaxEfakturWizard(models.TransientModel):
    _name = 'coretax.efaktur.wizard'
    _description = 'CORETAX e-Faktur (Faktur PK) Export'

    export_type = fields.Selection([
        ('pk', 'Faktur Keluaran (Output)'),
        ('pm_return', 'Retur Faktur Masukan (Input Return)'),
        ('lampiran_c', 'Lampiran C (VAT collected by other collector)'),
        ('pencatatan', 'Pencatatan (Simple Bookkeeping)'),
        ('l9_depreciation', 'L9 - Depreciation / Amortization'),
        ('l3b_otherparties', 'L3B - PPh Withheld by Other Parties'),
        ('l11a_uncollectible', 'L11A - Uncollectible Debt'),
        ('l11a_nonperforming', 'L11A - Non-Performing Credit'),
    ], string='Export Type', default='pk', required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company,
                                 required=True)
    date_from = fields.Date(
        default=lambda s: fields.Date.today().replace(day=1))
    date_to = fields.Date(default=fields.Date.today)
    tax_year = fields.Integer(string='Tax Year',
                              default=lambda s: fields.Date.today().year)
    is_register = fields.Boolean(compute='_compute_is_register')
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
    REGISTER_TYPES = ('l9_depreciation', 'l3b_otherparties',
                      'l11a_uncollectible', 'l11a_nonperforming')

    @api.depends('export_type')
    def _compute_is_register(self):
        for rec in self:
            rec.is_register = rec.export_type in self.REGISTER_TYPES

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

    def _build_pencatatan(self, moves):
        """Pencatatan — SimpleBookKeepingBulk from customer invoices."""
        company_partner = self.company_id.partner_id
        root = Element('SimpleBookKeepingBulk')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation', 'schema.xsd')
        _se(root, 'TIN', company_partner.coretax_tin or company_partner.vat or '')
        lst = SubElement(root, 'ListOfTransaction')
        for mv in moves:
            trx = SubElement(lst, 'Transaction')
            _se(trx, 'IdTku', mv.coretax_seller_idtku
                or company_partner.coretax_idtku or '')
            _se(trx, 'TransactionNumber', mv.name or '')
            _se(trx, 'TransactionDate',
                fields.Date.to_string(mv.invoice_date or mv.date))
            _se(trx, 'Customer', mv.partner_id.name or '')
            details = SubElement(trx, 'DetailsTransaction')
            discount_total = 0.0
            for line in mv.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                if not line.product_id and not line.name:
                    continue
                d = SubElement(details, 'Detail')
                _se(d, 'DetailsOfGoodService',
                    line.name or (line.product_id.name or ''))
                _se(d, 'PricePerUnit', _money(line.price_unit))
                _se(d, 'Qty', _qty(line.quantity))
                discount_total += (line.price_unit or 0.0) * (line.quantity or 0.0) \
                    * (line.discount or 0.0) / 100.0
            _se(trx, 'Discount', _money(discount_total))
        return b'<?xml version="1.0" encoding="utf-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _build_depreciation(self, records):
        root = Element('DepreciationAmortization')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation', 'schema.xsd')
        dep_list = SubElement(root, 'ListOfDepreciation')
        amo_list = SubElement(root, 'ListOfAmortization')
        for rec in records:
            tag = 'Depreciation' if rec.kind == 'depreciation' else 'Amortization'
            parent = dep_list if rec.kind == 'depreciation' else amo_list
            el = SubElement(parent, tag)
            _se(el, 'CodeOfAsset', rec.code_of_asset or '')
            _se(el, 'GroupOfAsset', rec.group_of_asset or '')
            _se(el, 'MonthOfAcquisition', rec.month_of_acquisition or 0)
            _se(el, 'YearOfAcquisition', rec.year_of_acquisition or 0)
            _se(el, 'AcquisitionPrice', _num(rec.acquisition_price))
            _se(el, 'RemainingValue', _num(rec.remaining_value))
            _se(el, 'CommercialMethode', rec.commercial_method or '')
            _se(el, 'FiscalMethode', rec.fiscal_method or '')
            _se(el, 'FiscalDepretiationThisYear',
                _num(rec.fiscal_depreciation_this_year))
            _se(el, 'Notes', rec.notes or '')
        return b'<?xml version="1.0" encoding="utf-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _build_otherparties(self, records):
        company_partner = self.company_id.partner_id
        root = Element('OtherParties')
        _se(root, 'TIN', company_partner.coretax_tin or company_partner.vat or '')
        _se(root, 'TaxYear', str(self.tax_year))
        lst = SubElement(root, 'OtherPartyList')
        for rec in records:
            el = SubElement(lst, 'List')
            _se(el, 'Tin', rec.partner_tin or '')
            _se(el, 'TaxType', rec.tax_type or '')
            _se(el, 'TaxBase', _num(rec.tax_base))
            _se(el, 'IncomeTax', _num(rec.income_tax))
            _se(el, 'IncomeTaxUsd', _num(rec.income_tax_usd))
            _se(el, 'WithholdingSlipNumber', rec.slip_number or '')
            _se(el, 'WithholdingSlipDate',
                rec.slip_date.strftime('%d-%m-%Y') if rec.slip_date else '')
        return b'<?xml version="1.0" encoding="utf-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _build_uncollectible(self, records):
        company_partner = self.company_id.partner_id
        root = Element('UncollectibleDebtBulk')
        _se(root, 'TIN', company_partner.coretax_tin or company_partner.vat or '')
        _se(root, 'TaxYear', str(self.tax_year))
        lst = SubElement(root, 'UncollectibleDebtList')
        for rec in records:
            el = SubElement(lst, 'List')
            _se(el, 'IdentityNumber', rec.identity_number or '')
            _se(el, 'NameOfRecipient', rec.name_of_recipient or '')
            _se(el, 'Address', rec.address or '')
            _se(el, 'DebtCeiling', _num(rec.debt_ceiling))
            _se(el, 'UncollectibleDebtAmount', _num(rec.uncollectible_amount))
            _se(el, 'DeductionMethod', rec.deduction_method or '01')
            _se(el, 'TypeOfFulfillmentProvingDocument',
                rec.proving_document_type or '01')
            _se(el, 'Remarks', rec.remarks or '')
        return b'<?xml version="1.0" encoding="UTF-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _build_nonperforming(self, records):
        company_partner = self.company_id.partner_id
        root = Element('NonPerforming')
        _se(root, 'TIN', company_partner.coretax_tin or company_partner.vat or '')
        _se(root, 'TaxYear', str(self.tax_year))
        lst = SubElement(root, 'NonPerformingList')
        for rec in records:
            el = SubElement(lst, 'List')
            _se(el, 'IdentityNumber', rec.identity_number or '')
            _se(el, 'DebtorName', rec.debtor_name or '')
            _se(el, 'Address', rec.address or '')
            _se(el, 'AmountBeginning', _num(rec.amount_beginning))
            _se(el, 'AmountEndOfYear', _num(rec.amount_end_of_year))
            _se(el, 'AmountOfInterest', _num(rec.amount_of_interest))
            _se(el, 'Category', rec.category or '01')
        return b'<?xml version="1.0" encoding="UTF-8"?>\n' + \
            tostring(root, encoding='utf-8')

    def _get_register_records(self):
        model_map = {
            'l9_depreciation': 'coretax.asset.depreciation',
            'l3b_otherparties': 'coretax.withholding.other',
            'l11a_uncollectible': 'coretax.uncollectible.debt',
            'l11a_nonperforming': 'coretax.nonperforming.credit',
        }
        model = model_map[self.export_type]
        return self.env[model].search([
            ('company_id', '=', self.company_id.id),
            ('tax_year', '=', self.tax_year)])

    # ----- action ---------------------------------------------------------
    def action_export(self):
        self.ensure_one()
        company_partner = self.company_id.partner_id

        if self.is_register:
            records = self._get_register_records()
            if not records:
                raise UserError(self.env._(
                    "No register entries found for tax year %s.") % self.tax_year)
            builders = {
                'l9_depreciation': (self._build_depreciation, 'L9_Penyusutan'),
                'l3b_otherparties': (self._build_otherparties, 'L3B_OtherParties'),
                'l11a_uncollectible': (self._build_uncollectible, 'L11A_Uncollectible'),
                'l11a_nonperforming': (self._build_nonperforming, 'L11A_NonPerforming'),
            }
            builder, prefix = builders[self.export_type]
            if self.export_type != 'l9_depreciation' and not (
                    company_partner.coretax_tin or company_partner.vat):
                raise UserError(self.env._(
                    "Set the CORETAX TIN / NPWP on company '%s'.")
                    % self.company_id.name)
            xml_bytes = builder(records)
            fname = '%s_%s.xml' % (prefix, self.tax_year)
            self.write({
                'file_data': base64.b64encode(xml_bytes),
                'file_name': fname,
                'invoice_count': len(records),
                'state': 'done',
            })
            return self._reload()

        # Document-based exports
        if not (self.date_from and self.date_to):
            raise UserError(self.env._("Set the period (From / To)."))
        moves = self._get_invoices()
        if not moves:
            raise UserError(self.env._(
                "No posted documents found for the selected criteria."))
        if not (company_partner.coretax_tin or company_partner.vat):
            raise UserError(self.env._(
                "Set the CORETAX TIN / NPWP on company '%s'.") % self.company_id.name)
        builders = {
            'pm_return': (self._build_pm_return, 'ReturFakturPM'),
            'lampiran_c': (self._build_lampiran_c, 'LampiranC'),
            'pencatatan': (self._build_pencatatan, 'Pencatatan'),
            'pk': (self._build_xml, 'FakturPK'),
        }
        builder, prefix = builders.get(self.export_type, builders['pk'])
        xml_bytes = builder(moves)
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
        return self._reload()

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'coretax.efaktur.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
