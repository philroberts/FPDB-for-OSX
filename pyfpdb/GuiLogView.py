#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
#In the "official" distribution you can find the license in agpl-3.0.txt.

import L10n
_ = L10n.get_translation()

import os
import Queue

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import os
import traceback
import logging
import Configuration
if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("logview")

MAX_LINES = 100000         # max lines to display in window
EST_CHARS_PER_LINE = 150   # used to guesstimate number of lines in log file
LOGFILES = [ [ _('Fpdb Errors'),        'fpdb-errors.txt',   False, 'log']  # label, filename, start value, path
           , [ _('Fpdb Log'),           'fpdb-log.txt',      True,  'log']
           , [ _('HUD Errors'),         'HUD-errors.txt',    False, 'log']
           , [ _('HUD Log'),            'HUD-log.txt',       False, 'log']
           , [ _('fpdb.exe log'),       'fpdb.exe.log',      False, 'pyfpdb']
           , [ _('HUD_main.exe Log'),   'HUD_main.exe.log ', False, 'pyfpdb']
           ]

class GuiLogView:

    def __init__(self, config, mainwin, closeq):
        self.config = config
        self.main_window = mainwin
        self.closeq = closeq

        self.logfile = os.path.join(self.config.dir_log, LOGFILES[1][1])
        self.dia = gtk.Dialog(title=_("Log Messages")
                             ,parent=None
                             ,flags=gtk.DIALOG_DESTROY_WITH_PARENT
                             ,buttons=(gtk.STOCK_CLOSE,gtk.RESPONSE_OK))
        self.dia.set_modal(False)

        self.vbox = self.dia.vbox
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
        self.listview.selection = self.listview.get_selection()
        self.listview.selection.connect('changed', self.row_selection_changed)
        self.clipboard = gtk.Clipboard(display=gtk.gdk.display_get_default(), selection="CLIPBOARD")
        self.selected_rows = None
        self.listview.selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.listview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)
        self.listcols = []

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.add(self.listview)
        self.vbox.pack_start(scrolledwindow, expand=True, fill=True, padding=0)

        hb1 = gtk.HBox(False, 0)
        grp = None
        for logf in LOGFILES:
            rb = gtk.RadioButton(group=grp, label=logf[0], use_underline=True)
            if grp is None: grp = rb
            rb.set_active(logf[2])
            rb.connect('clicked', self.__set_logfile, logf[0])
            hb1.pack_start(rb, False, False, 3)
            
        hb2 = gtk.HBox(False, 0)
        refreshbutton = gtk.Button(_("Refresh"))
        refreshbutton.connect("clicked", self.refresh, None)
        hb2.pack_start(refreshbutton, False, False, 3)
        refreshbutton.show()
        
        copybutton = gtk.Button(_("Copy to Clipboard"))
        copybutton.connect("clicked", self.copy_to_clipboard, None)
        hb2.pack_start(copybutton, False, False, 3)
        copybutton.show()
        
        self.vbox.pack_start(hb1, False, False, 0)
        self.vbox.pack_start(hb2, False, False, 0)
        
        self.listview.show()
        scrolledwindow.show()
        self.vbox.show()
        self.dia.set_focus(self.listview)

        col = self.addColumn(_("Date/Time"), 0)
        col = self.addColumn(_("Module"), 1)
        col = self.addColumn(_("Level"), 2)
        col = self.addColumn(_("Text"), 3)

        self.loadLog()
        self.vbox.show_all()
        self.dia.show()

        self.dia.connect('response', self.dialog_response_cb)

    def row_selection_changed(self, selection):
        model, self.selected_rows = selection.get_selected_rows()
    
    def copy_to_clipboard(self, widget, data):
        
        if not self.selected_rows:
            return
        text = ""
        for i in self.selected_rows:
            text = text + (self.liststore[i][0].ljust(23) + " " +
                    self.liststore[i][1].ljust(6) + " " +
                    self.liststore[i][2].ljust(7) + " " +
                    self.liststore[i][3]) + "\n"
        self.clipboard.set_text(text, len=-1)
            
    def __set_logfile(self, w, file):
        #print "w is", w, "file is", file, "active is", w.get_active()
        if w.get_active():
            for logf in LOGFILES:
                if logf[0] == file:
                    if logf[3] == 'pyfpdb':
                        self.logfile = os.path.join(self.config.pyfpdb_path, logf[1])
                    else:
                        self.logfile = os.path.join(self.config.dir_log, logf[1])                        
            self.refresh(w, file)  # params are not used

    def dialog_response_cb(self, dialog, response_id):
        # this is called whether close button is pressed or window is closed
        self.closeq.put(self.__class__)
        dialog.destroy()

    def get_dialog(self):
        return self.dia

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

    def loadLog(self):

        self.liststore.clear()
#        self.listcols = [] blanking listcols causes sortcols() to fail with index out of range

        # guesstimate number of lines in file
        if os.path.exists(self.logfile):
            stat_info = os.stat(self.logfile)
            lines = stat_info.st_size / EST_CHARS_PER_LINE
            #print "logview: size =", stat_info.st_size, "lines =", lines

            # set startline to line number to start display from
            startline = 0
            if lines > MAX_LINES:
                # only display from startline if log file is large
                startline = lines - MAX_LINES

            l = 0
            for line in open(self.logfile):
                # example line in logfile format:
                # 2009-12-02 15:23:21,716 - config       DEBUG    config logger initialised
                l = l + 1
                if l > startline:
                    # NOTE selecting a sort column and then switching to a log file
                    # with several thousand rows will send cpu 100% for a prolonged period.
                    # reason is that the append() method seems to sort every record as it goes, rather than
                    # pulling in the whole file and sorting at the end.
                    # one fix is to check if a column sort has been selected, reset to date/time asc
                    # append all the rows and then reselect the required sort order.
                    # Note: there is no easy method available to revert the list to an "unsorted" state.
                    # always defaulting to date/time asc doesn't work, because some rows do not have date/time info
                    # and would end up sorted out of context.
                    if len(line) > 49 and line[23:26] == ' - ' and line[34:39] == '     ':
                        iter = self.liststore.append( (line[0:23], line[26:32], line[39:46], line[48:].strip(), True) )
                    else:
                        iter = self.liststore.append( ('', '', '', line.strip(), True) )

    def sortCols(self, col, n):
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

    def refresh(self, widget, data):
        self.loadLog()



if __name__=="__main__":

    config = Configuration.Config()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title(_("Log Viewer"))
    win.set_border_width(1)
    win.set_default_size(600, 500)
    win.set_resizable(True)

    dia = gtk.Dialog(_("Log Viewer"),
                     win,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
    dia.set_default_size(500, 500)
    log = GuiLogView(config, win, dia.vbox)
    response = dia.run()
    if response == gtk.RESPONSE_ACCEPT:
        pass
    dia.destroy()




