# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GrowthSampleRow(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		abw_g: DF.Float
		adg_g: DF.Float
		count_per_kg: DF.Int
		culture_day: DF.Int
		est_biomass_kg: DF.Float
		fcr: DF.Float
		feed_day_kg: DF.Float
		feed_period_kg: DF.Float
		feed_to_date_kg: DF.Float
		notes: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pond: DF.Link | None
		pond_cycle: DF.Link
		population: DF.Int
		sr: DF.Percent
	# end: auto-generated types

	pass
