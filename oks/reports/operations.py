#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from core.output import *
from core.report import Report
from core.utils import date_to_str
import oks

class OperationsReport(Report):   
    OPTIONS = oks.DATE_RANGE_OPTIONS + [("status", 
                                         oks.REPORT_OPTION_BOOL,
                                         "Mostrar apenas operações concluídas", 
                                         True)]
                         
    def __init__(self, db):
        Report.__init__(self, db)
                         
    def make(self, type_):  
        Report.make(self)
        if self.status == True:
            status = oks.TYPE_STATUS_COMPLETE
        else:
            status = (oks.TYPE_STATUS_INCOMPLETE, oks.TYPE_STATUS_COMPLETE)
            
        operations = self.db.cached_load(oks.OPERATION, 
                                         date=(self.start_date, self.end_date),
                                         type_=type_,
                                         status=status)
        operations.sort(key = lambda operation: operation.date)

        total = 0.0        
        for operation in operations:
            subtotal = operation.get_total_value()
            total += subtotal
            self.data.append([operation.date, operation.company, 
                              operation.oid, subtotal])
        if total:
            self.bits.append(CurrencyData("total", "Total", total, unit="R$"))
 
    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))        
        return TableSection("compact_companies_report", title,
                            (DateData("date", "Data"),
                             StringData("company", "Empresa"),
                             IntegerData("oid", "ID"),
                             CurrencyData("value", "Valor", unit="R$")), 
                            self.data, self.bits)
        

class OutgoingOperationsReport(OperationsReport):
    NAME = "Operações de venda"
    DESCRIPTION = "Listar as operações de venda para um dado período."
    
    def __init__(self, db):
        OperationsReport.__init__(self, db)
                                
    def make(self):
        OperationsReport.make(self, oks.TYPE_SALE_OPERATION)


class IncomingOperationsReport(OperationsReport):
    NAME = "Operações de compra"
    DESCRIPTION = "Listar as operações de compra para um dado período."
                                    
    def __init__(self, db):
        OperationsReport.__init__(self, db)
                                
    def make(self):
        OperationsReport.make(self, oks.TYPE_PURCHASE_OPERATION)


class ProductionOperationsReport(Report):    
    NAME = "Operações de produção"
    DESCRIPTION = "Listar as operações de produção para um dado período."
    OPTIONS = oks.DATE_RANGE_OPTIONS + [("status", 
                                         oks.REPORT_OPTION_BOOL,
                                         "Mostrar operações já concluídas", 
                                         False)]
              
    def __init__(self, db):
        Report.__init__(self, db)
        
    def make(self):        
        Report.make(self)
        if self.status == True:
            status = (oks.TYPE_STATUS_INCOMPLETE, oks.TYPE_STATUS_COMPLETE)
        else:
            status = oks.TYPE_STATUS_INCOMPLETE
        
        operations = self.db.cached_load(oks.OPERATION, 
                                         date=(self.start_date, self.end_date),
                                         type_ = oks.TYPE_PRODUCTION_OPERATION,
                                         status = status)

        count = 0    
        for operation in operations:            
            for (iter_, item) in operation.input:
                self.data.append((operation.date, operation.company, 
                                  operation.oid, item.name, item.quantity))
            count += 1
        
        self.data.sort(key = lambda row: row[2])
        
        if count != 0:
            self.bits.append("%i itens em %i operações" % (len(self.data), 
                                                           count))
    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))        
        return TableSection("production_operations_report", title,
                            (DateData("date", "Data"),
                             StringData("company", "Empresa"),
                             IntegerData("oid", "ID"),
                             StringData("item", "Item"),
                             FloatData("quantity", "Quantidade", strip_zeros=True)), 
                            self.data, self.bits)
        

class ProductionCostReport(Report):
    NAME = "Custo de produção"
    DESCRIPTION = "Listar os custos da produção de itens em operações de um "\
                  "dado período."
                   
    OPTIONS = oks.DATE_RANGE_OPTIONS
    
    def __init__(self, db):
        Report.__init__(self, db)

    def make(self):
        Report.make(self)
        operations = self.db.cached_load(oks.OPERATION, 
                                         date=(self.start_date, self.end_date),
                                         type_ = oks.TYPE_PRODUCTION_OPERATION)
        operations.sort(key = lambda operation: operation.date)
            
        raw_materials = [(item.name, item.price) for item in
                         self.db.cached_load(oks.ITEM, 
                                             type_=oks.TYPE_RAW_MATERIAL)]
        raw_materials = dict(raw_materials)
                                           
        total = 0.0
        self.data = []
        for operation in operations:
            for (iter_, item) in operation.input:
                if item.TYPE == oks.PRODUCTION_ITEM:
                    cost = 0.0
                    for (iter_, raw_material) in item.formula:
                        if raw_material.name in raw_materials:
                            cost += (raw_material.quantity * 
                                     raw_materials[raw_material.name])
                    self.data.append((operation.oid,
                                      item.name,
                                      item.quantity,
                                      cost / item.quantity,
                                      cost))
                    total += cost
                
        self.bits.append(CurrencyData("total", "Custo total no período", total,
                                      unit="R$"))

    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))        
        return TableSection("production_cost_report", title,
                            (IntegerData("oid", "OS"),
                             StringData("item", "Item"),
                             FloatData("quantity", "Quantidade", strip_zeros=True), 
                             CurrencyData("value", "Custo unitário", unit="R$"), 
                             CurrencyData("total", "Custo total", unit="R$")), 
                            self.data, self.bits)

            
class ProductionSalesReport(Report):
    NAME = "Venda de itens de produção"
    DESCRIPTION = "Vendas de itens de produção em um período."
    OPTIONS = oks.DATE_RANGE_OPTIONS
        
    def __init__(self, db):
        Report.__init__(self, db)
         
    def make(self):
        Report.make(self)
        
        operations = self.db.cached_load(oks.OPERATION,
                                         date=(self.start_date, self.end_date),
                                         type_=oks.TYPE_SALE_OPERATION,
                                         status=oks.TYPE_STATUS_COMPLETE)
        operations.sort(key = lambda operation: operation.date)
        
        total = 0.0
        self.data = []
        valid_items = {}
        for operation in operations:
            for (iter_, element) in operation.output:
                if element.name not in valid_items:
                    pitems = self.db.cached_load(oks.ITEM,
                                                 name = element.name,
                                                 type_ = oks.TYPE_PRODUCTION_ITEM)
                    pitems = [pitem.name for pitem in pitems]
                    valid_items[element.name] = element.name in pitems
                valid = valid_items[element.name]
                
                if valid:
                    item = element
                    item_total = item.get_value_for_operation()
                    self.data.append((operation.date,
                                      operation.company,
                                      item.name,
                                      item.quantity,
                                      item.price,
                                      item_total))
                    total += item_total
                    
        self.bits.append(CurrencyData("total", "Total", total, unit="R$"))
  
    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))        
        return TableSection("production_sales_report", title,
                            (DateData("date", "Data"),
                             StringData("company", "Empresa"),
                             StringData("item", "Item"),
                             FloatData("quantity", "Quantidade", strip_zeros=True), 
                             CurrencyData("value", "Valor", unit="R$"), 
                             CurrencyData("total", "Total", unit="R$")), 
                            self.data, self.bits)
