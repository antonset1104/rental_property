# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Property Procurement (Purchase)",
    'summary': "Link Odoo Purchase Orders to properties, lease contracts and "
               "maintenance requests; vendor bills flow into the Owners Statement.",
    'description': """
Property Procurement (Purchase integration)
===========================================
Integrates the standard Odoo **Purchase** app with the TechKhedut
*rental_management* addon so property spend follows a real RFQ → PO →
receipt → vendor bill flow instead of ad-hoc direct bills.

Features:
 * Property / Contract / Maintenance links on the Purchase Order.
 * Those links propagate to the vendor bill (account.move), so the spend is
   attributed to the property and appears in the Owners Statement Payment
   Details (when the financial-report module is installed).
 * One-click "Create Purchase Order" from a Maintenance Request (using its
   product lines and vendor), with a PO smart button.
 * A "Property Purchase Orders" menu.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'purchase'],
    'data': [
        'views/purchase_order_views.xml',
        'views/maintenance_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
