#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from core.output import *
from oks.elements.operation import OperationElement
import oks

class Transaction(OperationElement):
    TYPE = oks.TRANSACTION
    CHANGE_STATUS_WITH_PARENT = False
    
    def __init__(self, **kwargs):
        self.way = ""
        self.value = 2.0
        self.notes = ""
        
        self.row = ("ddate", "way", "value", "notes")
        OperationElement.__init__(self, **kwargs)
        
    def get_value_for_operation(self):
        return self.value
        
    def make_output(self):        
        transaction = Section("transaction_{0}".format(self.row_id), 
                              oks.TRANSACTION_TYPES_DESC[self.IO])
        
        ddate = DateData("ddate", "Data", self.ddate)
        transaction.add_child(ddate)
        
        way = StringData("way", "Forma", self.way)
        transaction.add_child(way)
        
        value = CurrencyData("value", "Valor", self.value, "R$")
        transaction.add_child(value)

        notes = StringData("notes", "Observações", self.notes)
        transaction.add_child(notes) 

        status = StringData("status", "Status",
                            oks.TRANSACTION_STATUS_DESC[self.status])
        transaction.add_child(status)

        return transaction
