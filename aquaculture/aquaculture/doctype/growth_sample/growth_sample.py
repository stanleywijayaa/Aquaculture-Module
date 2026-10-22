# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import date_diff, flt, getdate, today

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

		r.culture_day = date_diff(self.sample_date, stocking_date)
		r.abw_g = 1000 / r.count_per_kg

		harvested_pcs, harvested_kg = harvested_until(r.pond_cycle, self.sample_date)
		alive = max(flt(total_stocked) - deaths_until(r.pond_cycle, self.sample_date) - harvested_pcs, 0)
		r.est_biomass_kg = alive * r.abw_g / 1000

		r.feed_to_date_kg = feed_until(r.pond_cycle, self.sample_date)
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


def feed_until(pond_cycle, date):
	"""Total kg fed to this cycle up to and including `date` (submitted Feed Logs only)."""
	fl = frappe.qb.DocType("Feed Log")
	fi = frappe.qb.DocType("Feed Log Item")
	total = (
		frappe.qb.from_(fi).join(fl).on(fi.parent == fl.name)
		.select(Sum(fi.qty_kg))
		.where((fi.pond_cycle == pond_cycle) & (fl.docstatus == 1) & (fi.feed_date <= date))
	).run()[0][0]
	return flt(total)


def deaths_until(pond_cycle, date):
	"""Dead shrimp counted for this cycle up to and including `date`."""
	dc = frappe.qb.DocType("Daily Pond Check")
	dr = frappe.qb.DocType("Daily Pond Check Row")
	total = (
		frappe.qb.from_(dr).join(dc).on(dr.parent == dc.name)
		.select(Sum(dr.death_count))
		.where((dr.pond_cycle == pond_cycle) & (dc.check_date <= date))
	).run()[0][0]
	return flt(total)

def harvested_until(pond_cycle, date):
	"""Pieces and kg taken out of this cycle by submitted harvests up to and including `date`."""
	he = frappe.qb.DocType("Harvest Event")
	hr = frappe.qb.DocType("Harvest Event Pond")
	pcs, kg = (
		frappe.qb.from_(hr).join(he).on(hr.parent == he.name)
		.select(Sum(hr.pieces), Sum(hr.weight_kg))
		.where((hr.pond_cycle == pond_cycle) & (he.docstatus == 1) & (he.harvest_date <= date))
	).run()[0]
	return flt(pcs), flt(kg)


def update_cycles(cycles):
	for name in cycles:
		if frappe.db.exists("Pond Cycle", name):
			frappe.get_doc("Pond Cycle", name).update_growth()

	pass
