#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re

from core.output import *
from core.report import Report
from core.utils import date_to_str
import oks

class InventoryReport(Report):
    NAME = "Listagem"
    DESCRIPTION = "Listagem do inventário. Selecione as opções para filtrar."
    OPTIONS = [("common_items", oks.REPORT_OPTION_BOOL, 
                "Incluir itens comuns", True),
                
               ("raw_materials",oks.REPORT_OPTION_BOOL,
                "Incluir matérias primas", True),
                
               ("production_items", oks.REPORT_OPTION_BOOL, 
                "Incluir itens de produção",True),
                
               ("services", oks.REPORT_OPTION_BOOL,
                "Incluir serviços", True),
                
               ("name", oks.REPORT_OPTION_TEXT,
                "Filtrar por nome", ""),]
              
    def __init__(self, db):
        Report.__init__(self, db)
    
    def make(self):        
        Report.make(self)
        
        items = []
        for (option, type_) in ((self.common_items, oks.TYPE_COMMON_ITEM),
                                (self.raw_materials, oks.TYPE_RAW_MATERIAL),
                                (self.production_items, oks.TYPE_PRODUCTION_ITEM), 
                                (self.services, oks.TYPE_SERVICE)):
            if option:
                items.extend(self.db.cached_load(oks.ITEM,
                                                 type_ = type_,
                                                 name = "~%%%s%%" % self.name))
        
        items.sort(key = lambda item: item.name)
        

        total = 0.0        
        for item in items:
            self.data.append((item.name,
                              item.quantity,
                              item.price))
            total += item.price * item.quantity
                            
        self.bits.append(CurrencyData("total", "Total", total, unit="R$"))

    def make_output(self):
        Report.make_output(self)
        return TableSection("inventory_report", self.NAME,
                            (StringData("item", "Item"),
                             FloatData("quantity", "Quantidade",
                                       strip_zeros=True),
                             CurrencyData("price", "Preço", unit="R$")),
                            self.data, self.bits)
    
class MostImportantItems(Report):
    NAME = "Items com maior circulação"
    DESCRIPTION = "Listagem itens do inventário por ordem de circulação."
    OPTIONS = oks.DATE_RANGE_OPTIONS + [("name", oks.REPORT_OPTION_TEXT,
                                         "Filtrar por nome", ""),]
              
    def __init__(self, db):
        Report.__init__(self, db)
    
    def get_items_list(self, element, use):
        if element.HAS_CHILDREN:
            for container in element.children.values():
                for (iter_, element) in container:
                    if hasattr(element, "quantity"):
                        try:
                            use[element.name] += element.quantity
                        except KeyError:
                            use[element.name] = element.quantity
                    use = self.get_items_list(element, use)
        return use
            
    def make(self):        
        Report.make(self)
        
        operations = self.db.cached_load(oks.OPERATION,
                                         date=(self.start_date, self.end_date),
                                         status=oks.TYPE_STATUS_COMPLETE)
        
        expr = self.name
        expr = expr.replace("%", "*")
        expr = expr.replace("_", ".")
        regex = re.compile(expr, re.IGNORECASE)
        
        use = {}
        for operation in operations:
            tmp = self.get_items_list(operation, {})
            for (item, quantity) in tmp.items():
                if regex.search(item) is not None:
                    try:
                        use[item] += quantity
                    except KeyError:
                        use[item] = quantity
                
        self.data = use.items()
        self.data.sort(key = lambda (item, quantity): quantity)

    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))    
        return TableSection("most_important_items", title,
                            (StringData("item", "Item"),
                             FloatData("quantity", "Quantidade",
                                       strip_zeros=True)),
                            self.data, self.bits)
