# -*- coding: utf-8 -*-
{
    'name': "Rental Management - CORETAX e-Faktur (Indonesia)",
    'summary': "Export customer tax invoices to CORETAX Faktur Pajak Keluaran "
               "bulk XML (Faktur PK template v1.4).",
    'description': """
CORETAX e-Faktur Output (Faktur Pajak Keluaran)
===============================================
Indonesian VAT localisation helper for the TechKhedut *rental_management* addon.
Adds the data and a wizard required to export posted customer invoices to the
DJP **CORETAX** *TaxInvoiceBulk* XML (Faktur PK template v1.4) for bulk upload.

Adds:
 * CORETAX taxpayer data on partners (TIN, ID TKU, document type, country).
 * e-Faktur fields on customer invoices (transaction code, Normal/Replacement,
   additional info, customs document, facility stamp, seller/buyer ID TKU).
 * CORETAX goods/service options on products (A/B, code, unit code).
 * A wizard that builds the TaxInvoiceBulk XML for a date range / selection and
   returns it as a downloadable file, then flags the invoices as exported.

Scope: output tax invoices (Faktur Keluaran). Input-return (Retur PM) and
Lampiran C exports can be added on the same pattern if required.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Accounting/Localizations',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/coretax_export_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/product_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
