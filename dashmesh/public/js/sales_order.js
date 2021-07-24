frappe.ui.form.on('Sales Order Item', {
	qty:function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frappe.call({
            method: "dashmesh.events.sales_order.get_profit",
            args:{
                net : d.net_amount,
                profit : d.gross_profit
            },
            callback: function(r) {
                if(r.message){
                    frappe.model.set_value(cdt, cdn, "profit_margin", r.message)
                }
            }
        })
        frm.trigger('calculate_amount');
    },

    rate:function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frappe.call({
            method: "dashmesh.events.sales_order.get_profit",
            args:{
                net : d.net_amount,
                profit : d.gross_profit
            },
            callback: function(r) {
                if(r.message){
                    frappe.model.set_value(cdt, cdn, "profit_margin", r.message)
                }
            }
        })
        frm.trigger('calculate_amount');
    },
});

frappe.ui.form.on('Sales Order', {
    calculate_amount: function (frm){
        // triggers when you change row value in Goods In Transit Note Item
        let doc = frm.doc;
        let profit_total = 0;
        let amount_total = 0;
        let net_profit_margin = 0;
        for (let i in doc.items){
            if (doc.items[i].net_amount){
                amount_total += doc.items[i].net_amount;
                profit_total += doc.items[i].gross_profit
            }       
        }
        if(profit_total != 0){
            net_profit_margin = (amount_total/profit_total)*100
        }
        frm.refresh_field('items');
        frm.set_value('net_profit_margin', net_profit_margin);
    },
});