# Copyright (c) 2026, Stanley and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FarmSite(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from aquaculture.aquaculture.doctype.farm_site_warehouse.farm_site_warehouse import FarmSiteWarehouse
		from frappe.types import DF

		cost_center: DF.Link
		site_code: DF.Data
		site_name: DF.Data
		warehouse: DF.Link
		warehouses: DF.Table[FarmSiteWarehouse]
	# end: auto-generated types

	def validate(self):
		self.site_code = (self.site_code or "").strip().upper()
		self.validate_site_warehouse()
		self.validate_storage_rules()

	def validate_site_warehouse(self):
		if self.warehouse and not frappe.db.get_value("Warehouse", self.warehouse, "is_group"):
			frappe.throw(_("Warehouse {0} must be a group warehouse").format(self.warehouse))

	def validate_storage_rules(self):
		seen = set()
		for row in self.warehouses:
			if row.item_group in seen:
				frappe.throw(_("Row {0}: Item Group {1} is listed twice")
							 .format(row.idx, row.item_group))
			seen.add(row.item_group)
