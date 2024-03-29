import frappe
from frappe import _
from frappe.utils import cint, flt, cstr, comma_or

def set_profit(doc, handler=None):
	t = margin = 0
	for item in doc.items:
		last_purchase_rate = 0
		profit_total = amount_total = net_profit_margin = 0
		valuation_rate = frappe.db.sql("""
				SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
				AND warehouse = %s AND valuation_rate > 0
				ORDER BY posting_date DESC, posting_time DESC, creation DESC LIMIT 1
				""", (item.item_code, item.warehouse))
		if valuation_rate:
			item.valuation_rate = valuation_rate[0][0]
			item.gross_profit = flt(((item.base_rate - valuation_rate[0][0]) * item.stock_qty))
			t += (valuation_rate[0][0] * item.stock_qty)
		last_purchase_rate = frappe.get_cached_value("Item", item.item_code, "last_purchase_rate")
		item.gross_profit_based_on_last_purchase_rate = flt(((item.base_rate - last_purchase_rate) * item.stock_qty))
		if item.base_net_amount != 0:
			item.profit_margin = flt((item.gross_profit/item.base_net_amount)*100)
		
		amount_total += item.base_net_amount;
		profit_total += item.gross_profit_based_on_last_purchase_rate

	if doc.base_total != 0:
		margin = (doc.base_total - t) 
		net_profit_margin = (margin/doc.base_total)*100
	# if profit_total != 0:
	# 	net_profit_margin = (amount_total/profit_total)*100

	doc.net_profit_margin = net_profit_margin

	frappe.db.set_value("Quotation",doc.name,"net_profit_margin",net_profit_margin)
   

@frappe.whitelist()
def get_profit(item=None,wh=None,base_rate=0,stock_qty=0,net=None,profit=None):
	last_purchase_rate = 0
	gross_profit = flt(profit)
	item_doc = frappe.get_doc("Item",item)
	val_rate = 0
	valuation_rate = frappe.db.sql("""
			SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
			AND warehouse = %s AND valuation_rate > 0
			ORDER BY posting_date DESC, posting_time DESC, creation DESC LIMIT 1
			""", (item_doc.item_code, wh))

	net_amount = flt(net)
	if valuation_rate:
		val_rate = valuation_rate[0][0]
		gross_profit = flt((flt(base_rate) - valuation_rate[0][0]) * flt(stock_qty))
	last_purchase_rate = frappe.get_cached_value("Item", item_doc.item_code, "last_purchase_rate")
	gross_profit_purchase_rate = flt((flt(base_rate) - last_purchase_rate) * flt(stock_qty))
	margin = 0.0
	if net_amount != 0:
		margin = flt((gross_profit/net_amount)*100)
	return [margin,gross_profit,gross_profit_purchase_rate,last_purchase_rate,val_rate]