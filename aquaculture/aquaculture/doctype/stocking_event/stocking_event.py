# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate


class StockingEvent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.stocking_event_pond.stocking_event_pond import StockingEventPond
		from frappe.types import DF

		farm_site: DF.Link
		notes: DF.SmallText | None
		ponds: DF.Table[StockingEventPond]
		stocking_date: DF.Date
		supplier: DF.Link
		total_quantity: DF.Int
	# end: auto-generated types

	def autoname(self):
		# STK-26-001, STK-26-002 …
		self.name = make_autoname("STK-.YY.-.###")

	def validate(self):
		seen = set()
		total = 0

		for row in self.ponds:
			if row.pond_cycle in seen:
				frappe.throw(_("Row {0}: {1} is listed twice").format(row.idx, row.pond_cycle))
			seen.add(row.pond_cycle)

			cycle = frappe.db.get_value(
				"Pond Cycle", row.pond_cycle,
				["pond", "farm_site", "status", "prep_start_date"], as_dict=True,
			)
			row.pond = cycle.pond

			if cycle.farm_site != self.farm_site:
				frappe.throw(_("Row {0}: {1} is at {2}, not {3}")
							 .format(row.idx, row.pond_cycle, cycle.farm_site, self.farm_site))

			if cycle.status in ("Partially Harvested", "Closed"):
				frappe.throw(_("Row {0}: cycle {1} is {2} and cannot be stocked")
							 .format(row.idx, row.pond_cycle, cycle.status))

			other = frappe.db.get_value(
				"Stocking Event Pond",
				{"pond_cycle": row.pond_cycle, "parenttype": "Stocking Event", "parent": ["!=", self.name]},
				"parent",
			)
			if other:
				frappe.throw(_("Row {0}: {1} was already stocked in {2}")
							 .format(row.idx, row.pond_cycle, other))

			if getdate(self.stocking_date) < getdate(cycle.prep_start_date):
				frappe.throw(_("Row {0}: Stocking Date is before the prep start of {1}")
							 .format(row.idx, row.pond_cycle))

			if not row.quantity or row.quantity <= 0:
				frappe.throw(_("Row {0}: Quantity must be more than 0").format(row.idx))

			total += row.quantity

		self.total_quantity = total

	def on_update(self):
		cycles = {row.pond_cycle for row in self.ponds}
		before = self.get_doc_before_save()
		if before:
			cycles |= {row.pond_cycle for row in before.ponds}
		for c in cycles:
			frappe.get_doc("Pond Cycle", c).update_stocking()

	def after_delete(self):
		for row in self.ponds:
			frappe.get_doc("Pond Cycle", row.pond_cycle).update_stocking()

	pass
