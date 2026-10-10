// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pond Cycle", {
	setup(frm) {
		frm.set_query("pond", () => ({
			query: "aquaculture.aquaculture.doctype.pond.pond.pond_query",
		}));
	},
	refresh(frm) {
		if (frm.doc.status === "Closed" && !frappe.user.has_role("System Manager")) {
			["pond", "status", "prep_start_date", "stocking_date", "end_date"].forEach((f) =>
				frm.set_df_property(f, "read_only", 1),
			);
			frm.set_intro(__("This cycle is closed. Only Notes can be edited."), "blue");
		}
	},
});
