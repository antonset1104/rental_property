# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Tenant Bank & Insurance Guarantees",
    'summary': "Track tenant bank guarantees / insurance bonds with expiry "
               "reminders and lifecycle (active, expiring, expired, released, claimed).",
    'description': """
Tenant Bank & Insurance Guarantee Management
============================================
Companion module for the TechKhedut *rental_management* addon that registers the
security instruments a tenant lodges against a lease (bank guarantee, insurance
bond, etc.), tracks their value and expiry, and proactively reminds the
responsible user before they lapse.

Features:
 * Guarantee register linked to the tenancy contract.
 * Types: Bank Guarantee, Insurance Bond, Security Guarantee, Other.
 * Lifecycle: Draft → Active → (Expiring) → Expired / Released / Claimed.
 * Days-to-expiry indicator with list colour coding.
 * Daily scheduled action that auto-expires lapsed guarantees and schedules a
   reminder activity ahead of expiry (configurable lead time per guarantee).
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        'views/guarantee_views.xml',
        'views/tenancy_guarantee_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
