# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Order
from frappe.utils import add_days, date_diff, flt, getdate, today

from aquaculture.aquaculture.utils import deaths, feed_kg, harvested

ACTIVE = ("Stocked", "Partially Harvested")


class GrowthSample(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.growth_sample_row.growth_sample_row import GrowthSampleRow
		from frappe.types import DF

		block: DF.Link
		farm_site: DF.Link | None
		notes: DF.SmallText | None
		rows: DF.Table[GrowthSampleRow]
		sample_date: DF.Date
		sampled_by: DF.Link | None
	# end: auto-generated types

	def autoname(self):
		self.name = f"GS-{self.block}-{self.sample_date}"

	def validate(self):
		if getdate(self.sample_date) > getdate(today()):
			frappe.throw(_("Sample Date can't be in the future"))

		self.rows = [r for r in self.rows if r.count_per_kg]
		for i, r in enumerate(self.rows, start=1):
			r.idx = i
		if not self.rows:
			frappe.throw(_("Enter the count per kg for at least one pond"))

		seen = set()
		for r in self.rows:
			self.validate_row(r, seen)
			self.calculate_row(r)

	def validate_row(self, r, seen):
		if r.pond_cycle in seen:
			frappe.throw(_("Row {0}: {1} is entered twice").format(r.idx, r.pond_cycle))
		seen.add(r.pond_cycle)

		cycle = frappe.db.get_value("Pond Cycle", r.pond_cycle,
			["block", "status", "stocking_date"], as_dict=True)
		if cycle.block != self.block:
			frappe.throw(_("Row {0}: {1} is not in block {2}").format(r.idx, r.pond_cycle, self.block))
		if cycle.status not in ACTIVE:
			frappe.throw(_("Row {0}: {1} is {2}, not stocked").format(r.idx, r.pond_cycle, cycle.status))
		if not cycle.stocking_date or getdate(self.sample_date) < getdate(cycle.stocking_date):
			frappe.throw(_("Row {0}: {1} wasn't stocked yet on {2}")
						 .format(r.idx, r.pond_cycle, self.sample_date))
		if r.count_per_kg <= 0:
			frappe.throw(_("Row {0}: count per kg must be more than 0").format(r.idx))

	def calculate_row(self, r):
		stocking_date, total_stocked = frappe.db.get_value(
			"Pond Cycle", r.pond_cycle, ["stocking_date", "total_stocked"])
		date = self.sample_date

		r.culture_day = date_diff(date, stocking_date)
		r.abw_g = 1000 / r.count_per_kg

		harvested_pcs, harvested_kg = harvested(r.pond_cycle, before=date)
		if not r.population:
			r.population = max(flt(total_stocked) - deaths(r.pond_cycle, to_date=date) - harvested_pcs, 0)

		# harvested shrimp survived too, so they count towards SR
		r.sr = (flt(r.population) + harvested_pcs) / flt(total_stocked) * 100 if total_stocked else 0
		r.est_biomass_kg = flt(r.population) * r.abw_g / 1000

		prev = previous_sample(r.pond_cycle, date)
		if prev:
			r.adg_g = (r.abw_g - flt(prev.abw_g)) / date_diff(date, prev.sample_date)
			r.feed_period_kg = feed_kg(r.pond_cycle, to_date=date, after=prev.sample_date)
		else:
			r.adg_g = r.abw_g / r.culture_day if r.culture_day else 0
			r.feed_period_kg = feed_kg(r.pond_cycle, to_date=date)

		r.feed_day_kg = feed_kg(r.pond_cycle, to_date=date, after=add_days(date, -1))
		r.feed_to_date_kg = feed_kg(r.pond_cycle, to_date=date)

		grown_kg = r.est_biomass_kg + harvested_kg
		r.fcr = r.feed_to_date_kg / grown_kg if grown_kg else 0

	def on_update(self):
		cycles = {r.pond_cycle for r in self.rows}
		before = self.get_doc_before_save()
		if before:
			cycles |= {r.pond_cycle for r in before.rows}
		update_cycles(cycles)

	def after_delete(self):
		update_cycles({r.pond_cycle for r in self.rows})


def previous_sample(pond_cycle, date):
	"""The latest earlier sample of this cycle (date and MBW), or None."""
	gs = frappe.qb.DocType("Growth Sample")
	gr = frappe.qb.DocType("Growth Sample Row")
	rows = (
		frappe.qb.from_(gr).join(gs).on(gr.parent == gs.name)
		.select(gs.sample_date, gr.abw_g)
		.where((gr.pond_cycle == pond_cycle) & (gs.sample_date < date))
		.orderby(gs.sample_date, order=Order.desc)
		.limit(1)
	).run(as_dict=True)
	return rows[0] if rows else None


def update_cycles(cycles):
	for name in cycles:
		if frappe.db.exists("Pond Cycle", name):
			frappe.get_doc("Pond Cycle", name).update_growth()

	pass
