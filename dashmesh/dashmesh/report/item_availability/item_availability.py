# Copyright (c) 2013, Roshna and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []

	columns = [
		{
			"fieldname": "item_code",
			"label": _("Item"),
			"fieldtype": "Link",
			"options":"Item",
			"width": "120",
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Link",
			"options":"Item",
			"width": "120",
			
		},
		{
			"fieldname": "item_group",
			"label": _("Item Group"),
			"fieldtype": "Link",
			"options":"Item Group",
			"width": "120",
		},
		{
			"fieldname": "warehouse",
			"label": _("Warehouse"),
			"fieldtype": "Link",
			"options":"Warehouse",
			"width": "120",
		},
		{
			"fieldname": "actual_qty",
			"label": _("Actual Qty"),
			"fieldtype": "Float",
		},
		{
			"fieldname": "reserved_qty",
			"label": _("Reserved Qty"),
			"fieldtype": "Float",
		},
		{
			"fieldname": "available_qty",
			"label": _("Available Qty"),
			"fieldtype": "Float",
		},
		{
			"fieldname": "ordered_qty",
			"label": _("Ordered Qty"),
			"fieldtype": "Float",
		},
	]
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	item_filters = ""

	if filters.get("item") is not None and filters.get("item") != "":
		item_filters += """ and ti.item_code = '{item_code}' """.format(item_code=filters.get("item"))
	if filters.get("item_group") is not None and filters.get("item_group") != "":
		item_filters += """ and ti.item_group = '{item_group}' """.format(item_group=filters.get("item_group"))
	if filters.get("warehouse") is not None and filters.get("warehouse") != "":
		item_filters += """ and tb.warehouse = '{warehouse}' """.format(warehouse=filters.get("warehouse"))

	bin_items = frappe.db.sql(""" select 
										ti.item_code,
										ti.item_name,
										ti.item_group,
										tb.warehouse,
										tb.actual_qty,
										tb.reserved_qty,
										(tb.actual_qty - tb.reserved_qty) as available_qty,
										tb.ordered_qty
									from
										`tabItem` ti
									left join `tabBin` tb on
										ti.item_code = tb.item_code
									WHERE
										tb.docstatus = 0 {item_filters}
									""".format(item_filters=item_filters), as_dict=True)

	for row in bin_items:
		record = {
					'item_code': row.item_code,
					'item_name': row.item_name,
					'item_group': row.item_group,
					'warehouse': row.warehouse,
					'actual_qty': row.actual_qty,
					'reserved_qty': row.reserved_qty,
					'available_qty': row.available_qty,
					'ordered_qty': row.ordered_qty,
					}
		data.append(record)

	return data
