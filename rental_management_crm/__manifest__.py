# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Leasing CRM Pipeline",
    'summary': "Tenant/leasing pipeline on Odoo CRM with one-click lease "
               "contract creation from a lead.",
    'description': """
Leasing CRM Pipeline
====================
Extends Odoo **CRM** for prospective-tenant management on top of the
*rental_management* addon (the base addon already links a lead to a property):

 * Leasing fields on the lead (expected move-in, expected rent, lease months).
 * One-click **Create Lease Contract** that opens a new tenancy contract
   pre-filled from the lead (property + tenant).
 * Lease Contracts smart button (contracts for the lead's contact).
 * A dedicated "Property Leasing" sales team and a "Leasing" tag.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'crm'],
    'data': [
        'data/crm_data.xml',
        'views/crm_lead_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
