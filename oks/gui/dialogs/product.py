#!/usr/bin/env python
#-*- coding:utf-8 -*-

from oks.gui.dialog import Dialog

class DialogProduct(Dialog):    
    def __init__(self, builder, parent):
        Dialog.__init__(self,
                        builder, 
                        parent, 
                        "dialog_product", 
                        "entry_product_name",
                        ("entry_product_name", "name"),
                        ("spinbutton_product_quantity", "quantity"),
                        ("spinbutton_product_price", "price"),
                        ("entry_product_notes", "notes"))
            
        completion = self.services["completion"]
        completion = completion("inventory:item")
        # Autocomplete the item's quantity and price
        completion.connect("match-selected", self.auto_set_quantity_and_price)
        self.entry_product_name.set_completion(completion)
        
    def auto_set_quantity_and_price(self, completion, table, rowIter):
        self.spinbutton_product_quantity.set_value(table.get_value(rowIter, 4))
        self.spinbutton_product_price.set_value(table.get_value(rowIter, 5))

