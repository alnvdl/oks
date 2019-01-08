#!/usr/bin/env python
#-*- coding:utf-8 -*-

import core.db
from core.db.models.internal import InternalModel

MASS_CONVERSION_UNIT = 1000 # TODO: Move this somewhere else or integrate in 
                            # the db

class Formula(InternalModel):
    def __init__(self, productionItem):
        InternalModel.__init__(self)
        self.productionItem = productionItem
        self.update_IO()
             
    def update_IO(self):
        if self.productionItem.IO == 0:
            self.IO = 1
        else:
            self.IO = 0
        for (iter_, component) in self:
            component.IO = self.IO
                
    def add_to_proportion_sum(self, proportion):
        self.productionItem.proportion_sum += proportion
        
    def remove_from_proportion_sum(self, proportion):
        self.productionItem.proportion_sum -= proportion
        
    def get_proportion_for_component(self, componentMass):
        proportion_sum = self.productionItem.proportion_sum
        totalMass = self.productionItem.get_totalMass()
        if not totalMass or not proportion_sum:
            return 0.0
        return (self.productionItem.proportion_sum * componentMass * MASS_CONVERSION_UNIT) / totalMass
        
    def update_components(self):
        proportion_sum = self.productionItem.proportion_sum
        if proportion_sum <= 0:
            return
        totalMass = self.productionItem.get_totalMass()
        for (iter_, component) in self:
            component.quantity = (
            ((component.proportion * totalMass) / proportion_sum)
            / MASS_CONVERSION_UNIT)
            InternalModel.update(self, component, iter_)
        
    def insert(self, rowObject, type_=core.db.NEW):
        if type_ == core.db.NEW:
            self.add_to_proportion_sum(rowObject.proportion)
            rowObject.IO = self.IO
        else:
            proportion = self.get_proportion_for_component(rowObject.quantity)
            rowObject.proportion = proportion
        rowIter = InternalModel.insert(self, rowObject, type_)
        self.update_components()
        return rowIter
          
    def update(self, *args):
        pass # No support for direct updates
        
    def delete(self, rowIter):
        oldRowObject = self.get_object(rowIter)
        InternalModel.delete(self, rowIter)
        self.remove_from_proportion_sum(oldRowObject.proportion)
