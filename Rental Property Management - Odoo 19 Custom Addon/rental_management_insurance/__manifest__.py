# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Property Insurance",
    'summary': "Register building/property insurance policies with expiry reminders.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management', 'mail'],
    'data': ['security/ir.model.access.csv', 'data/sequence.xml', 'data/cron.xml',
             'views/insurance_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
