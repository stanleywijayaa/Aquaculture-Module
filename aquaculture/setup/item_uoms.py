import frappe

# Kg per Sak; every feed item not listed here is 25 kg
SAK_KG = {
	"PAK01": 10, "PAK18": 10,                                       # 681V, 999-110
	"PAK19": 20, "PAK20": 20, "PAK21": 20, "PAK22": 20, "PAK23": 20,  # 999-212/3/4, PU TOV 20 kg
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
		print(code, item.item_name, "1 Sak =", kg, "Kg")

	frappe.db.commit()