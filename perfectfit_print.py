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

        # Manually create the UI
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.set_border_width(6)
        dialog.get_content_area().add(grid)

        # Width
        label = Gtk.Label.new_with_mnemonic("_Width:")
        grid.attach(label, 0, 0, 1, 1)
        widget = GimpUi.prop_spin_button_new(config, "width", 0.05, 1.0, 2)
        label.set_mnemonic_widget(widget)
        grid.attach(widget, 1, 0, 1, 1)

        # Height
        label = Gtk.Label.new_with_mnemonic("_Height:")
        grid.attach(label, 0, 1, 1, 1)
        widget = GimpUi.prop_spin_button_new(config, "height", 0.05, 1.0, 2)
        label.set_mnemonic_widget(widget)
        grid.attach(widget, 1, 1, 1, 1)

        # Unit
        label = Gtk.Label.new_with_mnemonic("_Unit:")
        grid.attach(label, 0, 2, 1, 1)
        widget = GimpUi.prop_unit_combo_box_new(config, "unit")
        label.set_mnemonic_widget(widget)
        grid.attach(widget, 1, 2, 1, 1)

        grid.show_all()

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

        return procedure


Gimp.main(PerfectFitPrint.__gtype__, sys.argv)
