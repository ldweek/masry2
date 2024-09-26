# -*- coding: utf-8 -*-
{
    'name': "Material Request",

    'summary': 'This module contains handling of Material Request',

    'description': """
        This module contains handling of Material Request
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock', 'green_contracts', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_material_request.xml',
        'views/product_warehouse.xml',
        'views/purchase.xml',
        'views/material_request.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
