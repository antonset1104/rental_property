# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Property Valuation",
    'summary': "Periodic market valuation register per property with latest value.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': ['security/ir.model.access.csv', 'views/valuation_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
