// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Growth Sample", {
	setup(frm) {
		frm.set_query("pond_cycle", "rows", () => ({
			filters: { block: frm.doc.block, status: ["in", ["Stocked", "Partially Harvested"]] },
		}));
	},

	refresh(frm) {
		frm.add_custom_button(__("Get Ponds"), () => get_ponds(frm));
	},
});

async function get_ponds(frm) {
	const { block, sample_date } = frm.doc;
	if (!block || !sample_date) {
		frappe.msgprint(__("Set Block and Sample Date first"));
		return;
	}

	const cycles = await frappe.db.get_list("Pond Cycle", {
		filters: {
			block,
			status: ["in", ["Stocked", "Partially Harvested"]],
			stocking_date: ["<=", sample_date],
		},
		fields: ["name", "pond"],
		limit: 100,
	});
	if (!cycles.length) {
		frappe.msgprint(__("No ponds in block {0} were stocked by {1}", [block, sample_date]));
		return;
	}
	cycles.sort((a, b) => a.pond.localeCompare(b.pond, undefined, { numeric: true }));

	const fill = () => {
		frm.clear_table("rows");
		for (const c of cycles) {
			frm.add_child("rows", { pond_cycle: c.name, pond: c.pond });
		}
		frm.refresh_field("rows");
	};

	if ((frm.doc.rows || []).length) {
		frappe.confirm(__("Replace the rows already entered?"), fill);
	} else {
		fill();
	}
}
