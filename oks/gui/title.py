#!/usr/bin/env python
#-*- coding:utf-8 -*-

import gtk
import pango

class Title(gtk.EventBox):
    def __init__(self, parent_window, actions_label):
        gtk.EventBox.__init__(self)
        self.label = gtk.Label()
        self.button_actions = ButtonMenu(parent_window, actions_label)
        
        attributes = pango.AttrList()
        attributes.insert(pango.AttrWeight(700, 0, -1))
        attributes.insert(pango.AttrSize(16000, 0, -1))
        self.label.set_attributes(attributes)
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.label.set_alignment(0.0, 0.5)
        self.label.set_padding(2, 0)
        
        hbox = gtk.HBox()
        hbox.pack_start(self.label)
        hbox.pack_start(self.button_actions, False, False)
        self.add(hbox)
        
        self.connect("realize", self.on_realize)
        self.show_all()
        
    def on_realize(self, widget):
        style = self.get_style()
        self.modify_bg(gtk.STATE_NORMAL, style.bg[gtk.STATE_SELECTED])
        self.label.modify_fg(gtk.STATE_NORMAL, style.fg[gtk.STATE_SELECTED])
        self.button_actions.set_color(style.fg[gtk.STATE_SELECTED]) 
    
    def set_label(self, text):
        self.label.set_text(text)
    
    def enable_actions(self, flag):
        self.button_actions.set_sensitive(flag)
            
    def set_actions(self, *actions_list):
        self.button_actions.menu.set_actions(*actions_list)
        
    def clear(self):
        self.button_actions.menu.clear()
        
        
class ButtonMenu(gtk.ToggleButton):
    def __init__(self, parent_window, label, *actions_list):
        gtk.ToggleButton.__init__(self)
        self.set_relief(gtk.RELIEF_NONE)
        self.set_property("can_focus", False)
        
        self.parent_window = parent_window
        
        self.label = gtk.Label(label)
        self.label.set_use_underline(True)
        self.arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_NONE)
        
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_start(self.label)
        hbox.pack_start(self.arrow)
        self.add(hbox)

        self.menu = ActionsMenu()
        # Using set property, since PyGTK doesn't support the setter method
        # for this property yet.
        # self.menu.set_property("reserve-toggle-size", False)
        self.menu.set_actions(*actions_list)
        self.menu.connect("selection-done", self.on_selection_done)
        self.connect("button-press-event", self.on_button_press_event)
        self.connect("activate", self.on_button_press_event)

    def set_color(self, color):
        self.label.modify_fg(gtk.STATE_NORMAL, color)
        self.arrow.modify_fg(gtk.STATE_NORMAL, color)
                                                   
    def on_selection_done(self, widget):
        self.set_active(False)
        
    def on_button_press_event(self, widget, event=None):
        # Set the toggle button to active to emulate a toggle button
        self.show_all()
        if event is not None:
            self.set_active(True)
            self.menu.popup(None, None, self.get_menu_position, 
                            event.button, event.time)
        else:
            # FIXME: is is healthy to pass 0 for button and activate_time?
            self.menu.popup(None, None, self.get_menu_position, 0, 0) 
                                     
    def get_menu_position(self, menu):
        # Get the button position by translating it from the window position
        button_x, button_y = self.translate_coordinates(self.parent_window, 
                                                        0, 0)
        
        # Get the windows coordinates
        window_x, window_y = self.parent_window.window.get_origin()
        
        # Add the coordinates and the button height
        x = window_x + button_x
        y = window_y + button_y
    	y += self.allocation.height
    	
    	return (x, y, True)


class ActionsMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)
        
    def set_actions(self, *actions_list):
        self.clear()
        for (label, function) in actions_list:
            menuitem = gtk.MenuItem(label, True)
            menuitem.connect("activate", function)
            self.append(menuitem)
        self.show_all()
        
    def clear(self):
        for child in self.get_children():
            child.hide_all()
            self.remove(child)
            child.destroy()
            del child
