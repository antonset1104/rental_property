# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Access Cards & Visitors",
    'summary': "Tenant access/parking card register and visitor check-in log.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': ['security/ir.model.access.csv', 'views/access_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
