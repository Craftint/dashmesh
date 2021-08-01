// Copyright (c) 2016, Roshna and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Reorder level report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			"get_query": function() {
				var item_group = frappe.query_report.get_filter_value('item_group');
				if(item_group){
					return {
						filters: {
							'item_group': item_group
						}
					};
				}
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Warehouse",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				if(company){
					return {
						filters: {
							'company': company
						}
					};
				}
			}
		},


	]
};

