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


import mmap

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import Configuration

log = Configuration.get_logger("logging.conf", "logview")

MAX_LINES = 100000

class GuiLogView:

    def __init__(self, config, mainwin, vbox):
        self.config = config
        self.main_window = mainwin
        self.vbox = vbox
        gtk.Widget.set_size_request(self.vbox, 700, 400);

        self.liststore = gtk.ListStore(str, str, str, str, gobject.TYPE_BOOLEAN)  # date, module, level, text

        # this is how to add a filter:
        #
        # # Creation of the filter, from the model
        # filter = self.liststore.filter_new()
        # filter.set_visible_column(1)
        #
        # # The TreeView gets the filter as model
        # self.listview = gtk.TreeView(filter)

        self.listview = gtk.TreeView(model=self.liststore)
        self.listview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)

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
        self.listcols = []

        col = self.addColumn("Date/Time", 0)

        col = self.addColumn("Module", 1)
        col = self.addColumn("Level", 2)
        col = self.addColumn("Text", 3)

        # count number of lines in file
        f = open('logging.out', "r+")
        buf = mmap.mmap(f.fileno(), 0)
        readline = buf.readline
        lines = 0
        while readline():
            lines += 1
        f.close()

        startline = 0
        if lines > MAX_LINES:
            # only display from startline if log file is large
            startline = lines - MAX_LINES

        f = open('logging.out', "r+")
        buf = mmap.mmap(f.fileno(), 0)
        readline = buf.readline
        l = 0
        line = readline()
        while line:
            # eg line:
            # 2009-12-02 15:23:21,716 - config       DEBUG    config logger initialised
            l = l + 1
            if l > startline and len(line) > 49:
                iter = self.liststore.append( (line[0:23], line[26:32], line[39:46], line[48:].strip(), True) )
            line = readline()
        f.close()

    def addColumn(self, title, n):
        col = gtk.TreeViewColumn(title)
        self.listview.append_column(col)
        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', n)
        col.set_max_width(1000)
        col.set_spacing(0)  # no effect
        self.listcols.append(col)
        col.set_clickable(True)
        col.connect("clicked", self.sortCols, n)
        return(col)

    def sortCols(self, col, n):
        try:
            if not col.get_sort_indicator() or col.get_sort_order() == gtk.SORT_ASCENDING:
                col.set_sort_order(gtk.SORT_DESCENDING)
            else:
                col.set_sort_order(gtk.SORT_ASCENDING)
            self.liststore.set_sort_column_id(n, col.get_sort_order())
            #self.liststore.set_sort_func(n, self.sortnums, (n,grid))
            for i in xrange(len(self.listcols)):
                self.listcols[i].set_sort_indicator(False)
            self.listcols[n].set_sort_indicator(True)
            # use this   listcols[col].set_sort_indicator(True)
            # to turn indicator off for other cols
        except:
            err = traceback.extract_tb(sys.exc_info()[2])
            print "***sortCols error: " + str(sys.exc_info()[1])
            print "\n".join( [e[0]+':'+str(e[1])+" "+e[2] for e in err] )



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




