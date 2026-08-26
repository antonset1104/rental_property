# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Move-in / Fit-out / Move-out",
    'summary': "Tenant handover workflow (move-in, fit-out, move-out) with "
               "checklists, condition reports and document management.",
    'description': """
Move-in / Fit-out / Move-out (Handover Management)
==================================================
Companion module for the TechKhedut *rental_management* addon that manages the
physical handover lifecycle of a leased space (IFCA RentX "Move in, Fit Out and
Move Out – Legal Documents Management").

Features:
 * One handover record per event: Move-in, Fit-out or Move-out.
 * Type-specific fields: contractor & fit-out bond/dates, condition reports,
   make-good, keys issued/returned.
 * Editable checklists with one-click default templates per handover type and a
   completion progress bar.
 * Document management via the chatter (attach condition reports, drawings,
   insurance certificates, permits, make-good evidence).
 * Lifecycle: Draft → In Progress → Completed / Cancelled.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/handover_views.xml',
        'views/tenancy_handover_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
