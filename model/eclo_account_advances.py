# -*- coding: utf-8 -*-
#-----------------------------------------------------
#  Eclosion 
#  Carlos Alberto Navarrete 
#  Cambia los esquemas de tipo de cambio.
#  2021-06-11
#    
#-----------------------------------------------------
# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, date, timedelta
from openerp.osv import osv
import logging
_logger = logging.getLogger(__name__)

class account_advances(models.Model):
	_name = 'account.advances'	
	_inherit = ['mail.thread']
	_description = 'Tabla de echos anticipos'   
	name = fields.Char('Nombre', requerid=True,)
	state = fields.Selection([('1', 'Borrador'),
							('2', 'Validado'),
							('3', 'Rechazado'),], 
			string="Estado", track_visibility='onchange' )
	date = fields.Date('Fecha')
	type_id = fields.Many2one('account.advances_type', string='Concepto', requerid=True)
	order_id = fields.Many2one('purchase.order', string='Orden Compra',)
	partner_id = fields.Many2one('res.partner', string='Proveedor', requerid=True)
	journal_id = fields.Many2one('account.journal', string='Diario', requerid=True)
	bank_journal_id = fields.Many2one('account.journal', string='Diario Banco', requerid=True)

	period_id = fields.Many2one('account.period', string='Periodo', requerid=True)
	move_id = fields.Many2one('account.move', string='Asiento Contable',)
	amount = fields.Float('Valor')
	info = fields.Text('Descripcion')
	advances_ids=fields.One2many('account.advances_line', 'advances_line_id', "Advances")

	@api.multi
	def set_conciliar(self):
		sw=0
#		self.move_id=move_id.id
		total_tramite=0
		for i in self.advances_ids:
			if i.state=='1':

				if not i.cuenta_analitica_id: 
					raise osv.except_osv(_('Error!'), _('Revise las cuentas analiticas'))
				if not i.product_id: 
					raise osv.except_osv(_('Error!'), _('Revise los productos'))
				if not i.partner_id: 
					raise osv.except_osv(_('Error!'), _('Revise los Proveedores'))
				if not i.name: 
					raise osv.except_osv(_('Error!'), _('Revise las Referencias'))
				if not i.date: 
					raise osv.except_osv(_('Error!'), _('Revise las Fechas de la transaccion'))
				if i.valor<=0: 
					raise osv.except_osv(_('Error!'), _('Revise los Valores '))

				if sw==0:	
					move_ds= {
					'journal_id':self.journal_id.id,
					'ref': 'Conciliacion Anticipos ' + self.name, 
					}
					move_id = self.env['account.move'].create(move_ds)	
					sw=1

				cuenta_id=i.product_id.categ_id.property_account_expense_categ.id
				purchase_ds=self.env['car.purchase'].search([('cuenta_analitica_id','=',i.cuenta_analitica_id.id)])

				if purchase_ds:
					purchase_id=self.env['car.purchase'].browse(purchase_ds.id)
					if purchase_id:
						c_gastos=i.product_id.categ_id.property_account_expense_categ.id
						if  purchase_id.tipo_contrato=='1':	
							if purchase_id.sale_id.factura_id:     		
								cuenta_id=i.product_id.categ_id.property_account_income_categ.id	

				i.state='2'
				total_tramite+=i.valor
				move_line_ds= {
					'move_id':move_id.id,
					'name':  i.product_id.name + '-'  + i.name,
					'account_id':cuenta_id,
					'analytic_account_id':i.cuenta_analitica_id.id,
					'partner_id':i.partner_id.id,
					'credit':0,
					'debit':i.valor, 
					'ref':'Conciliacion-' +  i.name,
					}
				move_line_id = self.env['account.move.line'].create(move_line_ds)			

		move_line_ds1= {
			'move_id':move_id.id,
			'name': 'Conciliacion' + str(self.name),
			'partner_id':self.partner_id.id,
			'account_id':self.journal_id.default_debit_account_id.id,
			'credit':total_tramite,
			'debit':0, 
			'ref':'Conciliacion ',
			}
		move_line_id = self.env['account.move.line'].create(move_line_ds1)			
		return True

	@api.one
	def unlink(self):
		if self.state!='1':
			raise osv.except_osv(_('Error!'), _('EL anticipo debe estar en Borrador, para poder eliminarlo'))	
		return super(account_advances, self).unlink()

	@api.model
	def create(self, vals):
		rec=super(account_advances, self).create(vals)
		rec.state='1'
		rec.name = rec.type_id.name + '-' + str(rec.id)
 		return rec

	@api.one
	def set_rechazar(self):
		self.state='3'

	@api.one
	def set_confirmar(self):
		self.state='2'

# Crea Cabecera de Comprobantes
		move= {
			'name':self.name,
			'journal_id':self.bank_journal_id.id,
			}

		move_id = self.env['account.move'].create(move)	
		self.move_id=move_id.id

# Detalles 
		move_line={
			'name':self.name,
			'move_id':move_id.id,
			'account_id':self.type_id.account_id.id,
			'partner_id':self.partner_id.id,
			'debit':self.amount,
			'credit':0,
			}
		move_line_id = self.env['account.move.line'].create(move_line)		

		move_line2={
			'name':self.name,
			'move_id':move_id.id,
			'account_id':self.bank_journal_id.default_credit_account_id.id,
			'partner_id':self.partner_id.id,
			'debit':0,
			'credit':self.amount,
			}
		move_line_id = self.env['account.move.line'].create(move_line2)		
		return 	

class account_advances_line(models.Model):
	_name = 'account.advances_line'
	_description = 'Detalle anticipos '   

	name = fields.Char('Referencia', requerid=True )
	product_id = fields.Many2one('product.product', 'Producto', requerid=True )
	partner_id = fields.Many2one('res.partner', 'Proveedor', requerid=True )
	valor = fields.Float('Valor', requerid=True)
	date = fields.Date('Fecha',requerid=True)
	cuenta_analitica_id=fields.Many2one('account.analytic.account','Cuenta Analitica', requerid=True)
	advances_line_id=fields.Many2one('account.advances','Avance', requerid=True)
	state = fields.Selection([('1', 'Borrador'), ('2', 'Validado'),],string="Estado", default='1')

class account_advances_type(models.Model):
	_name = 'account.advances_type'
	_description = 'Tabla conceptos  anticipos'   
	name = fields.Char('Nombre', requerid=True,)
	purchase_order = fields.Boolean('Requiere Orden De compra',)
	account_id = fields.Many2one('account.account', string='Cuenta', )	
