# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FeedLogItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cost: DF.Currency
		feed_date: DF.Date
		item_code: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		pond: DF.Link
		pond_cycle: DF.Link
		qty_kg: DF.Float
		stock_entry: DF.Link | None
	# end: auto-generated types

	pass
