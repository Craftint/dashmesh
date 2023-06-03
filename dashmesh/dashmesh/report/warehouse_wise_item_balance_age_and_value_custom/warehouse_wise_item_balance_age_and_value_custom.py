
# Copyright (c) 2013, Roshna and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate
from frappe.query_builder.functions import Coalesce, CombineDatetime
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.report.stock_ageing.stock_ageing import FIFOSlots, get_average_age
from six import iteritems




def execute(filters=None):
	if not filters: filters = {}
	validate_filters(filters)

	columns = get_columns(filters)
	items = get_items(filters)
	sle = get_stock_ledger_entries(filters, items)

	item_map = get_item_details(items, sle, filters)
	iwb_map = get_item_warehouse_map(filters,sle)
	warehouse_list = get_warehouse_list(filters)
	item_ageing = FIFOSlots(filters).generate()
	data = []
	item_balance = {}
	item_value = {}

	item_filters = ""

	if filters.get("item_code") is not None and filters.get("item_code") != "":
			item_filters += """ and ti.item_code = '{item_code}' """.format(item_code=filters.get("item_code"))
	if filters.get("item_group") is not None and filters.get("item_group") != "":
		item_filters += """ and ti.item_group = '{item_group}' """.format(item_group=filters.get("item_group"))
	if filters.get("warehouse") is not None and filters.get("warehouse") != "":
		item_filters += """ and tb.warehouse = '{warehouse}' """.format(warehouse=filters.get("warehouse"))

	for (company, item, warehouse) in sorted(iwb_map):
		if not item_map.get(item):  continue
		row = []
		qty_dict = iwb_map[(company, item, warehouse)]
		bin_list = frappe.get_list('Bin', filters={'item_code': item, 'warehouse': warehouse}, fields=['actual_qty','reserved_qty'])


		item_balance.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]), [])
		total_stock_value = 0.00
		for wh in warehouse_list:
			res_qty = 0
			avl_qty = 0
			row += [qty_dict.bal_qty] if wh.name == warehouse else [0.00]
			total_stock_value += qty_dict.bal_val if wh.name == warehouse else 0.00
			if bin_list:
				row += [bin_list[0].reserved_qty] if wh.name == warehouse else [0.00]
				row += [(bin_list[0].actual_qty)-(bin_list[0].reserved_qty)] if wh.name == warehouse else [0.00]
			else:
				row += [0.00]
				row += [0.00]


		item_balance[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(row)
		item_value.setdefault((item,item_map[item]["item_name"],item_map[item]["item_group"]),[])
		item_value[(item,item_map[item]["item_name"],item_map[item]["item_group"])].append(total_stock_value)


	# sum bal_qty by item
	for (item,item_name,item_group), wh_balance in iteritems(item_balance):
		if not item_ageing.get(item):  continue

		reserv_qty = 0
		avail_qty = 0
		total_stock_value = sum(item_value[(item,item_name,item_group)])
		row = [item,item_name,item_group]

		fifo_queue = item_ageing[item]["fifo_queue"]
		average_age = 0.00
		if fifo_queue:
			average_age = get_average_age(fifo_queue, filters['to_date'])

		row += [average_age]
		item_doc = frappe.get_doc("Item",item)
		row += [item_doc.bottles_per_crate]

		res = [wh_balance[i] for i in range(len(wh_balance)) if i % 2 == 0]

		bal_qty = [sum(bal_qty) for bal_qty in zip(*wh_balance)]
		bal_qty_split = [bal_qty[i:i + 3] for i in range(0, len(bal_qty), 3)]
		actual = sum(list(map(float,[i[0] for i in bal_qty_split])))
		reserv = sum(list(map(float,[i[1] for i in bal_qty_split])))
		avail = sum(list(map(float,[i[2] for i in bal_qty_split])))

		total_qty = actual
		if len(warehouse_list) > 1:
			row += [reserv]
			row += [avail]
			row += [actual]
			if total_qty == 0:
				row += [actual]
			else:
				row += [total_stock_value/actual]
			row += [total_stock_value]
		row += bal_qty
		if total_qty > 0:
			data.append(row)
		elif not filters.get("filter_total_zero_qty"):
			data.append(row)

	add_warehouse_column(columns, warehouse_list)
	return columns, data

def get_columns(filters):
	"""return columns"""

	columns = [
		_("Item")+":Link/Item:120",
		_("Item Name")+"::170",
		_("Item Group")+"::110",
		_("Age")+":Float:80",
		_("No of Bottles")+":Float:80",
	]
	return columns

def validate_filters(filters):
	if not (filters.get("item_code") or filters.get("warehouse")):
		sle_count = flt(frappe.db.sql("""select count(name) from `tabStock Ledger Entry`""")[0][0])
		if sle_count > 500000:
			frappe.throw(_("Please set filter based on Item or Warehouse"))
	if not filters.get("company"):
		filters["company"] = frappe.defaults.get_user_default("Company")

def get_warehouse_list(filters):
	from frappe.core.doctype.user_permission.user_permission import get_permitted_documents

	condition = ''
	user_permitted_warehouse = get_permitted_documents('Warehouse')
	value = ()
	if user_permitted_warehouse:
		condition = "and name in %s"
		value = set(user_permitted_warehouse)
	elif not user_permitted_warehouse and filters.get("warehouse"):
		condition = "and name = %s"
		value = filters.get("warehouse")

	return frappe.db.sql("""select name
		from `tabWarehouse` where is_group = 0
		{condition}""".format(condition=condition), value, as_dict=1)

def add_warehouse_column(columns, warehouse_list):
	if len(warehouse_list) > 1:
		columns += [_("Reserved Qty")+":Float:100"]
		columns += [_("Available Qty")+":Float:100"]
		columns += [_("Total Qty")+":Float:100"]
		columns += [_("Per case value")+":Float:110"]
		columns += [_("Total Value")+":Float:110"]

	for wh in warehouse_list:
		columns += [_(wh.name)+":Float:140"]
		columns += [_(wh.name)+"\nReserved Qty"+":Float:200"]
		columns += [_(wh.name)+"\nAvailable Qty"+":Float:200"]


def get_item_details(items, sle, filters):
        item_details = {}
        if not items:
                items = list(set(d.item_code for d in sle))

        if not items:
                return item_details

        item_table = frappe.qb.DocType("Item")

        query = (
                frappe.qb.from_(item_table)
                .select(
                        item_table.name,
                        item_table.item_name,
                        item_table.description,
                        item_table.item_group,
                        item_table.brand,
                        item_table.stock_uom,
                )
                .where(item_table.name.isin(items))
        )

        if uom := filters.get("include_uom"):
                uom_conv_detail = frappe.qb.DocType("UOM Conversion Detail")
                query = (
                        query.left_join(uom_conv_detail)
                        .on((uom_conv_detail.parent == item_table.name) & (uom_conv_detail.uom == uom))
                        .select(uom_conv_detail.conversion_factor)
                )

        result = query.run(as_dict=1)
        for item_table in result:
                item_details.setdefault(item_table.name, item_table)

        if filters.get("show_variant_attributes"):
                variant_values = get_variant_values_for(list(item_details))
                item_details = {k: v.update(variant_values.get(k, {})) for k, v in item_details.items()}

        return item_details




def get_items(filters):
	"Get items based on item code, item group or brand."
	if item_code := filters.get("item_code"):
		return [item_code]
	else:
		item_filters = {}
		if item_group := filters.get("item_group"):
			children = get_descendants_of("Item Group", item_group, ignore_permissions=True)
			item_filters["item_group"] = ("in", children + [item_group])
		if brand := filters.get("brand"):
			item_filters["brand"] = brand

		return frappe.get_all("Item", filters=item_filters, pluck="name", order_by=None)



def get_stock_ledger_entries(filters, items):
	sle = frappe.qb.DocType("Stock Ledger Entry")
	query = (
		frappe.qb.from_(sle)
		.select(
			sle.item_code,
			sle.warehouse,
			sle.posting_date,
			sle.actual_qty,
			sle.valuation_rate,
			sle.company,
			sle.voucher_type,
			sle.qty_after_transaction,
			sle.stock_value_difference,
			sle.item_code.as_("name"),
			sle.voucher_no,
			sle.stock_value,
			sle.batch_no,
		)
		.where((sle.docstatus < 2) & (sle.is_cancelled == 0))
		.orderby(CombineDatetime(sle.posting_date, sle.posting_time))
		.orderby(sle.creation)
		.orderby(sle.actual_qty)
	)

	inventory_dimension_fields = get_inventory_dimension_fields()
	if inventory_dimension_fields:
		for fieldname in inventory_dimension_fields:
			query = query.select(fieldname)
			if fieldname in filters and filters.get(fieldname):
				query = query.where(sle[fieldname].isin(filters.get(fieldname)))

	if items:
		query = query.where(sle.item_code.isin(items))

	query = apply_conditions(query, filters)
	return query.run(as_dict=True)


def apply_conditions(query, filters):
	sle = frappe.qb.DocType("Stock Ledger Entry")
	warehouse_table = frappe.qb.DocType("Warehouse")

	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if to_date := filters.get("to_date"):
		query = query.where(sle.posting_date <= to_date)
	else:
		frappe.throw(_("'To Date' is required"))

	if company := filters.get("company"):
		query = query.where(sle.company == company)

	if filters.get("warehouse"):
		query = apply_warehouse_filter(query, sle, filters)
	elif warehouse_type := filters.get("warehouse_type"):
		query = (
			query.join(warehouse_table)
			.on(warehouse_table.name == sle.warehouse)
			.where(warehouse_table.warehouse_type == warehouse_type)
		)

	return query

def get_inventory_dimension_fields():
	return [dimension.fieldname for dimension in get_inventory_dimensions()]


def get_item_warehouse_map(filters,sle):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	opening_vouchers = get_opening_vouchers(to_date)
	float_precision = cint(frappe.db.get_default("float_precision")) or 3
	inventory_dimensions = get_inventory_dimension_fields()

	for d in sle:
		group_by_key = get_group_by_key(d, filters, inventory_dimensions)
		if group_by_key not in iwb_map:
			iwb_map[group_by_key] = frappe._dict(
				{
					"opening_qty": 0.0,
					"opening_val": 0.0,
					"in_qty": 0.0,
					"in_val": 0.0,
					"out_qty": 0.0,
					"out_val": 0.0,
					"bal_qty": 0.0,
					"bal_val": 0.0,
					"val_rate": 0.0,
				}
			)

		qty_dict = iwb_map[group_by_key]
		for field in inventory_dimensions:
			qty_dict[field] = d.get(field)

		if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
			qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)

		if d.posting_date < from_date or d.voucher_no in opening_vouchers.get(d.voucher_type, []):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff

		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(qty_diff, float_precision) >= 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)

		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff

	iwb_map = filter_items_with_no_transactions(iwb_map, float_precision, inventory_dimensions)

	return iwb_map


def get_opening_vouchers(to_date):
	opening_vouchers = {"Stock Entry": [], "Stock Reconciliation": []}

	se = frappe.qb.DocType("Stock Entry")
	sr = frappe.qb.DocType("Stock Reconciliation")

	vouchers_data = (
		frappe.qb.from_(
			(
				frappe.qb.from_(se)
				.select(se.name, Coalesce("Stock Entry").as_("voucher_type"))
				.where((se.docstatus == 1) & (se.posting_date <= to_date) & (se.is_opening == "Yes"))
			)
			+ (
				frappe.qb.from_(sr)
				.select(sr.name, Coalesce("Stock Reconciliation").as_("voucher_type"))
				.where((sr.docstatus == 1) & (sr.posting_date <= to_date) & (sr.purpose == "Opening Stock"))
			)
		).select("voucher_type", "name")
	).run(as_dict=True)

	if vouchers_data:
		for d in vouchers_data:
			opening_vouchers[d.voucher_type].append(d.name)

	return opening_vouchers


def filter_items_with_no_transactions(iwb_map, float_precision: float, inventory_dimensions: list):
	pop_keys = []
	for group_by_key in iwb_map:
		qty_dict = iwb_map[group_by_key]

		no_transactions = True
		for key, val in qty_dict.items():
			if key in inventory_dimensions:
				continue

			val = flt(val, float_precision)
			qty_dict[key] = val
			if key != "val_rate" and val:
				no_transactions = False

		if no_transactions:
			pop_keys.append(group_by_key)

	for key in pop_keys:
		iwb_map.pop(key)

	return iwb_map


def get_group_by_key(self, row) -> tuple:
		group_by_key = [row.company, row.item_code, row.warehouse]

		for fieldname in self.inventory_dimensions:
			if self.filters.get(fieldname):
				group_by_key.append(row.get(fieldname))

		return tuple(group_by_key)