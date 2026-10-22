# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HarvestEventPond(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		abw_g: DF.Float
		count_per_kg: DF.Int
		harvest_type: DF.Literal["Partial", "Total"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pieces: DF.Float
		pond: DF.Link | None
		pond_cycle: DF.Link
		weight_kg: DF.Float
	# end: auto-generated types

	pass
