# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Lease Expiry & Renewal",
    'summary': "Lease expiry list/filters and automated renewal reminder activities.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management', 'mail'],
    'data': ['data/cron.xml', 'views/lease_expiry_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
