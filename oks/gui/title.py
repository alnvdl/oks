from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import Pango as pango


class Title(gtk.EventBox):
    def __init__(self, parent_window, actions_label):
        gtk.EventBox.__init__(self)
        self.label = gtk.Label()
        self.button_actions = ButtonMenu(parent_window, actions_label)

        self.label.set_name("label-element-name")
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.label.set_alignment(0.0, 0.5)
        self.label.set_padding(2, 0)

        hbox = gtk.HBox()
        hbox.set_name("hbox")
        hbox.pack_start(self.label)
        hbox.pack_start(self.button_actions, False, False)
        self.add(hbox)

        self.enable_actions(False)
        self.show_all()

    def set_label(self, text):
        if text == "":
            self.label.hide()
        self.label.show()
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
        self.arrow = gtk.Arrow(gtk.ArrowType.DOWN, gtk.ShadowType.NONE)

        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_start(self.label, True, True, 0)
        hbox.pack_start(self.arrow, True, True, 0)
        self.add(hbox)

        self.menu = ActionsMenu()
        # Using set property, since PyGTK doesn't support the setter method
        # for this property yet.
        # self.menu.set_property("reserve-toggle-size", False)
        self.menu.set_actions(*actions_list)
        self.menu.connect("selection-done", self.on_selection_done)
        self.connect("button-press-event", self.on_button_press_event)
        self.connect("activate", self.on_button_press_event)

    def on_selection_done(self, widget):
        self.set_active(False)

    def on_button_press_event(self, widget, event=None):
        # Set the toggle button to active to emulate a toggle button
        self.show_all()
        if event is not None:
            self.set_active(True)
            self.menu.popup_at_widget(
                self, gdk.GRAVITY_SOUTH_WEST, gdk.GRAVITY_NORTH_WEST, event
            )


class ActionsMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)

    def set_actions(self, *actions_list):
        self.clear()
        for label, function in actions_list:
            menuitem = gtk.MenuItem(label, True)
            menuitem.set_use_underline(True)
            menuitem.connect("activate", function)
            self.append(menuitem)
        self.show_all()

    def clear(self):
        for child in self.get_children():
            child.hide_all()
            self.remove(child)
            child.destroy()
            del child
