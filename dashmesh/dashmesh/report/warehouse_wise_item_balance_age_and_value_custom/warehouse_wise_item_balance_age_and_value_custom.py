
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

	item_filters = ""

	if filters.get("item_code") is not None and filters.get("item_code") != "":
			item_filters += """ and ti.item_code = '{item_code}' """.format(item_code=filters.get("item_code"))
	if filters.get("item_group") is not None and filters.get("item_group") != "":
		item_filters += """ and ti.item_group = '{item_group}' """.format(item_group=filters.get("item_group"))
	if filters.get("warehouse") is not None and filters.get("warehouse") != "":
		item_filters += """ and tb.warehouse = '{warehouse}' """.format(warehouse=filters.get("warehouse"))

	for (company, item, warehouse) in sorted(iwb_map):
		if not item_map.get(item):  continue
		row = []
		qty_dict = iwb_map[(company, item, warehouse)]
		bin_list = frappe.get_list('Bin', filters={'item_code': item, 'warehouse': warehouse}, fields=['actual_qty','reserved_qty'])


		item_balance.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]), [])
		total_stock_value = 0.00
		for wh in warehouse_list:
			res_qty = 0
			avl_qty = 0
			row += [qty_dict.bal_qty] if wh.name == warehouse else [0.00]
			if bin_list:
				row += [bin_list[0].reserved_qty] if wh.name == warehouse else [0.00]
				row += [(bin_list[0].actual_qty)-(bin_list[0].reserved_qty)] if wh.name == warehouse else [0.00]
			else:
				row += [0.00]
				row += [0.00]

			total_stock_value += qty_dict.bal_val if wh.name in warehouse else 0.00

		item_balance[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(row)
		item_value.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]),[])
		item_value[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(total_stock_value)


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
			average_age = get_average_age(fifo_queue, filters['to_date'])

		row += [average_age]
		item_doc = frappe.get_doc("Item",item)
		row += [item_doc.bottles_per_crate]

		res = [wh_balance[i] for i in range(len(wh_balance)) if i % 2 == 0]

		bal_qty = [sum(bal_qty) for bal_qty in zip(*wh_balance)]
		bal_qty_split = [bal_qty[i:i + 3] for i in range(0, len(bal_qty), 3)]
		actual = sum(list(map(float,[i[0] for i in bal_qty_split])))
		reserv = sum(list(map(float,[i[1] for i in bal_qty_split])))
		avail = sum(list(map(float,[i[2] for i in bal_qty_split])))

		total_qty = actual
		if len(warehouse_list) > 1:
			row += [reserv]
			row += [avail]
			row += [actual]
			if total_qty == 0:
				row += [actual]
			else:
				row += [total_stock_value/actual]
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
		_("Age")+":Float:80",
		_("No of Bottles")+":Float:80",
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
		columns += [_("Reserved Qty")+":Float:100"]
		columns += [_("Available Qty")+":Float:100"]
		columns += [_("Total Qty")+":Float:100"]
		columns += [_("Per case value")+":Float:110"]
		columns += [_("Total Value")+":Float:110"]

	for wh in warehouse_list:
		columns += [_(wh.name)+":Float:140"]
		columns += [_(wh.name)+"\nReserved Qty"+":Float:200"]
		columns += [_(wh.name)+"\nAvailable Qty"+":Float:200"]