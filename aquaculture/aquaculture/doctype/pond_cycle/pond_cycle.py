# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import date_diff, flt, getdate, today
from frappe.query_builder.functions import Min, Sum
from frappe.query_builder import Order


class PondCycle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		block: DF.Link | None
		end_date: DF.Date | None
		est_biomass_kg: DF.Float
		farm_site: DF.Link | None
		fcr: DF.Float
		final_fcr: DF.Float
		harvest_survival: DF.Percent
		last_abw_g: DF.Float
		last_count_per_kg: DF.Int
		last_sample_date: DF.Date | None
		notes: DF.SmallText | None
		pond: DF.Link
		prep_start_date: DF.Date
		status: DF.Literal["Preparation", "Stocked", "Partially Harvested", "Closed"]
		stocking_date: DF.Date | None
		total_death: DF.Int
		total_feed_cost: DF.Currency
		total_feed_kg: DF.Float
		total_harvest_kg: DF.Float
		total_harvest_pcs: DF.Float
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

	@property
	def est_alive(self):
		return max(flt(self.total_stocked) - flt(self.total_deaths) - flt(self.total_harvest_pcs), 0)

	@property
	def est_survival(self):
		if not self.total_stocked:
			return 0
		return (self.est_alive + flt(self.total_harvest_pcs)) / flt(self.total_stocked) * 100

	def update_mortality(self):
		row = frappe.qb.DocType("Daily Pond Check Row")
		total = (
			frappe.qb.from_(row)
			.select(Sum(row.death_count))
			.where((row.pond_cycle == self.name) & (row.parenttype == "Daily Pond Check"))
		).run()[0][0]
		self.db_set("total_death", total or 0)

	def update_feed(self):
		fl = frappe.qb.DocType("Feed Log")
		fi = frappe.qb.DocType("Feed Log Item")
		kg, cost = (
			frappe.qb.from_(fi)
			.join(fl).on(fi.parent == fl.name)
			.select(Sum(fi.qty_kg), Sum(fi.cost))
			.where((fi.pond_cycle == self.name) & (fl.docstatus == 1))
		).run()[0]
		self.db_set({"total_feed_kg": flt(kg), "total_feed_cost": flt(cost)})

	def update_growth(self):
		gs = frappe.qb.DocType("Growth Sample")
		gr = frappe.qb.DocType("Growth Sample Row")
		rows = (
			frappe.qb.from_(gr).join(gs).on(gr.parent == gs.name)
			.select(gs.sample_date, gr.count_per_kg, gr.abw_g, gr.est_biomass_kg, gr.fcr)
			.where(gr.pond_cycle == self.name)
			.orderby(gs.sample_date, order=Order.desc)
			.limit(1)
		).run(as_dict=True)
		last = rows[0] if rows else {}
		self.db_set({
			"last_sample_date": last.get("sample_date"),
			"last_count_per_kg": last.get("count_per_kg") or 0,
			"last_abw_g": last.get("abw_g") or 0,
			"est_biomass_kg": last.get("est_biomass_kg") or 0,
			"fcr": last.get("fcr") or 0,
		})

	def update_harvest(self):
		he = frappe.qb.DocType("Harvest Event")
		hr = frappe.qb.DocType("Harvest Event Pond")
		rows = (
			frappe.qb.from_(hr).join(he).on(hr.parent == he.name)
			.select(he.harvest_date, hr.harvest_type, hr.weight_kg, hr.pieces)
			.where((hr.pond_cycle == self.name) & (he.docstatus == 1))
		).run(as_dict=True)

		kg = sum(flt(r.weight_kg) for r in rows)
		pcs = sum(flt(r.pieces) for r in rows)
		totals = [r for r in rows if r.harvest_type == "Total"]

		if totals:
			status, end_date = "Closed", max(r.harvest_date for r in totals)
		elif rows:
			status, end_date = "Partially Harvested", None
		else:
			status, end_date = "Stocked", None

		closed = bool(totals)
		self.db_set({
			"status": status,
			"end_date": end_date,
			"total_harvest_kg": kg,
			"total_harvest_pcs": pcs,
			"harvest_survival": pcs / flt(self.total_stocked) * 100 if closed and pcs and self.total_stocked else 0,
			"final_fcr": flt(self.total_feed_kg) / kg if closed and kg else 0,
		})

	pass
