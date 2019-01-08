#!/usr/bin/env python
#-*- coding:utf-8 -*-

import gtk
from oks.gui.dialog import Dialog
        
class DialogSelectOperationType(Dialog):
    def __init__(self, builder, parent):
        Dialog.__init__(self,
                        builder,
                        parent,
                        "dialog_operation_type")

        self.load_widget("radiobuttonOut")
        self.radiobuttonOut.connect("activate", self.response)
        self.radiobuttonOut.connect("button-press-event", self.negative_response)
        
        self.load_widget("radiobuttonIn")
        self.radiobuttonIn.connect("activate", self.response)
        self.radiobuttonIn.connect("button-press-event", self.negative_response)
                
        self.load_widget("radiobuttonProduction")
        self.radiobuttonProduction.connect("activate", self.response)
        self.radiobuttonProduction.connect("button-press-event", self.negative_response)
        
        self.load_widget("radiobuttonExchange")
        self.radiobuttonExchange.connect("activate", self.response)
        self.radiobuttonExchange.connect("button-press-event", self.negative_response)
        
        self.negative = False
        
    def run(self, date = None):
        response = self.dialog.run()
        operationType = 0
        if response == gtk.RESPONSE_OK:
            if self.radiobuttonOut.get_active():
                operationType = 0
            if self.radiobuttonIn.get_active():
                operationType = 1
            if self.radiobuttonProduction.get_active():
                operationType = 2
            if self.radiobuttonExchange.get_active():
                operationType = 3
        return (response, operationType, self.negative)
        
    def response(self, widget):
        self.dialog.response(gtk.RESPONSE_OK)
        
    def negative_response(self, widget, event):
        if event.type == gtk.gdk._3BUTTON_PRESS:
            self.negative = True
            self.dialog.response(gtk.RESPONSE_OK)
