
# Copyright (c) 2013, Roshna and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate
from erpnext.stock.report.stock_balance.stock_balance import (get_item_details,
	get_item_reorder_details, get_item_warehouse_map, get_items, get_stock_ledger_entries)
from erpnext.stock.report.stock_ageing.stock_ageing import get_fifo_queue, get_average_age
from six import iteritems

def execute(filters=None):
	if not filters: filters = {}

	validate_filters(filters)

	columns = get_columns(filters)

	items = get_items(filters)
	sle = get_stock_ledger_entries(filters, items)

	item_map = get_item_details(items, sle, filters)
	iwb_map = get_item_warehouse_map(filters, sle)
	warehouse_list = get_warehouse_list(filters)
	item_ageing = get_fifo_queue(filters)
	data = []
	item_balance = {}
	item_value = {}

	for (company, item, warehouse) in sorted(iwb_map):
		if not item_map.get(item):  continue

		row = []
		qty_dict = iwb_map[(company, item, warehouse)]
		item_balance.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]), [])
		total_stock_value = 0.00
		for wh in warehouse_list:
			res_qty = 0
			row += [qty_dict.bal_qty] if wh.name in warehouse else [0.00]
			if wh.name in warehouse:
				res_qty = frappe.db.get_value('Bin',{'item_code': item, 'warehouse': wh.name}, 'reserved_qty')
			row += [res_qty] if res_qty else [0.00]
			total_stock_value += qty_dict.bal_val if wh.name in warehouse else 0.00

		item_balance[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(row)
		item_value.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]),[])
		item_value[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(total_stock_value)

	item_filters = ""

	if filters.get("item_code") is not None and filters.get("item_code") != "":
			item_filters += """ and ti.item_code = '{item_code}' """.format(item_code=filters.get("item_code"))
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


	# sum bal_qty by item
	for (item,item_name,item_group), wh_balance in iteritems(item_balance):
		if not item_ageing.get(item):  continue

		reserv_qty = 0
		avail_qty = 0
		total_stock_value = sum(item_value[(item,item_name,item_group)])
		row = [item,item_name,item_group]

		fifo_queue = item_ageing[item]["fifo_queue"]
		average_age = 0.00
		if fifo_queue:
			average_age = get_average_age(fifo_queue, filters["to_date"])

		row += [average_age]
		item_doc = frappe.get_doc("Item",item)
		row += [item_doc.bottles_per_crate]

		for r in bin_items:
			if r.item_code == item_doc.item_code:
				reserv_qty += r.reserved_qty
				avail_qty += r.available_qty
		row += [reserv_qty]
		row += [avail_qty]

		bal_qty = [sum(bal_qty) for bal_qty in zip(*wh_balance)]
		total_qty = sum(bal_qty)
		if len(warehouse_list) > 1:
			row += [total_qty]
			if total_qty == 0:
				row += [total_qty]
			else:
				row += [total_stock_value/total_qty]
			row += [total_stock_value]

		row += bal_qty
		if total_qty > 0:
			data.append(row)
		elif not filters.get("filter_total_zero_qty"):
			data.append(row)
	add_warehouse_column(columns, warehouse_list)
	return columns, data

def get_columns(filters):
	"""return columns"""

	columns = [
		_("Item")+":Link/Item:120",
		_("Item Name")+"::170",
		_("Item Group")+"::110",
		# _("Total Value")+"::110",
		_("Age")+":Float:80",
		_("No of Bottles")+":Float:80",
		_("Reserved Qty")+":Float:80",
		_("Available Qty")+":Float:80",
	]
	return columns

def validate_filters(filters):
	if not (filters.get("item_code") or filters.get("warehouse")):
		sle_count = flt(frappe.db.sql("""select count(name) from `tabStock Ledger Entry`""")[0][0])
		if sle_count > 500000:
			frappe.throw(_("Please set filter based on Item or Warehouse"))
	if not filters.get("company"):
		filters["company"] = frappe.defaults.get_user_default("Company")

def get_warehouse_list(filters):
	from frappe.core.doctype.user_permission.user_permission import get_permitted_documents

	condition = ''
	user_permitted_warehouse = get_permitted_documents('Warehouse')
	value = ()
	if user_permitted_warehouse:
		condition = "and name in %s"
		value = set(user_permitted_warehouse)
	elif not user_permitted_warehouse and filters.get("warehouse"):
		condition = "and name = %s"
		value = filters.get("warehouse")

	return frappe.db.sql("""select name
		from `tabWarehouse` where is_group = 0
		{condition}""".format(condition=condition), value, as_dict=1)

def add_warehouse_column(columns, warehouse_list):
	if len(warehouse_list) > 1:
		columns += [_("Total Qty")+":Int:100"]
		columns += [_("Per case value")+":Float:110"]
		columns += [_("Total Value")+":Float:110"]

	for wh in warehouse_list:
		columns += [_(wh.name)+":Int:140"]
		columns += [_(wh.name)+"\nReserved Qty"+":Int:200"]

