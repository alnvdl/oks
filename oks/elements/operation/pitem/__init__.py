#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re
import math

import core.db
from core.output import *
from core.utils import str_to_float
from oks.elements.operation import OperationElement
from oks.elements.operation.pitem.formula import Formula, MASS_CONVERSION_UNIT
from oks.elements.operation.pitem.rawmaterial import RawMaterial
import oks

ITEM_PATTERN = """
^ # beginning of string
([^ ]*)[ ]* # type, whitespace
(\d*[,.]*\d*)[xX]*[ ]* # diameter, "x" separator, whitespace
(\d*[,.]*\d*)[xX]*[ ]* # thickness, "x" separator, whitespace
(\d*[,.]*\d*)[ ]* # hole, whitespace
(?:[(](\d*[,.]*\d*)[xX]* # start unretrievable group, start parenthesis, recess diameter, "x" separator
(\d*[,.]*\d*)[)])*[ ]* # recess thickness, end parenthesis, end unretrievable group, whitespace
([^ ]*)[ ]* # grit (matches anything but a whitespace), whitespace
([^ ]*)[ ]* # hardness (matches anything but a whitespace), whitespace
([^ ]*).* # bond (matches anything but a whitespace), and then matches and ignores everything else
$ # end of string
"""

class ProductionItem(OperationElement):
    TYPE = oks.PRODUCTION_ITEM
    HAS_CHILDREN = True
    CHILDREN_TYPE = (oks.RAW_MATERIAL,)
        
    def __init__(self, **kwargs):
        self.name = ""
        self.quantity = 1
        self.name_production = ""
        self.quantity_production = 1
        self.density = 2.0
        self.volume = 0.0
        self.rounding = 1.05
        self.proportion_sum = 0.0
        self.notes = ""
        
        self.row = ("name", "quantity", "name_production", 
                    "quantity_production","density", "volume", "rounding",
                    "proportion_sum", "notes")
        self._IO = 1
        self.formula = Formula(self)
        
        OperationElement.__init__(self, **kwargs)
        self.children["formula"] = self.formula
        
    def load_child(self, child):
        self.formula.insert(child, core.db.LOAD)
        
    def get_IO(self):
        return self._IO
          
    def set_IO(self, IO):
        self._IO = IO
        self.formula.update_IO()
        
    IO = property(get_IO, set_IO)
    
    def get_mass(self, rounding = True):
        mass = self.volume * self.density
        if rounding:
            mass = mass * self.rounding
        return mass
        
    def get_totalMass(self, rounding = True):
        return self.get_mass(rounding) * self.quantity_production
        
    def get_formula_masses(self):
        masses = []
        for (iter_, component) in self.formula:
            masses.append([component.name, 
                           component.proportion, 
                           component.quantity])
        return masses
        
    def make_output(self):
        item = Section("item", self.name_production)
       
        quantity = FloatData("quantity", "Quantidade", self.quantity_production,
                             strip_zeros=True)
        item.add_child(quantity)

        density = FloatData("density", "Densidade", self.density, "g/cm³")
        item.add_child(density)

        volume = FloatData("volume", "Volume", self.volume, "cm³")
        item.add_child(volume)

        mass = FloatData("mass", "Massa", self.get_mass(False), "g")
        item.add_child(mass)

        formula = TableSection("formula", "Fórmula",
                               (StringData("comp", "Componente"),
                                FloatData("prop", "Proporção"),
                                FloatData("mass", "Massa", unit="g")))
        item.add_child(formula)
        totalMass = 0.0
        for component in self.get_formula_masses():
            component, proportion, mass = component
            mass = mass * MASS_CONVERSION_UNIT
            totalMass += mass
            formula.add_row((component, proportion, mass))
            

        formula.add_child(FloatData("total", "Total", totalMass, "g"))
        formula.add_child(Info("infomass",
                               "Valor das massas com acréscimo de {0}%".format((self.rounding - 1) * 100)))
        
        finishing = Section("finishing", "Acabamento")
        item.add_child(finishing)

        finished_item = StringData("finished_item", "Item", self.name)
        finishing.add_child(finished_item)

        finished_quantity = FloatData("finished_quantity", "Quantidade", 
                                      self.quantity, strip_zeros=True)
        finishing.add_child(finished_quantity)

        notes = StringData("notes", "Observações", self.notes)
        item.add_child(notes)
                    
        return item
       
    @staticmethod
    def parse_description(description):
        parts = re.search(ITEM_PATTERN, description, re.VERBOSE)
        
        if not description:
            raise oks.DescriptionError("Não foi possível interpretar a "\
                                       "especificação")
        else:
            parts = parts.groups()
        
        description = {}
        try:
            description["type_"] = parts[0]
            description["diameter"] = parts[1]
            description["thickness"] = parts[2]
            description["hole"] = parts[3]
            description["recess_diameter"] = ""
            description["recess_thickness"] = ""
            if parts[4] and parts[5]:
                description["recess_diameter"] = parts[4]
                description["recess_thickness"] = parts[5]
            description["grit"] = parts[6]
            description["hardness"] = parts[7]
            description["bond"] = parts[8]
        except Exception, e:
            raise oks.DescriptionError("Não foi possível interpretar a "\
                                       "especificação")
        
        return description

    @staticmethod
    def get_specification(description):
        description = ProductionItem.parse_description(description)
        return "%s %s %s" % (description["grit"],
                             description["hardness"],
                             description["bond"])

    @staticmethod
    def get_measurements(description):
        description = ProductionItem.parse_description(description)
        if description["recess_diameter"] and description["recess_thickness"]:
            return "%s %sx%sx%s (%sx%s)" % (description["type_"],
                                            description["diameter"],
                                            description["thickness"],
                                            description["hole"],
                                            description["recess_diameter"],
                                            description["recess_thickness"])
        return "%s %sx%sx%s" % (description["type_"],
                                description["diameter"],
                                description["thickness"],
                                description["hole"])

    @staticmethod
    def get_description(measurements, specification):
        return measurements + " " + specification

    @staticmethod
    def calculate_volume(desc):
        desc = ProductionItem.parse_description(desc)
       
        if desc["type_"] not in ("RT", "UL"):
            raise oks.DescriptionError("Só é possível calcular automaticamente o "\
                                       "volume de itens RT e UL.")

        try:
            diameter = str_to_float(desc["diameter"])
            thickness = str_to_float(desc["thickness"])
            hole = str_to_float(desc["hole"])
            recess_diameter = 0.0
            recess_thickness = 0.0 
            if (desc["recess_diameter"] and 
                desc["recess_thickness"]):
                recess_diameter = str_to_float(
                    desc["recess_diameter"])
                recess_thickness = str_to_float(
                    desc["recess_thickness"])
        except ValueError:
            raise oks.DescriptionError("São necessários diâmetro, espessura, "\
                                       "furo e opcionalmente, rebaixo " \
                                       "completo.")

        # Make sure that we don't have a hole bigger than the item itself
        if hole >= diameter:
            raise oks.DescriptionError("O furo não pode ser maior que o "\
                                       "diâmetro.")
            
        # In case there is a recess...
        if recess_diameter != 0.0 and recess_thickness != 0.0:
            # Recess diameter and thickness shouldn't be bigger than their 
            # larger counterparts
            if (recess_diameter > diameter or 
                recess_thickness > thickness):
                raise oks.DescriptionError("O diâmetro ou a espessura do "\
                                           "rebaixo não podem ser maiores que "\
                                           "o diâmetro ou a espessura da peça.")


        volume = ((math.pi * ((diameter / 2) ** 2) * thickness) - 
                  (math.pi * ((hole / 2) ** 2) * thickness))
        recess_volume = 0.0
        if recess_diameter and recess_thickness:
            recess_volume = (math.pi * ((recess_diameter / 2) ** 2) * 
                             recess_thickness)
            recess_volume -= (math.pi * ((hole / 2) ** 2) * recess_thickness)
        # Converting to cubic centimeters
        return ((volume - recess_volume) / 1000) 
