
import os
import pygtk
pygtk.require('2.0')
import gtk

#*******************************************************************************************************
class DatabaseManager(object):
    DatabaseTypes = {}
    
    @classmethod
    def from_fpdb(klass, data, defaultDatabaseType=None):
        #TODO: parse whatever data is
        databases = (
                DatabaseTypeSqLite(name='myDb'),
                DatabaseTypeSqLite(name='myDb2'),
                
                )
        return klass(databases=databases, defaultDatabaseType=defaultDatabaseType)
    
    
    def __init__(self, databases=None, defaultDatabaseType=None):
        self._defaultDatabaseType = defaultDatabaseType
        self._databases = [] if databases is None else list(databases)
    def __iter__(self):
        return iter(self._databases)
    def set_default_database_type(self, databaseType):
        self._defaultDatabaseType = defaultDatabaseType
    def get_default_database_type(self):
        return self._defaultDatabaseType
    def database_from_id(self, idDatabase):
        for database in self._databases:
            if idDatabase == id(database):
                return database
    def database_id(self, database):
        return id(database)
    def add_database(self, database):
        if database in self._databases:
            raise ValueError('database already registered')
        self._databases.append(database)
    def remove_database(self, database):
        self._databases.remove(database)

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
    Params = ()

class DatabaseTypePostgres(DatabaseTypeBase):
    Type = 'postgres'
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

class DatabaseTypeSqLite(DatabaseTypeBase):
    Type = 'sqlite'
    @classmethod
    def display_name(klass):
        return 'SqLite'
    def __init__(self, name='', host='', file=''):
        self.name = name
        self.file = file

#TODO: how do we want to handle unsupported database types?
# ..uncomment to remove unsupported database types
#try: import psycopg2
#except ImportError: del DatabaseManager.DatabaseTypes['postgres']
#try: import MySQLdb
#except ImportError: del DatabaseManager.DatabaseTypes['mysql']
#try: import sqlite3
#except ImportError: del DatabaseManager.DatabaseTypes['sqlite']

#***************************************************************************************************************************
class MyFileChooserButton(gtk.HBox):
    #NOTE: for some weird reason it is impossible to let the user choose a non exiting filename with gtk.FileChooserButton, so impl our own on the fly
    def __init__(self):
        gtk.HBox.__init__(self)
        self.set_homogeneous(False)
        
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
        dlg = gtk.FileChooserDialog(
                title='Choose an exiting database file or type in name of a new one', 
                parent=None, 
                action=gtk.FILE_CHOOSER_ACTION_SAVE, 
                buttons=(
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_OK,
                        ), 
                backend=None
                )
        dlg.connect('confirm-overwrite', self.on_dialog_confirm_overwrite)
        dlg.set_default_response(gtk.RESPONSE_OK)
        dlg.set_do_overwrite_confirmation(True)
        if dlg.run() == gtk.RESPONSE_OK:
            self.set_filename(dlg.get_filename())
        dlg.destroy()
        
    #TODO: when the user selects a sqLite database file we got three possible actions
    #    1. user types in a new filename. easy one, create the file
    #    2. user selectes a file with the intention to overwrite it
    #    3. user selects a file with the intention to plug an existing database file in
    #
    # if we create a new one, choice is create_new or overwrite
    # if we add a database we may have to sanity check user picked one
    def on_dialog_confirm_overwrite(self, dlg):
        print dlg.get_filename()
        
        gtk.FILE_CHOOSER_CONFIRMATION_CONFIRM
        #The file chooser will present its stock dialog to confirm overwriting an existing file.

        gtk.FILE_CHOOSER_CONFIRMATION_ACCEPT_FILENAME
        #The file chooser will terminate and accept the user's choice of a file name.

        gtk.FILE_CHOOSER_CONFIRMATION_SELECT_AGAIN
        #
        

#TODO: derrive from gtk.VBox?
class WidgetDatabaseProperties(gtk.VBox):
        
    ModeNew = 0
    ModeEdit = 1
    ModeAdd = 2
    
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
        
    def __init__(self, databaseManager, database, mode=ModeEdit):
            gtk.VBox.__init__(self)
                        
            self.databaseManager = databaseManager
            self.database = database
            self.mode = mode
                
            self.fieldWidgets = (
                        self.FieldWidget(
                                text='Name:',
                                attrDatabase='name', 
                                widget=gtk.Entry(),
                                defaultValue='',
                                attrGet='get_text', 
                                attrSet='set_text', 
                                canEdit=True,
                                tooltip=''
                        ),
                        self.FieldWidget(
                            text='File:', 
                            attrDatabase='file', 
                            widget=MyFileChooserButton(), 
                            defaultValue='',
                            attrGet='get_filename', 
                            attrSet='set_filename', 
                            canEdit=False, 
                            tooltip=''
                        ),
                        self.FieldWidget(
                            text='Host:', 
                            attrDatabase='host', 
                            widget=gtk.Entry(), 
                            defaultValue='',
                            attrGet='get_text', 
                            attrSet='set_text', 
                            canEdit=False, 
                            tooltip=''
                        ),
                        self.FieldWidget(
                            text='Port:', 
                            attrDatabase='port', 
                            widget=gtk.SpinButton(adjustment=gtk.Adjustment(value=0, lower=0, upper=999999, step_incr=1, page_incr=10) ), 
                            defaultValue=0,
                            attrGet='get_value', 
                            attrSet='set_value', 
                            canEdit=False, 
                            tooltip=''
                        ),
                        self.FieldWidget(
                            text='User:', 
                            attrDatabase='user', 
                            widget=gtk.Entry(), 
                            defaultValue='',
                            attrGet='get_text', 
                            attrSet='set_text', 
                            canEdit=False, 
                            tooltip=''
                        ),
                        self.FieldWidget(
                            text='Pwd:', 
                            attrDatabase='password', 
                            widget=gtk.Entry(), 
                            defaultValue='',
                            attrGet='get_text', 
                            attrSet='set_text', 
                            canEdit=False, 
                            tooltip=''
                        ),
                        self.FieldWidget(
                            text='Db:', 
                            attrDatabase='database', 
                            widget=gtk.Entry(), 
                            defaultValue='',
                            attrGet='get_text', 
                            attrSet='set_text', 
                            canEdit=False,
                            tooltip=''
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
        self.widgetDatabaseProperties = WidgetDatabaseProperties(databaseManager,database, mode=mode)
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
    def __init__(self, databaseManager, parentWidget=None):
        gtk.VBox.__init__(self)
        
        self.databaseManager = databaseManager
        self.parentWidget = parentWidget
            
        #TODO: dono how to make word wrap work as expected
        self.labelInfo = gtk.Label('database management')
        self.labelInfo.set_line_wrap(True)
        self.labelInfo.set_selectable(True)
        self.labelInfo.set_single_line_mode(False)
        self.labelInfo.set_alignment(0, 0)
        
        # database management buttons
        
        #TODO: bit messy the distinction New/Add/Edit. we'd have to pass three flags to DialogDatabaseProperties
        # to handle this. maybe drop Edit (is just a Remove + Add), to keep things simple
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
        
        #TODO: i dont think we should do any real database management here. maybe drop it
        self.buttonDatabaseDelete = gtk.Button("Delete")
        self.buttonDatabaseDelete.set_tooltip_text('removes the database from the list and deletes it')
        self.buttonDatabaseDelete.set_sensitive(False)
            
        # init database tree        
        self.treeDatabases = gtk.TreeView()
        self.treeDatabaseColumns = (        #NOTE: column names starting with '_' will be hidden
                'Name', 
                'Status', 
                'Type', 
                '_id',
                )
        
        store = gtk.ListStore(str, str, str, int)
        self.treeDatabases.set_model(store)
        columns = ('Name', 'Status', 'Type', '_id')
        for i, column in enumerate(columns):
            col = gtk.TreeViewColumn(column, gtk.CellRendererText(), text=i)
            self.treeDatabases.append_column(col)
            if column.startswith('_'):
                col.set_visible(False)
        
        self.treeDatabaseColumns = dict([(name, i) for (i, name) in enumerate(self.treeDatabaseColumns)])
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
        vbox.pack_start(self.buttonDatabaseNew, False, False, 2)
        vbox.pack_start(self.buttonDatabaseAdd, False, False, 2)
        vbox.pack_start(self.buttonDatabaseEdit, False, False, 2)
        vbox.pack_start(self.buttonDatabaseRemove, False, False, 2)
        vbox.pack_start(self.buttonDatabaseDelete, False, False, 2)
        box = gtk.VBox()
        vbox.pack_start(box, True, True, 0)
        
        hbox.pack_start(gtk.VSeparator(), False, False, 2)
        hbox.pack_end(self.treeDatabases, True, True, 2)
        
        self.show_all()
        
        # init widget
        for database in self.databaseManager:
            self.treeDatabases.get_model().append( (database.name, 'foo', database.Type, self.databaseManager.database_id(database)) )
        
    #TODO: for some reason i have to click OK/Cancel twice to close the dialog        
    def on_button_database_new_clicked(self, button):
        databaseType = self.databaseManager.get_default_database_type()
        if databaseType is None:
            raise ValueError('no defult database type set')
        dlg = DialogDatabaseProperties(
                self.databaseManager, 
                databaseType(), 
                parent=self.parentWidget, 
                mode=WidgetDatabaseProperties.ModeNew,
                title='[New database] - database properties'
                )
        if dlg.run() == gtk.RESPONSE_REJECT:
            pass
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            database = dlg.get_widget_database_properties().get_database()
            #TODO: sanity checks + init databse if necessary
            self.databaseManager.add_database(database)
            self.treeDatabases.get_model().append( (database.name, 'foo', database.Type, self.databaseManager.database_id(database)) )
        dlg.destroy()

    def on_button_database_add_clicked(self, button):
        databaseType = self.databaseManager.get_default_database_type()
        if databaseType is None:
            raise ValueError('no defult database type set')
        dlg = DialogDatabaseProperties(
                self.databaseManager, 
                databaseType(), 
                parent=self.parentWidget, 
                mode=WidgetDatabaseProperties.ModeAdd,
                title='[Add database] - database properties'
                )
        if dlg.run() == gtk.RESPONSE_REJECT:
            pass
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            database = dlg.get_widget_database_properties().get_database()
            #TODO: sanity checks
            self.databaseManager.add_database(database)
            self.treeDatabases.get_model().append( (database.name, 'foo', database.Type, self.databaseManager.database_id(database)) )
        dlg.destroy()
        
    def on_button_database_edit_clicked(self, button):
        selection = self.treeDatabases.get_selection()
        if selection is None:
                return
                
        model, iter = selection.get_selected()
        idDatabase = model.get_value(iter, self.treeDatabaseColumns['_id'])
        database = self.databaseManager.database_from_id(idDatabase)
        dlg = DialogDatabaseProperties(
                self.databaseManager, 
                database=database, 
                parent=self.parentWidget, 
                mode=WidgetDatabaseProperties.ModeEdit, 
                title='[Edit database] - database properties'
                )
        if dlg.run() == gtk.RESPONSE_REJECT:
            pass
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            database = dlg.get_database()
            selection = self.treeDatabases.get_selection()
            if selection is not None:
                model, iter = selection.get_selected()
                model.set_value(iter, 0, database.name)
        dlg.destroy()

    def on_tree_databases_selection_changed(self, treeSelection):
        hasSelection = bool(treeSelection.count_selected_rows())
        
            # enable/disable selection dependend widgets
        self.buttonDatabaseEdit.set_sensitive(hasSelection)
        self.buttonDatabaseRemove.set_sensitive(hasSelection)
        self.buttonDatabaseDelete.set_sensitive(hasSelection)
        

class DialogDatabaseManager(gtk.Dialog):
    def __init__(self, databaseManager, parent=None):
        gtk.Dialog.__init__(self,
        title="My dialog", 
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


