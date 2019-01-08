#!/usr/bin/env python
#-*- coding:utf-8 -*-

from core.db.models.internal import FilteredInternalModel
from oks.elements.operation.pitem import ProductionItem
from oks.elements.operation.pitem.rawmaterial import RawMaterial
from oks.gui.dialog import Dialog
from oks.gui.columns import *
from oks.gui.title import ButtonMenu
import oks

class DialogProductionItem(Dialog):    
    def __init__(self, builder, parent):
        Dialog.__init__(self,
                        builder,
                        parent, 
                        "dialog_pitem", 
                        "entry_pitem_name",
                        ("entry_pitem_name", "name"),
                        ("spinbutton_pitem_quantity", "quantity"),
                        ("entry_pitem_name_production", 
                         "name_production"),
                        ("spinbutton_pitem_quantity_production", 
                         "quantity_production"),
                        ("spinbutton_pitem_volume", "volume"),
                        ("spinbutton_pitem_density", "density"),
                        ("entry_pitem_notes", "notes"),)
       
        # Actions menu for the production item description
        actions = (("Calcular volume",
                    self.on_button_pitem_calc_volume_clicked),
                   ("Ajustar medidas",
                    self.on_action_guess_measurements),
                   ("Deduzir fórmula",
                    self.on_action_guess_formula))

        actions_button = ButtonMenu(self.dialog, "Ações", *actions)
        self.get_widget("hbox_pitem_actions").pack_start(actions_button)
        actions_button.show_all()

        # Setting the item completion
        completion = self.services["completion"]
        self.entry_pitem_name.set_completion(
            completion("inventory:production_item"))

        # Setting the formula widget...
        self.load_widget("treeview_pitem_components")
        self.get_selected_component = lambda *args: self.treeview_pitem_components.get_selection().get_selected()[1]
        
        columns = [
        TextColumn("Componente", 0),
        FloatColumn("Proporção", 1),
        ]
        for column in columns:
            self.treeview_pitem_components.append_column(column)        

        self.load_widget("entry_pitem_component")
        self.load_widget("spinbutton_pitem_proportion")
        self.entry_pitem_component.set_completion(
            completion("inventory:raw_material"))
        # FIXME
        # For some reason, GtkBuilder doesn't set just this spinbutton. So we
        # set it manually
        self.spinbutton_pitem_proportion.set_value(50.0)

        # Components callbacks
        self.get_widget("entry_pitem_component").connect("activate",
        self.on_entry_pitem_component_activate)
        self.get_widget("spinbutton_pitem_proportion").connect("activate",
        self.on_button_pitem_add_component_clicked)
        self.get_widget("button_pitem_add_component").connect("clicked",
        self.on_button_pitem_add_component_clicked)
        self.get_widget("button_pitem_remove_component").connect("clicked",
        self.on_button_pitem_remove_component_clicked)  
                
    def load_from_content(self, content):
        self.formula = FilteredInternalModel(content.formula, 
                                             ("name", str), 
                                             ("proportion", float))
        self.treeview_pitem_components.set_model(self.formula.filteredModel)
            
        # Loading the content...
        Dialog.load_from_content(self, content)

    def save_to_content(self, content):
        Dialog.save_to_content(self, content)
        content.formula.update_components()

    def on_button_pitem_add_component_clicked(self, widget):
        component = self.entry_pitem_component.get_text()
        self.spinbutton_pitem_proportion.update()
        proportion = self.spinbutton_pitem_proportion.get_value()
        
        rawMaterial = RawMaterial(name = component, proportion = proportion)
                
        self.formula.insert(rawMaterial)
        
        self.entry_pitem_component.set_text("")
        self.spinbutton_pitem_proportion.set_value(50.0)
        
        self.entry_pitem_component.grab_focus()
        
    def on_button_pitem_remove_component_clicked(self, widget):
        rowIter = self.get_selected_component()
        self.formula.delete(rowIter)

    def on_entry_pitem_component_activate(self, widget):
        self.spinbutton_pitem_proportion.grab_focus()

    def on_button_pitem_calc_volume_clicked(self, button):
        try:
            value = ProductionItem.calculate_volume(self.entry_pitem_name_production.get_value())
        except oks.DescriptionError, e:
            self.show_message("Erro ao calcular o volume", e.secondaryText)
        else:
            self.spinbutton_pitem_volume.set_value(value)
        
    def on_action_guess_formula(self, action):
        description = self.entry_pitem_name_production.get_value()
        guess_formula = self.services["guess_formula"]
        density, formula = guess_formula(description, self.content.row_id)
        if not formula:
            self.show_message("Fórmula não encontrada", 
                              "Não foi encontrada fórmula para a "\
                              "especificação %s." %
                              ProductionItem.get_specification(description))
        else:
            self.spinbutton_pitem_density.set_value(density)
            self.formula.clear()
            for name, proportion in formula:
                raw_material = RawMaterial(name = name, proportion = proportion)
                self.formula.insert(raw_material)

    def on_action_guess_measurements(self, action):
        description = self.entry_pitem_name.get_value()
        guess_measurements = self.services["guess_measurements"]
        measurements = guess_measurements(description, self.content.row_id)
        if not measurements:
            self.show_message("Medidas não encontradas", 
                              "Não foram encontradas as medidas de produção "\
                              "para o item %s." % description)
        else:
            specification = ProductionItem.get_specification(description)
            description = ProductionItem.get_description(measurements, 
                                                         specification)
            self.entry_pitem_name_production.set_value(description)
