frappe.ui.form.on("Purchase Receipt", {

    refresh: function(frm) {
    //Add custom button Get Items From
		if (frm.doc.docstatus == 0){
			frm.add_custom_button(__('Goods In Transit'), 
			() => frm.trigger('get_items_from_goodsintransit'), 
			__('Get items from'));
			
        }
    },

    //Add custom function
	get_items_from_goodsintransit: function (frm) {
		if (!frm.doc.supplier){
			frappe.msgprint('Supplier not selected')
		}
		else{
		new frappe.ui.form.MultiSelectDialog({
			doctype: "Goods In Transit Note",
			target: cur_frm,
			setters: {
				company: cur_frm.doc.company,
				
			},
			date_field: "posting_date",
			get_query() {
				return {
					filters: { 
						docstatus: ['=', 1],
						status:['!=', 'Received'],
						invoiced_by: cur_frm.doc.supplier
					}
				}
			},
			action(selections) {
				if (selections.length == 0){
					frappe.msgprint('Select Goods In Transit Note')
				}
				else{
					cur_frm.doc.items = []
					for (let row in selections){
						frappe.db.get_doc('Goods In Transit Note', selections[row])
						.then(doc => {
							for (let i in doc.items){
								cur_frm.add_child('items', {
									item_code : doc.items[i].item_code,
									item_name: doc.items[i].item_name,
									description: doc.items[i].description,
									warehouse: doc.items[i].warehouse,
									received_qty:doc.items[i].qty,
									purchase_order: doc.items[i].purchase_order,
									qty : doc.items[i].qty , // doc.items[i].dispatched_qty,
									uom : doc.items[i].uom,
									conversion_factor: doc.items[i].conversion_factor,	
									stock_uom: doc.items[i].stock_uom,
									rate : doc.items[i].rate,
									amount : doc.items[i].qty* doc.items[i].rate,
									goods_in_transit_note: doc.name,
									goods_in_transit_note_item: doc.items[i].name,
									transit_qty: doc.items[i].qty,
								})
							}

						})
					}
					cur_frm.refresh();
				}
			}
		});
	}
	}
});