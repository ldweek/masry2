# -*- coding: utf-8 -*-
{
    'name': "Transfer request to Distortion",

    'summary': 'This module contains handling of Transfer request to Distortion',

    'description': """
        This module contains handling of Transfer request to Distortion
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'green_contracts', ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_distortion.xml',
        'views/contract.xml',
        'views/distortion.xml',
        'wizard/transfer.xml',
        'views/types_model.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
