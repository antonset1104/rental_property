# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Preventive Maintenance (PPM)",
    'summary': "Scheduled preventive maintenance plans that auto-generate "
               "maintenance requests, with SLA.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': ['security/ir.model.access.csv', 'data/cron.xml', 'views/ppm_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
