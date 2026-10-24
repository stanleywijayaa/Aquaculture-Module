# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockingEventPond(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		counted_qty: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pond: DF.Link | None
		pond_cycle: DF.Link
		quantity: DF.Int
	# end: auto-generated types

	pass
