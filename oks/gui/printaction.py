from gi.repository import Gtk as gtk
from gi.repository import Pango as pango
from gi.repository import PangoCairo as pango_cairo
import math
import cairo


class PrintAction:
    def __init__(
        self,
        parent,
        content="",
        font_name="monospace",
        font_size=10,
        wrap=False,
    ):
        self.parent = parent
        self.content = "\n" * 11 + content  # Dirty offset for the logo
        self.layout = None
        self.font_name = font_name
        self.font_size = font_size
        self.wrap = wrap
        self._linesppage = 0
        self._current_line = 0

        self.operation = gtk.PrintOperation()
        self.operation.set_unit(gtk.UNIT_MM)

        # Setting paper size as A4
        paper_size = gtk.PaperSize(gtk.PAPER_NAME_A4)
        setup = gtk.PageSetup()
        setup.set_paper_size(paper_size)
        self.operation.set_default_page_setup(setup)

        self.operation.connect("begin_print", self.begin_print)
        self.operation.connect("draw_page", self.draw_page)

    def run(self, action=gtk.PrintOperationAction.PRINT_DIALOG):
        return self.operation.run(action, self.parent)

    def begin_print(self, operation, context):
        # Try setting the default parameters...
        self.layout = context.create_pango_layout()
        font = pango.FontDescription(
            "%s %i" % (self.font_name, self.font_size)
        )
        self.layout.set_font_description(font)
        self.layout.set_text(self.content, -1)

        # And then enable wrap or dynamic resizing if needed...
        if self.wrap:
            self.layout.set_width(int(context.get_width() * pango.SCALE))
        else:
            ink, logical = self.layout.get_pixel_extents()
            ax, ay, width, by = (
                logical.x,
                logical.y,
                logical.width,
                logical.height,
            )
            if width > context.get_width():
                self.font_size = (self.font_size * context.get_width()) / width
                font = pango.FontDescription(
                    "%s %i" % (self.font_name, self.font_size)
                )
                self.layout.set_font_description(font)

        nlines = self.layout.get_line_count()
        self._linesppage = int(context.get_height() / (self.font_size / 2))
        pages = int(math.ceil(nlines / float(self._linesppage)))
        operation.set_n_pages(pages)

    def draw_page(self, operation, context, page_number):
        cairo_context = context.get_cairo_context()

        # Draw the logo
        if page_number == 0:
            surface = cairo.ImageSurface.create_from_png("gui/header.png")
            scale = float(context.get_width()) / float(surface.get_width())
            cairo_context.save()
            cairo_context.translate(0, 0)  # Top left
            cairo_context.scale(scale, scale)
            cairo_context.set_source_surface(surface)
            cairo_context.paint()
            cairo_context.restore()

        # Draw the content
        cairo_context.set_source_rgb(0, 0, 0)

        last_line = (page_number + 1) * self._linesppage
        # In case we are at the last page...
        if page_number == operation.get_property("n_pages") - 1:
            last_line = self.layout.get_line_count()

        cairo_context.move_to(0, 0)
        while self._current_line < last_line:
            line = self.layout.get_line(self._current_line)
            cairo_context.rel_move_to(0, self.font_size / 2)
            pango_cairo.show_layout_line(cairo_context, line)
            self._current_line += 1
