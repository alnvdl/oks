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
        self.content = content
        self.font_name = font_name
        self.font_size = font_size
        self.wrap = wrap

        self.layout = None
        self.linesppage = 0
        self.lineheight = self.font_size / 2
        self.current_line = 0

        self.operation = gtk.PrintOperation()
        self.operation.set_unit(gtk.UNIT_MM)

        setup = gtk.PageSetup()
        setup.set_paper_size(gtk.PaperSize(gtk.PAPER_NAME_A4))
        self.operation.set_default_page_setup(setup)

        self.operation.connect("begin_print", self.begin_print)
        self.operation.connect("draw_page", self.draw_page)

    def run(self, action=gtk.PrintOperationAction.PRINT_DIALOG):
        return self.operation.run(action, self.parent)

    def begin_print(self, operation, context):
        self.header = cairo.ImageSurface.create_from_png("gui/header.png")
        self.header_scale = float(context.get_width()) / float(
            self.header.get_width()
        )
        header_offset = math.ceil(
            (self.header.get_height() * self.header_scale) / self.lineheight
        )
        self.content = "\n" * header_offset + self.content

        self.layout = context.create_pango_layout()
        font = pango.FontDescription(
            "%s %i" % (self.font_name, self.font_size)
        )
        self.layout.set_font_description(font)
        self.layout.set_text(self.content, -1)

        # Enable wrapping or dynamic resizing as needed.
        if self.wrap:
            self.layout.set_width(int(context.get_width() * pango.SCALE))
        else:
            ink, logical = self.layout.get_pixel_extents()
            if logical.width > context.get_width():
                self.font_size = (
                    self.font_size * context.get_width()
                ) / logical.width
                font = pango.FontDescription(
                    "%s %i" % (self.font_name, self.font_size)
                )
                self.layout.set_font_description(font)

        nlines = self.layout.get_line_count()
        self.linesppage = int(context.get_height() / self.lineheight)
        pages = int(math.ceil(nlines / float(self.linesppage)))
        operation.set_n_pages(pages)

    def draw_page(self, operation, context, page_number):
        cairo_context = context.get_cairo_context()

        # Draw the header.
        if page_number == 0:
            cairo_context.save()
            cairo_context.translate(0, 0)  # Top left
            cairo_context.scale(self.header_scale, self.header_scale)
            cairo_context.set_source_surface(self.header)
            cairo_context.paint()
            cairo_context.restore()

        # Draw the content.
        cairo_context.set_source_rgb(0, 0, 0)

        last_line = (page_number + 1) * self.linesppage
        # In case we are at the last page...
        if page_number == operation.get_property("n_pages") - 1:
            last_line = self.layout.get_line_count()

        cairo_context.move_to(0, 0)
        while self.current_line < last_line:
            line = self.layout.get_line(self.current_line)
            cairo_context.rel_move_to(0, self.lineheight)
            pango_cairo.show_layout_line(cairo_context, line)
            self.current_line += 1
