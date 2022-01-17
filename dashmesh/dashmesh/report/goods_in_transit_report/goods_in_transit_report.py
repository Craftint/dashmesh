# Copyright (c) 2013, Roshna and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters):
	columns, data = [], []
	columns = [{
	"fieldname": "purchase_order",
	"label": _("Purchase Order ID"),
	"fieldtype": "Link",
	"options" : "Purchase Order"
	
	},
	{
	"fieldname": "git",
	"label": _("GIT ID"),
	"fieldtype": "Link",
	"options": "Goods In Transit Note",
	
	
	},
	{
	"fieldname": "supplier_name",
	"label": _("Supplier Name"),
	"fieldtype": "Link",
	"options": "Supplier",
	
	
	},
	{
	"fieldname": "grn",
	"label": _("GRN ID"),
	"fieldtype": "Link",
	"options": "Purchase Receipt",
	
	
	},
	{
	"fieldname": "posting_date",
	"label": _("Date"),
	"fieldtype": "date",
	"width": "80"
	
	},
	{
		"fieldname": "invoiced_by",
		"label": _("Invoiced By"),
		"fieldtype": "Link",
		"options": "Supplier",
		"width": "90"
	
	}]
	if filters.show_goods_in_transit_item:
			columns.extend([{
		"fieldname": "item_code",
		"label": _("Item Code"),
		"fieldtype": "Link",
		"options":"Item"
		
	},
	{
		"fieldname": "item_name",
		"label": _("Item Name"),
		"fieldtype": "Link",
		"options":"Item"
		
	},
	{
		"fieldname": "eta",
		"label": _("ETA"),
		"fieldtype": "Data",		
	},
	{
		"fieldname": "etd",
		"label": _("ETD"),
		"fieldtype": "Data",
	},
	{
		"fieldname": "status",
		"label": _("Status"),
		"fieldtype": "Select",
		"width": 100
	},
	{
		"fieldname": "warehouse",
		"label": _("warehouse"),
		"fieldtype": "Data",
		
		
	},
	{
		"fieldname": "actual_qty",
		"label": _("PO Qty"),
		"fieldtype": "Float",
	},
	{
		"fieldname": "qty",
		"label": _("GIT Qty"),
		"fieldtype": "Float",
		
	},
	{
		"fieldname": "pending_qty",
		"label": _("Pending Qty"),
		"fieldtype": "Float",
		
	},
	{
		"fieldname": "accepted_qty",
		"label": _("Accepted Qty"),
		"fieldtype": "Float",
		
	},
	{
		"fieldname": "rate",
		"label": _("Rate"),
		"fieldtype": "Float",
		
		
	},
	{
		"fieldname": "amount",
		"label": _("Amount"),
		"fieldtype": "Currency",
		"width": "100"
		
		
	}

	])
	
	columns.extend([{
		"fieldname": "invoiced_to",
		"label": _("Invoiced To"),
		"fieldtype": "Link",
		"options": "Company",
		"width": "130"
		
	},
	{
		"fieldname": "company",
		"label": _("Company"),
		"fieldtype": "Link",
		"options": "Company",
		"width": "130"
		
		
	},
	])
	
	data = get_data(filters)
	return columns,data
	
def get_data(filters):
	p_filter = {}
	c_filter={}
	data = []
	if filters.get("name"):
		p_filter["name"] = filters.get("name")
	
	if filters.get("posting_date"):
		p_filter["posting_date"] = filters.get("posting_date")

	if filters.get("eta"):
		p_filter["eta"] = ['between',filters.get('eta')]

	if filters.get("etd"):
		p_filter["etd"] = ['between',filters.get('etd')]
	
	if filters.get("item"):
		c_filter["item_code"] = filters.get('item')

	doclist = frappe.db.get_list('Goods In Transit Note',p_filter)
	for x in doclist:
		docname = x.name
		doc = frappe.get_doc('Goods In Transit Note', docname)
		for y in doc.items:
			filter ={}
			q_filter={
				'goods_in_transit_note': doc.name,
				'item_code':y.item_code 
			}
			accepted_qty = frappe.db.get_value('Purchase Receipt Item', q_filter, ['qty'])
			if accepted_qty is None:
				accepted_qty = 0
			purchase_order =frappe.db.get_value('Purchase Order Item',{'parent':y.purchase_order}, ['qty'])
			grn =frappe.db.get_value('Purchase Receipt Item',{'goods_in_transit_note':doc.name}, ['parent'])
			item = frappe.get_doc('Item', y.item_code)
			if c_filter:
				if item.item_code == c_filter['item_code'] :	
					data.append({
						'purchase_order' : y.purchase_order,
						'git' : doc.name,
						'supplier_name':doc.supplier_name,
						'grn' : grn,
						'posting_date' : doc.posting_date,
						'invoiced_by' : doc.invoiced_by,
						'invoiced_to': doc.invoiced_to,
						'item_code' : y.item_code,
						'item_name' : item.item_name,
						'warehouse' : y.warehouse,
						'actual_qty': purchase_order,
						'qty' : y.qty,
						'pending_qty': y.qty-accepted_qty,
						'accepted_qty': accepted_qty,
						'rate' : y.rate,
						'amount' : y.amount,
						'eta':doc.eta,
						'etd':doc.etd,
						'company' : doc.company, 
						'status' : doc.status
					})
			else:
				data.append({
					'purchase_order' : y.purchase_order,
					'git' : doc.name,
					'supplier_name':doc.supplier_name,
					'grn' : grn,
					'posting_date' : doc.posting_date,
					'invoiced_by' : doc.invoiced_by,
					'invoiced_to': doc.invoiced_to,
					'item_code' : y.item_code,
					'item_name' : item.item_name,
					'warehouse' : y.warehouse,
					'actual_qty': purchase_order,
					'qty' : y.qty,
					'pending_qty': y.qty-accepted_qty,
					'accepted_qty': accepted_qty,
					'rate' : y.rate,
					'amount' : y.amount,
					'eta':doc.eta,
					'etd':doc.etd,
					'company' : doc.company, 
					'status' : doc.status
				})
								
	return data
