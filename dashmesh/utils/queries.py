import frappe

@frappe.whitelist()
def get_uoms(item=None):
    return frappe.db.sql("""select uom.uom
		from `tabUOM Conversion Detail` uom
		where
			uom.parent = {item_code}"""
                         .format(item_code=frappe.db.escape(item))
                                 , as_dict=True)