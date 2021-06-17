# -*- coding: utf-8 -*-
{
	'name': "eclo_account_advances_cars",
	'summary': "Controla y administra los anticipos modulo Anticipo",
	'description': "Permite crear un comprobamte contable de causacion de Anticipos automobiles",
	'author': "Eclosion ",
	'website': "http://www.eclosionit.com",
	'category': 'account',
	'version': '2021-06-11',
	'depends': ['base', 'account', 'eclo_crm_cars' ],
	 "data":['views/eclo_account_advances_view.xml',
		'security/ir.model.access.csv',  	 
	  ],
}
