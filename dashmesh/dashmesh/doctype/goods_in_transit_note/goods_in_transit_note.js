// Copyright (c) 2020, Havenir and contributors
// For license information, please see license.txt

frappe.ui.form.on('Goods In Transit Note', {
	eta:function(frm,dt,dn){
		if (frm.doc.eta && frm.doc.etd){
			if(frm.doc.eta < frm.doc.etd){
				frappe.model.set_value(dt,dn,'eta','')
				frappe.msgprint(__('ETD cannot be after ETA'));
			}
			else{
				var n = frappe.datetime.get_day_diff(frm.doc.eta,frm.doc.etd)
				frm.set_value("no_of_days_expected_to_deliver",n)
			}
		}
	},
	etd:function(frm,dt,dn){
		if (frm.doc.etd && frm.doc.eta){
			if(frm.doc.eta < frm.doc.etd){
				frappe.model.set_value(dt,dn,'etd','')
				frappe.msgprint(__('ETD cannot be after ETA'));
			}
			else{
				var n = frappe.datetime.get_day_diff(frm.doc.eta,frm.doc.etd)
				frm.set_value("no_of_days_expected_to_deliver",n)
			}
		}
	},
	
	refresh: function(frm) {
		frappe.breadcrumbs.add("Stock", "Goods In Transit Note")	
		if (frm.is_new()){
			frm.add_custom_button(__('Get items from purchase order'), 
			() => frm.trigger('get_items_from_purchase_order'), __('Get Items'));
			
		}
		if (cur_frm.doc.docstatus == 1 && cur_frm.doc.status != 'Received'){
			frm.add_custom_button('Create purchase receipt', () => {
				frm.doc.git_status='Completed'
				frm.refresh_field('git_status')

				let doc = frm.doc
				frappe.run_serially([
					() => frappe.new_doc('Purchase Receipt'),
					() => {
						cur_frm.doc.supplier = doc.invoiced_by;
						cur_frm.doc.company = doc.company;
						cur_frm.doc.currency = doc.currency;
						cur_frm.doc.batch_number = doc.batch_number
						
						if (doc.exchange_rate) {
							cur_frm.doc.exchange_rate = doc.exchange_rate;
						}

						cur_frm.doc.ignore_pricing_rule = 1;
						cur_frm.doc.items = []
						for (let i in doc.items){
							if(doc.items[i].qty - doc.items[i].received_qty != 0){
								cur_frm.add_child('items', {
								item_code : doc.items[i].item_code,
								item_name: doc.items[i].item_name,
								description: doc.items[i].description,
								warehouse: doc.items[i].warehouse,
								qty : doc.items[i].qty,
								received_qty:doc.items[i].qty,
								uom : doc.items[i].uom,
								conversion_factor: doc.items[i].conversion_factor,
								stock_uom: doc.items[i].stock_uom,
								rate : doc.items[i].rate,
								amount : doc.items[i].amount,
								goods_in_transit_note: doc.name,
								goods_in_transit_note_item: doc.items[i].name,
								purchase_order: doc.items[i].purchase_order,
								purchase_order_item: doc.items[i].purchase_order_item,
								transit_qty: doc.items[i].qty 
							})
							}
						}
						cur_frm.refresh_field('items')
					}
				]);
			});
		}

	},
	before_save:function(frm){
		if(!frm.is_new()){
			frappe.db.exists('Goods In Transit Note', frm.doc.name)
			.then(exists => {
				if(exists==true){
					if(frm.doc.eta || frm.doc.etd){
						frappe.call({
							method: 'dashmesh.api.document',
							args: {
								parent_doc: 'Goods In Transit Note',
								doc_name: frm.doc.name
							},
							callback: (r) => {
								let old_eta = r.message.eta
								let old_etd = r.message.etd
								let frm_eta = frm.doc.eta
								let frm_etd = frm.doc.etd
								if(frm_eta!=old_eta && frm_etd!=old_etd){
									frappe.show_alert({
										message:__('ETA and ETD is changed successfully'),
										indicator:'green',
									}, 5);	
								}
								else if(frm_eta!=old_eta){
									console.log('changed');
									frappe.show_alert({
											message:__('ETA is changed successfully'),
											indicator:'green',
									}, 5);	
								}
								else if(frm_etd!=old_etd){
									frappe.show_alert({
										message:__('ETD is changed successfully'),
										indicator:'green',
									}, 5);	
								}
								
							},
						})
					}
				}
			})
		}
	},

	get_items_from_purchase_order: function (frm) {
		if (!frm.doc.invoiced_by){
			frappe.msgprint('Invoiced By not selected')
		}
		else{
		new frappe.ui.form.MultiSelectDialog({
			doctype: "Purchase Order",
			target: cur_frm,
			setters: {
				company: cur_frm.doc.company,
				
			},
			
			get_query() {
				return {
					filters: { 
						docstatus: ['=', 1],
						supplier: cur_frm.doc.invoiced_by,
						goods_status:["!=", "Dispatched"]
					}
				}
			},
			action(selections) {
				console.log(selections[0])
				if (selections.length == 0){
					frappe.msgprint('Select a Purchase Order')
				}
				else{
					cur_frm.doc.items = null
					console.log(selections)
					frm.call('get_items_from_purchase_order',selections)
					cur_frm.refresh();
					cur_frm.trigger('calculate_amount');
					// disable_adding_items(frm);
					cur_dialog.hide();
				}
			}
		});
	}
	},

	calculate_amount: function (frm){
		// triggers when you change row value in Goods In Transit Note Item
		let doc = frm.doc;
		let qty_total = 0;
		let amount_total = 0;
		for (let i in doc.items){
			if (doc.items[i].qty && doc.items[i].rate){
				doc.items[i].amount = (doc.items[i].qty)*(doc.items[i].rate);
				amount_total += doc.items[i].amount;
			}
			if (doc.items[i].qty){
				qty_total += doc.items[i].qty;
			}		
		}
		frm.refresh_field('items');
		frm.set_value('total_qty', qty_total);
		frm.set_value('total', amount_total);
	},
	
});
frappe.listview_settings['Courses'] = {
	add_fields: [],
	onload: function(listview) {
		frappe.route_options = {
			"purchase order": getCurrentAcid()
		};      
	}
};
function getCurrentAcid()
{
	frappe.call({                        
			method: "frappe.client.get_value", 
			args: { 
					doctype: "Academic Year",
					fieldname: "academic_year",
					filters: { status: 1 },
					},
				callback: function(r) {
					return r.message.academic_year;
				}
		});
}

frappe.ui.form.on('Goods In Transit Item', {
	qty: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn]
		frappe.db.get_doc('Purchase Order',row.purchase_order)
		.then(doc => {
			for(let item of doc.items){
				if(row.item_code == item.item_code){
					let val=item.qty-item.git_qty
					if(row.qty>val){
						frappe.model.set_value(cdt,cdn,"qty",'')
						frappe.msgprint({
							title: __('Warning'),
							indicator: 'red',
							message: __('Item quantity cannot be greater then Purchase Order quantity')
						});
					}
				}
			}
		})
		frm.trigger('calculate_amount');
	},

	item_code:function(frm,cdt,cdn){
		
		disable_new_row(frm,cdt,cdn)
	},

	rate: function(frm, cdt, cdn) {
		
		frm.trigger('calculate_amount');	
	},
});

const disable_new_row = function(frm,cdt,cdn) {
	let row=locals[cdt][cdn]
		if(row.item_code){
			frappe.model.remove_from_locals(cdt, cdn);
    		frm.refresh_field('items');
			frappe.msgprint('You cannot add a new row here!');
		}
}

//This function will disable the remove button and also the child table itself will be disabled
const disable_adding_items = function(frm) {
	frm.set_df_property("items", "read_only", 1);
	// frm.set_df_property("item_code", "read_only", 1, frm.doc.name, "items");
}