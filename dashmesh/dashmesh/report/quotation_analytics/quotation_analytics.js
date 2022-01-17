// Copyright (c) 2016, Roshna and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Quotation Analytics"] = {
	"filters": [
		{
			fieldname:"quot",
			label: __("Quotation"),
			fieldtype: "Link",
			options: "Quotation",
			reqd:1
		},

	]
};
