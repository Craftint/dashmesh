# Copyright (c) 2013, Mohammad ALi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import getdate, flt

def execute(filters=None):
	columns, data = [], []

	columns = get_columns()
	items = get_item_info(filters)

	for item in items:
		wh = frappe.get_doc("Warehouse",item.warehouse)
		row = {
			"item_code": item.item_code,
			"item_name": item.name,
			"item_group": item.item_group,
			"saftey_stock": item.saftey_stock,
			"chk_warehouse": item.warehouse_group,
			"req_warehouse": item.warehouse,
			"reorder_level":item.warehouse_reorder_level,
			"reorder_qty":item.warehouse_reorder_qty,
			"mr_type": item.material_request_type,
			"company": wh.company
		}
		data.append(row)

	return columns, data

def get_columns():
	"""return columns"""
	columns = [
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 150},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 100},
		{"label": _("Saftey Stock"), "fieldname": "saftey_stock", "fieldtype": "Float", "width": 110},
		{"label": _("Check In"), "fieldname": "chk_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 120},
		{"label": _("Request for"), "fieldname": "req_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
		{"label": _("Reorder Level"), "fieldname": "reorder_level", "fieldtype": "Float", "width": 110, "convertible": "qty"},
		{"label": _("Reorder Qty"), "fieldname": "reorder_qty", "fieldtype": "Float", "width": 90, "convertible": "qty"},
		{"label": _("MR Type"), "fieldname": "mr_type", "fieldtype": "Select","options":"\nPurchase\nTransfer\nMaterial Issue\nManufacture", "width": 90},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120}
	]

	return columns

def get_item_info(filters):
	conditions = ""
	if filters.get("item_group"):
		conditions += "AND item.item_group ='%s'" %filters.item_group
	if filters.get("item_code"):
		conditions += "AND item.item_code='%s'" %filters.item_code
	if filters.get("warehouse"):
		conditions += "AND reorder.warehouse='%s'" %filters.warehouse

	import os
	clear = lambda: os.system('clear')
	clear()

	items = []
	if conditions:
		items = frappe.db.sql("""
			SELECT
				item.item_code,item.name, item.item_group, item.safety_stock,
				reorder.warehouse_group, reorder.warehouse, reorder.warehouse_reorder_level, reorder.warehouse_reorder_qty,
				reorder.material_request_type
			FROM
				`tabItem` item, `tabItem Reorder` reorder
			JOIN
				`tabWarehouse` wh
			ON
				reorder.warehouse_group = wh.name
			WHERE
				item.name = reorder.parent
				%s"""
			% conditions, as_dict=1)
	else:
		items = frappe.db.sql("""
			SELECT
				item.item_code,item.name, item.item_group, item.safety_stock,
				reorder.warehouse_group, reorder.warehouse, reorder.warehouse_reorder_level, reorder.warehouse_reorder_qty,
				reorder.material_request_type
			FROM
				`tabItem` item, `tabItem Reorder` reorder
			JOIN
				`tabWarehouse` wh
			ON
				reorder.warehouse_group = wh.name
			WHERE
				item.name = reorder.parent""", as_dict=1)

	return items