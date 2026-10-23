import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import flt


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

def feed_kg(pond_cycle, to_date=None, after=None):
	"""kg fed to a cycle (submitted Feed Logs), up to `to_date` (incl.) and after `after` (excl.)."""
	fl = frappe.qb.DocType("Feed Log")
	fi = frappe.qb.DocType("Feed Log Item")
	q = (
		frappe.qb.from_(fi).join(fl).on(fi.parent == fl.name)
		.select(Sum(fi.qty_kg))
		.where((fi.pond_cycle == pond_cycle) & (fl.docstatus == 1))
	)
	if to_date:
		q = q.where(fi.feed_date <= to_date)
	if after:
		q = q.where(fi.feed_date > after)
	return flt(q.run()[0][0])


def deaths(pond_cycle, to_date=None, after=None):
	"""Dead shrimp counted for a cycle, up to `to_date` (incl.) and after `after` (excl.)."""
	dc = frappe.qb.DocType("Daily Pond Check")
	dr = frappe.qb.DocType("Daily Pond Check Row")
	q = (
		frappe.qb.from_(dr).join(dc).on(dr.parent == dc.name)
		.select(Sum(dr.death_count))
		.where(dr.pond_cycle == pond_cycle)
	)
	if to_date:
		q = q.where(dc.check_date <= to_date)
	if after:
		q = q.where(dc.check_date > after)
	return flt(q.run()[0][0])


def harvested(pond_cycle, before=None, since=None):
	"""(pieces, kg) taken out by submitted harvests, before `before` (excl.) and since `since` (incl.)."""
	he = frappe.qb.DocType("Harvest Event")
	hr = frappe.qb.DocType("Harvest Event Pond")
	q = (
		frappe.qb.from_(hr).join(he).on(hr.parent == he.name)
		.select(Sum(hr.pieces), Sum(hr.weight_kg))
		.where((hr.pond_cycle == pond_cycle) & (he.docstatus == 1))
	)
	if before:
		q = q.where(he.harvest_date < before)
	if since:
		q = q.where(he.harvest_date >= since)
	pcs, kg = q.run()[0]
	return flt(pcs), flt(kg)