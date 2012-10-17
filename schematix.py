#!/usr/bin/env python
import wx
import schematix.component_selector

#Create an application and show the main window
app = wx.App()

frame = wx.Frame(None, size=(1024,768), title="Design Browser")
selector = schematix.component_selector.Selector(frame, -1)
frame.Show()
app.MainLoop()
