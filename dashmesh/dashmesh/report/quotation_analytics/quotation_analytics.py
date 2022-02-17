# Copyright (c) 2013, Roshna and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns=[
			{
				"label": "Item Code",
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width":100
			},
			{
				"label": "Item Name",
				"fieldname": "item_name",
				"fieldtype": "Data",
				"width":160
			},
			{
				"label": "Qty",
				"fieldname": "qty",
				"fieldtype": "Float",
				"width":80
			},
			{
				"fieldname": "rate",
				"label": _("Sales Price"),
				"fieldtype": "Currency",
				"width":100
			},
			{
				"fieldname": "last_sold_price",
				"label": _("Last Sold Price"),
				"fieldtype": "Currency",
				"width":110
			},
			{
				"fieldname": "last_sold_date",
				"label": _("Last Sold Date"),
				"fieldtype": "Date",
				"width":110
			},
			{
				"fieldname": "valuation_rate",
				"label": _("Average Cost"),
				"fieldtype": "Currency",
				"width":100
			},
			{
				"fieldname": "last_purchase_price",
				"label": _("Last Purchase Price"),
				"fieldtype": "Currency",
				"width":140
			},
			{
				"fieldname": "last_purchase_date",
				"label": _("Last Purchase Date"),
				"fieldtype": "Date",
				"width":140
			},
		]

	warehouse_list = get_warehouse_list(filters)

	for wh in warehouse_list:
		columns += [
			{
				"fieldname":wh.name,
				"label": _(wh.name),
				"fieldtype": "Float",
				"width":140
			}
		]

	if len(warehouse_list) > 1:
		columns += [
			{
				"fieldname": "total_stock",
				"label": _("Total Stock"),
				"fieldtype": "Float",
				"width":140
			},
			{
				"fieldname": "req_qty",
				"label": _("Required Qty"),
				"fieldtype": "Float",
				"width":140
			}
		]

	columns += [
			{
				"fieldname": "margin_cost",
				"label": _("Margin on Average Cost(%)"),
				"fieldtype": "Float",
				"width":180
			},
		]


	return columns

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


def get_data(filters):
	data = []

	quot_items = frappe.db.get_list("Quotation Item", {"parent": filters.get("quot")},['item_code','item_name','qty','base_rate','warehouse'])
	customer = frappe.db.get_value('Quotation',{'name':filters.get('quot')},'customer_name')
	warehouse_list = get_warehouse_list(filters)

	for item in quot_items:
		valuation_rate = frappe.db.sql("""
				SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
				AND warehouse = %s AND valuation_rate > 0
				ORDER BY posting_date DESC, posting_time DESC, creation DESC LIMIT 1
				""", (item.item_code, item.warehouse))
		if not valuation_rate:
			val_rate = [[0.00]]
		else:
			val_rate = valuation_rate

		last_sold = frappe.db.sql(
			"""select base_rate,posting_date from `tabSales Invoice Item` sid inner join `tabSales Invoice` si 
			on sid.parent= si.name where sid.item_code = '{}' and si.customer_name = '{}' and si.docstatus != 2
			order by si.posting_date DESC""".format(
				item.item_code, customer),as_dict=1)

		if last_sold:
			last_sold_price = last_sold[0]['base_rate']
			last_sold_date = last_sold[0]['posting_date']
		else:
			last_sold_price = 0
			last_sold_date = ''


		last_purchase = frappe.db.sql(
			"""select base_rate,posting_date from `tabPurchase Invoice Item` sid inner join `tabPurchase Invoice` si 
			on sid.parent= si.name where sid.item_code = '{}' and si.docstatus != 2 
			order by si.posting_date DESC""".format(
				item.item_code),as_dict=1)
		if last_purchase:
			last_purchase_price = last_purchase[0]['base_rate']
			last_purchase_date = last_purchase[0]['posting_date']
		else:
			last_purchase_price = 0
			last_purchase_date = ''

		if item.base_rate != 0:
			margin = round(flt(((item.base_rate - val_rate[0][0])/item.base_rate))*100,3)
		else:
			margin = round((item.base_rate - item.val_rate[0][0]),3)

		row = {
			"item_code":item.item_code,
			"item_name":item.item_name,
			"qty":item.qty,
			"rate":item.base_rate,
			"last_sold_price":last_sold_price,
			"last_sold_date":last_sold_date,
			"valuation_rate":val_rate[0][0],
			"last_purchase_price":last_purchase_price,
			"last_purchase_date":last_purchase_date,
			"margin_cost":flt(margin)
		}
		
		total_st = req_qt = 0

		for wh in warehouse_list:
			act_qty = frappe.db.get_value('Bin',{'item_code': item.item_code, 'warehouse': wh.name}, 'actual_qty')
			res_qty = frappe.db.get_value('Bin',{'item_code': item.item_code, 'warehouse': wh.name}, 'reserved_qty')
			if act_qty or res_qty:
				avail_qty = act_qty - res_qty
			else:
				avail_qty = 0.00
			
			# avail_qty = frappe.db.get_value('Bin',{'item_code': item.item_code, 'warehouse': wh.name}, 'actual_qty')
			# row[wh.name] = avail_qty if avail_qty else 0.00
			# total_st += avail_qty if avail_qty else 0.00

			row[wh.name] = avail_qty
			total_st += avail_qty

		req_qt = item.qty - total_st

		row["total_stock"] = total_st
		row["req_qty"] = req_qt if req_qt > 0 else 0.00

		data.append(row)

	return data
