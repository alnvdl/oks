import datetime

from gi.repository import Gtk as gtk

import core.utils
from oks.gui.fields import Field


class DialogSelectDate(gtk.Dialog):
    def __init__(self, parent, blank_date_enabled):
        actions = [
            gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK,
            gtk.ResponseType.OK,
        ]
        if blank_date_enabled:
            actions.insert(0, gtk.RESPONSE_REJECT)
            actions.insert(0, "Nenhuma")

        gtk.Dialog.__init__(
            self,
            "Selecionar data",
            parent.window,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            tuple(actions),
        )
        content_area = self.get_content_area()
        self.calendar = gtk.Calendar()
        content_area.pack_start(self.calendar)
        self.calendar.show()

    def run(self, date=None):
        previous_date = date
        if date:
            # GTK counts months from 0 to 11
            self.calendar.select_month(date.month - 1, date.year)
            self.calendar.select_day(date.day)

        response = gtk.Dialog.run(self)
        if response == gtk.ResponseType.OK:
            year, month, day = self.calendar.get_date()
            return datetime.date(year, month + 1, day)
        elif response == gtk.RESPONSE_REJECT:
            return None
        return previous_date


class EntryDate(Field):
    def __init__(self, parent, attribute=None, blank_date_enabled=False):
        self.entry = gtk.Entry()
        self.widget = gtk.HBox(spacing=6)
        Field.__init__(self, self.widget, attribute)
        self.entry.set_editable(False)
        self.widget.pack_start(self.entry)
        self.blank_date_enabled = blank_date_enabled

        self.button = gtk.Button(label="Data...")
        self.button.connect("clicked", self.select_date_from_dialog, parent)
        self.widget.pack_start(self.button, False)

        self.date = datetime.date.today()
        self.widget.show_all()

    def select_date_from_dialog(self, button, parent):
        dialog = DialogSelectDate(parent, self.blank_date_enabled)
        date = dialog.run(self.date)
        dialog.destroy()
        self.set_value(date)

    def get_value(self):
        return self.date

    def set_value(self, value):
        self.date = value
        if value is not None:
            self.entry.set_text(core.utils.date_to_str(self.date))
        else:
            self.entry.set_text("")
        self.emit_new_value()
