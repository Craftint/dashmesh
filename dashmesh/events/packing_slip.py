import frappe
from frappe import _
from frappe.utils import cint, flt, cstr, comma_or

def set_total_volume(doc, handler=None):
	total = 0
	for item in doc.items:
		if item.stock_uom in ['Case','Case(s)']:
			item_doc = frappe.get_doc("Item",item.item_code)
			total += flt(item_doc.volume) * flt(item.qty)
	doc.total_volume = total 
