# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class DailyPondCheck(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.daily_pond_check_row.daily_pond_check_row import DailyPondCheckRow
		from frappe.types import DF

		check_date: DF.Date
		checked_by: DF.Data
		farm_site: DF.Link
		rows: DF.Table[DailyPondCheckRow]
		session: DF.Literal["Morning", "Afternoon"]
		total_death: DF.Int
	# end: auto-generated types

	def autoname(self):
		# SR-B-2026-10-01-M  (block, date, session initial)
		self.name = f"{self.block}-{self.check_date}-{self.session[0]}"

	def validate(self):
		site = frappe.db.get_value("Block", self.block, "farm_site")
		if site != self.farm_site:
			frappe.throw(_("Block {0} is not at {1}").format(self.block, self.farm_site))

		seen = set()
		total = 0
		for row in self.rows:
			if row.pond_cycle in seen:
				frappe.throw(_("Row {0}: {1} is listed twice").format(row.idx, row.pond_cycle))
			seen.add(row.pond_cycle)

			cycle = frappe.db.get_value(
				"Pond Cycle", row.pond_cycle,
				["pond", "block", "status", "stocking_date"], as_dict=True,
			)
			row.pond = cycle.pond

			if cycle.block != self.block:
				frappe.throw(_("Row {0}: {1} is not in block {2}")
							 .format(row.idx, row.pond_cycle, self.block))

			if cycle.status not in ("Stocked", "Partially Harvested"):
				frappe.throw(_("Row {0}: cycle {1} is {2}, not active")
							 .format(row.idx, row.pond_cycle, cycle.status))

			if cycle.stocking_date and getdate(self.check_date) < getdate(cycle.stocking_date):
				frappe.throw(_("Row {0}: Check Date is before {1} was stocked")
							 .format(row.idx, row.pond_cycle))

			total += row.death_count or 0

		self.total_death = total

	def on_update(self):
		cycles = {row.pond_cycle for row in self.rows}
		before = self.get_doc_before_save()
		if before:
			cycles |= {row.pond_cycle for row in before.rows}
		for c in cycles:
			frappe.get_doc("Pond Cycle", c).update_mortality()

	def after_delete(self):
		for row in self.rows:
			frappe.get_doc("Pond Cycle", row.pond_cycle).update_mortality()

	pass
