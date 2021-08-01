import frappe
from frappe import _
from frappe.utils import cint, flt, cstr, comma_or

def set_profit(doc, handler=None):
	for item in doc.items:
		if item.net_amount != 0:
			item.profit_margin = flt((item.gross_profit/item.net_amount)*100)

@frappe.whitelist()
def get_profit(net=None,profit=None):
	net_amount = flt(net)
	gross_profit = flt(profit)
	margin = 0.0
	if net_amount != 0:
		margin = (gross_profit/net_amount)*100
	return margin

def check_reservation(doc,handler=None):
	for item in doc.items:
		db_exist = frappe.db.exists({
					"doctype": "Bin",
					"item_code": item.item_code,
					"warehouse": item.warehouse,
		})
		if db_exist:
			item_bin = frappe.get_doc("Bin",db_exist[0][0])
			available_qty = item_bin.actual_qty - item_bin.reserved_qty
			if item.qty > available_qty:
				frappe.throw(
					msg = _(f'Available quantity for item code {item.item_code} is only {available_qty}. Please choose quantity less than or equal to available quantity'),
					title= 'Item not available',
				)
	frappe.msgprint("All quantities has been reserved!")