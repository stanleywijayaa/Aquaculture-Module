// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pond", {
	length_m(frm) {
		frm.trigger("calc_area");
	},
	width_m(frm) {
		frm.trigger("calc_area");
	},
	calc_area(frm) {
		frm.set_value("area_m2", (frm.doc.length_m || 0) * (frm.doc.width_m || 0));
	},
});
