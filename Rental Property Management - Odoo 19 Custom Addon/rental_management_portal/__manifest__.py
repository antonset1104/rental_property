# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Tenant Portal",
    'summary': "Self-service portal for tenants to view their lease contracts "
               "and invoices.",
    'description': """
Tenant Portal
=============
Companion module for the TechKhedut *rental_management* addon that gives tenants
a self-service area under /my (IFCA RentX "Tenant Portal/App"):

 * "Contracts" card on the portal home with a live count.
 * /my/contracts — paginated list of the tenant's own lease contracts.
 * /my/contracts/<id> — contract detail (rent, term, dates, property) with a
   shortcut to the tenant's invoices.
 * Record rules ensure a portal user only ever sees their own contracts.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'portal', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_security.xml',
        'views/portal_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
