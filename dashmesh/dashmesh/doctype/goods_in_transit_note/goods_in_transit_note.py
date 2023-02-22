# -*- coding: utf-8 -*-
# Copyright (c) 2020, Havenir and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
import datetime
from frappe.utils import date_diff


class GoodsInTransitNote(Document):
	def validate(self):
		self.calculate_item_total()
		self.checking_git()
	
	def checking_git(self):
		for row in self.items:
			git_qty = 0
			records = frappe.db.get_all("Goods In Transit Item", { "purchase_order": row.purchase_order, "item_code": row.item_code ,'docstatus':['!=',2]}, ["qty"])
			for record in records:
				git_qty += record.qty

			frappe.db.set_value('Purchase Order Item', { "parent": row.purchase_order, "item_code": row.item_code }, "git_qty", git_qty)
			frappe.db.commit()

	def before_save(self):
		if self.docstatus == 0:
			available = frappe.db.exists('Goods In Transit Note', self.name)
			if available:
				old_doc = frappe.get_doc('Goods In Transit Note', self.name)
				if old_doc.eta and old_doc.etd: 
					new_eta = datetime.datetime.strptime(self.eta, '%Y-%m-%d %H:%M:%S')
					new_etd = datetime.datetime.strptime(self.etd, '%Y-%m-%d %H:%M:%S')
					
					if old_doc.eta != new_eta or old_doc.etd != new_etd:
						all_eta = frappe.db.sql("""select previous_eta from `tabGoods In Transit History`
							where parent = %s order by modified asc""",(self.name),as_list = 1)
						if all_eta:
							first = all_eta[0]
							first = first[0]
							eta_dt = datetime.datetime.strptime(first, '%Y-%m-%d %H:%M:%S')
						else:
							first = old_doc.eta
							eta_dt = old_doc.eta
						self.total_delayed = date_diff(new_eta,eta_dt)
						self.append('history',{
							'previous_eta':old_doc.eta,
							'previous_etd':old_doc.etd,
							'delayed_by':date_diff(new_eta,old_doc.eta)
						})

	def on_submit(self):
		self.db_set('status', 'Waiting to Receive Items')
		self.update_purchase_order_items()

	def on_cancel(self):
		self.change_po_git_qty()
		self.update_purchase_order_on_cancel()
		

	def calculate_item_total(self):
		total_qty = 0
		total_amount = 0
		for row in self.items:
			total_qty += row.qty
			total_amount += row.amount
		
		self.total_qty = total_qty
		self.amount = total_amount
	
	def change_po_git_qty(self):
		for row in self.items:
			doc = frappe.get_doc('Purchase Order',row.purchase_order)
			for item in doc.items:
				if item.item_code == row.item_code:
					git_qty=item.git_qty-row.qty
			
			frappe.db.set_value('Purchase Order Item', { "parent": row.purchase_order, "item_code": row.item_code }, "git_qty", git_qty)
			frappe.db.commit()



	def update_purchase_order_items(self):
		'''validating items from the purchase order if they are still available'''		
		for row in self.items:
			if row.purchase_order:
				qty, dispatched_qty = frappe.db.get_value('Purchase Order Item', 
				{'name': row.purchase_order_item}, 
				['qty', 'dispatched_qty'])

				if (qty - dispatched_qty < row.qty):
					frappe.throw(f'Row# {row.idx}: {row.qty} quantity not available for item {row.item_code}')
				
				new_dispatched_qty = dispatched_qty + row.qty
				frappe.db.set_value('Purchase Order Item', row.purchase_order_item, 'dispatched_qty', new_dispatched_qty)
				self.update_purchase_order_goods_status(row)
	
	def update_purchase_order_goods_status(self, row):
		''' updates Purchase Order Goods Status 
			Goods Status = [To Dispatch, Partially Dispatched, Dispatched]
			if all goods dispatched then goods status = Dispatched
			if some goods dispatched then goods status = Partially Dispatched
		'''

		#Getting Purchase order document
		purchase_doc = frappe.get_doc('Purchase Order', row.purchase_order)
		total_dispatched_qty = 0
		for row in purchase_doc.items:
			total_dispatched_qty += row.dispatched_qty
		
		if total_dispatched_qty == purchase_doc.total_qty:
			purchase_doc.db_set('goods_status', 'Dispatched')
		elif total_dispatched_qty == 0:
			purchase_doc.db_set('goods_status', 'To Dispatch')
		else:
			purchase_doc.db_set('goods_status', 'Partially Dispatched')
		
	def update_purchase_order_on_cancel(self):
		for row in self.items:
			if row.purchase_order:
				dispatched_qty = frappe.db.get_value('Purchase Order Item', 
				{'name': row.purchase_order_item}, 
				['dispatched_qty'])

				new_dispatched_qty = dispatched_qty - row.qty
				frappe.db.set_value(
					'Purchase Order Item', 
					row.purchase_order_item, 
					'dispatched_qty', 
					new_dispatched_qty
				)
				self.update_purchase_order_goods_status(row)

	def get_items_from_purchase_order(self,selections):
		total_qty = 0
		amount = 0
		for doc_id in selections:
			purchase_order = frappe.get_doc('Purchase Order', doc_id)
			for row in purchase_order.items:
				if row.qty - row.git_qty > 0:
					qty = row.qty - row.git_qty
					item_amount = row.rate * qty
					self.append('items',{
						'item_code' :row.item_code,
						'item_name': row.item_name,
						'description': row.description,
						'warehouse': row.warehouse,
						'qty' :row.qty - row.git_qty, #row.dispatched_qty,
						'uom' :row.uom,
						'conversion_factor': row.conversion_factor,
						'stock_uom': row.stock_uom,
						'rate' :row.rate,
						'amount' :row.rate * qty,
						'purchase_order': purchase_order.name,
						'purchase_order_item': row.name,
						'actual_qty':row.qty - row.git_qty
					})
					total_qty += qty
					amount += item_amount
		self.total_qty = total_qty
		self.total = amount

	

				
		
		

		 
		
	
