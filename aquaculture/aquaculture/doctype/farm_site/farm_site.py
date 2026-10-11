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

		cost_center: DF.Link | None
		site_code: DF.Data
		site_name: DF.Data
		warehouses: DF.Table[FarmSiteWarehouse]
	# end: auto-generated types

	def validate(self):
		self.site_code = (self.site_code or "").strip().upper()
		self.validate_warehouses()

	def validate_warehouses(self):
		seen = set()
		for row in self.warehouses:
			if row.item_group in seen:
				frappe.throw(_("Row {0}: Item Group {1} is listed twice")
							 .format(row.idx, row.item_group))
			seen.add(row.item_group)

			if frappe.db.get_value("Warehouse", row.warehouse, "is_group"):
				frappe.throw(_("Row {0}: {1} is a group warehouse — pick a gudang under it")
				             .format(row.idx, row.warehouse))
