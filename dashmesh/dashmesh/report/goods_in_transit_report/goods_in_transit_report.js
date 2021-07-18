// Copyright (c) 2016, Roshna and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Goods In Transit Report"] = {
	"filters": [
		{
			'label': 'Name',
			'fieldname': 'name',
			'fieldtype': 'Link',
			'options': 'Goods In Transit Note'
			
		},
		// {
		// 	'label': 'Status',
		// 	'fieldname': 'status',
		// 	'fieldtype': 'Select',
		// 	'options' : 'Draft\nTo Receive\nPartially Received\nReceived'
			
		// },
		{
			'label': 'Date',
			'fieldname': 'posting_date',
			'fieldtype': 'Date',
			
		},
		{
		'label': 'Item',
		'fieldname': 'item',
			'fieldtype': 'Link',
			'options':'Item',
			
		},
		{
			'label': 'Item Origin',
			'fieldname': 'item_origin',
			'fieldtype': 'Data',
			
		},
		{
			'label': 'ETA',
			'fieldname': 'eta',
			'fieldtype': 'Date Range',
			
		},
		{
			'label': 'ETD',
			'fieldname': 'etd',
			'fieldtype': 'Date Range',
			
		},
		{
			"fieldname": "show_goods_in_transit_item",
			"label": __("Show Goods In Transit Item"),
			"fieldtype": "Check",
			"default": 1,
			on_change: () => {
				$('button[data-label="Refresh"]').click();
			}
		},
	],
	onload: function (report){
		frappe.breadcrumbs.add("Stock", "Goods In Transit Note");
	}
};
