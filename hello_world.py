#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
import sys

plug_in_proc   = "plug-in-zemarmot-py3-demo-hello-world"
plug_in_binary = "py3-hello-world"

def hello_world_run(procedure, run_mode, image, drawables, config, data):
  if len(drawables) > 1:
    return procedure.new_return_values (Gimp.PDBStatusType.CALLING_ERROR,
                                        GLib.Error(f"Procedure '{plug_in_proc}' works with zero or one layer."))
  elif len(drawables) == 1:
    if not isinstance(drawables[0], Gimp.Layer):
      return procedure.new_return_values (Gimp.PDBStatusType.CALLING_ERROR,
                                          GLib.Error(f"Procedure '{plug_in_proc}' works with layers only."))

    parent   = drawables[0].get_parent ()
    position = image.get_item_position (drawables[0])

  if run_mode == Gimp.RunMode.INTERACTIVE:
    GimpUi.init(plug_in_binary)

    dialog = GimpUi.ProcedureDialog.new(procedure, config, "Hello World")
    box = dialog.fill_box("size-box", ["font-size", "font-unit"])
    box.set_orientation (Gtk.Orientation.HORIZONTAL)
    dialog.fill_frame("size-frame", "compute-size", True, "size-box")
    dialog.fill(["text", "font", "size-frame"])
    if not dialog.run():
      dialog.destroy()
      return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
    else:
      dialog.destroy()

  text         = config.get_property('text')
  font         = config.get_property('font')
  compute_size = config.get_property('compute-size')
  size         = config.get_property('font-size')
  unit         = config.get_property('font-unit')

  image.undo_group_start()
  text_layer = Gimp.TextLayer.new (image, text, font, size, unit)
  image.insert_layer (text_layer, parent, position)
  if compute_size:
    image_width = image.get_width()
    layer_width = text_layer.get_width()

    size = size * (image_width - 1) / layer_width
    text_layer.set_font_size(size, Gimp.Unit.pixel())

    while size > 1:
      layer_width = text_layer.get_width()

      if layer_width < image_width:
        break

      size -= 1
      text_layer.set_font_size(size, Gimp.Unit.pixel())

  image.undo_group_end()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

class HelloWorld (Gimp.PlugIn):
  def do_query_procedures(self):
    return [ plug_in_proc ]

  def do_create_procedure(self, name):
    procedure = None

    if name == plug_in_proc:
      procedure = Gimp.ImageProcedure.new(self, name,
                                          Gimp.PDBProcType.PLUGIN,
                                          hello_world_run, None)
      procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE |
                                      Gimp.ProcedureSensitivityMask.NO_DRAWABLES)
      procedure.set_menu_label("_Python 3 Hello World")
      procedure.set_attribution("Jehan", "Jehan, ZeMarmot project", "2025")
      procedure.add_menu_path ("<Image>/Hell_o Worlds")
      procedure.set_documentation ("Official Hello World Tutorial in Python 3",
                                   "Some longer text to explain about this procedure. " + \
                                   "This is mostly for other developers calling this procedure.",
                                   None)

      procedure.add_string_argument  ("text", "Text", None, "Hello World!",
                                      GObject.ParamFlags.READWRITE)
      procedure.add_font_argument    ("font", "Font", None, False, None, True,
                                      GObject.ParamFlags.READWRITE)
      procedure.add_boolean_argument ("compute-size", "Compute Ideal Size",
                                      "This option will compute a font size " + \
                                      "so that the text optimally fills the whole canvas",
                                      False, GObject.ParamFlags.READWRITE)
      procedure.add_int_argument     ("font-size", "Font Size", None,
                                      1, 1000, 20, GObject.ParamFlags.READWRITE)
      procedure.add_unit_argument    ("font-unit", "Font Unit", None,
                                      True, False, Gimp.Unit.pixel(),
                                      GObject.ParamFlags.READWRITE)

    return procedure

Gimp.main(HelloWorld.__gtype__, sys.argv)
