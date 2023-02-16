# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "dashmesh"
app_title = "Dashmesh"
app_publisher = "Roshna"
app_description = "Alcohol trading company"
app_icon = "octicon octicon-file-directory"
app_color = "blue"
app_email = "roshna@craftinteractive.ae"
app_license = "MIT"

fixtures = [
	{
	"dt":
	"Custom Field",
	"filters": [
			[
				"name", "in",
				[
					'Item-alcohol','Packing Slip Item-country_of_origin','Packing Slip Item-alcohol',
					'Purchase Order Item-git_qty','Purchase Receipt Item-transit_qty','Purchase Order Item-dispatched_qty',
					'Purchase Order-goods_status','Purchase Receipt Item-goods_in_transit_note','Purchase Receipt Item-goods_in_transit_note_item',
					'Sales Order Item-profit_margin','Sales Order-net_profit_margin','Item-bottles_per_crate','Item-volume',
					'Packing Slip-total_volume','Packing Slip Item-volume','Quotation Item-profit_margin',
					'Quotation-net_profit_margin','Purchase Receipt Item-batch_expiry','Purchase Receipt Item-batch_number',
					'Quotation Item-gross_profit_based_on_last_purchase_rate','Sales Order Item-gross_profit_based_on_last_purchase_rate','Quotation Item-last_purchase_rate',
					'Sales Order Item-last_purchase_rate','Quotation-warehouse'
				]
			]
		] 
	},
	{
		"dt":"Property Setter",
		"filters": [
			[
				"name", "in", [
					'Sales Order Item-delivery_date-in_list_view','Purchase Receipt Item-serial_no-in_list_view','Purchase Receipt Item-rate-columns',
					'Purchase Receipt Item-warehouse-in_list_view','Purchase Receipt Item-net_amount-in_list_view','Purchase Receipt Item-net_amount-columns',
					'Purchase Receipt Item-amount-columns','Purchase Receipt Item-base_rate-columns','Sales Order Item-gross_profit-label','Purchase Receipt Item-uom-columns',
					'Purchase Receipt Item-uom-in_list_view','Purchase Order Item-amount-columns','Purchase Order Item-uom-columns',
					'Purchase Order Item-uom-in_list_view','Sales Invoice Item-uom-columns','Sales Invoice Item-uom-in_list_view','Sales Invoice Item-qty-columns',
					'Sales Order Item-rate-columns','Sales Order Item-uom-columns','Sales Order Item-uom-in_list_view','Quotation Item-uom-columns','Quotation Item-rate-columns',
					'Quotation Item-uom-in_list_view',''

				]
			]
		]
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/css/dashmesh.min.css"
# app_include_js = "/assets/dashmesh/js/dashmesh.js"

# include js, css files in header of web template
# web_include_css = "/assets/dashmesh/css/dashmesh.css"
# web_include_js = "/assets/dashmesh/js/dashmesh.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Purchase Order" : "public/js/purchase_order.js",
    "Purchase Receipt" : "public/js/purchase_receipt.js",
    "Sales Order" : "public/js/sales_order.js",
    "Packing Slip":"public/js/packing_slip.js",
    "Quotation" : "public/js/quotation.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "dashmesh.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "dashmesh.install.before_install"
# after_install = "dashmesh.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dashmesh.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Receipt": {
		"on_submit": "dashmesh.events.purchase_receipt.update_goods_in_transit_note_items",
        "on_cancel": "dashmesh.events.purchase_receipt.update_goods_in_transit_note_items_on_cancel",
        "validate": "dashmesh.events.purchase_receipt.create_batch"
	},
	"Sales Order": {
		"validate": "dashmesh.events.sales_order.set_profit",
		"before_submit" : "dashmesh.events.sales_order.check_reservation"
	},
	"Packing Slip": {
		"validate":"dashmesh.events.packing_slip.set_total_volume"
	},
	"Quotation": {
		"validate":"dashmesh.events.quotation.set_profit"
	},
	"Pick List": {
        "before_save": "dashmesh.events.pick_list.set_warehouses",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dashmesh.tasks.all"
# 	],
# 	"daily": [
# 		"dashmesh.tasks.daily"
# 	],
# 	"hourly": [
# 		"dashmesh.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dashmesh.tasks.weekly"
# 	]
# 	"monthly": [
# 		"dashmesh.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "dashmesh.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dashmesh.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dashmesh.task.get_dashboard_data"
# }

