// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Block", {
	setup(frm) {
		frm.set_query("cost_center", () => ({
			filters: { is_group: 0 },
		}));
	},
});
