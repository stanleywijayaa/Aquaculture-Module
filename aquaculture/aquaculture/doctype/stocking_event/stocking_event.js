// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stocking Event", {
	setup(frm) {
		frm.set_query("pond_cycle", "ponds", () => {
			const filters = { status: "Preparation" };
			if (frm.doc.farm_site) filters.farm_site = frm.doc.farm_site;
			return { filters };
		});
	},
});