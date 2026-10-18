# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, getdate, nowtime, today
from aquaculture.aquaculture.utils import get_block_warehouse

ACTIVE = ("Stocked", "Partially Harvested")


class FeedLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.feed_log_item.feed_log_item import FeedLogItem
		from frappe.types import DF

		amended_from: DF.Link | None
		block: DF.Link
		default_item: DF.Link | None
		default_item_2: DF.Link | None
		farm_site: DF.Link | None
		from_date: DF.Date
		items: DF.Table[FeedLogItem]
		notes: DF.SmallText | None
		to_date: DF.Date
		total_kg: DF.Float
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(f"FL-{self.block}-.YY.-.###")

	def validate(self):
		if getdate(self.from_date) > getdate(self.to_date):
			frappe.throw(_("From Date must be on or before To Date"))
		if getdate(self.to_date) > getdate(today()):
			frappe.throw(_("To Date can't be after today: feed is entered after it has been given"))
		self.drop_empty_rows()
		if not self.items:
			frappe.throw(_("Enter the feed (kg) for at least one pond"))
		self.validate_rows()
		self.total_kg = sum(flt(r.qty_kg) for r in self.items)

	def drop_empty_rows(self):
		self.items = [r for r in self.items if flt(r.qty_kg) > 0]
		for i, r in enumerate(self.items, start=1):
			r.idx = i

	def validate_rows(self):
		start, end = getdate(self.from_date), getdate(self.to_date)
		seen = set()
		for r in self.items:
			if not r.item_code:
				frappe.throw(_("Row {0}: choose the feed item").format(r.idx))
			if not start <= getdate(r.feed_date) <= end:
				frappe.throw(_("Row {0}: {1} is outside {2} – {3}")
							 .format(r.idx, r.feed_date, self.from_date, self.to_date))

			cycle = frappe.db.get_value("Pond Cycle", r.pond_cycle,
				["block", "status", "stocking_date"], as_dict=True)
			if cycle.block != self.block:
				frappe.throw(_("Row {0}: {1} is not in block {2}").format(r.idx, r.pond_cycle, self.block))
			if cycle.status not in ACTIVE:
				frappe.throw(_("Row {0}: {1} is {2}, not stocked").format(r.idx, r.pond_cycle, cycle.status))
			if cycle.stocking_date and getdate(r.feed_date) < getdate(cycle.stocking_date):
				frappe.throw(_("Row {0}: {1} is before {2} was stocked")
							 .format(r.idx, r.feed_date, r.pond_cycle))

			if frappe.db.get_value("Item", r.item_code, "item_group") != "Pakan":
				frappe.throw(_("Row {0}: {1} is not a feed (Pakan) item").format(r.idx, r.item_code))

			key = (r.pond_cycle, str(r.feed_date), r.item_code)
			if key in seen:
				frappe.throw(_("Row {0}: {1} on {2} with {3} is entered twice")
							 .format(r.idx, r.pond_cycle, r.feed_date, r.item_code))
			seen.add(key)

	def on_submit(self):
		wh = get_block_warehouse(self.block, "Pakan")
		company = frappe.db.get_value("Warehouse", wh, "company")
		cost_center = frappe.db.get_value("Block", self.block, "cost_center")

		by_date = {}
		for r in self.items:
			by_date.setdefault(str(r.feed_date), []).append(r)

		for feed_date, rows in sorted(by_date.items()):
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Issue"
			se.company = company
			se.set_posting_time = 1
			se.posting_date = feed_date
			se.posting_time = nowtime() if feed_date == today() else "23:00:00"
			se.remarks = _("Feed Log {0}").format(self.name)
			for r in rows:
				se.append("items", {
					"s_warehouse": wh,
					"item_code": r.item_code,
					"qty": r.qty_kg,
					"uom": frappe.db.get_value("Item", r.item_code, "stock_uom"),
					"conversion_factor": 1,
					"cost_center": cost_center,
				})
			se.flags.ignore_permissions = True
			se.insert()
			se.submit()

			for r, se_row in zip(rows, se.items):
				r.db_set({"cost": se_row.amount, "stock_entry": se.name})

		self.update_cycles()

	def on_cancel(self):
		for name in {r.stock_entry for r in self.items if r.stock_entry}:
			se = frappe.get_doc("Stock Entry", name)
			if se.docstatus == 1:
				se.flags.ignore_permissions = True
				se.ignore_linked_doctypes = tuple(getattr(se, "ignore_linked_doctypes", ())) + ("Feed Log",)
				se.cancel()
		self.update_cycles()

	def update_cycles(self):
		for name in {r.pond_cycle for r in self.items}:
			frappe.get_doc("Pond Cycle", name).update_feed()

	pass
