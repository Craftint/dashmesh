frappe.ui.form.on("Purchase Order", {
	//add custom function
	before_submit: function (frm) {
		let doc = frm.doc;
		doc.goods_status = "Goods pending for departure"
	},
	// Add Custom Button Goods In Transit
	refresh: function (frm) {
		frm.events.duplicate_init(frm);
		frm.events.create_goods_in_transit_button(frm);
		frappe.call({
			method: 'dashmesh.api.count',
			args: {
				name: frm.doc.name
			},
			// callback: (r) => {
			// 	const content =
			// 		`<div class="document-link" data-doctype="Goods In Transit Note">
			// 		<a class="badge-link small" href="javascript:void(0)"
			// 		onclick="frappe.set_route('List', 'Goods In Transit Note', 'List', {'Goods In Transit Item.purchase_order':'`+frm.doc.name+`'});">
			// 			Goods In Transit Note
			// 		</a>
			// 		<span class="text-muted small count">`+
			// 		r.message +
			// 		`<span>
			// 	</div>`;
			// 	$(".document-link[data-doctype='Goods In Transit Note']").remove();
			// 	$(".form-dashboard-wrapper .form-links .transactions .form-documents").append(content);
			// },
			error: (r) => {
				// on error
			}
		})

	},

	duplicate_init: function (frm) {
		if (frm.is_new()) {
			let items = frm.doc.items;
			for (let i in items) {
				items[i].dispatched_qty = 0;
			}
			frm.refresh_field('items');
		}
	},

	create_goods_in_transit_button: function (frm) {
		if (cur_frm.doc.docstatus == 1) {
			let create_cust_btn = 0;
			for (let row of frm.doc.items) {
				if (row.dispatched_qty < row.qty) {
					create_cust_btn = 1;
				}
			}
			if (create_cust_btn) {
				create_custom_button(frm);
			}
		}
	},
});

function set_route_git() {
	alert();
}


const create_custom_button = function (frm) {
	frm.add_custom_button('Goods In Transit', () => {
		let doc = frm.doc
		frappe.run_serially([
			() => frappe.new_doc('Goods In Transit Note'),
			() => {
				cur_frm.doc.invoiced_by = doc.supplier;
				cur_frm.doc.company = doc.company;
				cur_frm.doc.invoiced_to = doc.invoiced_to;
				cur_frm.doc.currency = doc.currency;

				if (doc.exchange_rate) {
					cur_frm.doc.exchange_rate = doc.exchange_rate;
				}

				cur_frm.doc.ignore_pricing_rule = doc.ignore_pricing_rule;
				cur_frm.doc.items = []
				for (let i in doc.items) {
					let qty
					if (doc.items[i].qty - doc.items[i].git_qty>0){
						qty=doc.items[i].qty - doc.items[i].git_qty
					}else{
						qty=0
					}
					cur_frm.add_child('items', {
						item_code: doc.items[i].item_code,
						item_name: doc.items[i].item_name,
						description: doc.items[i].description,
						warehouse: doc.items[i].warehouse,
						qty: qty, // doc.items[i].dispatched_qty,
						uom: doc.items[i].uom,
						conversion_factor: doc.items[i].conversion_factor,
						stock_uom: doc.items[i].stock_uom,
						rate: doc.items[i].rate,
						amount: doc.items[i].amount,
						purchase_order: doc.name,
						purchase_order_item: doc.items[i].name,
						actual_qty: qty,
					})
				}
				cur_frm.refresh();
				cur_frm.trigger('calculate_amount');
			}
		]);
	}, __("Create"));
};
