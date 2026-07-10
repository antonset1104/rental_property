# -*- coding: utf-8 -*-
{
    'name': "Rental Management - GTO & Meter Management",
    'summary': "Gross-Turnover (percentage rent / revenue sharing) and utility "
               "meter management with tenant recharge for the rental_management module.",
    'description': """
GTO / Revenue Sharing & Meter Management
========================================
Companion module that adds two RentX-style operational capabilities on top of
the TechKhedut *rental_management* addon:

**GTO (Gross Turnover) / Revenue Sharing**
 * Configure percentage-rent terms on a tenancy contract
   (Higher-of base/%, Base + Overage, or Pure %).
 * Capture periodic tenant turnover declarations.
 * Auto-compute percentage / overage rent and raise the customer invoice
   (linked to the tenancy so it flows into the Owners Statement as income).

**Meter Management (Electricity / Water / Gas)**
 * Register meters per property/unit with a recharge product and tariff.
 * Record sequential readings (auto previous reading, consumption & amount).
 * One-click recharge invoice to the tenant (linked to the tenancy).
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/product_data.xml',
        'views/gto_views.xml',
        'views/meter_views.xml',
        'views/tenancy_gto_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
