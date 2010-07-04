#!/usr/bin/python2
# -*- coding: utf-8 -*-

#Copyright 2008-2010 J. Urner
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

"""Database manager

@todo: (gtk) how to validate user input in gtk.Dialog? as soon as the user clicks ok the dialog is dead. we use a while loop as workaround. not nice
@todo: (fpdb) we need the application name 'fpdb' from somewhere to put it in dialog titles
@todo: (fpdb) config object should be initialized globally and accessible from all modules via Configuration.py

@todo: (all dialogs) save/restore size and pos

@todo: (WidgetDatabaseManager) give database status meaningful colors
@todo: (WidgetDatabaseManager) implement database purging
@todo: (WidgetDatabaseManager) implement database export
@todo: (WidgetDatabaseManager) what to do on database doubleclick?
@todo: (WidgetDatabaseManager) context menu for database tree
@todo: (WidgetDatabaseManager) initializing/validating databases may take a while. how to give feedback?

"""

import os
import pygtk
pygtk.require('2.0')
import gtk
import gobject

#*******************************************************************************************************
class DatabaseManager(gobject.GObject):
    DatabaseTypes = {}

    @classmethod
    def from_fpdb(klass, data, defaultDatabaseType=None):

        #NOTE: if no databases are present in config fpdb fails with
        #    Traceback (most recent call last):
        #      File "/home/me2/Scr/Repos/fpdb-mme/pyfpdb/DatabaseManager.py", line 783, in <module>
        #        databaseManager = DatabaseManager.from_fpdb('', defaultDatabaseType=DatabaseTypeSqLite)
        #      File "/home/me2/Scr/Repos/fpdb-mme/pyfpdb/DatabaseManager.py", line 36, in from_fpdb
        #        config = Configuration.Config(file=options.config, dbname=options.dbname)
        #      File "/home/me2/Scr/Repos/fpdb-mme/pyfpdb/Configuration.py", line 436, in __init__
        #        db = self.get_db_parameters()
        #      File "/home/me2/Scr/Repos/fpdb-mme/pyfpdb/Configuration.py", line 583, in get_db_parameters
        #        name = self.db_selected
        #    AttributeError: Config instance has no attribute 'db_selected'
        import sys
        import Options
        import Configuration
        #NOTE: fpdb should perform this globally
        (options, argv) = Options.fpdb_options()
        config = Configuration.Config(file=options.config, dbname=options.dbname)
        #TODO: handle no database present
        defaultDatabaseName = config.get_db_parameters().get('db-databaseName', None)
        #TODO: fpdb stores databases in no particular order. this has to be fixed somehow
        databases = []
        for name, fpdbDatabase in config.supported_databases.items():
            databaseKlass = klass.DatabaseTypes.get(fpdbDatabase.db_server, None)
            #NOTE: Config does not seem to validate user input, so anything may end up here
            if databaseKlass is None:
                raise ValueError('Unknown databasetype: %s' % fpdbDatabase.db_server)

            database = databaseKlass()
            if database.Type == 'sqlite':
                database.name = fpdbDatabase.db_name
                database.file = fpdbDatabase.db_server
            else:
                database.name = fpdbDatabase.db_name
                database.host = fpdbDatabase.db_server
                #NOTE: fpdbDatabase.db_ip is no is a string
                database.port = int(fpdbDatabase.db_ip)
                database.user = fpdbDatabase.db_user
                database.password = fpdbDatabase.db_pass
            databases.append(database)

        return klass(databases=databases, defaultDatabaseType=defaultDatabaseType)

    def to_fpdb(self):
        pass


    def __init__(self, databases=None, defaultDatabaseType=None):
        gobject.GObject.__init__(self)

        self._defaultDatabaseType = defaultDatabaseType
        self._databases = [] if databases is None else list(databases)
        self._activeDatabase = None
    def __iter__(self):
        return iter(self._databases)
    def set_default_database_type(self, databaseType):
        self._defaultDatabaseType = defaultDatabaseType
    def get_default_database_type(self):
        return self._defaultDatabaseType
    def database_from_id(self, idDatabase):
        for database in self._databases:
            if idDatabase == self.database_id(database):
                return database
    def database_id(self, database):
        return id(database)
    def add_database(self, database):
        if database in self._databases:
            raise ValueError('database already registered')
        self._databases.append(database)
    def remove_database(self, database):
        self._databases.remove(database)

    def activate_database(self, database):
        if self._activeDatabase is not None:
            self._activeDatabase.status = self._activeDatabase.StatusInactive
            #TODO: finalize database
            self.emit('database-deactivated', self.database_id(self._activeDatabase) )

        database.status = database.StatusActive
        #TODO: activate database
        self._activeDatabase = database
        self.emit('database-activated', self.database_id(database) )

    def active_database(self):
        return self._activeDatabase

# register DatabaseManager signals
gobject.type_register(DatabaseManager)
gobject.signal_new('database-activated', DatabaseManager, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int, ))
gobject.signal_new('database-deactivated', DatabaseManager, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int, ))
gobject.signal_new('database-error', DatabaseManager, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int, ))

class DatabaseTypeMeta(type):
    def __new__(klass, name, bases, kws):
        newKlass = type.__new__(klass, name, bases, kws)
        if newKlass.Type is not None:
            if newKlass.Type in DatabaseManager.DatabaseTypes:
                raise ValueError('data base type already registered for: %s' % newKlass.Type)
            DatabaseManager.DatabaseTypes[newKlass.Type] = newKlass
        return newKlass

class DatabaseTypeBase(object):
    __metaclass__ = DatabaseTypeMeta
    Type = None
    StatusActive = 'active'
    StatusInactive = 'inactive'
    StatusError = 'error'        #TODO: not implemented

    #TODO: not happy with returning error string. just being too lazy to impl dozens of error codes for later translation
    def init_new_database(self):
        """initializes a new empty database
        @return: (str) error if something goes wrong, None otherwise
        """
        raise NotImplementedError()

    def validate_database(self):
        """checks if the database is valid
        @return: (str) error if something goes wrong, None otherwise
        """
        raise NotImplementedError()

class DatabaseTypePostgres(DatabaseTypeBase):
    Type = 'postgresql'
    @classmethod
    def display_name(klass):
        return 'Postgres'
    def __init__(self, name='', host='localhost', port=5432, user='postgres', password='', database='fpdb'):
        self.name = name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.status = self.StatusInactive

    #TODO: implement
    def init_new_database(self):
        pass

    #TODO: implement
    def validate_database(self):
        pass

class DatabaseTypeMysql(DatabaseTypeBase):
    Type = 'mysql'
    @classmethod
    def display_name(klass):
        return 'MySql'
    def __init__(self, name='', host='localhost', port=3306, user='root', password='', database='fpdb'):
        self.name = name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.status = self.StatusInactive

    #TODO: implement
    def init_new_database(self):
        pass

    #TODO: implement
    def validate_database(self):
        pass


class DatabaseTypeSqLite(DatabaseTypeBase):
    Type = 'sqlite'
    @classmethod
    def display_name(klass):
        return 'SqLite'
    def __init__(self, name='', host='', file='', database='fpdb'):
        self.name = name
        self.file = file
        self.status = self.StatusInactive

    def init_new_database(self):
        # make shure all attrs are specified
        if not self.file:
            return 'no database file specified'
        # create file if necessary (this will truncate file if it exists)
        try:
            open(self.file, 'w').close()
        except IOError:
            return 'can not write file'

        #TODO: init tables (...)


    def validate_database(self):
        pass
        #TODO: check if tables (...) exist



#TODO: how do we want to handle unsupported database types?
# ..uncomment to remove unsupported database types
#try: import psycopg2
#except ImportError: del DatabaseManager.DatabaseTypes['postgres']
#try: import MySQLdb
#except ImportError: del DatabaseManager.DatabaseTypes['mysql']
#try: import sqlite3
#except ImportError: del DatabaseManager.DatabaseTypes['sqlite']

#***************************************************************************************************************************
#TODO: there is no title (on linux), wtf?
def DialogError(parent=None, msg=''):
    dlg = gtk.MessageDialog(
                parent=parent,
                flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_OK,
                message_format=msg,
                )
    dlg.run()
    dlg.destroy()
    return None


#TODO: derrive from gtk.VBox?
class WidgetDatabaseProperties(gtk.VBox):

    ModeNew = 0
    ModeEdit = 1
    ModeAdd = 2

    class SqLiteFileChooserButton(gtk.HBox):
        #NOTE: for some weird reason it is impossible to let the user choose a non exiting filename with gtk.FileChooserButton, so impl our own on the fly
        def __init__(self, widgetDatabaseProperties, parentWidget):
            gtk.HBox.__init__(self)
            self.set_homogeneous(False)

            self.parentWidget = parentWidget
            self.widgetDatabaseProperties = widgetDatabaseProperties
            self.entry = gtk.Entry()
            self.button = gtk.Button('...')
            self.button.connect('clicked', self.on_button_clicked)

            # layout widgets
            self.pack_start(self.entry, True, True)
            self.pack_start(self.button, False, False)

        def get_filename(self):
            return self.entry.get_text()

        def set_filename(self, name):
            self.entry.set_text(name)

        def on_button_clicked(self, button):
            if self.widgetDatabaseProperties.mode == WidgetDatabaseProperties.ModeAdd:
                action = gtk.FILE_CHOOSER_ACTION_OPEN
            elif self.widgetDatabaseProperties.mode == WidgetDatabaseProperties.ModeNew:
                action = gtk.FILE_CHOOSER_ACTION_SAVE
            else:
                raise ValueError('unsupported dialog mode')
            dlg = gtk.FileChooserDialog(
                    title='Choose an exiting database file or type in name of a new one',
                    parent=self.parentWidget,
                    action=action,
                    buttons=(
                            gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_OK,
                            ),
                    backend=None
                    )
            dlg.set_default_response(gtk.RESPONSE_OK)
            dlg.set_do_overwrite_confirmation(True)
            if dlg.run() == gtk.RESPONSE_OK:
                fileName = dlg.get_filename()
                self.set_filename(fileName)
            dlg.destroy()


    #TODO: bit ugly this thingy. try to find a better way to map database attrs to gtk widgets
    class FieldWidget(object):
        def __init__(self, text='', attrDatabase='', widget=None, attrGet=None, attrSet=None, defaultValue=None, canEdit=False, tooltip=''):
            """
            @param canEdit: True if the user can edit the attr in edit mode, False otherwise
            """
            self._label = gtk.Label(text)
            self._attrDatabase = attrDatabase
            self._widget = widget
            self._defaultValue = defaultValue
            self._attrGetter=None,
            self._attrGet = attrGet
            self._attrSet = attrSet
            self._canEdit = canEdit

            self._label.set_tooltip_text(tooltip)
            self._widget.set_tooltip_text(tooltip)

        def widget(self):
            return self._widget
        def label(self):
            return self._label
        def is_sensitive(self, database):
            return hasattr(database, self._attrDatabase)
        def can_edit(self):
            return self._canEdit
        def set_sensitive(self, flag):
            self._label.set_sensitive(flag)
            self._widget.set_sensitive(flag)
        def value_from_database(self, database):
            getattr(self._widget, self._attrSet)( getattr(database, self._attrDatabase) )
        def value_to_database(self, database):
            setattr(database, self._attrDatabase, getattr(self._widget, self._attrGet)() )
        def reset_value(self):
            getattr(self._widget, self._attrSet)(self._defaultValue)

    def __init__(self, databaseManager, database, mode=ModeEdit, parentWidget=None):
            gtk.VBox.__init__(self)

            self.databaseManager = databaseManager
            self.database = database
            self.mode = mode
            self.parentWidget = parentWidget
            self.fieldWidgets = (
                        self.FieldWidget(
                                text='Name:',
                                attrDatabase='name',
                                widget=gtk.Entry(),
                                defaultValue='',
                                attrGet='get_text',
                                attrSet='set_text',
                                canEdit=True,
                                tooltip='Any name you like to name the database '
                        ),
                        self.FieldWidget(
                            text='File:',
                            attrDatabase='file',
                            widget=self.SqLiteFileChooserButton(self, self.parentWidget),
                            defaultValue='',
                            attrGet='get_filename',
                            attrSet='set_filename',
                            canEdit=False,
                            tooltip='Fully qualified path of the file to hold the database '
                        ),
                        self.FieldWidget(
                            text='Host:',
                            attrDatabase='host',
                            widget=gtk.Entry(),
                            defaultValue='',
                            attrGet='get_text',
                            attrSet='set_text',
                            canEdit=False,
                            tooltip='Host the database is located at'
                        ),
                        self.FieldWidget(
                            text='Port:',
                            attrDatabase='port',
                            widget=gtk.SpinButton(adjustment=gtk.Adjustment(value=0, lower=0, upper=999999, step_incr=1, page_incr=10) ),
                            defaultValue=0,
                            attrGet='get_value',
                            attrSet='set_value',
                            canEdit=False,
                            tooltip='Port to use to connect to the host'
                        ),
                        self.FieldWidget(
                            text='User:',
                            attrDatabase='user',
                            widget=gtk.Entry(),
                            defaultValue='',
                            attrGet='get_text',
                            attrSet='set_text',
                            canEdit=False,
                            tooltip='User name used to login to the host'
                        ),
                        self.FieldWidget(
                            text='Pwd:',
                            attrDatabase='password',
                            widget=gtk.Entry(),
                            defaultValue='',
                            attrGet='get_text',
                            attrSet='set_text',
                            canEdit=False,
                            tooltip='Password used to login to the host'
                        ),
                        self.FieldWidget(
                            text='Db:',
                            attrDatabase='database',
                            widget=gtk.Entry(),
                            defaultValue='',
                            attrGet='get_text',
                            attrSet='set_text',
                            canEdit=False,
                            tooltip='Name of the database'
                        ),
                    )

            # setup database type combo
            self.comboType = gtk.ComboBox()
            listStore= gtk.ListStore(str, str)
            self.comboType.set_model(listStore)
            cell = gtk.CellRendererText()
            self.comboType.pack_start(cell, True)
            self.comboType.add_attribute(cell, 'text', 0)
            self.comboType.connect('changed', self.on_combo_type_changed)

            # fill database type combo with available database klasses. we store (databaseDisplayName, databaseType) in our model for later lookup
            iCurrentDatabase = 0
            databaseTypes = [(klass.display_name(), klass.Type) for klass in databaseManager.DatabaseTypes.values()]
            databaseTypes.sort()
            for i, (databaseDisplayName, databaseType) in enumerate(databaseTypes):
                listStore.append( (databaseDisplayName, databaseType) )
                if databaseType == self.database.Type:
                    iCurrentDatabase = i
            if self.mode == self.ModeEdit or len(databaseTypes) < 2:
                self.comboType.set_button_sensitivity(gtk.SENSITIVITY_OFF)

            # init and layout field widgets
            self.pack_start(self.comboType, False, False, 2)
            table = gtk.Table(rows=len(self.fieldWidgets) +1, columns=2, homogeneous=False)
            self.pack_start(table, False, False, 2)
            for i,fieldWidget in enumerate(self.fieldWidgets):
                table.attach(fieldWidget.label(), 0, 1, i, i+1, xoptions=gtk.FILL)
                table.attach(fieldWidget.widget(), 1, 2, i, i+1)

            # init widget
            self.comboType.set_active(iCurrentDatabase)
            self._adjust_widgets(self.database)

    def _adjust_widgets(self, database):
        for fieldWidget in self.fieldWidgets:
            isSensitive = fieldWidget.is_sensitive(database)
            if isSensitive:
                fieldWidget.value_from_database(database)
            else:
                fieldWidget.reset_value()
            if self.mode == self.ModeEdit:
                isSensitive = isSensitive and fieldWidget.can_edit()
            fieldWidget.set_sensitive(isSensitive)


    def on_combo_type_changed(self, combo):
        i = self.comboType.get_active()
        if i < 0:
            return

        # check if we need to init a new database
        currentDatabaseType = self.comboType.get_model()[i][1]
        if currentDatabaseType == self.database.Type:
            return

        # create new empty database
        #NOTE: we dont register it in DatabaseManager
        self.database = self.databaseManager.DatabaseTypes[currentDatabaseType]()
        self._adjust_widgets(self.database)


    def get_database(self):
        for fieldWidget in self.fieldWidgets:
            if fieldWidget.is_sensitive(self.database):
                fieldWidget.value_to_database(self.database)
        return self.database


class DialogDatabaseProperties(gtk.Dialog):
    def __init__(self, databaseManager, database, parent=None,  mode=WidgetDatabaseProperties.ModeEdit, title=''):
        gtk.Dialog.__init__(self,
                title=title,
                parent=parent,
                flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons=(
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                        )
                )
        self.connect('response', self.on_dialog_response)

        # setup widget
        self.widgetDatabaseProperties = WidgetDatabaseProperties(databaseManager,database, mode=mode, parentWidget=self)
        self.vbox.pack_start(self.widgetDatabaseProperties, True, True)
        self.show_all()

    def get_widget_database_properties(self):
        return self.widgetDatabaseProperties

    def on_dialog_response(self, dlg, responseId):
        if responseId == gtk.RESPONSE_REJECT:
            pass
        elif responseId == gtk.RESPONSE_ACCEPT:
            pass


#TODO: derrive from gtk.VBox?
# ..is there a way to derrive from gtk.Widget or similar? this would make parentWidget kw obsolete
class WidgetDatabaseManager(gtk.VBox):
    """
    """

    def __init__(self, databaseManager, parentWidget=None):
        gtk.VBox.__init__(self)

        self.parentWidget = parentWidget
        self.databaseManager = databaseManager
        self.databaseManager.connect('database-activated', self.on_database_manager_database_activated)
        self.databaseManager.connect('database-deactivated', self.on_database_manager_database_deactivated)
        self.databaseStatusNames = {
                DatabaseTypeBase.StatusActive: 'Active',
                DatabaseTypeBase.StatusInactive: 'Inactive',
                DatabaseTypeBase.StatusError: 'Error',
                }


        #TODO: dono how to make word wrap work as expected
        self.labelInfo = gtk.Label('database management')
        self.labelInfo.set_line_wrap(True)
        self.labelInfo.set_selectable(True)
        self.labelInfo.set_single_line_mode(False)
        self.labelInfo.set_alignment(0, 0)

        # database management buttons

        #TODO: bit messy the distinction New/Add/Edit. we'd have to pass three flags to DialogDatabaseProperties
        # to handle this. maybe drop Edit (is just a Remove + Add), to keep things simple
        self.buttonDatabaseActivate = gtk.Button("Activate")
        self.buttonDatabaseActivate.set_tooltip_text('activates the database')
        self.buttonDatabaseActivate.connect('clicked', self.on_button_database_activate_clicked)
        self.buttonDatabaseActivate.set_sensitive(False)
        self.buttonDatabaseNew = gtk.Button("New..")
        self.buttonDatabaseNew.set_tooltip_text('creates a new database')
        self.buttonDatabaseNew.connect('clicked', self.on_button_database_new_clicked)
        self.buttonDatabaseAdd = gtk.Button("Add..")
        self.buttonDatabaseAdd.set_tooltip_text('adds an existing database')
        self.buttonDatabaseAdd.connect('clicked', self.on_button_database_add_clicked)
        self.buttonDatabaseEdit = gtk.Button("Edit..")
        self.buttonDatabaseEdit.set_tooltip_text('edit database settings')
        self.buttonDatabaseEdit.connect('clicked', self.on_button_database_edit_clicked)
        self.buttonDatabaseEdit.set_sensitive(False)
        self.buttonDatabaseRemove = gtk.Button("Remove")
        self.buttonDatabaseRemove.set_tooltip_text('removes the database from the list')
        self.buttonDatabaseRemove.set_sensitive(False)
        self.buttonDatabaseRemove.connect('clicked', self.on_button_database_remove_clicked)

        #TODO: i dont think we should do any real database management here. maybe drop it
        #self.buttonDatabaseDelete = gtk.Button("Delete")
        #self.buttonDatabaseDelete.set_tooltip_text('removes the database from the list and deletes it')
        #self.buttonDatabaseDelete.set_sensitive(False)

        # init database tree
        self.treeDatabases = gtk.TreeView()
        treeDatabaseColumns = (    # name, displayName, dataType
                ('name', 'Name', str),
                ('status', 'Status', str),
                ('type', 'Type', str),
                ('_id', '', int),
                )
        self.treeDatabaseColumns = {}    # name --> index
        store = gtk.ListStore( *[i[2] for i in treeDatabaseColumns]  )
        self.treeDatabases.set_model(store)
        for i, (name, displayName, dataType) in enumerate(treeDatabaseColumns):
            col = gtk.TreeViewColumn(displayName, gtk.CellRendererText(), text=i)
            self.treeDatabases.append_column(col)
            if name.startswith('_'):
                col.set_visible(False)
            self.treeDatabaseColumns[name] = i
        self.treeDatabases.get_selection().connect('changed', self.on_tree_databases_selection_changed)

        # layout widgets
        vbox = gtk.VBox(self)
        vbox.pack_start(self.labelInfo, False, False, 2)
        vbox.pack_start(gtk.HSeparator(), False, False, 2)
        hbox = gtk.HBox()
        self.add(hbox)
        hbox.set_homogeneous(False)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 2)
        vbox.pack_start(self.buttonDatabaseActivate, False, False, 2)
        vbox.pack_start(self.buttonDatabaseNew, False, False, 2)
        vbox.pack_start(self.buttonDatabaseAdd, False, False, 2)
        vbox.pack_start(self.buttonDatabaseEdit, False, False, 2)
        vbox.pack_start(self.buttonDatabaseRemove, False, False, 2)
        #vbox.pack_start(self.buttonDatabaseDelete, False, False, 2)
        box = gtk.VBox()
        vbox.pack_start(box, True, True, 0)

        hbox.pack_start(gtk.VSeparator(), False, False, 2)
        hbox.pack_end(self.treeDatabases, True, True, 2)

        self.show_all()

        # init widget
        model = self.treeDatabases.get_model()
        for database in self.databaseManager:
            it = model.append()
            model.set_value(it, self.treeDatabaseColumns['name'], database.name)
            model.set_value(it, self.treeDatabaseColumns['status'], self.databaseStatusNames[database.status] )
            model.set_value(it, self.treeDatabaseColumns['type'], database.display_name() )
            model.set_value(it, self.treeDatabaseColumns['_id'], self.databaseManager.database_id(database))


    def on_database_manager_database_activated(self, databaseManager, idDatabase):
        database = self.databaseManager.database_from_id(idDatabase)
        model = self.treeDatabases.get_model()
        for row in iter(model):
            if row[self.treeDatabaseColumns['_id']] == idDatabase:
                row[self.treeDatabaseColumns['status']] = self.databaseStatusNames[database.StatusActive]
                break
        else:
            raise ValueError('database not found')


    def on_database_manager_database_deactivated(self, databaseManager, idDatabase):
        database = self.databaseManager.database_from_id(idDatabase)
        model = self.treeDatabases.get_model()
        for row in iter(model):
            if row[self.treeDatabaseColumns['_id']] == idDatabase:
                row[self.treeDatabaseColumns['status']] = self.databaseStatusNames[database.StatusInactive]
                break
        else:
            raise ValueError('database not found')


    def on_button_database_activate_clicked(self, button):
        selection = self.treeDatabases.get_selection()
        if selection is None:
                return

        model, it = selection.get_selected()
        idDatabase = model.get_value(it, self.treeDatabaseColumns['_id'])
        database = self.databaseManager.database_from_id(idDatabase)
        self.databaseManager.activate_database(database)


    #TODO: for some reason i have to click OK/Cancel twice to close the dialog
    def on_button_database_new_clicked(self, button):
        databaseKlass = self.databaseManager.get_default_database_type()
        if databaseKlass is None:
            raise ValueError('no default database type set')
        database = databaseKlass()

        while True:
            dlg = DialogDatabaseProperties(
                    self.databaseManager,
                    database,
                    parent=self.parentWidget,
                    mode=WidgetDatabaseProperties.ModeNew,
                    title='New database'
                    )
            response = dlg.run()
            if response == gtk.RESPONSE_ACCEPT:
                database = dlg.get_widget_database_properties().get_database()
                #TODO: initing may or may not take a while. how to handle?
                error = database.init_new_database()
                if error:
                    DialogError(parent=dlg, msg=error)
                    dlg.destroy()
                    continue
            else:
                database = None
            dlg.destroy()
            break


            if database is None:
                return

            self.databaseManager.add_database(database)
            model = self.treeDatabases.get_model()
            it = model.append()
            model.set_value(it, self.treeDatabaseColumns['name'], database.name)
            model.set_value(it, self.treeDatabaseColumns['status'], self.databaseStatusNames[database.status] )
            model.set_value(it, self.treeDatabaseColumns['type'], database.display_name() )
            model.set_value(it, self.treeDatabaseColumns['_id'], self.databaseManager.database_id(database))


    def on_button_database_add_clicked(self, button):
        databaseKlass = self.databaseManager.get_default_database_type()
        if databaseKlass is None:
            raise ValueError('no defult database type set')
        database = databaseKlass()

        while True:
            dlg = DialogDatabaseProperties(
                    self.databaseManager,
                    database,
                    parent=self.parentWidget,
                    mode=WidgetDatabaseProperties.ModeAdd,
                    title='Add database'
                    )
            response = dlg.run()
            if response == gtk.RESPONSE_ACCEPT:
                database = dlg.get_widget_database_properties().get_database()
                #TODO: validating may or may not take a while. how to handle?
                error = database.validate_database()
                if error:
                    DialogError(parent=self.parentWidget, msg=error)
                    dlg.destroy()
                    continue
            else:
                database = None
            dlg.destroy()
            break

            if database is None:
                return

            self.databaseManager.add_database(database)
            model = self.treeDatabases.get_model()
            it = model.append()
            model.set_value(it, self.treeDatabaseColumns['name'], database.name)
            model.set_value(it, self.treeDatabaseColumns['status'], self.databaseStatusNames[database.status] )
            model.set_value(it, self.treeDatabaseColumns['type'], database.display_name() )
            model.set_value(it, self.treeDatabaseColumns['_id'], self.databaseManager.database_id(database))
        dlg.destroy()

    def on_button_database_edit_clicked(self, button):
        selection = self.treeDatabases.get_selection()
        if selection is None:
                return

        model, it = selection.get_selected()
        idDatabase = model.get_value(it, self.treeDatabaseColumns['_id'])
        database = self.databaseManager.database_from_id(idDatabase)
        dlg = DialogDatabaseProperties(
                self.databaseManager,
                database,
                parent=self.parentWidget,
                mode=WidgetDatabaseProperties.ModeEdit,
                title='Edit database'
                )
        response = dlg.run()
        if response == gtk.RESPONSE_REJECT:
            pass
        elif response == gtk.RESPONSE_ACCEPT:
            database = dlg.get_database()
            selection = self.treeDatabases.get_selection()
            if selection is not None:
                model, it = selection.get_selected()
                model.set_value(it, self.treeDatabaseColumns['name'], database.name)
        dlg.destroy()


    def on_button_database_remove_clicked(self, button):
        selection = self.treeDatabases.get_selection()
        if selection is None:
                return

        model, it = selection.get_selected()
        #TODO: finalize database
        model.remove(it)


    def on_tree_databases_selection_changed(self, treeSelection):
        hasSelection = bool(treeSelection.count_selected_rows())

        # enable/disable selection dependend widgets
        self.buttonDatabaseActivate.set_sensitive(hasSelection)
        self.buttonDatabaseEdit.set_sensitive(hasSelection)
        self.buttonDatabaseRemove.set_sensitive(hasSelection)
        #self.buttonDatabaseDelete.set_sensitive(hasSelection)


class DialogDatabaseManager(gtk.Dialog):
    def __init__(self, databaseManager, parent=None):
        gtk.Dialog.__init__(self,
        title="Databases",
                parent=parent,
                flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons=(
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                        ))
        #self.set_size_request(260, 250)
        self.widgetDatabaseManager = WidgetDatabaseManager(databaseManager, parentWidget=self)
        self.vbox.pack_start(self.widgetDatabaseManager, True, True)
        self.show_all()

#**************************************************************************************************
if __name__ == '__main__':
    databaseManager = DatabaseManager.from_fpdb('', defaultDatabaseType=DatabaseTypeSqLite)

    #d = DialogDatabaseProperties(
    #        DatabaseManager(defaultDatabaseType=DatabaseTypeSqLite),
            #database=DatabaseTypePostgres(),
    #        database=None,
    #        )
    d = DialogDatabaseManager(databaseManager)
    d.connect("destroy", gtk.main_quit)
    d.run()
    #gtk.main()
