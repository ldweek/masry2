# -*- coding: utf-8 -*-
{
    'name': "MO Request",

    'summary': 'This module contains handling of MO Request',

    'description': """
        This module contains handling of MO Request
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp', 'green_contracts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_mo_request.xml',
        'views/mo_request.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
