// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Farm Site", {
	setup(frm) {
		frm.set_query("warehouse", "warehouses", () => {
			return {
				filters: {
					is_group: 0,
					disabled: 0,
				},
			};
		});
	},
});
