# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Block(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		block_letter: DF.Data
		cost_center: DF.Link
		farm_site: DF.Link
		warehouse: DF.Link
	# end: auto-generated types

	def autoname(self):
		site_code = frappe.db.get_value("Farm Site", self.farm_site, "site_code")
		self.name = f"{site_code}-{self.block_letter.strip().upper()}"

	def validate(self):
		self.block_letter = (self.block_letter or "").strip().upper()
		self.validate_cost_center()
		self.validate_warehouse()

	def validate_cost_center(self):
		site_cc = frappe.db.get_value("Farm Site", self.farm_site, "cost_center")
		cc = frappe.db.get_value(
			"Cost Center", self.cost_center, ["is_group", "parent_cost_center"], as_dict=True
		)

		if cc.is_group:
			frappe.throw(_("{0} is a group cost center — pick a block cost center under it")
						 .format(self.cost_center))

		if site_cc and cc.parent_cost_center != site_cc:
			frappe.throw(_("Cost Center {0} does not belong to {1} (expected under {2})")
						 .format(self.cost_center, self.farm_site, site_cc))

	def validate_warehouse(self):
		site_wh = frappe.db.get_value("Farm Site", self.farm_site, "warehouse")
		wh = frappe.db.get_value(
			"Warehouse", self.warehouse, ["is_group", "parent_warehouse"], as_dict=True
		)
		if not wh.is_group:
			frappe.throw(_("{0} must be a group warehouse (the block's own group)")
						 .format(self.warehouse))
		if site_wh and wh.parent_warehouse != site_wh:
			frappe.throw(_("Warehouse {0} is not under {1}'s warehouse {2}")
						 .format(self.warehouse, self.farm_site, site_wh))

	pass
