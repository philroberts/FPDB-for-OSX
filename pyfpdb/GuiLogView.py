#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2008 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.


import xml.dom.minidom
from xml.dom.minidom import Node

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import Configuration

log = Configuration.get_logger("logging.conf", "logview")

class GuiLogView:

    def __init__(self, config, mainwin, vbox):
        self.config = config
        self.main_window = mainwin
        self.vbox = vbox
        gtk.Widget.set_size_request(self.vbox, 700, 400);

        self.liststore = gtk.ListStore(str, str, str, str)  # date, module, level, text
        self.listview = gtk.TreeView(model=self.liststore)
        self.listview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(scrolledwindow, expand=True, fill=True, padding=0)
        scrolledwindow.add(self.listview)

        self.listview.show()
        scrolledwindow.show()
        self.vbox.show()

        self.loadLog()
        self.vbox.show_all()

    def loadLog(self):

        #self.configStore = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING)
        #self.configView = gtk.TreeView(self.configStore)
        #self.configView.set_enable_tree_lines(True)
        self.liststore.clear()

        col = gtk.TreeViewColumn("Date/Time")
        self.listview.append_column(col)
        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', 0)
        col.set_max_width(1000)

        col = gtk.TreeViewColumn("Module")
        self.listview.append_column(col)
        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', 1)
        col.set_max_width(1000)

        col = gtk.TreeViewColumn("Level")
        self.listview.append_column(col)
        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', 2)
        col.set_max_width(1000)

        col = gtk.TreeViewColumn("Text")
        self.listview.append_column(col)
        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', 3)
        col.set_max_width(1000)

        l = 0
        for line in open('logging.out', 'r'):
            #self.addLogText(line)
            iter = self.liststore.append([line.strip(), "", "", ""])
            l = l + 1
            if l >= 100:
                break



if __name__=="__main__":

    config = Configuration.Config()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title("Test Log Viewer")
    win.set_border_width(1)
    win.set_default_size(600, 500)
    win.set_resizable(True)

    dia = gtk.Dialog("Log Viewer",
                     win,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
    dia.set_default_size(500, 500)
    log = GuiLogView(config, win, dia.vbox)
    response = dia.run()
    if response == gtk.RESPONSE_ACCEPT:
        pass
    dia.destroy()




