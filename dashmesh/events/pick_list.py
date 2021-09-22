from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
import frappe.defaults

def set_warehouses(doc, handler =None):
	for item in doc.locations:
		if item.sales_order_item:
			so_item = frappe.get_doc("Sales Order Item",item.sales_order_item)
			item.warehouse = so_item.warehouse