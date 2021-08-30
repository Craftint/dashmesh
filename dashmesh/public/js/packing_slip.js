frappe.ui.form.on('Packing Slip Item', {
	qty:function(frm,cdt,cdn){
        frm.trigger('calculate_amount');
    },
});

frappe.ui.form.on('Packing Slip', {
    calculate_amount: function (frm){
        // triggers when you change row value
        let doc = frm.doc;
        let unit_volume = 0;
        let total_volume = 0;
        for (let i in doc.items){
            if (doc.items[i].volume){
                total_volume += doc.items[i].volume*doc.items[i].qty;
            }       
        }
        frm.set_value('total_volume', total_volume);
    },
});