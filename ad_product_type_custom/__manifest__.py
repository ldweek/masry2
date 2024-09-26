# -*- coding: utf-8 -*-
{
    'name': "Product Type Customization",

    'summary': 'This module contains handling of Product Type Customization',

    'description': """
        This module contains handling of Product Type Customization as products storable take a feature from product service
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale_project', 'sale', 'green_contracts', 'project'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product.xml',
        'views/contract.xml',
        'views/task.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
