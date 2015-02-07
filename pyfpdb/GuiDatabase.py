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
import sys
import traceback
import Queue
import re

import logging

import Exceptions
import Configuration
import Database
import SQL

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("maintdbs")

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
            self.action_area = self.dia.action_area
            #gtk.Widget.set_size_request(self.vbox, 700, 400);

            h = gtk.HBox(False, spacing=3)
            h.show()
            self.vbox.pack_start(h, padding=3)

            vbtn = gtk.VBox(True, spacing=3)
            vbtn.show()
            h.pack_start(vbtn, expand=False, fill=False, padding=2)

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
            h.pack_start(self.scrolledwindow, expand=True, fill=True, padding=0)

            add_button = SideButton(_("Add"), gtk.STOCK_ADD)
            add_button.connect("clicked", self.addDB, None)
            vbtn.pack_start(add_button, False, False, 3)

            refresh_button = SideButton(_("Refresh"), gtk.STOCK_REFRESH)
            refresh_button.connect("clicked", self.refresh, None)
            vbtn.pack_start(refresh_button, False, False, 3)

            col = self.addTextColumn(_("Type"), 0, False)
            col = self.addTextColumn(_("Name"), 1, False)
            col = self.addTextColumn(_("Description"), 2, True)
            col = self.addTextColumn(_("Username"), 3, True)
            col = self.addTextColumn(_("Password"), 4, True)
            col = self.addTextColumn(_("Host"), 5, True)
            col = self.addTextObjColumn(_("Open"), 6, 6)
            col = self.addTextObjColumn(_("Status"), 7, 8)

            #self.listview.get_selection().set_mode(gtk.SELECTION_SINGLE)
            #self.listview.get_selection().connect("changed", self.on_selection_changed)
            self.listview.add_events(gtk.gdk.BUTTON_PRESS_MASK)
            self.listview.connect('button_press_event', self.selectTest)

            self.dia.show_all()
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
        dia = InfoBox( parent=self.dia, str1=_('Testing database connections ... ') )
        while gtk.events_pending():
            gtk.main_iteration() 

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
                
                status, err_msg, icon = GuiDatabase.testDB(self.config, dbms, dbms_num, name, user, passwd, host)

                b = gtk.Button(name)
                b.show()
                iter = self.liststore.append( (dbms, name, comment, user, passwd, host, "", default_icon, status, icon) )

            dia.add_msg( _("finished."), False, True )
            self.listview.show()
            self.scrolledwindow.show()
            self.vbox.show()
            self.dia.set_focus(self.listview)

            self.vbox.show_all()
            self.dia.show()
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _('loadDbs error: ')+str(dbms_num)+','+host+','+name+','+user+','+passwd+' failed: ' \
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
            print "***sortCols " + _("error") + ": " + str(sys.exc_info()[1])
            print "\n".join( [e[0]+':'+str(e[1])+" "+e[2] for e in err] )
            log.info('sortCols ' + _('error') + ': ' + str(sys.exc_info()) )

    def refresh(self, widget, data):
        self.loadDbs()

    def addDB(self, widget, data):
        adb = AddDB(self.config, self.dia)
        (status, err_msg, icon, dbms, dbms_num, name, comment, user, passwd, host) = adb.run()
        adb.destroy()

        # save in liststore
        if status == 'ok':
            iter = self.liststore.append( (dbms, name, comment, user, passwd, host, "", None, status, icon) )

            # keep config save code in line with edited_cb()? call common routine?

            valid = True
            # Validate new value (only for dbms so far, but dbms now not updateable so no validation at all!)
            #if col == self.COL_DBMS:
            #    if new_text not in Configuration.DATABASE_TYPES:
            #        valid = False

            if valid:
                self.config.add_db_parameters( db_server = dbms
                                             , db_name = name
                                             , db_desc = comment
                                             , db_ip   = host
                                             , db_user = user
                                             , db_pass = passwd )
                self.config.save()
                self.changes = False


    @staticmethod
    def testDB(config, dbms, dbms_num, name, user, passwd, host):
        status = ""
        icon = None
        err_msg = ""

        sql = SQL.Sql(db_server=dbms)
        db = Database.Database(config, sql = sql, autoconnect = False)
        # try to connect to db, set status and err_msg if it fails
        try:
            # is creating empty db for sqlite ... mod db.py further?
            # add noDbTables flag to db.py?
            log.debug("testDB: " + _("trying to connect to:") + " %s/%s, %s, %s/%s" % (str(dbms_num),dbms,name,user,passwd))
            db.connect(backend=dbms_num, host=host, database=name, user=user, password=passwd, create=False)
            if db.connected:
                log.debug(_("connected ok"))
                status = 'ok'
                icon = gtk.STOCK_APPLY
                if db.wrongDbVersion:
                    status = 'old'
                    icon = gtk.STOCK_INFO
            else:
                log.debug(_("not connected but no exception"))
        except Exceptions.FpdbMySQLAccessDenied:
            err_msg = _("MySQL Server reports: Access denied. Are your permissions set correctly?")
            status = "failed"
            icon = gtk.STOCK_CANCEL
        except Exceptions.FpdbMySQLNoDatabase:
            err_msg = _("MySQL client reports: 2002 or 2003 error. Unable to connect - ") \
                      + _("Please check that the MySQL service has been started")
            status = "failed"
            icon = gtk.STOCK_CANCEL
        except Exceptions.FpdbPostgresqlAccessDenied:
            err_msg = _("PostgreSQL Server reports: Access denied. Are your permissions set correctly?")
            status = "failed"
        except Exceptions.FpdbPostgresqlNoDatabase:
            err_msg = _("PostgreSQL client reports: Unable to connect - ") \
                      + _("Please check that the PostgreSQL service has been started")
            status = "failed"
            icon = gtk.STOCK_CANCEL
        except:
            # add more specific exceptions here if found (e.g. for sqlite?)
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            err_msg = err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])
            status = "failed"
            icon = gtk.STOCK_CANCEL
        if err_msg:
            log.info( _('db connection to %s, %s, %s, %s, %s failed: %s') % (str(dbms_num), host, name, user, passwd, err_msg))

        return( status, err_msg, icon )


class AddDB(gtk.Dialog):

    def __init__(self, config, parent):
        log.debug(_("AddDB starting"))
        self.dbnames = { 'Sqlite'     : Configuration.DATABASE_TYPE_SQLITE
                       , 'MySQL'      : Configuration.DATABASE_TYPE_MYSQL
                       , 'PostgreSQL' : Configuration.DATABASE_TYPE_POSTGRESQL
                       }
        self.config = config
        # create dialog and add icon and label
        super(AddDB,self).__init__( parent=parent
                                  , flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                                  , title=_("Add New Database")
                                  , buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                                              ,gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT)
                                  ) # , buttons=btns
        self.set_default_size(450, 280)
        #self.connect('response', self.response_cb)

        t = gtk.Table(5, 3, True)
        self.vbox.pack_start(t, expand=False, fill=False, padding=3)

        l = gtk.Label( _("DB Type") )
        l.set_alignment(1.0, 0.5)
        t.attach(l, 0, 1, 0, 1, xpadding=3)
        self.cb_dbms = gtk.combo_box_new_text()
        for s in ('Sqlite',):  # keys(self.dbnames):
            self.cb_dbms.append_text(s)
        self.cb_dbms.set_active(0)
        t.attach(self.cb_dbms, 1, 3, 0, 1, xpadding=3)
        self.cb_dbms.connect("changed", self.db_type_changed, None)

        l = gtk.Label( _("DB Name") )
        l.set_alignment(1.0, 0.5)
        t.attach(l, 0, 1, 1, 2, xpadding=3)
        self.e_db_name = gtk.Entry()
        self.e_db_name.set_width_chars(15)
        t.attach(self.e_db_name, 1, 3, 1, 2, xpadding=3)
        self.e_db_name.connect("focus-out-event", self.db_name_changed, None)

        l = gtk.Label( _("DB Description") )
        l.set_alignment(1.0, 0.5)
        t.attach(l, 0, 1, 2, 3, xpadding=3)
        self.e_db_desc = gtk.Entry()
        self.e_db_desc.set_width_chars(15)
        t.attach(self.e_db_desc, 1, 3, 2, 3, xpadding=3)

        self.l_username = gtk.Label( _("Username") )
        self.l_username.set_alignment(1.0, 0.5)
        t.attach(self.l_username, 0, 1, 3, 4, xpadding=3)
        self.e_username = gtk.Entry()
        self.e_username.set_width_chars(15)
        t.attach(self.e_username, 1, 3, 3, 4, xpadding=3)

        self.l_password = gtk.Label( _("Password") )
        self.l_password.set_alignment(1.0, 0.5)
        t.attach(self.l_password, 0, 1, 4, 5, xpadding=3)
        self.e_password = gtk.Entry()
        self.e_password.set_width_chars(15)
        t.attach(self.e_password, 1, 3, 4, 5, xpadding=3)

        self.l_host = gtk.Label( _("Host Computer") )
        self.l_host.set_alignment(1.0, 0.5)
        t.attach(self.l_host, 0, 1, 5, 6, xpadding=3)
        self.e_host = gtk.Entry()
        self.e_host.set_width_chars(15)
        self.e_host.set_text("localhost")
        t.attach(self.e_host, 1, 3, 5, 6, xpadding=3)

        parent.show_all()
        self.show_all()

        # hide username/password fields as not used by sqlite
        self.l_username.hide()
        self.e_username.hide()
        self.l_password.hide()
        self.e_password.hide()

    def run(self):
        response = super(AddDB,self).run()
        log.debug(_("addDB.run: response is %s, accept is %s") % (str(response), str(int(gtk.RESPONSE_ACCEPT))))

        ok,retry = False,True
        while response == gtk.RESPONSE_ACCEPT:
            ok,retry = self.check_fields()
            if retry:
                response = super(AddDB,self).run()
            else:
                response = gtk.RESPONSE_REJECT

        (status, err_msg, icon, dbms, dbms_num
        ,name, db_desc, user, passwd, host) = ("error", "error", None, None, None
                                              ,None, None, None, None, None)
        if ok:
            log.debug(_("start creating new db"))
            # add a new db
            master_password = None
            dbms     = self.dbnames[ self.cb_dbms.get_active_text() ]
            dbms_num = self.config.get_backend(dbms)
            name     = self.e_db_name.get_text()
            db_desc  = self.e_db_desc.get_text()
            user     = self.e_username.get_text()
            passwd   = self.e_password.get_text()
            host     = self.e_host.get_text()
            
            # TODO:
            # if self.cb_dbms.get_active_text() == 'Postgres':
            #     <ask for postgres master password>
            
            # create_db()  in Database.py or here? ... TODO

            # test db after creating?
            status, err_msg, icon = GuiDatabase.testDB(self.config, dbms, dbms_num, name, user, passwd, host)
            log.debug(_('tested new db, result=%s') % str((status,err_msg)))
            if status == 'ok':
                #dia = InfoBox( parent=self, str1=_('Database created') )
                str1 = _('Database created')
            else:
                #dia = InfoBox( parent=self, str1=_('Database creation failed') )
                str1 = _('Database creation failed')
            #dia.add_msg("", True, True)
            btns = (gtk.BUTTONS_OK)
            dia = gtk.MessageDialog( parent=self, flags=gtk.DIALOG_DESTROY_WITH_PARENT
                                   , type=gtk.MESSAGE_INFO, buttons=(btns), message_format=str1 )
            dia.run()

        return( (status, err_msg, icon, dbms, dbms_num, name, db_desc, user, passwd, host) )

    def check_fields(self):
        """check fields and return true/false according to whether user wants to try again
           return False if fields are ok
        """
        log.debug(_("check_fields: starting"))
        try_again = False
        ok = True

        # checks for all db's
        if self.e_db_name.get_text() == "":
            msg = _("No Database Name given")
            ok = False
        elif self.e_db_desc.get_text() is None or self.e_db_desc.get_text() == "":
            msg = _("No Database Description given")
            ok = False
        elif self.cb_dbms.get_active_text() != 'Sqlite' and self.e_username.get_text() == "":
            msg = _("No Username given")
            ok = False
        elif self.cb_dbms.get_active_text() != 'Sqlite' and self.e_password.get_text() == "":
            msg = _("No Password given")
            ok = False
        elif self.e_host.get_text() == "":
            msg = _("No Host given")
            ok = False

        if ok:
            if self.cb_dbms.get_active_text() == 'Sqlite':
                # checks for sqlite
                pass
            elif self.cb_dbms.get_active_text() == 'MySQL':
                # checks for mysql
                pass
            elif self.cb_dbms.get_active_text() == 'Postgres':
                # checks for postgres
                pass
            else:
                msg = _("Unknown Database Type selected")
                ok = False

        if not ok:
            log.debug(_("check_fields: open dialog"))
            dia = gtk.MessageDialog( parent=self
                                   , flags=gtk.DIALOG_DESTROY_WITH_PARENT
                                   , type=gtk.MESSAGE_ERROR
                                   , message_format=msg
                                   , buttons = gtk.BUTTONS_YES_NO
                                   )
            #l = gtk.Label(msg)
            #dia.vbox.add(l)
            l = gtk.Label( _("Do you want to try again?") )
            dia.vbox.add(l)
            dia.show_all()
            ret = dia.run()
            #log.debug(_("check_fields: ret is %s cancel is %s") % (str(ret), str(int(gtk.RESPONSE_CANCEL))))
            if ret == gtk.RESPONSE_YES:
                try_again = True
            #log.debug(_("check_fields: destroy dialog"))
            dia.hide()
            dia.destroy()

        #log.debug(_("check_fields: returning ok as %s, try_again as %s") % (str(ok), str(try_again)))
        return(ok,try_again)

    def db_type_changed(self, widget, data):
        if self.cb_dbms.get_active_text() == 'Sqlite':
            self.l_username.hide()
            self.e_username.hide()
            self.e_username.set_text("")
            self.l_password.hide()
            self.e_password.hide()
            self.e_password.set_text("")
        else:
            self.l_username.show()
            self.e_username.show()
            self.l_password.show()
            self.e_password.show()
        return(response)

    def db_name_changed(self, widget, event, data):
        log.debug('db_name_changed: text='+widget.get_text())
        if not re.match('\....$', widget.get_text()):
            widget.set_text(widget.get_text()+'.db3')
            widget.show()

    #def response_cb(self, dialog, data):
    #    dialog.destroy()
    #    return(data)


class InfoBox(gtk.Dialog):

    def __init__(self, parent, str1):
        # create dialog and add icon and label
        btns = (gtk.BUTTONS_OK)
        btns = None
        # messagedialog puts text in inverse colors if no buttons are displayed??
        #dia = gtk.MessageDialog( parent=self.main_window, flags=gtk.DIALOG_DESTROY_WITH_PARENT
        #                       , type=gtk.MESSAGE_INFO, buttons=(btns), message_format=str1 )
        # so just use Dialog instead
        super(InfoBox,self).__init__( parent=parent
                                    , flags=gtk.DIALOG_DESTROY_WITH_PARENT
                                    , title="" ) # , buttons=btns
        
        h = gtk.HBox(False, 2)
        i = gtk.Image()
        i.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        l = gtk.Label(str1)
        h.pack_start(i, padding=5)
        h.pack_start(l, padding=5)
        self.vbox.pack_start(h)
        parent.show_all()
        self.show_all()

    def add_msg(self, str1, run, destroy):
        # add extra label
        self.vbox.pack_start( gtk.Label(str1) )
        self.show_all()
        response = None
        if run:      response = self.run()
        if destroy:  self.destroy()
        return (response)


class SideButton(gtk.Button):
    """Create a button with the label below the icon"""

    # to change label on buttons:
    # ( see http://faq.pygtk.org/index.py?req=show&file=faq09.005.htp )
    # gtk.stock_add([(gtk.STOCK_ADD, _("Add"), 0, 0, "")])

    # alternatively:
    # button = gtk.Button(stock=gtk.STOCK_CANCEL)
    # button.show()
    # alignment = button.get_children()[0]
    # hbox = alignment.get_children()[0]
    # image, label = hbox.get_children()
    # label.set_text('Hide')

    def __init__(self, label=None, stock=None, use_underline=True):
        gtk.stock_add([(stock, label, 0, 0, "")])

        super(SideButton, self).__init__(label=label, stock=stock, use_underline=True)
        alignment = self.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        #label.set_text('Hide')
        hbox.remove(image)
        hbox.remove(label)
        v = gtk.VBox(False, spacing=3)
        v.pack_start(image, 3)
        v.pack_start(label, 3)
        alignment.remove(hbox)
        alignment.add(v)
        self.show_all()



if __name__=="__main__":

    config = Configuration.Config()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title(_("Maintain Databases"))
    win.set_border_width(1)
    win.set_default_size(600, 500)
    win.set_resizable(True)

    dia = gtk.Dialog(_("Maintain Databases"),
                     win,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
    dia.set_default_size(500, 500)
    log = GuiDatabase(config, win, dia)
    response = dia.run()
    if response == gtk.RESPONSE_ACCEPT:
        pass
    dia.destroy()




