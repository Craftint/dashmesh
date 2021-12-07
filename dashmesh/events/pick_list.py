from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
import frappe.defaults

def set_warehouses(doc, handler =None):
	loc_list = []
	item_dict = {}
	for item in doc.locations:
		if item.sales_order:
			if item.item_code not in item_dict.keys():
				item_dict.update({item.item_code : [item.sales_order_item]})
				loc_list.append(item)
			else:
				if item.sales_order_item not in item_dict[item.item_code]:
					item_dict[item.item_code].append(item.sales_order_item)
					loc_list.append(item)
	doc.locations = loc_list

	for item in doc.locations:
		if item.sales_order_item:
			so_item = frappe.get_doc("Sales Order Item",item.sales_order_item)
			db_exist = frappe.db.exists({
						"doctype": "Bin",
						"item_code": item.item_code,
						"warehouse": so_item.warehouse,
			})
			if db_exist:
				item_bin = frappe.get_doc("Bin",db_exist[0][0])
				actual_qty = item_bin.actual_qty
				item.warehouse = so_item.warehouse
				if actual_qty <= so_item.qty:
					item.qty = actual_qty
					item.stock_qty = actual_qty
					item.picked_qty = actual_qty
				else:
					item.qty = so_item.qty
					item.stock_qty = so_item.qty
					item.picked_qty = so_item.qty
	
	for item in doc.locations:
		if item.qty == 0:
			doc.locations.remove(item)

	sl_no = 1
	for sl in doc.locations:
		sl.idx = sl_no
		sl_no+=1

					