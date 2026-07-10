# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Documents (Property Folders)",
    'summary': "Organise property files in Odoo Documents: one folder per property.",
    'description': """
Property Documents (Odoo Documents integration)
==============================================
Bridges the *rental_management* addon with the Odoo **Documents** app
(Enterprise). Creates a Documents folder per property and lets you push the
property's attachments into it for centralised, shareable document management.

NOTE: Requires the Enterprise *documents* app. Targets the Odoo 19 unified
``documents.document`` model (folders are documents of type 'folder').
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'documents'],
    'data': [
        'views/property_documents_views.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False,
}
