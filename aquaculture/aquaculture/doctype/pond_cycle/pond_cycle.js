// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pond Cycle", {
	setup(frm) {
		frm.set_query("pond", () => ({
			query: "aquaculture.aquaculture.doctype.pond.pond.pond_query",
		}));
	},
});
