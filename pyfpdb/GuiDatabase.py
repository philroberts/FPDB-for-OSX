#!/usr/bin/python
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
import SQL

import gettext
trans = gettext.translation("fpdb", localedir="locale", languages=["de_DE"])
trans.install()

class GuiDatabase:

    # columns in liststore:
    MODEL_DBMS = 0
    MODEL_NAME = 1
    MODEL_DESC = 2
    MODEL_USER = 3
    MODEL_PASS = 4
    MODEL_HOST = 5
    MODEL_DFLT = 6
    MODEL_DFLTIC = 7
    MODEL_STATUS = 8
    MODEL_STATIC = 9

    # columns in listview:
    COL_DBMS = 0
    COL_NAME = 1
    COL_DESC = 2
    COL_USER = 3
    COL_PASS = 4
    COL_HOST = 5
    COL_DFLT = 6
    COL_ICON = 7

    def __init__(self, config, mainwin, dia):
        self.config = config
        self.main_window = mainwin
        self.dia = dia

        try:
            #self.dia.set_modal(True)
            self.vbox = self.dia.vbox
            #gtk.Widget.set_size_request(self.vbox, 700, 400);

            # list of databases in self.config.supported_databases:
            self.liststore = gtk.ListStore(str, str, str, str, str
                                          ,str, str, str, str, str)
            #                              dbms, name, comment, user, passwd, host, "", default_icon, status, icon
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
            self.changes = False

            self.scrolledwindow = gtk.ScrolledWindow()
            self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self.scrolledwindow.add(self.listview)
            self.vbox.pack_start(self.scrolledwindow, expand=True, fill=True, padding=0)

            refreshbutton = gtk.Button(_("Refresh"))
            refreshbutton.connect("clicked", self.refresh, None)
            self.vbox.pack_start(refreshbutton, False, False, 3)
            refreshbutton.show()

            col = self.addTextColumn(_("Type"), 0, False)
            col = self.addTextColumn(_("Name"), 1, False)
            col = self.addTextColumn(_("Description"), 2, True)
            col = self.addTextColumn(_("Username"), 3, True)
            col = self.addTextColumn(_("Password"), 4, True)
            col = self.addTextColumn(_("Host"), 5, True)
            col = self.addTextObjColumn(_("Default"), 6, 6)
            col = self.addTextObjColumn(_("Status"), 7, 8)

            #self.listview.get_selection().set_mode(gtk.SELECTION_SINGLE)
            #self.listview.get_selection().connect("changed", self.on_selection_changed)
            self.listview.add_events(gtk.gdk.BUTTON_PRESS_MASK)
            self.listview.connect('button_press_event', self.selectTest)

            self.loadDbs()

            #self.dia.connect('response', self.dialog_response_cb)
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print 'guidbmaint: '+ err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])

    def dialog_response_cb(self, dialog, response_id):
        # this is called whether close button is pressed or window is closed
        log.info('dialog_response_cb: response_id='+str(response_id))
        #if self.changes:
        #    self.config.save()
        dialog.destroy()
        return(response_id)


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
        log.info('edited_cb: col = '+str(col))
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
                                         , db_desc = self.liststore[path][self.COL_DESC]
                                         , db_ip = self.liststore[path][self.COL_HOST]
                                         , db_user = self.liststore[path][self.COL_USER]
                                         , db_pass = self.liststore[path][self.COL_PASS] )
            self.changes = True
        return

    def check_new_name(self, path, new_text):
        name_ok = True
        for i,db in enumerate(self.liststore):
            if i != path and new_text == db[self.COL_NAME]:
                name_ok = False
        #TODO: popup an error message telling user names must be unique
        return name_ok

    def addTextObjColumn(self, title, viewcol, storecol, editable=False):
        col = gtk.TreeViewColumn(title)
        self.listview.append_column(col)

        cRenderT = gtk.CellRendererText()
        cRenderT.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        col.pack_start(cRenderT, False)
        col.add_attribute(cRenderT, 'text', storecol)

        cRenderP = gtk.CellRendererPixbuf()
        col.pack_start(cRenderP, True)
        col.add_attribute(cRenderP, 'stock-id', storecol+1)

        col.set_max_width(1000)
        col.set_spacing(0)  # no effect
        self.listcols.append(col)

        col.set_clickable(True)
        col.connect("clicked", self.sortCols, viewcol)
        return(col)

    def selectTest(self, widget, event):
        if event.button == 1:  # and event.type == gtk.gdk._2BUTTON_PRESS:
            pthinfo = self.listview.get_path_at_pos( int(event.x), int(event.y) )
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                row = path[0]
                if col == self.listcols[self.COL_DFLT]:
                    if self.liststore[row][self.MODEL_STATUS] == 'ok' and self.liststore[row][self.MODEL_DFLTIC] is None:
                        self.setDefaultDB(row)

    def setDefaultDB(self, row):
        print "set new defaultdb:", row, self.liststore[row][self.MODEL_NAME]
        for r in xrange(len(self.liststore)):
            if r == row:
                self.liststore[r][self.MODEL_DFLTIC] = gtk.STOCK_APPLY
                default = "True"
            else:
                self.liststore[r][self.MODEL_DFLTIC] = None
                default = "False"

            self.config.set_db_parameters( db_server = self.liststore[r][self.COL_DBMS]
                                         , db_name = self.liststore[r][self.COL_NAME]
                                         , db_desc = self.liststore[r][self.COL_DESC]
                                         , db_ip   = self.liststore[r][self.COL_HOST]
                                         , db_user = self.liststore[r][self.COL_USER]
                                         , db_pass = self.liststore[r][self.COL_PASS]
                                         , default = default
                                         )
        self.changes = True
        return
        

    def loadDbs(self):

        self.liststore.clear()
        #self.listcols = []
        dia = self.info_box2(None, _('Testing database connections ... '), "", False, False)
        while gtk.events_pending():
            gtk.mainiteration() 

        try:
            # want to fill: dbms, name, comment, user, passwd, host, default, status, icon
            for name in self.config.supported_databases: #db_ip/db_user/db_pass/db_server
                dbms = self.config.supported_databases[name].db_server  # mysql/postgresql/sqlite
                dbms_num = self.config.get_backend(dbms)              #   2  /    3     /  4
                comment = self.config.supported_databases[name].db_desc
                if dbms == 'sqlite':
                    user = ""
                    passwd = ""
                else:
                    user = self.config.supported_databases[name].db_user
                    passwd = self.config.supported_databases[name].db_pass
                host = self.config.supported_databases[name].db_ip
                default = (name == self.config.db_selected)
                default_icon = None
                if default:  default_icon = gtk.STOCK_APPLY
                status = ""
                icon = None
                err_msg = ""
                
                sql = SQL.Sql(db_server=dbms)
                db = Database.Database(self.config, sql = sql, autoconnect = False)
                # try to connect to db, set status and err_msg if it fails
                try:
                    # is creating empty db for sqlite ... mod db.py further?
                    # add noDbTables flag to db.py?
                    log.debug(_("loaddbs: trying to connect to: %s/%s, %s, %s/%s") % (str(dbms_num),dbms,name,user,passwd))
                    db.connect(backend=dbms_num, host=host, database=name, user=user, password=passwd, create=False)
                    if db.connected:
                        log.debug(_("         connected ok"))
                        status = 'ok'
                        icon = gtk.STOCK_APPLY
                        if db.wrongDbVersion:
                            status = 'old'
                            icon = gtk.STOCK_INFO
                    else:
                        log.debug(_("         not connected but no exception"))
                except Exceptions.FpdbMySQLAccessDenied:
                    err_msg = _("MySQL Server reports: Access denied. Are your permissions set correctly?")
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except Exceptions.FpdbMySQLNoDatabase:
                    err_msg = _("MySQL client reports: 2002 or 2003 error. Unable to connect - Please check that the MySQL service has been started")
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except Exceptions.FpdbPostgresqlAccessDenied:
                    err_msg = _("Postgres Server reports: Access denied. Are your permissions set correctly?")
                    status = "failed"
                except Exceptions.FpdbPostgresqlNoDatabase:
                    err_msg = _("Postgres client reports: Unable to connect - Please check that the Postgres service has been started")
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                except:
                    err = traceback.extract_tb(sys.exc_info()[2])[-1]
                    log.info( 'db connection to '+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: '
                              + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1]) )#TODO Gettextify
                    status = "failed"
                    icon = gtk.STOCK_CANCEL
                if err_msg:
                    log.info( 'db connection to '+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: '
                              + err_msg )#TODO Gettextify

                b = gtk.Button(name)
                b.show()
                iter = self.liststore.append( (dbms, name, comment, user, passwd, host, "", default_icon, status, icon) )

            self.info_box2(dia[0], _("finished."), "", False, True)
            self.listview.show()
            self.scrolledwindow.show()
            self.vbox.show()
            self.dia.set_focus(self.listview)

            self.vbox.show_all()
            self.dia.show()
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _('loaddbs error: ')+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: ' \
                      + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])

    def sortCols(self, col, n):
        try:
            log.info('sortcols n='+str(n))
            if not col.get_sort_indicator() or col.get_sort_order() == gtk.SORT_ASCENDING:
                col.set_sort_order(gtk.SORT_DESCENDING)
            else:
                col.set_sort_order(gtk.SORT_ASCENDING)
            self.liststore.set_sort_column_id(n, col.get_sort_order())
            #self.liststore.set_sort_func(n, self.sortnums, (n,grid))
            log.info('sortcols len(listcols)='+str(len(self.listcols)))
            for i in xrange(len(self.listcols)):
                log.info('sortcols i='+str(i))
                self.listcols[i].set_sort_indicator(False)
            self.listcols[n].set_sort_indicator(True)
            # use this   listcols[col].set_sort_indicator(True)
            # to turn indicator off for other cols
        except:
            err = traceback.extract_tb(sys.exc_info()[2])
            print _("***sortCols error: ") + str(sys.exc_info()[1])
            print "\n".join( [e[0]+':'+str(e[1])+" "+e[2] for e in err] )
            log.info(_('sortCols error: ') + str(sys.exc_info()) )

    def refresh(self, widget, data):
        self.loadDbs()

    def info_box(self, dia, str1, str2, run, destroy):
        if dia is None:
            #if run:  
            btns = gtk.BUTTONS_NONE
            btns = gtk.BUTTONS_OK
            dia = gtk.MessageDialog( parent=self.main_window, flags=gtk.DIALOG_DESTROY_WITH_PARENT
                                   , type=gtk.MESSAGE_INFO, buttons=(btns), message_format=str1 )
            # try to remove buttons!
            # (main message is in inverse video if no buttons, so try removing them after 
            # creating dialog)
            # NO! message just goes back to inverse video :-(    use info_box2 instead
            for c in dia.vbox.get_children():
                if isinstance(c, gtk.HButtonBox):
                    for d in c.get_children():
                        log.info('child: '+str(d)+' is a '+str(d.__class__))
                        if isinstance(d, gtk.Button):
                            log.info(_('removing button %s'% str(d)))
                            c.remove(d)
            if str2:
                dia.format_secondary_text(str2)
        else:
            dia.set_markup(str1)
            if str2:
                dia.format_secondary_text(str2)
        dia.show()
        response = None
        if run:      response = dia.run()
        if destroy:  dia.destroy()
        return (dia, response)

    def info_box2(self, dia, str1, str2, run, destroy):
        if dia is None:
            # create dialog and add icon and label
            btns = (gtk.BUTTONS_OK)
            btns = None
            # messagedialog puts text in inverse colors if no buttons are displayed??
            #dia = gtk.MessageDialog( parent=self.main_window, flags=gtk.DIALOG_DESTROY_WITH_PARENT
            #                       , type=gtk.MESSAGE_INFO, buttons=(btns), message_format=str1 )
            dia = gtk.Dialog( parent=self.main_window, flags=gtk.DIALOG_DESTROY_WITH_PARENT
                            , title="" ) # , buttons=btns
            vbox = dia.vbox
            
            h = gtk.HBox(False, 2)
            i = gtk.Image()
            i.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
            l = gtk.Label(str1)
            h.pack_start(i, padding=5)
            h.pack_start(l, padding=5)
            vbox.pack_start(h)
        else:
            # add extra label
            vbox = dia.vbox
            vbox.pack_start( gtk.Label(str1) )
        dia.show_all()
        response = None
        if run:      response = dia.run()
        if destroy:  dia.destroy()
        return (dia, response)


if __name__=="__main__":

    config = Configuration.Config()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title(_("Test Log Viewer"))
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




