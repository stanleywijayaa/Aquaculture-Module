# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import date_diff, getdate, today
from frappe.query_builder.functions import Min, Sum


class PondCycle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		block: DF.Link | None
		end_date: DF.Date | None
		farm_site: DF.Link | None
		notes: DF.SmallText | None
		pond: DF.Link
		prep_start_date: DF.Date
		status: DF.Literal["Preparation", "Stocked", "Partially Harvested", "Closed"]
		stocking_date: DF.Date | None
		total_stocked: DF.Int
	# end: auto-generated types

	def autoname(self):
		# SR-A1-26-01: pond, year, then a counter per pond per year
		self.name = make_autoname(f"{self.pond}-.YY.-.##")

	@property
	def days_of_culture(self):
		if not self.stocking_date:
			return None
		end = self.end_date or today()
		return date_diff(end, self.stocking_date)

	def validate(self):
		self.validate_closed_lock()
		pond = frappe.db.get_value("Pond", self.pond, ["block", "farm_site", "disabled"], as_dict=True)
		self.block = pond.block
		self.farm_site = pond.farm_site

		if pond.disabled and self.is_new():
			frappe.throw(_("Pond {0} is disabled and cannot start a new cycle").format(self.pond))

		self.validate_dates()
		self.validate_one_open_cycle()

	def validate_dates(self):
		if self.stocking_date and getdate(self.stocking_date) < getdate(self.prep_start_date):
			frappe.throw(_("Stocking Date cannot be before Prep Start Date"))
		if self.end_date and self.stocking_date and getdate(self.end_date) < getdate(self.stocking_date):
			frappe.throw(_("End Date cannot be before Stocking Date"))
		if self.status == "Closed" and not self.end_date:
			frappe.throw(_("Set an End Date before closing the cycle"))

	def validate_one_open_cycle(self):
		if self.status == "Closed":
			return
		other = frappe.db.exists("Pond Cycle", {
			"pond": self.pond,
			"status": ["!=", "Closed"],
			"name": ["!=", self.name],
		})
		if other:
			frappe.throw(_("Pond {0} already has an open cycle: {1}. Close it first.")
						 .format(self.pond, other))
			
	def validate_closed_lock(self):
		before = self.get_doc_before_save()
		if not before or before.status != "Closed":
			return
		if "System Manager" in frappe.get_roles():
			return

		locked = ("pond", "status", "prep_start_date", "stocking_date", "end_date")
		changed = [f for f in locked if str(self.get(f) or "") != str(before.get(f) or "")]
		if changed:
			frappe.throw(_("Cycle {0} is closed. Only a manager can change it.").format(self.name))

	@property
	def density_per_m2(self):
		area = frappe.db.get_value("Pond", self.pond, "area_m2")
		return (self.total_stocked or 0) / area if area else None

	def update_stocking(self):
		row = frappe.qb.DocType("Stocking Event Pond")
		event = frappe.qb.DocType("Stocking Event")
		first_date, total = (
			frappe.qb.from_(row)
			.join(event).on(row.parent == event.name)
			.select(Min(event.stocking_date), Sum(row.quantity))
			.where((row.pond_cycle == self.name) & (row.parenttype == "Stocking Event"))
		).run()[0]

		self.db_set({"stocking_date": first_date, "total_stocked": total or 0})

		if first_date and self.status == "Preparation":
			self.db_set("status", "Stocked")
		elif not first_date and self.status == "Stocked":
			self.db_set("status", "Preparation")

	pass
