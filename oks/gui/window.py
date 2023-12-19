#!/usr/bin/env python
# -*- coding:utf-8 -*-

from gi.repository import Gtk as gtk

import core.db
import oks.gui.fields as Fields
import oks


class Window:
    def __init__(self, builder, window, *fields):
        self.builder = builder
        self.window = self.builder.get_object(window)
        self.window.connect("destroy", self.close)
        self.fields = {}
        for widget_name, attribute in fields:
            widget = self.get_widget(widget_name)
            if widget is None:
                raise oks.InvalidWidgetName(widget_name)
            fieldClass = getattr(Fields, "%sField" % widget.__class__.__name__)
            field = fieldClass(widget, attribute)
            self.register_field(widget_name, field)
        self.builder.connect_signals(self)
        self.editors = {}

    def set_title(self, title):
        self.window.set_title(title)

    def register_field(self, widget_name, field):
        setattr(self, widget_name, field)
        self.fields[widget_name] = field.attribute

    def get_widget(self, widget_name):
        return self.builder.get_object(widget_name)

    def load_widget(self, widget_name):
        return setattr(self, widget_name, self.builder.get_object(widget_name))

    def run(self):
        self.window.show_all()
        gtk.main()

    def close(self, *args):
        gtk.main_quit()

    def run_editor(self, editorClass, action, content, *args):
        # Make a complete copy of the content for editing if it has children,
        # so that the children containers don't get corrupted when the user
        # cancels a change
        if content.HAS_CHILDREN:
            content = content.copy(core.db.COMPLETE_COPY)

        if editorClass not in self.editors:
            editor = editorClass(self.builder, self)
            self.editors[editorClass] = editor
        editor = self.editors[editorClass]
        editor.load_from_content(content)
        response = editor.run()
        while response == gtk.ResponseType.OK:
            try:
                editor.save_to_content(content)
                action(content, *args)
                response = gtk.ResponseType.NONE  # end the loop
            except oks.OksException as exception:
                self.show_message(exception.text, exception.secondaryText)
                response = editor.run()
        if response == gtk.ResponseType.NONE:
            # if the loop was ended succesfully
            response = gtk.ResponseType.OK
        return response

    def show_message(
        self,
        text,
        secondaryText,
        messageType=gtk.MessageType.ERROR,
        buttons=gtk.ButtonsType.OK,
    ):
        dialogMessage = gtk.MessageDialog(
            self.window, 0, messageType, buttons, text
        )
        dialogMessage.format_secondary_text(secondaryText)
        response = dialogMessage.run()
        dialogMessage.hide()
        dialogMessage.destroy()
        return response

    def set_size(self, width=-1, height=-1):
        self.window.set_size_request(width, height)
