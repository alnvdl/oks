#!/usr/bin/env python
#-*- coding:utf-8 -*-

from oks.gui.dialog import Dialog
import oks

class DialogCompany(Dialog):
    def __init__(self, gladeFile, parent):
        Dialog.__init__(self,
                        gladeFile, 
                        parent,
                        "dialog_company", 
                        "entry_company_name",
                        ("entry_company_name", "name"),
                        ("entry_company_realname", "full_name"),
                        ("entry_company_cnpj", "cnpj"),
                        ("entry_company_zipcode", "zip_code"),
                        ("entry_company_address", "address"),
                        ("entry_company_neighborhood", "neighborhood"),
                        ("entry_company_phone", "phone"),
                        ("entry_company_state", "state"),
                        ("entry_company_city", "city"),
                        ("combobox_company_type", "type_"),
                        ("entry_company_email", "email"),
                        ("entry_company_fax", "fax"),
                        ("entry_company_ie", "ie"),
                        ("textview_company_notes", "notes"),)
        self.set_size(480)
        self.combobox_company_type.set_options(*oks.COMPANY_TYPES_DESC[:-1])

        completion = self.services["completion"]
        self.entry_company_city.set_completion(completion("companies:city"))
        self.entry_company_state.set_completion(completion("companies:state"))
