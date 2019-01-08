#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from core.output import *
from core.db.models.internal import InternalModel
from core.db.row import Row, ChildRow, RowWithStatus
import oks

class OperationElement(RowWithStatus, ChildRow):
    def __init__(self, **kwargs):
        self.IO = 0
        self.row = ("IO",) + self.row
        
        RowWithStatus.__init__(self, self.row)
        ChildRow.__init__(self, **kwargs)
        
                
class Operation(RowWithStatus, Row):
    TYPE = oks.OPERATION
    HAS_CHILDREN = True
    CHILDREN_TYPE = (oks.PRODUCT, oks.PRODUCTION_ITEM, oks.EXCHANGE_ITEM, 
                     oks.TRANSACTION)
                     
    def __init__(self, **kwargs):
        self.type_ = oks.TYPE_SALE_OPERATION
        self.company = ""
        self.oid = 0
        self.date = datetime.date.today()
        self.notes = ""
        self.row = ("type_", "company", "oid", "date", "notes")
        
        self.input = InternalModel(oks.INPUT)
        self.output = InternalModel(oks.OUTPUT)
        
        self.title = ""
        
        self.top = 0
        self.bottom = 1
        
        self.topName = ""
        self.bottomName = ""
        
        self.inputType = ()
        self.outputType = ()
                                 
        RowWithStatus.__init__(self, self.row)
        Row.__init__(self, **kwargs)

        self.children["input"] = self.input
        self.children["output"] = self.output
        
    def insert_element(self, IO, element, loading = False):
        if IO == oks.INPUT:
            return self.input.insert(element, not loading)
        elif IO == oks.OUTPUT:
            return self.output.insert(element, not loading)
    
    def update_element(self, IO, iter_, element):
        if IO == oks.INPUT:
            self.input.update(element, iter_)
        elif IO == oks.OUTPUT:
            self.output.update(element, iter_)
             
    def delete_element(self, IO, iter_):
        if IO == oks.INPUT:
            self.input.delete(iter_)
        elif IO == oks.OUTPUT:
            self.output.delete(iter_)
            
    def load_child(self, child):
        if child.IO == oks.INPUT:
            return self.input.insert(child, False)
        elif child.IO == oks.OUTPUT:
            return self.output.insert(child, False)
        
    def get_type_(self):
        return self._type_
    
    def set_type_(self, type_):
        if type_ == oks.TYPE_SALE_OPERATION:
            self.title = "Operação de saída - NF %i"
            
            self.top = oks.OUTPUT
            self.bottom = oks.INPUT
            
            self.topName = "Itens"
            self.bottomName = "Transações"

            self.inputType = (oks.TRANSACTION, )
            self.outputType = (oks.PRODUCT, )
            
        elif type_ == oks.TYPE_PURCHASE_OPERATION:
            self.title = "Operação de entrada - NF %i"
            
            self.top = oks.INPUT
            self.bottom = oks.OUTPUT
            
            self.topName = "Itens"
            self.bottomName = "Transações"
            
            self.inputType = (oks.PRODUCT, )
            self.outputType = (oks.TRANSACTION, )
            
        elif type_ == oks.TYPE_PRODUCTION_OPERATION:
            self.title = "Operação de produção %i"
            
            self.top = oks.INPUT
            self.bottom = None

            self.topName = "Itens de produção"
            self.bottomName = ""
                        
            self.inputType = (oks.PRODUCTION_ITEM, )
            self.outputType = (None, )
            
        elif type_ == oks.TYPE_EXCHANGE_OPERATION:
            self.title = "Operação de troca %i"
            
            self.top = oks.OUTPUT
            self.bottom = oks.INPUT

            self.topName = "Itens (Saída)"
            self.bottomName = "Itens (Entrada)"
            
            self.inputType = (oks.EXCHANGE_ITEM, )
            self.outputType = (oks.EXCHANGE_ITEM, )
            
        self._type_ = type_
    
    type_ = property(get_type_, set_type_)
    
    def get_total_value(self, IO = oks.OUTPUT):
        """ Get the total value for elements in the input or output that have
        the 'get_value_for_operation' method """
        totalValue = 0.0
        
        if IO == oks.INPUT:
            model = self.input
        elif IO == oks.OUTPUT:
            model = self.output
            
        for (iter_, element) in model:
            if hasattr(element, "get_value_for_operation"):
                totalValue += element.get_value_for_operation()

        return totalValue
        
    def make_output(self):
        title = self.title
        if self.oid < 0:
            title = title.replace("- NF ", "")
            
        operation = Section("operation_{0}".format(self.oid), 
                            title % self.oid)

        date = DateData("date", "Data", self.date)
        operation.add_child(date)
        
        company = StringData("company", "Empresa", self.company)
        operation.add_child(company)

        notes = StringData("notes", "Observações", self.notes)
        operation.add_child(notes) 

        for (IO, label) in ((self.top, self.topName), 
                            (self.bottom, self.bottomName)):
            if IO == oks.INPUT:
                model = self.input
            elif IO == oks.OUTPUT:
                model = self.output
            else:
                continue

            count = 1
            totalValue = 0.0
            items = Section("items".format(count), label)
            operation.add_child(items)
    
            for (iter_, element) in model:
                items.add_child(element.make_output())
                count += 1
                # Shouldn't this use the method get_total_value?
                if hasattr(element, "get_value_for_operation"):
                    totalValue += element.get_value_for_operation()
            if totalValue:
                total = CurrencyData("total", "Total", totalValue, "R$")
                items.add_child(total)
        
        return operation
