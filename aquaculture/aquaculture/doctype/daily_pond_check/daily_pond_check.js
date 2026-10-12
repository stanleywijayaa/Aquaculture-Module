// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Pond Check", {
	setup(frm) {
		frm.set_query("block", () => ({
			filters: frm.doc.farm_site ? { farm_site: frm.doc.farm_site } : {},
		}));
		frm.set_query("pond_cycle", "rows", () => ({
			filters: {
				block: frm.doc.block,
				status: ["in", ["Stocked", "Partially Harvested"]],
			},
		}));
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Ponds"), () => frm.trigger("get_ponds"));
		}
	},

	block(frm) {
		if (frm.doc.block && !(frm.doc.rows || []).length) {
			frm.trigger("get_ponds");
		}
	},

	async get_ponds(frm) {
		if (!frm.doc.block) {
			frappe.msgprint(__("Select a Block first"));
			return;
		}
		const cycles = await frappe.db.get_list("Pond Cycle", {
			filters: { block: frm.doc.block, status: ["in", ["Stocked", "Partially Harvested"]] },
			fields: ["name", "pond"],
			limit: 100,
		});
		cycles.sort((a, b) => a.pond.localeCompare(b.pond, undefined, { numeric: true }));

		frm.clear_table("rows");
		cycles.forEach((c) => {
			const row = frm.add_child("rows");
			row.pond_cycle = c.name;
			row.pond = c.pond;
		});
		frm.refresh_field("rows");
	},
});
