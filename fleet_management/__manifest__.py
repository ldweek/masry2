# -*- coding: utf-8 -*-
{
    'name': "Fleet Management",

    'summary': 'This module contains handling of Fleet Management',

    'description': """
        This module contains handling of Fleet Management
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'hr', 'green_contracts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/access_right.xml',
        'data/sequence.xml',
        'views/fleet_expenses.xml',
        'views/city.xml',
        'views/fleet_management.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
