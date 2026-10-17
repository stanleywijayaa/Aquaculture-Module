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

def check_storage_rule(item_code, warehouse, idx):
	"""Block an item from going into a typed block warehouse of the wrong type."""
	if not warehouse:
		return
	wtype, parent = frappe.db.get_value("Warehouse", warehouse, ["warehouse_type", "parent_warehouse"])
	if not wtype:
		return  # not one of our typed block warehouses
	site = frappe.db.get_value("Block", {"warehouse": parent}, "farm_site")
	if not site:
		return
	item_group = frappe.db.get_value("Item", item_code, "item_group")
	expected = frappe.db.get_value(
		"Farm Site Warehouse", {"parent": site, "item_group": item_group}, "warehouse_type"
	)
	if expected and expected != wtype:
		frappe.throw(_("Row {0}: {1} ({2}) must go into a {3} warehouse, not {4}")
					 .format(idx, item_code, item_group, expected, warehouse))


def validate_stock_rows(doc, method=None):
	"""doc_events hook for Purchase Receipt, Stock Entry, Stock Reconciliation."""
	for row in doc.items:
		# check only where stock is going, so misplaced stock can still be moved out
		check_storage_rule(row.item_code, row.get("t_warehouse") or row.get("warehouse"), row.idx)