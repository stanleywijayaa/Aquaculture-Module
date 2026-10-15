import frappe

ABBR = "TRA"

ITEM_GROUPS = ["Pakan", "Kapur & Mineral", "Pupuk", "Vitamin & Probiotik", "Benur"]
CONTAINER_UOMS = ["Sak", "Pail", "Bungkus", "Kotak", "Jerigen", "Drum", "Botol"]
WAREHOUSE_TYPES = ["Pakan", "Obat", "Kapur"]
STORAGE_RULES = {
	"Pakan": "Pakan",
	"Kapur & Mineral": "Kapur",
	"Pupuk": "Kapur",
	"Vitamin & Probiotik": "Obat",
}
SITES = [
	{"site_name": "Sri Rupat", "site_code": "SR", "blocks": {"A": 10, "B": 12, "C": 7}},
	{"site_name": "Jeram", "site_code": "JR", "blocks": {"A": 6, "B": 6, "C": 10, "D": 10}},
]


def execute():
	company = frappe.db.get_value("Company", {"abbr": ABBR}, "name")
	if not company:
		frappe.throw(f"No company with abbreviation {ABBR}. Run the setup wizard first.")

	create_item_groups()
	create_uoms()
	create_warehouse_types()
	for site in SITES:
		create_site(site, company)

	frappe.db.commit()
	print_summary()


# ---------- small helpers ----------

def ensure(doctype, name, values):
	"""Insert the record unless `name` already exists. Returns the name."""
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **values}).insert()
	return name


def ensure_cost_center(label, parent, is_group, company):
	return ensure("Cost Center", f"{label} - {ABBR}", {
		"cost_center_name": label, "parent_cost_center": parent,
		"is_group": is_group, "company": company,
	})


def ensure_warehouse(label, parent, is_group, company, warehouse_type=None):
	return ensure("Warehouse", f"{label} - {ABBR}", {
		"warehouse_name": label, "parent_warehouse": parent,
		"is_group": is_group, "company": company, "warehouse_type": warehouse_type,
	})


# ---------- sections ----------

def create_item_groups():
	for g in ITEM_GROUPS:
		ensure("Item Group", g, {"item_group_name": g, "parent_item_group": "All Item Groups"})


def create_uoms():
	for u in CONTAINER_UOMS:
		ensure("UOM", u, {"uom_name": u, "must_be_whole_number": 1})


def create_warehouse_types():
	for t in WAREHOUSE_TYPES:
		if not frappe.db.exists("Warehouse Type", t):
			frappe.get_doc({"doctype": "Warehouse Type"}).insert(set_name=t)


def create_site(site, company):
	root_cc = frappe.db.get_value("Cost Center",
		{"company": company, "is_group": 1, "parent_cost_center": ["is", "not set"]}, "name")
	root_wh = frappe.db.get_value("Warehouse",
		{"company": company, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name")
	if not root_cc or not root_wh:
		frappe.throw(f"Root not found: cost center={root_cc}, warehouse={root_wh}")

	name, code = site["site_name"], site["site_code"]

	if frappe.db.exists("Farm Site", name):
		# Already set up (e.g. the dev site): reuse its own cost center and warehouse
		site_cc, site_wh = frappe.db.get_value("Farm Site", name, ["cost_center", "warehouse"])
	else:
		site_cc = ensure_cost_center(name, root_cc, 1, company)
		site_wh = ensure_warehouse(name, root_wh, 1, company)
		frappe.get_doc({
			"doctype": "Farm Site",
			"site_name": name,
			"site_code": code,
			"cost_center": site_cc,
			"warehouse": site_wh,
			"warehouses": [
				{"item_group": g, "warehouse_type": t} for g, t in STORAGE_RULES.items()
			],
		}).insert()

	for letter, pond_count in site["blocks"].items():
		block = f"{code}-{letter}"
		if not frappe.db.exists("Block", block):
			label = f"{code} Blok {letter}"
			block_cc = ensure_cost_center(label, site_cc, 0, company)
			block_wh = ensure_warehouse(label, site_wh, 1, company)
			for t in WAREHOUSE_TYPES:
				ensure_warehouse(f"{label} {t}", block_wh, 0, company, warehouse_type=t)
			frappe.get_doc({
				"doctype": "Block",
				"farm_site": name,
				"block_letter": letter,
				"cost_center": block_cc,
				"warehouse": block_wh,
			}).insert()

		for n in range(1, pond_count + 1):
			if not frappe.db.exists("Pond", f"{block}{n}"):
				frappe.get_doc({"doctype": "Pond", "block": block, "pond_number": n}).insert()


def print_summary():
	print("Farm Sites:", frappe.db.count("Farm Site"))                                         # 2
	print("Blocks:", frappe.db.count("Block"))                                                 # 7
	print("Ponds:", frappe.db.count("Pond"))                                                   # 61
	print("Typed warehouses:", frappe.db.count("Warehouse", {"warehouse_type": ["in", WAREHOUSE_TYPES]}))  # 21