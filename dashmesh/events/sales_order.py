import frappe
from frappe import msgprint,_
from frappe.utils import cint, flt, cstr, comma_or

def set_profit(doc, handler=None):
	for item in doc.items:
		last_purchase_rate = 0
		valuation_rate = frappe.db.sql("""
				SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
				AND warehouse = %s AND valuation_rate > 0
				ORDER BY posting_date DESC, posting_time DESC, creation DESC LIMIT 1
				""", (item.item_code, item.warehouse))
		if valuation_rate:
			item.gross_profit = flt(((item.base_rate - valuation_rate[0][0]) * item.stock_qty))
		last_purchase_rate = frappe.get_cached_value("Item", item.item_code, "last_purchase_rate")
		item.gross_profit_based_on_last_purchase_rate = flt(((item.base_rate - last_purchase_rate) * item.stock_qty))
		if item.net_amount != 0:
			item.profit_margin = flt((item.gross_profit_based_on_last_purchase_rate/item.net_amount)*100)

@frappe.whitelist()
def get_profit(item=None,wh=None,base_rate=0,stock_qty=0,net=None,profit=None):
	last_purchase_rate = 0
	gross_profit = profit
	item_doc = frappe.get_doc("Item",item)
	valuation_rate = frappe.db.sql("""
			SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
			AND warehouse = %s AND valuation_rate > 0
			ORDER BY posting_date DESC, posting_time DESC, creation DESC LIMIT 1
			""", (item_doc.item_code, wh))

	net_amount = flt(net)
	if valuation_rate:
		gross_profit = flt((flt(base_rate) - valuation_rate[0][0]) * flt(stock_qty))
	last_purchase_rate = frappe.get_cached_value("Item", item_doc.item_code, "last_purchase_rate")
	gross_profit_purchase_rate = flt((flt(base_rate) - last_purchase_rate) * flt(stock_qty))
	margin = 0.0
	if net_amount != 0:
		margin = flt((gross_profit_purchase_rate/net_amount)*100)
	return [margin,gross_profit,gross_profit_purchase_rate,last_purchase_rate]

def check_reservation(doc,handler=None):
	def _get_msg(row_num, msg):
		return _("Row # {0}: ").format(row_num+1) + msg
	validation_messages = []
	for row_num,item in enumerate(doc.items):
		# try:
		available_qty = 0
		db_exist = frappe.db.exists({
					"doctype": "Bin",
					"item_code": item.item_code,
					"warehouse": item.warehouse,
		})
		if db_exist:
			item_bin = frappe.get_doc("Bin",db_exist[0][0])
			available_qty = item_bin.actual_qty - item_bin.reserved_qty
			if item.qty > available_qty:
				if available_qty > 0:
					validation_messages.append(_get_msg(row_num, _("Available quantity for item code {0} is only {1}.Please choose quantity less than or equal to available quantity").format(item.item_code,available_qty)))
				else:
					validation_messages.append(_get_msg(row_num, _("Available quantity for item code {0} is 0.Please choose quantity less than or equal to available quantity").format(item.item_code,available_qty)))

				# raise frappe.ValidationError(_("Available quantity for item code {0} is only {1}.Please choose quantity less than or equal to available quantity").format(item.item_code,available_qty))
				# raise frappe.ValidationError(_(f'Available quantity for item code {item.item_code} is only {available_qty}. Please choose quantity less than or equal to available quantity'))
				# frappe.throw(
				# 	msg = _(f'Available quantity for item code {item.item_code} is only {available_qty}. Please choose quantity less than or equal to available quantity'),
				# 	title= 'Item not available',
				# )
		else:
			validation_messages.append(_get_msg(row_num, _("Available quantity for item code {0} is only {1}.Please choose quantity less than or equal to available quantity").format(item.item_code,available_qty)))

		# except Exception as e:
		# 	validation_messages.append(_cstr(e))
	if validation_messages:
		for msg in validation_messages:
			msgprint(msg)

		raise frappe.ValidationError(validation_messages)
	frappe.msgprint("All quantities has been reserved!")

@frappe.whitelist()
def get_itemdata(item_code=None, item_name=None, item_group=None, customer=None, price_list=None):
	where_cond = False
	where_clause = ""
	item_price_list = []
	if (item_code is not None and item_code != "") or (item_group is not None and item_group != ""):
		if item_code is not None and item_code != "":
			where_clause = where_clause + "i.item_code='{}' and ".format(item_code)
			where_cond = True


		if item_group is not None and item_group != "":
			where_clause = where_clause + "i.item_group='{}' and ".format(item_group)
			where_cond = True

		where_clause = where_clause.rstrip("and ")

		if where_cond:
			where_clause = "where " + where_clause

		sql = """SELECT 
					i.item_code,
					i.item_name,
					i.description,
					i.item_group,
					COALESCE(i.sales_uom,'') as sales_uom
					FROM `tabItem` i
					{}
			""".format(where_clause)

		items = frappe.db.sql(sql, as_dict=True)

		for item in items:
			lvr = get_last_valuation_rates(item.item_code)
			last = get_last_selling_price(item.item_code, customer)
			latest_item_price = frappe.get_value("Item Price",
												 filters={"item_code": item.item_code, "price_list": price_list},
												 fieldname="price_list_rate")

			for cur_stock in last.stock_balance:
				item_price_list.append({
					"item_code": item.item_code,
					"item_name": item.item_name,
					"sales_uom": item.sales_uom,
					"description": item.description,
					"qty": cur_stock.actual_qty,
					"rate": latest_item_price or 0,
					"warehouse": cur_stock.warehouse,
					"valuation_rate": lvr

				})

	return item_price_list


@frappe.whitelist()
def get_item_history(item):
	'''
	Fetching last 5 sales prices for item
	'''
	result = frappe.db.get_list('Sales Invoice Item',
								filters={
									'item_code': item,
									'docstatus': 1
								},
								fields=['parent', 'rate'],
								page_length=5)
	sales_html = '<div><h3>Selling Prices</h3></div>'
	for row in result:
		customer = frappe.get_value('Sales Invoice', row.parent, 'customer')
		sales_html += f'<div>{customer}</div><div>{row.parent}: {row.rate}</div><br>'
	sales_html += '<hr>'

	result = frappe.db.get_list('Purchase Invoice Item',
								filters={
									'item_code': item,
									'docstatus': 1
								},
								fields=['parent', 'rate'],
								page_length=5)

	purchase_html = '<div><h3>Purchase Prices</h3></div>'
	for row in result:
		supplier = frappe.get_value('Purchase Invoice', row.parent, 'supplier')
		purchase_html += f'<div>{supplier}</div><div>{row.parent}: {row.rate}</div><br>'

	frappe.msgprint(f'{sales_html} {purchase_html}')


@frappe.whitelist()
def get_last_item_sales(item_code=None, item_group=None, customer=None, purchase_from=None, from_date=None):
	where_cond = False
	where_clause = ""
	item_price_list = []
	item_purchase_price_list = []
	if (item_code is not None and item_code != ""):
		if item_code is not None and item_code != "":
			where_clause = where_clause + "i.item_code='{}' and ".format(item_code)
			where_cond = True

		where_clause = where_clause.rstrip("and ")

		if where_cond:
			where_clause = "where " + where_clause

		sql = """SELECT 
					i.item_code,
					i.item_name,
					i.description
					FROM `tabItem` i
					{}
			""".format(where_clause)

		items = frappe.db.sql(sql, as_dict=True)

		for item in items:
			last = get_last_selling_price(item.item_code, customer, purchase_from, from_date)
			# print(last)
			item_price_list += last.item_price
			item_purchase_price_list += last.purchase_price
	return {'item_price_list':item_price_list, 'purchase_price': item_purchase_price_list}


@frappe.whitelist()
def get_last_selling_price(item_code='', customer='',purchase_from='', from_date=''):
	customer_cond = ""
	from_date_cond = ""
	po_from_date_cond = ""
	if customer != '' and customer is not None:
		customer_cond = """si.customer = '{customer}' and """.format(customer=customer)
	if from_date != "" and from_date is not None:
		from datetime import datetime
		from_date_cond = """and (Date(posting_date) between '{0}' and '{1}')""".format(from_date, datetime.today().date())
		po_from_date_cond = """and (Date(transaction_date) between '{0}' and '{1}')""".format(from_date, datetime.today().date())

	## SALES WORK
	sales_query = """select
				si.customer, 
				sid.item_code,
				sid.item_name,
				sid.description,
				sid.stock_uom,
				sid.qty,
				sid.rate,
				'Sale' as rate_type,
				si.posting_date,
				si.posting_time,
				sid.parent as `record_id`,
				'Sales Invoice' as doctype
			from
				`tabSales Invoice Item` sid
			inner join `tabSales Invoice` si on
				sid.parent = si.name
			where
				{customer}
				sid.item_code = '{item_code}'
				and si.docstatus != 2
				{from_date}
			order by
				posting_date desc, posting_time desc
			"""

	last_customer_prices = frappe.db.sql(sales_query.format(
			customer=customer_cond, item_code=item_code, from_date=from_date_cond), as_dict=True)

	## PURCHASE WORK
	purchase_query = """
			select
				pi.supplier,
				pid.item_code,
				pid.item_name,
				pid.description,
				pid.stock_uom,
				pid.qty,
				pid.rate,
				'Purchase' as rate_type,
				pi.posting_date,
				pi.posting_time,
				pid.parent as `record_id`,
				'Purchase Invoice' as doctype
			from
				`tabPurchase Invoice Item` pid
			inner join `tabPurchase Invoice` pi on
				pid.parent = pi.name
			where
				pid.item_code = '{item_code}'
				and pi.docstatus != 2
				{from_date}
			UNION ALL
			select
				po.supplier,
				pod.item_code,
				pod.item_name,
				pod.description,
				pod.stock_uom,
				pod.qty,
				pod.rate,
				'Purchase' as rate_type,
				po.transaction_date as `posting_date`,
				"" as posting_time,
				pod.parent as `record_id`,
				'Purchase Order' as doctype
			from
				`tabPurchase Order Item` pod
			inner join `tabPurchase Order` po on
				pod.parent = po.name
			where
				pod.item_code = '{item_code}'
				and po.docstatus != 2
				{po_from_date}
			order by
				posting_date desc,
				posting_time desc
			""".format(item_code=item_code, from_date=from_date_cond, po_from_date=po_from_date_cond)

	if purchase_from == 'Purchase Invoice':
		purchase_query = """
				select
					pi.supplier,
					pid.item_code,
						pid.item_name,
						pid.description,
						pid.stock_uom,
						pid.qty,
						pid.rate,
						'Purchase' as rate_type,
						pi.posting_date,
						pi.posting_time,
						pid.parent as `record_id`,
						'Purchase Invoice' as doctype
					from
						`tabPurchase Invoice Item` pid
					inner join `tabPurchase Invoice` pi on
						pid.parent = pi.name
					where
						pid.item_code = '{item_code}'
						and pi.docstatus != 2
						{from_date}
					order by
						posting_date desc ,posting_time desc
					""".format(item_code=item_code, from_date=from_date_cond)
	elif purchase_from == 'Purchase Order':
		purchase_query = """
				select
					pi.supplier,
					pid.item_code,
						pid.item_name,
						pid.description,
						pid.stock_uom,
						pid.qty,
						pid.rate,
						'Purchase' as rate_type,
						pi.transaction_date as `posting_date`,
						pid.parent as `record_id`,
						'Purchase Order' as doctype
					from
						`tabPurchase Order Item` pid
					inner join `tabPurchase Order` pi on
						pid.parent = pi.name
					where
						pid.item_code = '{item_code}'
						and pi.docstatus != 2
						{from_date}
					order by
						posting_date desc
					""".format(item_code=item_code, from_date=po_from_date_cond)

	last_purchase_prices = frappe.db.sql(purchase_query, as_dict=True)

	current_stock = frappe.db.sql(
		"""select warehouse,actual_qty from `tabBin` where item_code = '{}'""".format(item_code), as_dict=True)
	return frappe._dict({'item_price': last_customer_prices, 'stock_balance': current_stock, 'purchase_price': last_purchase_prices})

def get_last_valuation_rates(item_code):
	last_rates = frappe.get_list("Stock Ledger Entry", fields=['valuation_rate'], filters={'item_code':item_code}, order_by="modified desc", page_length = 1)
	rate = ''
	if len(last_rates) > 0:
		return last_rates[0]['valuation_rate']
	return rate

@frappe.whitelist()
def get_customer_info(customer=None):
	customer_list = []
	if customer:
		customer_doc = frappe.get_doc("Customer", customer)
		customer_list = [customer_doc.customer_name]
	return customer_list