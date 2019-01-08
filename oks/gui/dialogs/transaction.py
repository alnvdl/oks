#!/usr/bin/env python
#-*- coding:utf-8 -*-

from oks.gui.dialog import Dialog
from oks.gui.entrydate import EntryDate

class DialogTransaction(Dialog):
    def __init__(self, builder, parent):
        Dialog.__init__(self,
                        builder,
                        parent,
                        "dialog_transaction",
                        "entry_transaction_way",
                        ("entry_transaction_way", "way"),
                        ("spinbutton_transaction_value", "value"),
                        ("entry_transaction_notes", "notes"))
        # Setting the date...
        self.load_widget("hbox_transaction_date")
        self.entry_date = EntryDate(self, "ddate")
        self.register_field("entry_date", self.entry_date)
        self.hbox_transaction_date.pack_start(self.entry_date.widget)
        self.hbox_transaction_date.show_all()
        
        # Completion support for the way entry
        completion = self.services["completion"]
        self.entry_transaction_way.set_completion(
            completion("transactions:way"))
