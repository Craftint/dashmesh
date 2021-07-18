import frappe

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