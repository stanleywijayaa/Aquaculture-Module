# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Pond(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		area_m2: DF.Float
		block: DF.Link
		disabled: DF.Check
		farm_site: DF.Link | None
		length_m: DF.Float
		pond_label: DF.Data | None
		pond_number: DF.Int
		width_m: DF.Float
	# end: auto-generated types
	def autoname(self):
		self.name = f"{self.block}{self.pond_number}"

	def validate(self):
		if not self.pond_number or self.pond_number < 1:
			frappe.throw(_("Pond Number must be 1 or higher"))

		block = frappe.db.get_value("Block", self.block, ["farm_site", "block_letter"], as_dict=True)
		self.sort_key = f"{self.block}-{self.pond_number:02d}"   # SR-A-01, SR-A-02 … SR-A-10
		self.farm_site = block.farm_site
		self.pond_label = f"{block.block_letter}{self.pond_number}"
		self.area_m2 = (self.length_m or 0) * (self.width_m or 0)

	pass
