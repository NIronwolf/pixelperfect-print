#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

gi.require_version("GimpUi", "3.0")
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
import sys

plug_in_proc = "plug-in-perfectfit-print"
plug_in_binary = "perfectfit-print"


def perfectfit_print_run(procedure, run_mode, image, drawables, config, data):
    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init(plug_in_binary)

        dialog = GimpUi.ProcedureDialog.new(procedure, config, "PerfectFit Print")

        # --- Main UI Construction ---
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dialog.get_content_area().add(main_vbox)

        # Keep the top settings grid as the user has configured it
        settings_grid = Gtk.Grid()
        settings_grid.set_column_spacing(12)
        settings_grid.set_row_spacing(6)
        settings_grid.set_border_width(6)
        main_vbox.pack_start(settings_grid, False, False, 0)

        # Width (as per user's code)
        label = Gtk.Label.new_with_mnemonic("_Width:")
        settings_grid.attach(label, 0, 0, 1, 1)
        w_width = GimpUi.prop_spin_button_new(config, "width", 0.05, 1.0, 2)
        label.set_mnemonic_widget(w_width)
        settings_grid.attach(w_width, 1, 0, 1, 1)

        # Height (as per user's code)
        label = Gtk.Label.new_with_mnemonic("_Height:")
        settings_grid.attach(label, 0, 1, 1, 1)
        w_height = GimpUi.prop_spin_button_new(config, "height", 0.05, 1.0, 2)
        label.set_mnemonic_widget(w_height)
        settings_grid.attach(w_height, 1, 1, 1, 1)

        # Unit (as per user's code)
        label = Gtk.Label.new_with_mnemonic("_Unit:")
        settings_grid.attach(label, 0, 2, 1, 1)
        w_unit = GimpUi.prop_unit_combo_box_new(config, "unit")
        label.set_mnemonic_widget(w_unit)
        settings_grid.attach(w_unit, 1, 2, 1, 1)

        # Middle preview and scrollbars
        preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preview_box.set_border_width(6)
        main_vbox.pack_start(preview_box, True, True, 0)

        # Y-Offset Scrollbar
        adj_y_offset = Gtk.Adjustment(
            value=config.get_property("y_offset"),
            lower=-0.5,
            upper=0.5,
            step_increment=0.001,
            page_increment=0.01,
        )
        w_y_offset = Gtk.Scrollbar(
            orientation=Gtk.Orientation.VERTICAL, adjustment=adj_y_offset
        )
        config.bind_property(
            "y_offset", adj_y_offset, "value", GObject.BindingFlags.DEFAULT
        )
        preview_box.pack_start(w_y_offset, False, False, 0)

        center_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        preview_box.pack_start(center_vbox, True, True, 0)

        # X-Offset Scrollbar
        adj_x_offset = Gtk.Adjustment(
            value=config.get_property("x_offset"),
            lower=-0.5,
            upper=0.5,
            step_increment=0.001,
            page_increment=0.01,
        )
        w_x_offset = Gtk.Scrollbar(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj_x_offset
        )
        config.bind_property(
            "x_offset", adj_x_offset, "value", GObject.BindingFlags.DEFAULT
        )
        center_vbox.pack_start(w_x_offset, False, False, 0)

        preview_area = Gtk.DrawingArea()
        preview_area.set_size_request(800, 800)
        preview_frame = Gtk.Frame()
        preview_frame.set_shadow_type(Gtk.ShadowType.IN)  # Add a 1px border
        preview_frame.add(preview_area)
        center_vbox.pack_start(preview_frame, True, True, 0)

        # Y-Scale Scrollbar
        adj_y_scale = Gtk.Adjustment(
            value=config.get_property("y_scale"),
            lower=100.0,
            upper=200.0,
            step_increment=0.5,
            page_increment=5.0,
        )
        w_y_scale = Gtk.Scrollbar(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj_y_scale
        )
        config.bind_property(
            "y_scale", adj_y_scale, "value", GObject.BindingFlags.DEFAULT
        )
        center_vbox.pack_start(w_y_scale, False, False, 0)

        # X-Scale Scrollbar
        adj_x_scale = Gtk.Adjustment(
            value=config.get_property("x_scale"),
            lower=100.0,
            upper=200.0,
            step_increment=0.5,
            page_increment=5.0,
        )
        w_x_scale = Gtk.Scrollbar(
            orientation=Gtk.Orientation.VERTICAL, adjustment=adj_x_scale
        )
        config.bind_property(
            "x_scale", adj_x_scale, "value", GObject.BindingFlags.DEFAULT
        )
        preview_box.pack_start(w_x_scale, False, False, 0)

        # Bottom info and lock
        bottom_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_hbox.set_border_width(6)
        main_vbox.pack_start(bottom_hbox, False, False, 0)

        info_label = Gtk.Label(label="DPI: ... Crop: ...")
        bottom_hbox.pack_start(info_label, True, True, 0)

        # Lock Checkbox
        w_lock_scale = Gtk.CheckButton.new_with_label("Lock")
        config.bind_property(
            "lock_scale", w_lock_scale, "active", GObject.BindingFlags.DEFAULT
        )
        bottom_hbox.pack_start(w_lock_scale, False, False, 0)

        # --- Draw Handler ---
        def draw_preview(widget, cr):
            # Get allocation
            alloc = widget.get_allocation()
            width = alloc.width
            height = alloc.height

            # Dark grey background
            cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.rectangle(0, 0, width, height)
            cr.fill()

            # Placeholder for crop rectangle (white)
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.set_line_width(1.0)

            # Example: draw a rectangle that is 80% of the size of the preview area
            rect_w = width * 0.8
            rect_h = height * 0.8
            rect_x = (width - rect_w) / 2
            rect_y = (height - rect_h) / 2
            cr.rectangle(rect_x, rect_y, rect_w, rect_h)
            cr.stroke()

            return False

        preview_area.connect("draw", draw_preview)

        # Show all widgets
        dialog.get_content_area().show_all()

        # --- Logic and Signals ---
        def update_calculations(*args):
            if image is None:
                info_label.set_text("No image open")
                return

            img_width_px = image.get_width()
            img_height_px = image.get_height()

            target_width = config.get_property("width")
            target_height = config.get_property("height")
            unit = config.get_property("unit")

            if target_width == 0 or target_height == 0:
                info_label.set_text("Width or Height cannot be zero.")
                return

            # Use Gimp.Unit.get_factor to get conversion to inches (the base unit)
            conversion_factor = Gimp.Unit.get_factor(unit)
            if conversion_factor == 0:
                info_label.set_text(
                    f"Cannot get conversion factor for '{Gimp.Unit.get_symbol(unit)}'."
                )
                return

            target_width_in = target_width * conversion_factor
            target_height_in = target_height * conversion_factor

            if target_width_in == 0 or target_height_in == 0:
                info_label.set_text("Dimension in inches is zero.")
                return

            dpi_x = img_width_px / target_width_in
            dpi_y = img_height_px / target_height_in

            info_label.set_text(f"X-DPI: {dpi_x:.0f}, Y-DPI: {dpi_y:.0f}")

            # Trigger a redraw of the preview area
            preview_area.queue_draw()

        # Connect signals
        for prop in [
            "width",
            "height",
            "unit",
            "x_offset",
            "y_offset",
            "x_scale",
            "y_scale",
        ]:
            config.connect(f"notify::{prop}", update_calculations)

        # Initial call
        update_calculations()

        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
        else:
            dialog.destroy()

    # Get properties after the dialog has run or from the passed-in config
    width = config.get_property("width")
    height = config.get_property("height")
    unit = config.get_property("unit")

    # For now, just print the values.
    print(
        f"Dialog values: Width: {width}, Height: {height}, Unit: {Gimp.Unit.get_symbol(unit)}"
    )
    print(f"Preparing to crop to {width}x{height}")

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


class PerfectFitPrint(Gimp.PlugIn):
    def do_set_i18n(self, name):
        return False

    def do_query_procedures(self):
        return [plug_in_proc]

    def do_create_procedure(self, name):
        procedure = None

        if name == plug_in_proc:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, perfectfit_print_run, None
            )
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE
                | Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Perfect_Fit Print...")
            procedure.set_attribution("Dustin Hollon", "Dustin Hollon", "2025")
            procedure.add_menu_path("<Image>/File")
            procedure.set_documentation(
                "Precisely size images for printing.",
                "A GIMP 3-compatible plugin to prepare images for print at exact width and height.",
                None,
            )

            procedure.add_double_argument(
                "width",
                "Width",
                "Target width for the print",
                0.0,
                200.0,
                10.0,
                GObject.ParamFlags.READWRITE,
            )
            procedure.add_double_argument(
                "height",
                "Height",
                "Target height for the print",
                0.0,
                200.0,
                8.0,
                GObject.ParamFlags.READWRITE,
            )

            procedure.add_unit_argument(
                "unit",
                "Unit",
                "Units for width and height",
                False,
                False,
                Gimp.Unit.inch(),
                GObject.ParamFlags.READWRITE,
            )

            procedure.add_double_argument(
                "x_offset",
                "X-Offset",
                "X-Offset",
                -0.5,
                0.5,
                0.0,
                GObject.ParamFlags.READWRITE,
            )
            procedure.add_double_argument(
                "y_offset",
                "Y-Offset",
                "Y-Offset",
                -0.5,
                0.5,
                0.0,
                GObject.ParamFlags.READWRITE,
            )
            procedure.add_double_argument(
                "x_scale",
                "X-Scale",
                "X-Scale",
                100.0,
                200.0,
                100.0,
                GObject.ParamFlags.READWRITE,
            )
            procedure.add_double_argument(
                "y_scale",
                "Y-Scale",
                "Y-Scale",
                100.0,
                200.0,
                100.0,
                GObject.ParamFlags.READWRITE,
            )
            procedure.add_boolean_argument(
                "lock_scale",
                "Lock Scale",
                "Lock X and Y scale",
                True,
                GObject.ParamFlags.READWRITE,
            )

        return procedure


Gimp.main(PerfectFitPrint.__gtype__, sys.argv)
