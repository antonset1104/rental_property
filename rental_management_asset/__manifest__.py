# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Fixed Assets & Depreciation",
    'summary': "Property fixed-asset register with depreciation (straight-line / "
               "declining), revaluation, and CORETAX L9 sync.",
    'description': """
Fixed Assets, Depreciation & Revaluation
========================================
Community-compatible fixed-asset management for the *rental_management* addon
(Odoo's native asset accounting is Enterprise-only).

Features:
 * Asset register linked to a property (acquisition value, salvage, method).
 * Depreciation board (straight-line or declining balance) with posting of
   periodic journal entries (Dr Depreciation Expense / Cr Accumulated
   Depreciation), tagged to the property so it flows into the Owners Statement
   and analytic accounting.
 * Daily scheduled action to auto-post due depreciation lines.
 * **Asset revaluation** (upward/downward) with journal posting against a
   revaluation reserve and prospective recomputation of the remaining board.
 * One-click sync to the CORETAX L9 (Depreciation/Amortization) register when
   the coretax module is installed.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Accounting/Accounting',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        'views/asset_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
