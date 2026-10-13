# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DailyPondCheckRow(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		death_count: DF.Int
		feed_leftover: DF.Literal["", "Finished", "Little", "Much"]
		notes: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		ph: DF.Float
		pond: DF.Link | None
		pond_cycle: DF.Link
		temperature: DF.Float
	# end: auto-generated types

	pass
