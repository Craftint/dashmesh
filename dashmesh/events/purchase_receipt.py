import frappe
from frappe import _

def update_goods_in_transit_note_items(doc, method):
	'''validating items from the Goods In Transit Note if they are still available'''		
	for row in doc.items:
		if row.goods_in_transit_note:
			qty, received_qty = frappe.db.get_value('Goods In Transit Item', 
			{'name': row.goods_in_transit_note_item}, 
			['qty', 'received_qty'])

			if (qty - received_qty < row.qty):
				frappe.throw(f'Row# {row.idx}: {row.qty} quantity not available for item {row.item_code}')
			
			new_received_qty = received_qty + row.qty
			frappe.db.set_value(
				'Goods In Transit Item', 
				row.goods_in_transit_note_item, 
				'received_qty', 
				new_received_qty
			)

			update_goods_in_transit_status(row)

def update_goods_in_transit_note_items_on_cancel(doc, method):
	for row in doc.items:
		if row.goods_in_transit_note:
			received_qty = frappe.db.get_value('Goods In Transit Item', 
			{'name': row.goods_in_transit_note_item}, 
			['received_qty'])

			new_received_qty = received_qty - row.qty
			frappe.db.set_value(
				'Goods In Transit Item', 
				row.goods_in_transit_note_item, 
				'received_qty', 
				new_received_qty
			)
			update_goods_in_transit_status(row)

def update_goods_in_transit_status(row):
	''' updates Goods In Transit Note Status 
		Status = [To Receive, Partially Received, Received]
		if all goods dispatched then goods status = Received
		if some goods dispatched then goods status = Partially Received
	'''
	#Getting Goods In Transit Note document
	goods_doc = frappe.get_doc('Goods In Transit Note', row.goods_in_transit_note)
	total_received_qty = 0
	for row in goods_doc.items:
		total_received_qty += row.received_qty
	
	if total_received_qty == goods_doc.total_qty:
		goods_doc.db_set('status', 'Completed')
	elif total_received_qty == 0:
		goods_doc.db_set('status', 'To Receive')
	else:
		goods_doc.db_set('status', 'Partially Received')

def create_batch(doc,handler=None):
	for item in doc.items:
		if frappe.db.get_value("Item", item.item_code, "has_batch_no") == 0 and (item.batch_number or item.batch_expiry):
			frappe.throw(_("The item {0} cannot have Batch").format(item.item_code))
		if frappe.db.get_value("Item", item.item_code, "has_batch_no") == 1:
			if item.batch_number:
				existing_batches = frappe.db.get_list('Batch', {'item': item.item_code}, ['name', 'expiry_date']) #list of dict
				if len(existing_batches) > 0:
					old_batch = 0
					for batch in existing_batches:
						if batch.name == item.batch_number:
							item.batch_expiry = batch.expiry_date
							item.batch_no = batch.name
							old_batch = 1
					if old_batch == 0:
						new_batch = create_new_batch(item.item_code,item.batch_number,item.batch_expiry)
						item.batch_no = new_batch.name
				else:
					new_batch = create_new_batch(item.item_code,item.batch_number,item.batch_expiry)
					item.batch_no = new_batch.name
			else:
				if item.batch_no:
					batch_doc = frappe.get_doc("Batch",item.batch_no)
					item.batch_number = batch_doc.batch_id
					item.batch_expiry = batch_doc.expiry_date
				else:
					frappe.throw(_("Please provide batch details for item {0}").format(item.item_code))

def create_new_batch(item_code,batch_number,batch_expiry):
	if not batch_expiry:
		frappe.throw(_("Please provide batch expiry date for item {0}").format(item_code))
	else:
		new_batch = frappe.new_doc("Batch")
		new_batch.batch_id = batch_number
		new_batch.item = item_code
		new_batch.expiry_date = batch_expiry
		new_batch.insert()
		new_batch.save(ignore_permissions=True)
		return new_batch