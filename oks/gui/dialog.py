#!/usr/bin/env python
#-*- coding:utf-8 -*-

from oks.gui.window import Window

class Dialog(Window):
    def __init__(self, builder, parent, dialog, focus_widget=None, *fields):
        Window.__init__(self, builder, dialog, *fields)
        self.parent = parent
        self.dialog = self.window
        self.dialog.set_transient_for(self.parent.window)
        
        # FIXME: pass services as a parameter, don't dig it
        self.services = None
        while self.services is None and self.parent is not None:
            self.services = self.parent.services

        if focus_widget is not None:
            self.focus_widget = self.get_widget(focus_widget)
        else:
            self.focus_widget = None
            
        self.window.connect("response", self.close)
        
    def add_button(self, buttonText, responseID):
        self.dialog.add_button(buttonText, responseID)
        
    def save_to_content(self, content):
        for widget, attribute in self.fields.items():
            if attribute:
                widget = getattr(self, widget)
                setattr(content, attribute, widget.get_value())
    
    def load_from_content(self, content):
        self.content = content
        if self.fields:
            for widget, attribute in self.fields.items():
                if attribute:
                    widget = getattr(self, widget)
                    value = getattr(content, attribute)
                    widget.set_value(value)
        
    def run(self):
        if self.focus_widget is not None:
            self.focus_widget.grab_focus()
        response = self.dialog.run()
        return response
        
    def close(self, *args):
        self.dialog.hide()
