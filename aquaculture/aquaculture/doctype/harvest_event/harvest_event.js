// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Harvest Event", {
	setup(frm) {
		frm.set_query("pond_cycle", "rows", () => ({
			filters: { block: frm.doc.block, status: ["in", ["Stocked", "Partially Harvested"]] },
		}));
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Ponds"), () => get_ponds(frm));
		}
	},
});

frappe.ui.form.on("Harvest Event Pond", {
	weight_kg(frm) {
		update_totals(frm);
	},
	rows_remove(frm) {
		update_totals(frm);
	},
});

function update_totals(frm) {
	const rows = frm.doc.rows || [];
	frm.set_value("total_kg", rows.reduce((s, r) => s + (r.weight_kg || 0), 0));
}

async function get_ponds(frm) {
	const { block, harvest_date } = frm.doc;
	if (!block || !harvest_date) {
		frappe.msgprint(__("Set Block and Harvest Date first"));
		return;
	}
	const cycles = await frappe.db.get_list("Pond Cycle", {
		filters: {
			block,
			status: ["in", ["Stocked", "Partially Harvested"]],
			stocking_date: ["<=", harvest_date],
		},
		fields: ["name", "pond"],
		limit: 100,
	});
	if (!cycles.length) {
		frappe.msgprint(__("No stocked ponds in block {0}", [block]));
		return;
	}
	cycles.sort((a, b) => a.pond.localeCompare(b.pond, undefined, { numeric: true }));

	const fill = () => {
		frm.clear_table("rows");
		for (const c of cycles) {
			frm.add_child("rows", { pond_cycle: c.name, pond: c.pond });
		}
		frm.refresh_field("rows");
		update_totals(frm);
	};
	if ((frm.doc.rows || []).length) {
		frappe.confirm(__("Replace the rows already entered?"), fill);
	} else {
		fill();
	}
}
