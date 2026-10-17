import frappe

import frappe

# Kg per Sak, keyed by Item Code (the admin's KODE BARANG); every other Pakan item is 25 kg
SAK_KG = {
	"681V": 10,          # Pakan Irawan 681V
	"999-1": 10,         # Pakan Marine 999-110
	"999-2": 20,         # Pakan Marine 999-212
	"999-3": 20,         # Pakan Marine 999-3
	"999-4": 20,         # Pakan Marine 999-4
	"PU.P1.4.20": 20,    # PU TOV P1.4 (20 kg)
	"PU.P1.6.20": 20,    # PU TOV P1.6 (20 kg)
}
DEFAULT_SAK_KG = 25


def execute():
	codes = frappe.get_all("Item", filters={"item_group": "Pakan", "stock_uom": "Kg"}, pluck="name")
	for code in codes:
		item = frappe.get_doc("Item", code)
		kg = SAK_KG.get(code, DEFAULT_SAK_KG)
		row = next((r for r in item.uoms if r.uom == "Sak"), None)
		if row:
			row.conversion_factor = kg
		else:
			item.append("uoms", {"uom": "Sak", "conversion_factor": kg})
		item.purchase_uom = "Sak"
		item.save()
		print(code, item.item_name, "1 Sak = ", kg, "Kg")

	frappe.db.commit()