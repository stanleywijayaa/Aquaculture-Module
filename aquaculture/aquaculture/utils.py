import frappe
from frappe import _


def get_block_warehouse(block, item_group):
	"""The leaf warehouse under this block that stores this item group."""
	site, group_wh = frappe.db.get_value("Block", block, ["farm_site", "warehouse"])

	wtype = frappe.db.get_value(
		"Farm Site Warehouse", {"parent": site, "item_group": item_group}, "warehouse_type"
	)
	if not wtype:
		frappe.throw(_("No storage rule for item group {0} at {1}").format(item_group, site))

	wh = frappe.db.get_value(
		"Warehouse",
		{"parent_warehouse": group_wh, "warehouse_type": wtype, "is_group": 0},
		"name",
	)
	if not wh:
		frappe.throw(_("Block {0} has no {1} warehouse").format(block, wtype))
	return wh