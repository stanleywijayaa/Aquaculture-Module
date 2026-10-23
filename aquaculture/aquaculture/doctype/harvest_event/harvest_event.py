# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, getdate, today

ACTIVE = ("Stocked", "Partially Harvested")

class HarvestEvent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.harvest_event_pond.harvest_event_pond import HarvestEventPond
		from frappe.types import DF

		amended_from: DF.Link | None
		block: DF.Link
		farm_site: DF.Link | None
		harvest_date: DF.Date
		notes: DF.SmallText | None
		rows: DF.Table[HarvestEventPond]
		total_kg: DF.Float
	# end: auto-generated types

	def autoname(self):
		self.name = make_autoname(f"HRV-{self.block}-.YY.-.###")

	def validate(self):
		if getdate(self.harvest_date) > getdate(today()):
			frappe.throw(_("Harvest Date can't be in the future"))

		self.rows = [r for r in self.rows if flt(r.weight_kg) > 0]
		for i, r in enumerate(self.rows, start=1):
			r.idx = i
		if not self.rows:
			frappe.throw(_("Enter the harvested weight for at least one pond"))

		types = {}
		for r in self.rows:
			self.validate_row(r, types)
			r.abw_g = 1000 / r.count_per_kg if r.count_per_kg else 0
			r.pieces = flt(r.weight_kg) * (r.count_per_kg or 0)

		self.total_kg = sum(flt(r.weight_kg) for r in self.rows)

	def validate_row(self, r, seen):
		if not r.harvest_type:
			frappe.throw(_("Row {0}: choose Partial or Total").format(r.idx))
		if not r.count_per_kg or r.count_per_kg <= 0:
			frappe.throw(_("Row {0}: enter the size (count per kg) for {1}").format(r.idx, r.pond_cycle))
		# a pond may appear twice (e.g. two buyers), but with the same type and size
		first = seen.setdefault(r.pond_cycle, (r.harvest_type, r.count_per_kg))
		if first != (r.harvest_type, r.count_per_kg):
			frappe.throw(_("Row {0}: {1} has a different type or size in another row. One pond has one size per harvest")
						 .format(r.idx, r.pond_cycle))

		cycle = frappe.db.get_value("Pond Cycle", r.pond_cycle,
			["block", "status", "stocking_date"], as_dict=True)
		if cycle.block != self.block:
			frappe.throw(_("Row {0}: {1} is not in block {2}").format(r.idx, r.pond_cycle, self.block))
		if cycle.status not in ACTIVE:
			frappe.throw(_("Row {0}: {1} is {2}, so it can't be harvested")
						 .format(r.idx, r.pond_cycle, cycle.status))
		if not cycle.stocking_date or getdate(self.harvest_date) < getdate(cycle.stocking_date):
			frappe.throw(_("Row {0}: {1} wasn't stocked yet on {2}")
						 .format(r.idx, r.pond_cycle, self.harvest_date))

	def on_submit(self):
		self.update_cycles()

	def on_cancel(self):
		self.update_cycles()

	def update_cycles(self):
		for name in {r.pond_cycle for r in self.rows}:
			frappe.get_doc("Pond Cycle", name).update_harvest()

	pass
