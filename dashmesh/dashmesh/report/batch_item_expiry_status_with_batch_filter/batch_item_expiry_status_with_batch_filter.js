// Copyright (c) 2016, Roshna and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Batch Item Expiry Status with batch filter"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.sys_defaults.year_start_date,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					filters: {
						"has_batch_no": 1
					}
				}
			}
		},
		{
			"fieldname":"batch_no",
			"label": __("Batch No"),
			"fieldtype": "Link",
			"options": "Batch",
			"get_query": function() {
				let item_code = frappe.query_report.get_filter_value('item_code');
				if (item_code) {
					return {
						filters: {
							"item": item_code
						}
					}
				}
			}
		},
	]
}

