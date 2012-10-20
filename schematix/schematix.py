#!/usr/bin/env python
import pickle
import copy

import wx
from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources

import component_selector
import parameter_dialog
import name_dialog
from instance import Instance
from wire import Wire

bend_component = {
    "name" : "bend",
    "inputs" : ["in1"], 
    "outputs" : ["out1"],
    "parameters" : {},
    "device_inputs" : {},
    "device_outputs" : {},
}

tee_component = {
    "name" : "tee",
    "inputs" : ["in1"], 
    "outputs" : ["out1", "out2"],
    "parameters" : {},
    "device_inputs" : {},
    "device_outputs" : {},
}

class BlockFrame(wx.Frame):

    """The main schematic window.

    This class is also responsible for drawing the schematic,
    capturing schematic events, and managing the document objects

    """

    def __init__(self, selector, *args, **kwargs):

        """Create the main Window, and all the associated widgets.

        Initialises to an empty document, and sets up event bindings for 
        widgets."""

        #draw windows
        wx.Frame.__init__(self, *args, **kwargs)

        #make canvas
        canvas = NavCanvas.NavCanvas(self, style=wx.SUNKEN_BORDER)
        self.canvas = canvas.Canvas

        #make menu
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, 
             lambda evt: self.on_open(),
             file_menu.Append(wx.ID_OPEN, "Open"),
        )
        self.Bind(wx.EVT_MENU, 
             lambda evt: self.on_save(),
             file_menu.Append(wx.ID_SAVE, "Save"),
        )
        self.Bind(wx.EVT_MENU, 
             lambda evt: self.on_save_as(),
             file_menu.Append(wx.ID_SAVEAS, "Save As"),
        )
        self.Bind(wx.EVT_MENU, 
             lambda evt: self.on_exit(),
             file_menu.Append(wx.ID_EXIT, "Exit"),
        )
        edit_menu = wx.Menu()

        self.undo = edit_menu.Append(wx.ID_UNDO, "Undo")
        self.redo = edit_menu.Append(wx.ID_REDO, "Redo")

        self.undo.Enable(False)
        self.redo.Enable(False)

        self.Bind(wx.EVT_MENU, lambda evt: self.on_undo(), self.undo)
        self.Bind(wx.EVT_MENU, lambda evt: self.on_redo(), self.redo)

        menubar.Append(file_menu, "File")
        menubar.Append(edit_menu, "Edit")
        self.SetMenuBar(menubar)

        #make component selector
        self.selector=selector

        #layout windows
        #splitter.SplitVertically(self.selector, canvas, 0)

        #bind events
        self.state = "idle"
        self.canvas.Bind(FloatCanvas.EVT_LEFT_UP, self.on_left_up)
        self.canvas.Bind(FloatCanvas.EVT_LEFT_DOWN, self.on_left_down)
        self.canvas.Bind(FloatCanvas.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.canvas.Bind(FloatCanvas.EVT_RIGHT_DOWN, self.on_right_down)
        self.canvas.Bind(FloatCanvas.EVT_MOTION, self.on_motion)

        #state that doesn't get saved
        self.undos = []
        self.redos = []

        #state that gets saved
        self.sn = 0
        self.netlist = {}
        self.port_positions = {}
        self.wires = []

    def open(self, filename):

        """Open a document"""

        self.filename = filename
        self.SetTitle("Schematix (%s)"%self.filename)
        open_file = open(filename, 'r')
        self.sn = pickle.load(open_file)
        self.netlist = pickle.load(open_file)
        self.port_positions = pickle.load(open_file)
        self.wires = pickle.load(open_file)
        self.draw()
        self.undo.Enable(False)
        self.redo.Enable(False)
        self.undos = []
        self.redos = []
        open_file.close()

    def on_open(self):

        """Open a document"""

        dlg = wx.FileDialog(self, "Open Schematic", style = wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename =  dlg.GetPath()
            self.filename = filename
            self.SetTitle("Schematix (%s)"%self.filename)
            open_file = open(filename, 'r')
            self.sn = pickle.load(open_file)
            self.netlist = pickle.load(open_file)
            self.port_positions = pickle.load(open_file)
            self.wires = pickle.load(open_file)
            self.draw()
            self.undo.Enable(False)
            self.redo.Enable(False)
            self.undos = []
            self.redos = []
            open_file.close()

    def on_save_as(self):

        """Save document with a new file name"""

        dlg = wx.FileDialog(self, "Save Schematic", style = wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.SetTitle("Schematix (%s)"%self.filename)
            save_file = open(self.filename, 'w')
            pickle.dump(self.sn, save_file)
            pickle.dump(self.netlist, save_file)
            pickle.dump(self.port_positions, save_file)
            pickle.dump(self.wires, save_file)
            save_file.close()

        self.selector.update()

    def on_save(self):

        """Save, prompt for new file name if not allready saved"""

        if not hasattr(self, "filename"):
            dlg = wx.FileDialog(self, "Save Schematic", style = wx.FD_SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                self.filename = dlg.GetPath()
                self.SetTitle("Schematix (%s)"%self.filename)

        if hasattr(self, "filename"):
            save_file = open(self.filename, 'w')
            pickle.dump(self.sn, save_file)
            pickle.dump(self.netlist, save_file)
            pickle.dump(self.port_positions, save_file)
            pickle.dump(self.wires, save_file)
            save_file.close()

        self.selector.update()


    def snapshot(self):

        """This gets called before anything significant changes.
        
        The state of the document is placed on a stack so that changes 
        can be undone"""

        stuff = self.sn, self.netlist, self.port_positions, self.wires
        stuff = copy.deepcopy(stuff)
        self.undos.append(stuff)
        self.undo.Enable(True)

    def on_undo(self):

        """Undo the last action
        
        Stores the last change on a stack so that the last change can be redone.
        Pops the previous state of the document before the last change from the
        undo stack."""

        if self.undos:
            stuff = (
                self.sn, 
                self.netlist, 
                self.port_positions, 
                self.wires
            )
            stuff = copy.deepcopy(stuff)
            self.redos.append(stuff)
            stuff = self.undos.pop()
            (
                    self.sn, 
                    self.netlist, 
                    self.port_positions, 
                    self.wires 
            ) = stuff
            self.draw()
            self.redo.Enable(True)
            if not self.undos: self.undo.Enable(False)

    def on_redo(self):

        """Redo the previously undone action
        
        Stores the current state on the undo stack so that the redone change 
        can be undone again. Pops the last undone change from the undo stack.
        """

        if self.redos:
            stuff = (
                self.sn, 
                self.netlist, 
                self.port_positions, 
                self.wires
            )
            stuff = copy.deepcopy(stuff)
            self.undos.append(stuff)
            stuff = self.redos.pop()
            self.sn, self.netlist, self.port_positions, self.wires = stuff
            self.draw()
            self.undo.Enable(True)
            if not self.redos: self.redo.Enable(False)

    def on_left_down(self, event):

        """Capture the mouse left down on an unoccupied schematic area.  If a
        wire is being drawn, a left click places a wire bend, and starts a new
        wire."""

        if self.state == "join_port":
            #end old wire
            self.snapshot()
            instance = str("inst_{0}".format(self.sn))
            self.sn+=1
            self.netlist[instance] = {
                    "component": bend_component, 
                    "parameters": {},
                    "position": snap(event.Coords), 
                    "name":instance,
                    "port_name":instance
            }
            self.wires.append((
                self.from_instance, 
                self.from_port, 
                instance, 
                "in1"
            ))
            self.draw()

            #start new wire
            self.from_instance = instance
            self.from_port = "out1"
            self.from_port_position = self.port_positions[instance]["out1"] 
            position = self.port_positions[instance]["out1"] 
            self.trace = self.canvas.AddLine(
                (position, position),
                LineStyle = "LongDash",
                LineColor = "grey",
                LineWidth = 1
            )

    def on_left_dclick(self, event):

        """Capture the mouse left down on an unoccupied schematic area.  This
        causes the selected component to be placed."""

        if self.state == "idle":
            component = self.selector.new_instance()
            if component is not None:
                self.snapshot()
                instance = str("inst_{0}".format(self.sn))
                self.sn+=1
                self.netlist[instance] = {
                        "component":component, 
                        "parameters": copy.deepcopy(component["parameters"]),
                        "position": snap(event.Coords), 
                        "name": instance
                }
                if component["name"] in ["input", "output"]:
                    number = 1
                    while "port_%s"%number in self.get_names():
                        number += 1
                    self.netlist[instance]["port_name"] = "port_%s"%number
                self.draw()

        elif self.state == "join_port":
            self.snapshot()
            instance = str("inst_{0}".format(self.sn))
            self.sn+=1
            self.netlist[instance] = {
                    "component": bend_component, 
                    "parameters": {},
                    "position": snap(event.Coords), 
                    "name":instance
            }
            self.wires.append((
                self.from_instance, 
                self.from_port, 
                instance, 
                "in1"
            ))
            self.draw()
            self.state = "idle"

    def on_right_down(self, event):

        """Capture the mouse right down on an unoccupied schematic area.
        Causes a schematic context menu to be displayed."""

        if self.state == "join_port":
            self.snapshot()
            instance = str("inst_{0}".format(self.sn))
            self.sn+=1
            self.netlist[instance] = {
                    "component": bend_component, 
                    "parameters": {},
                    "position": snap(event.Coords), 
                    "name":instance
            }
            self.wires.append((
                self.from_instance, 
                self.from_port, 
                instance, 
                "in1"
            ))
            self.draw()
            self.state = "idle"

    def on_left_up(self, event):

        """Capture the mouse left up on an unoccupied schematic area.
        
        If a block is currently being moved, a left up event causes the
        move operation to terminate."""

        if self.state == "move_block":
            self.block["position"] = snap(event.Coords)
            self.draw()
            self.state = "idle"

    def on_motion(self, event):

        """Capture the motion event 1in the schematic area.
        
        If a block move operation is in progress, the block is moved and 
        redrawn. If a wire is being drawn, this event causes a "trace"
        line to be drawn to show the eventual potision of the wire, but does
        not draw the wire yet. if additional performance is needed, it may be
        improved by showing the outline of moving block, but not actualy moving
        the block until a mouse left up event. The undo state is not captured
        for each movement of the block."""

        if self.state == "move_block":
            self.block["position"] = event.Coords
            self.block_trace.SetPoint(snap(event.Coords))
            self.canvas.Draw(True)
            #self.draw()
        elif self.state == "join_port":
            self.trace.SetPoints([self.from_port_position, snap(event.Coords)])
            self.canvas.Draw(True)

    def on_block_left_down(self, instance, size, style):

        """Capture the mouse left down event on a block.
        
        This causes a block move operation to commence, and the current drawing
        state is captured."""

        if self.state == "idle":
            self.state = "move_block"
            self.snapshot()
            self.block = instance
            if style in ["node", "port"]:
                self.block_trace = self.canvas.AddCircle(
                        instance["position"], 
                        10,
                        LineWidth = 1,
                        LineColor = "grey",
                )
            else:
                self.block_trace = self.canvas.AddRectangle(
                        instance["position"], 
                        size,
                        LineWidth = 1,
                        LineColor = "grey",
                )
            self.canvas.Draw()

    def on_block_right_down(self, instance):

        """Capture the mouse right down event on a block.
        
        This causes a  block related context menu to be displayed.
        * Edit parameters displays a parameter editing dialog to be displayed.
        * Delete causes the block to be deleted. """

        if self.state == "idle":
            menu = wx.Menu()
            if instance["component"]["name"] in ["input", "output"]:
                self.Bind(wx.EVT_MENU, 
                    lambda evt: self.edit_name(
                        instance
                    ),
                    menu.Append(-1, "Edit Name"),
                )
            elif instance["parameters"]:
                self.Bind(wx.EVT_MENU, 
                    lambda evt: self.edit_parameters(
                        instance["parameters"]
                    ),
                    menu.Append(-1, "Edit Parameters"),
                )
            self.Bind(wx.EVT_MENU, 
                lambda evt: self.delete_instance(instance),
                menu.Append(-1, "Delete"),
            )
            self.PopupMenu(menu)

    def on_out_port_left_down(self, instance_name, port_name):

        """Capture the mouse left down event on a block output port.

        This causes a wire drawing operation to commence."""

        if self.state == "idle":
            if (instance_name not in self.netlist or
                port_name not in self.netlist[instance_name]):
                self.from_instance = instance_name
                self.from_port = port_name
                self.from_port_position = self.port_positions[instance_name][port_name] 
                position = self.port_positions[instance_name][port_name] 
                self.trace = self.canvas.AddLine(
                    (position, position),
                    LineStyle = "LongDash",
                    LineColor = "grey",
                    LineWidth = 1
                )
                self.state = "join_port"

    def on_in_port_left_down(self, instance_name, port_name):

        """Capture the mouse left down event on a block input port.

        If a wire draw operation is in progress, this causes a wire to be
        drawn, and the wire drawing operation to terminate."""

        if self.state == "join_port":
            self.snapshot()
            self.wires.append((
                self.from_instance, 
                self.from_port, 
                instance_name, 
                port_name
            ))
            self.draw()
            self.state = "idle"

    def on_wire_right_down(self, wire):

        """Capture the mouse right down event on a wire.

        This causes a context menu relating to the wire to be displayed::
        * Delete - deletes the wire
        * Tee - breaks the wire and placed a Tee object at the mid point.
        * Bend - breaks the wire and places a Bend object at the mid point.
        """

        if self.state == "idle":
            menu = wx.Menu()
            self.Bind(wx.EVT_MENU, 
                lambda evt: self.disconnect(wire),
                menu.Append(-1, "Delete"),
            )
            self.Bind(wx.EVT_MENU, 
                lambda evt: self.tee(wire),
                menu.Append(-1, "Tee"),
            )
            self.Bind(wx.EVT_MENU, 
                lambda evt: self.bend(wire),
                menu.Append(-1, "Bend"),
            )
            self.PopupMenu(menu)

    def edit_parameters(self, parameters):

        """Launch a parameter editing dialog."""

        dlg = parameter_dialog.ParameterDlg(parameters, self)
        dlg.ShowModal()
        self.draw()

    def get_names(self):

        """Find all the port names in the design."""

        names = []
        for i in self.netlist.values():
            if "port_name" in i:
                names.append(i["port_name"])

        return names

    def edit_name(self, instance):

        """Launch name editing dialog."""

        names = self.get_names()
        dlg = name_dialog.NameDlg(instance, names, self)
        dlg.ShowModal()
        self.draw()

    def bend(self, wire):

        """Break wire and place a Bend object at the mid point."""

        self.snapshot()
        from_instance, from_port, to_instance, to_port = wire
        x1, y1 = self.port_positions[from_instance][from_port]
        x2, y2 = self.port_positions[to_instance][to_port]
        self.disconnect(wire)
        instance = str("inst_{0}".format(self.sn))
        self.sn+=1
        self.netlist[instance] = {
                "component": bend_component, 
                "parameters": {},
                "position": snap(((x1+x2)/2, (y1+y2)/2)), 
                "name":instance
        }
        self.wires.append((from_instance, from_port, instance, "in1"))
        self.wires.append((instance, "out1", to_instance, to_port))
        self.draw()

    def tee(self, wire):

        """Break wire and place a Tee object at the mid point."""

        self.snapshot()
        from_instance, from_port, to_instance, to_port = wire
        x1, y1 = self.port_positions[from_instance][from_port]
        x2, y2 = self.port_positions[to_instance][to_port]
        self.disconnect(wire)
        instance = str("inst_{0}".format(self.sn))
        self.sn+=1
        self.netlist[instance] = {
                "component": tee_component, 
                "parameters": {},
                "position": snap(((x1+x2)/2, (y1+y2)/2)), 
                "name": instance
        }
        self.wires.append((from_instance, from_port, instance, "in1"))
        self.wires.append((instance, "out1", to_instance, to_port))
        self.draw()

    def delete_instance(self, instance):

        """Delete a component instance, and all conected wires"""

        self.snapshot()
        self.netlist.pop(instance["name"])
        wires = [] 
        for wire in self.wires:
            if (wire[0] != instance["name"] and wire[2] != instance["name"]): 
                wires.append(wire)
        self.wires = wires
        self.draw()

    def disconnect(self, wire):

        """Delete a wire"""

        self.snapshot()
        wires = []
        for w in self.wires:
            if w != wire:
                wires.append(w)
        self.wires = wires
        self.draw()

    def tidy(self):

        while True:
            clean = True
            #delete orphaned tees and bends
            for instance in self.netlist.values():
                component_name = instance["component"]["name"]
                instance_name = instance["name"]
                if component_name in ["tee", "bend"]:
                    keep = False
                    for from_instance, from_port, to_instance, to_port in self.wires:
                        if instance_name in [from_instance, to_instance]:
                            keep = True
                    if not keep:
                        clean = False
                        self.netlist.pop(instance_name)

            if clean:
                break

    def draw(self):

        """Draw the document objects to the schematic editor"""

        self.tidy()
        self.canvas.ClearAll()
        for instance in self.netlist.values():
            Instance(self, instance)
        for wire in self.wires:
            Wire(self, wire)
        self.canvas.Draw(True)

def snap(coord):

    """For a coordinate, returns the nearest grid coordinate"""

    x, y = coord
    x = ((x+10)//20)*20
    y = ((y+10)//20)*20
    return x, y
