#!/usr/bin/env python
#-*- coding:utf-8 -*-

from core.output import *
from oks.elements.operation import OperationElement
import oks

class ExchangeItem(OperationElement):
    TYPE = oks.EXCHANGE_ITEM        
    def __init__(self, **kwargs):
        self.name = ""
        self.quantity = 1
        self.notes = ""
        self.row = ("name", "quantity", "notes")

        OperationElement.__init__(self, **kwargs)
    
    def make_output(self):
        eitem = Section("eitem_{0}".format(self.row_id), self.name)
        
        quantity = FloatData("quantity", "Quantidade", self.quantity,
                             strip_zeros=True)
        eitem.add_child(quantity)
        
        notes = StringData("notes", "Observações", self.notes)
        eitem.add_child(notes) 

        return eitem
