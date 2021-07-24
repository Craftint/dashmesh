import frappe
from frappe.utils import cint, flt, cstr, comma_or

def set_profit(doc, handler=None):
	for item in doc.items:
		if item.gross_profit != 0:
			item.profit_margin = flt((item.net_amount/item.gross_profit)*100)

@frappe.whitelist()
def get_profit(net=None,profit=None):
	net_amount = flt(net)
	gross_profit = flt(profit)
	margin = 0.0
	if gross_profit != 0:
		margin = (net_amount/gross_profit)*100
	return margin
