#!/usr/bin/python2
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Carl Gherardi
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

import os
import sys
import traceback
import Queue

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("maintdbs")


import Exceptions
import Database


class GuiDatabase:

    COL_DBMS = 0
    COL_NAME = 1
    COL_DESC = 2
    COL_USER = 3
    COL_PASS = 4
    COL_HOST = 5
    COL_ICON = 6

    def __init__(self, config, mainwin, dia):
        self.config = config
        self.main_window = mainwin
        self.dia = dia

        try:
            #self.dia.set_modal(True)
            self.vbox = self.dia.vbox
            #gtk.Widget.set_size_request(self.vbox, 700, 400);

            # list of databases in self.config.supported_databases:
            self.liststore = gtk.ListStore(str, str, str, str
                                          ,str, str, str, str)  #object, gtk.gdk.Pixbuf)
            #                              dbms, name, comment, user, pass, ip, status(, icon?)
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
            self.listcols = []

            scrolledwindow = gtk.ScrolledWindow()
            scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scrolledwindow.add(self.listview)
            self.vbox.pack_start(scrolledwindow, expand=True, fill=True, padding=0)

            refreshbutton = gtk.Button("Refresh")
            refreshbutton.connect("clicked", self.refresh, None)
            self.vbox.pack_start(refreshbutton, False, False, 3)
            refreshbutton.show()

            col = self.addTextColumn("Type", 0, False)
            col = self.addTextColumn("Name", 1, False)
            col = self.addTextColumn("Description", 2, True)
            col = self.addTextColumn("Username", 3, True)
            col = self.addTextColumn("Password", 4, True)
            col = self.addTextColumn("Host", 5, True)
            col = self.addTextObjColumn("", 6)

            self.loadDbs()

            self.dia.connect('response', self.dialog_response_cb)
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print 'guidbmaint: '+ err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])

    def dialog_response_cb(self, dialog, response_id):
        # this is called whether close button is pressed or window is closed
        dialog.destroy()


    def get_dialog(self):
        return self.dia

    def addTextColumn(self, title, n, editable=False):
        col = gtk.TreeViewColumn(title)
        self.listview.append_column(col)

        cRender = gtk.CellRendererText()
        cRender.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        cRender.set_property('editable', editable)
        cRender.connect('edited', self.edited_cb, (self.liststore,n))

        col.pack_start(cRender, True)
        col.add_attribute(cRender, 'text', n)
        col.set_max_width(1000)
        col.set_spacing(0)  # no effect
        self.listcols.append(col)
        col.set_clickable(True)
        col.connect("clicked", self.sortCols, n)

        return(col)

    def edited_cb(self, cell, path, new_text, user_data):
        liststore, col = user_data
        valid = True
        name = self.liststore[path][self.COL_NAME]

        # Validate new value (only for dbms so far, but dbms now not updateable so no validation at all!)
        #if col == self.COL_DBMS:
        #    if new_text not in Configuration.DATABASE_TYPES:
        #        valid = False

        if valid:
            self.liststore[path][col] = new_text

            self.config.set_db_parameters( db_server = self.liststore[path][self.COL_DBMS]
                                         , db_name = name
                                         , db_ip = self.liststore[path][self.COL_HOST]
                                         , db_user = self.liststore[path][self.COL_USER]
                                         , db_pass = self.liststore[path][self.COL_PASS] )

        return

    def check_new_name(self, path, new_text):
        name_ok = True
        for i,db in enumerate(self.liststore):
            if i != path and new_text == db[self.COL_NAME]:
                name_ok = False
        #TODO: popup an error message telling user names must be unique
        return name_ok

    def addTextObjColumn(self, title, n):
        col = gtk.TreeViewColumn(title)
        self.listview.append_column(col)

        cRenderT = gtk.CellRendererText()
        cRenderT.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRenderT, False)
        col.add_attribute(cRenderT, 'text', n)

        cRenderP = gtk.CellRendererPixbuf()
        col.pack_start(cRenderP, False)
        col.add_attribute(cRenderP, 'stock-id', n+1)

        col.set_max_width(1000)
        col.set_spacing(0)  # no effect
        self.listcols.append(col)
        #col.set_clickable(True)
        #col.connect("clicked", self.sortCols, p)
        return(col)

    def loadDbs(self):

        self.liststore.clear()
        self.listcols = []
        self.dbs = []   # list of tuples:  (dbms, name, comment, user, passwd, host, status, icon)

        try:
            # want to fill: dbms, name, comment, user, passwd, host, status(, icon?)
            for name in self.config.supported_databases: #db_ip/db_user/db_pass/db_server
                dbms = self.config.supported_databases[name].db_server  # mysql/postgresql/sqlite
                dbms_num = self.config.get_backend(dbms)              #   2  /    3     /  4
                comment = ""
                if dbms == 'sqlite':
                    user = ""
                    passwd = ""
                else:
                    user = self.config.supported_databases[name].db_user
                    passwd = self.config.supported_databases[name].db_pass
                host = self.config.supported_databases[name].db_ip
                status = ""
                icon = None
                err_msg = ""
                
                db = Database.Database(self.config, sql = None, autoconnect = False)
                # try to connect to db, set status and err_msg if it fails
                try:
                    # is creating empty db for sqlite ... mod db.py further?
                    # add noDbTables flag to db.py?
                    db.connect(backend=dbms_num, host=host, database=name, user=user, password=passwd, create=False)
                    if db.connected:
                        status = 'ok'
                        icon = gtk.STOCK_APPLY
                        if db.wrongDbVersion:
                            status = 'old'
                            icon = gtk.STOCK_INFO
                except Exceptions.FpdbMySQLAccessDenied:
                    err_msg = "MySQL Server reports: Access denied. Are your permissions set correctly?"
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except Exceptions.FpdbMySQLNoDatabase:
                    err_msg = "MySQL client reports: 2002 or 2003 error. Unable to connect - " \
                              + "Please check that the MySQL service has been started"
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except Exceptions.FpdbPostgresqlAccessDenied:
                    err_msg = "Postgres Server reports: Access denied. Are your permissions set correctly?"
                    status = "failed"
                except Exceptions.FpdbPostgresqlNoDatabase:
                    err_msg = "Postgres client reports: Unable to connect - " \
                              + "Please check that the Postgres service has been started"
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except:
                    err = traceback.extract_tb(sys.exc_info()[2])[-1]
                    log.info( 'db connection to '+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: '
                              + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1]) )
                    status = "failed"
                    icon = gtk.STOCK_CANCEL

                b = gtk.Button(name)
                b.show()
                iter = self.liststore.append( (dbms, name, comment, user, passwd, host, status, icon) )

            self.listview.show()
            scrolledwindow.show()
            self.vbox.show()
            self.dia.set_focus(self.listview)

            self.vbox.show_all()
            self.dia.show()
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print 'loaddbs error: '+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: ' \
                      + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])

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

    def refresh(self, widget, data):
        self.loadDbs()



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




