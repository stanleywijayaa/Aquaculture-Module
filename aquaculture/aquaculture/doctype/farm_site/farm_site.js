// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Farm Site", {
	setup(frm) {
		frm.set_query("warehouse", () => ({ filters: { is_group: 1 } }));
		frm.set_query("cost_center", () => ({ filters: { is_group: 1 } }));
	},
});
