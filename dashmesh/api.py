# -*- coding: utf-8 -*-
# Copyright (c) 2021, Craft
# For license information, please see license.txt

import frappe
import json

@frappe.whitelist()
def count(name):
    """
    for getting count of Goods In Transit Note for a specific Purchase Order
    """
    unique={}
    parent_list = frappe.db.get_list("Goods In Transit Item", {"purchase_order": name }, ['parent'])
    if len(parent_list) >0:
        for row in parent_list:
            if row.parent not in unique:
                unique[row.parent]=row.parent
    return len(unique) or 0

@frappe.whitelist()
def document(parent_doc,doc_name):
    old_doc = frappe.get_doc(parent_doc, doc_name)
    return old_doc
