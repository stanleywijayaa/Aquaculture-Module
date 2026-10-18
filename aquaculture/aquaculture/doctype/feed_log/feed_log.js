// Copyright (c) 2026, Stanley and contributors
// For license information, please see license.txt

frappe.ui.form.on("Feed Log", {
	setup(frm) {
		frm.set_query("pond_cycle", "items", () => ({
			filters: { block: frm.doc.block, status: ["in", ["Stocked", "Partially Harvested"]] },
		}));
		frm.set_query("item_code", "items", () => ({ filters: { item_group: "Pakan", disabled: 0 } }));
		frm.set_query("default_item", () => ({ filters: { item_group: "Pakan", disabled: 0 } }));
        frm.set_query("default_item_2", () => ({ filters: { item_group: "Pakan", disabled: 0 } }));
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Ponds"), () => fill_rows(frm));
		}
	},
});

frappe.ui.form.on("Feed Log Item", {
	qty_kg(frm) {
		update_total(frm);
	},
	items_remove(frm) {
		update_total(frm);
	},
});

function update_total(frm) {
	const total = (frm.doc.items || []).reduce((sum, r) => sum + (r.qty_kg || 0), 0);
	frm.set_value("total_kg", total);
}

async function fill_rows(frm) {
	const { block, from_date, to_date, default_item, default_item_2 } = frm.doc;
	if (!block || !from_date || !to_date) {
		frappe.msgprint(__("Set Block, From Date and To Date first"));
		return;
	}

	const cycles = await frappe.db.get_list("Pond Cycle", {
		filters: { block, status: ["in", ["Stocked", "Partially Harvested"]] },
		fields: ["name", "pond", "stocking_date"],
		limit: 100,
	});
	cycles.sort((a, b) => a.pond.localeCompare(b.pond, undefined, { numeric: true }));

	const fill = () => {
		const feeds = [...new Set([default_item, default_item_2].filter(Boolean))];
		const items = feeds.length ? feeds : [null];

		frm.clear_table("items");
		for (const c of cycles) {                       // pond by pond…
			let d = from_date;
			while (d <= to_date) {                      // …day by day
				if (!c.stocking_date || d >= c.stocking_date) {
					for (const item_code of items) {
						frm.add_child("items", { feed_date: d, pond_cycle: c.name, pond: c.pond, item_code });
					}
				}
				d = frappe.datetime.add_days(d, 1);
			}
		}
		frm.refresh_field("items");
		update_total(frm);
	};

	if ((frm.doc.items || []).length) {
		frappe.confirm(__("Replace the rows already entered?"), fill);
	} else {
		fill();
	}
}