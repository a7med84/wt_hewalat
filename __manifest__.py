# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Wide Techno Bank Transfers Search',
    'version': '2.0.0',
    'sequence': 0,
    'category': 'account',
    'author': 'Ahmed Addawody',
    'summary': 'Wide Techno Bank Transfers Search',
    'description': """System to search wide techno bank transfers""",
    'depends': ['base'],
    'data': [
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'views/wt_hewalat_bank_account_views.xml',
        'views/wt_hewalat_bank_transfer_views.xml',
        'views/wt_hewalat_menus.xml',
        'wizard/search_wizard_views.xml',
        'wizard/import_wizard_views.xml',
        'views/assets.xml'
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3'
}
