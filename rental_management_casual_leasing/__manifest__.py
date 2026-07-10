# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Casual Leasing",
    'summary': "Short-term / casual leasing (booths, kiosks, pop-ups) with "
               "daily/weekly billing for the rental_management module.",
    'description': """
Casual Leasing
==============
Companion module for the TechKhedut *rental_management* addon to handle
short-term, casual lettings (promotional booths, kiosks, pop-up spaces, atrium
hire) that do not warrant a full tenancy contract.

Features:
 * Casual lease booking: property, space, customer, period and rate.
 * Daily / weekly / fixed pricing with automatic total computation.
 * One-click customer invoice (linked to the property so it flows into the
   Owners Statement when the financial-report module is installed).
 * Simple lifecycle: Draft → Confirmed → Active → Done / Cancelled.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/product_data.xml',
        'views/casual_lease_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
