#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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

import os
import sys
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-x", "--errorsToConsole", action="store_true",
                help="If passed error output will go to the console rather than .")
parser.add_option("-d", "--databaseName", dest="dbname", default="fpdb",
                help="Overrides the default database name")
(options, sys.argv) = parser.parse_args()

if not options.errorsToConsole:
    print "Note: error output is being diverted to fpdb-error-log.txt and HUD-error.txt. Any major error will be reported there _only_."
    errorFile = open('fpdb-error-log.txt', 'w', 0)
    sys.stderr = errorFile

import pygtk
pygtk.require('2.0')
import gtk

import fpdb_db
import fpdb_simple
import GuiBulkImport
import GuiPlayerStats
import GuiPositionalStats
import GuiTableViewer
import GuiAutoImport
import GuiGraphViewer
import FpdbSQLQueries
import Configuration

VERSION = "0.11"

class fpdb:
    def tab_clicked(self, widget, tab_name):
        """called when a tab button is clicked to activate that tab"""
        #print "start of tab_clicked"
        self.display_tab(tab_name)
    #end def tab_clicked

    def add_and_display_tab(self, new_tab, new_tab_name):
        """just calls the component methods"""
        self.add_tab(new_tab, new_tab_name)
        self.display_tab(new_tab_name)
    #end def add_and_display_tab

    def add_tab(self, new_tab, new_tab_name):
        """adds a tab, namely creates the button and displays it and appends all the relevant arrays"""
        #print "start of add_tab"
        for i in self.tab_names: #todo: check this is valid
            if i==new_tab_name:
                return # we depend on this to not create duplicate tabs, there's no reason to raise an error here?
#                raise fpdb_simple.FpdbError("duplicate tab_name not permitted")

        self.tabs.append(new_tab)
        self.tab_names.append(new_tab_name)

        new_tab_sel_button=gtk.ToggleButton(new_tab_name)
        new_tab_sel_button.connect("clicked", self.tab_clicked, new_tab_name)
        self.tab_box.add(new_tab_sel_button)
        new_tab_sel_button.show()
        self.tab_buttons.append(new_tab_sel_button)
    #end def add_tab

    def display_tab(self, new_tab_name):
        """displays the indicated tab"""
        #print "start of display_tab, len(self.tab_names):",len(self.tab_names)
        tab_no = -1
        for i, name in enumerate(self.tab_names):
            if name == new_tab_name:
                tab_no = i
                break

        if tab_no == -1:
            raise fpdb_simple.FpdbError("invalid tab_no")
        else:
            self.main_vbox.remove(self.current_tab)
            #self.current_tab.destroy()
            self.current_tab=self.tabs[tab_no]
            self.main_vbox.add(self.current_tab)
            self.tab_buttons[tab_no].set_active(True)
            self.current_tab.show()
    #end def display_tab

    def delete_event(self, widget, event, data=None):
        return False
    #end def delete_event

    def destroy(self, widget, data=None):
        self.quit(widget, data)
    #end def destroy

    def dia_about(self, widget, data):
        print "todo: implement dia_about",
        print " version = %s, requires database version %s" % (VERSION, "118")
    #end def dia_about

    def dia_create_del_database(self, widget, data):
        print "todo: implement dia_create_del_database"
        self.obtain_global_lock()
    #end def dia_create_del_database

    def dia_create_del_user(self, widget, data):
        print "todo: implement dia_create_del_user"
        self.obtain_global_lock()
    #end def dia_create_del_user

    def dia_database_stats(self, widget, data):
        print "todo: implement dia_database_stats"
        #string=fpdb_db.getDbStats(db, cursor)
    #end def dia_database_stats

    def dia_delete_db_parts(self, widget, data):
        print "todo: implement dia_delete_db_parts"
        self.obtain_global_lock()
    #end def dia_delete_db_parts

    def dia_edit_profile(self, widget=None, data=None, create_default=False, path=None):
        print "todo: implement dia_edit_profile"
        self.obtain_global_lock()
    #end def dia_edit_profile

    def dia_export_db(self, widget, data):
        print "todo: implement dia_export_db"
        self.obtain_global_lock()
    #end def dia_export_db

    def dia_get_db_root_credentials(self):
        """obtains db root credentials from user"""
        print "todo: implement dia_get_db_root_credentials"
#        user, pw=None, None
#        
#        dialog=gtk.Dialog(title="DB Credentials needed", parent=None, flags=0,
#                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,"Connect and recreate",gtk.RESPONSE_OK))
#        
#        label_warning1=gtk.Label("Please enter credentials for a database user for "+self.host+" that has permissions to create a database.")
#        
#        
#        label_user=gtk.Label("Username")
#        dialog.vbox.add(label_user)
#        label_user.show()
#        
#        response=dialog.run()
#        dialog.destroy()
#        return (user, pw, response)
    #end def dia_get_db_root_credentials

    def dia_import_db(self, widget, data):
        print "todo: implement dia_import_db"
        self.obtain_global_lock()
    #end def dia_import_db

    def dia_licensing(self, widget, data):
        print "todo: implement dia_licensing"
    #end def dia_licensing

    def dia_load_profile(self, widget, data):
        """Dialogue to select a file to load a profile from"""
        self.obtain_global_lock()
        chooser = gtk.FileChooserDialog(title="Please select a profile file to load",
                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_filename(self.profile)

        response = chooser.run()
        chooser.destroy()    
        if response == gtk.RESPONSE_OK:
            self.load_profile(chooser.get_filename())
        elif response == gtk.RESPONSE_CANCEL:
            print 'User cancelled loading profile'
    #end def dia_load_profile

    def dia_recreate_tables(self, widget, data):
        """Dialogue that asks user to confirm that he wants to delete and recreate the tables"""
        self.obtain_global_lock()
        
        dia_confirm = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_WARNING,
                buttons=(gtk.BUTTONS_YES_NO), message_format="Confirm deleting and recreating tables")
        diastring = "Please confirm that you want to (re-)create the tables. If there already are tables in the database "+self.db.database+" on "+self.db.host+" they will be deleted."
        dia_confirm.format_secondary_text(diastring)#todo: make above string with bold for db, host and deleted

        response = dia_confirm.run()
        dia_confirm.destroy()
        if response == gtk.RESPONSE_YES:
            self.db.recreate_tables()
        elif response == gtk.RESPONSE_NO:
            print 'User cancelled recreating tables'
    #end def dia_recreate_tables

    def dia_regression_test(self, widget, data):
        print "todo: implement dia_regression_test"
        self.obtain_global_lock()
    #end def dia_regression_test

    def dia_save_profile(self, widget, data):
        print "todo: implement dia_save_profile"
    #end def dia_save_profile

    def diaSetupWizard(self, path):
        print "todo: implement setup wizard"
        print "setup wizard not implemented - please create the default configuration file:", path    
        diaSetupWizard = gtk.Dialog(title="Fatal Error - Config File Missing", parent=None, flags=0, buttons=(gtk.STOCK_QUIT,gtk.RESPONSE_OK))

        label = gtk.Label("Please copy the config file from the docs folder to:")
        diaSetupWizard.vbox.add(label)
        label.show()

        label = gtk.Label(path)
        diaSetupWizard.vbox.add(label)
        label.show()

        label = gtk.Label("and edit it according to the install documentation at http://fpdb.sourceforge.net")
        diaSetupWizard.vbox.add(label)
        label.show()

        response = diaSetupWizard.run()
        sys.exit(1)
    #end def diaSetupWizard

    def get_menu(self, window):
        """returns the menu for this program"""
        accel_group = gtk.AccelGroup()
        self.item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
        self.item_factory.create_items(self.menu_items)
        window.add_accel_group(accel_group)
        return self.item_factory.get_widget("<main>")
    #end def get_menu

    def load_profile(self):
        """Loads profile from the provided path name."""
        self.settings = {}
        if (os.sep=="/"):
            self.settings['os']="linuxmac"
        else:
            self.settings['os']="windows"

        self.settings.update(self.config.get_db_parameters())
        self.settings.update(self.config.get_tv_parameters())
        self.settings.update(self.config.get_import_parameters())
        self.settings.update(self.config.get_default_paths())

        if self.db!=None:
            self.db.disconnect()

        self.db = fpdb_db.fpdb_db()
        #print "end of fpdb.load_profile, databaseName:",self.settings['db-databaseName']
        self.db.connect(self.settings['db-backend'],
            self.settings['db-host'],
            self.settings['db-databaseName'],
            self.settings['db-user'], 
            self.settings['db-password'])
<<<<<<< HEAD:pyfpdb/fpdb.py
        if self.db.wrongDbVersion:
            diaDbVersionWarning = gtk.Dialog(title="Strong Warning - Invalid database version", parent=None, flags=0, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))

            label = gtk.Label("An invalid DB version or missing tables have been detected.")
            diaDbVersionWarning.vbox.add(label)
            label.show()

            label = gtk.Label("This error is not necessarily fatal but it is strongly recommended that you recreate the tables by using the Database menu.")
            diaDbVersionWarning.vbox.add(label)
            label.show()

            label = gtk.Label("Not doing this will likely lead to misbehaviour including fpdb crashes, corrupt data etc.")
            diaDbVersionWarning.vbox.add(label)
            label.show()

            response = diaDbVersionWarning.run()
            diaDbVersionWarning.destroy()

        # Database connected to successfully, load queries to pass on to other classes
        self.querydict = FpdbSQLQueries.FpdbSQLQueries(self.db.get_backend_name())
        self.db.db.rollback()
    #end def load_profile

    def not_implemented(self):
        print "todo: called unimplemented menu entry (users: pls ignore this)"#remove this once more entries are implemented
    #end def not_implemented

    def obtain_global_lock(self):
        print "todo: implement obtain_global_lock (users: pls ignore this)"
    #end def obtain_global_lock

    def quit(self, widget, data):
        print "Quitting normally"
        #check if current settings differ from profile, if so offer to save or abort
        self.db.disconnect()
        gtk.main_quit()
    #end def quit_cliecked

    def release_global_lock(self):
        print "todo: implement release_global_lock"
    #end def release_global_lock

    def tab_abbreviations(self, widget, data):
        print "todo: implement tab_abbreviations"
    #end def tab_abbreviations

    def tab_auto_import(self, widget, data):
        """opens the auto import tab"""
        new_aimp_thread=GuiAutoImport.GuiAutoImport(self.settings, self.config)
        self.threads.append(new_aimp_thread)
        aimp_tab=new_aimp_thread.get_vbox()
        self.add_and_display_tab(aimp_tab, "Auto Import")
    #end def tab_auto_import

    def tab_bulk_import(self, widget, data):
        """opens a tab for bulk importing"""
        #print "start of tab_bulk_import"
        new_import_thread=GuiBulkImport.GuiBulkImport(self.db, self.settings, self.config)
        self.threads.append(new_import_thread)
        bulk_tab=new_import_thread.get_vbox()
        self.add_and_display_tab(bulk_tab, "Bulk Import")
    #end def tab_bulk_import

    def tab_player_stats(self, widget, data):
        new_ps_thread=GuiPlayerStats.GuiPlayerStats(self.db, self.config, self.querydict)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Player Stats")

    def tab_positional_stats(self, widget, data):
        new_ps_thread=GuiPositionalStats.GuiPositionalStats(self.db, self.config, self.querydict)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Positional Stats")


    def tab_main_help(self, widget, data):
        """Displays a tab with the main fpdb help screen"""
        #print "start of tab_main_help"
        mh_tab=gtk.Label("""Welcome to Fpdb!
For documentation please visit our website at http://fpdb.sourceforge.net/ or check the docs directory in the fpdb folder.
Please note that default.conf is no longer needed nor used, all configuration now happens in HUD_config.xml
This program is licensed under the AGPL3, see docs"""+os.sep+"agpl-3.0.txt")
        self.add_and_display_tab(mh_tab, "Help")
    #end def tab_main_help

    def tab_table_viewer(self, widget, data):
        """opens a table viewer tab"""
        #print "start of tab_table_viewer"
        new_tv_thread=GuiTableViewer.GuiTableViewer(self.db, self.settings)
        self.threads.append(new_tv_thread)
        tv_tab=new_tv_thread.get_vbox()
        self.add_and_display_tab(tv_tab, "Table Viewer")
    #end def tab_table_viewer

    def tabGraphViewer(self, widget, data):
        """opens a graph viewer tab"""
        #print "start of tabGraphViewer"
        new_gv_thread=GuiGraphViewer.GuiGraphViewer(self.db, self.settings, self.querydict, self.config)
        self.threads.append(new_gv_thread)
        gv_tab=new_gv_thread.get_vbox()
        self.add_and_display_tab(gv_tab, "Graphs")
    #end def tabGraphViewer

    def __init__(self):
        self.threads=[]
        self.db=None
        self.config = Configuration.Config(dbname=options.dbname)
        self.load_profile()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_title("Free Poker DB - v%s or higher" % (VERSION, ))
        self.window.set_border_width(1)
        self.window.set_default_size(900,720)
        self.window.set_resizable(True)

        self.menu_items = (
                ( "/_Main",                                 None,         None, 0, "<Branch>" ),
                ( "/Main/_Load Profile (broken)",                    "<control>L", self.dia_load_profile, 0, None ),
                ( "/Main/_Edit Profile (todo)",                    "<control>E", self.dia_edit_profile, 0, None ),
                ( "/Main/_Save Profile (todo)",                    None,         self.dia_save_profile, 0, None ),
                ("/Main/sep1", None, None, 0, "<Separator>" ),
                ("/Main/_Quit", "<control>Q", self.quit, 0, None ),
                ("/_Import",                               None,         None, 0, "<Branch>" ),
                ("/Import/_Bulk Import",  "<control>B", self.tab_bulk_import, 0, None ),
                ("/Import/_Auto Import and HUD", "<control>A", self.tab_auto_import, 0, None ),
                ("/Import/Auto _Rating (todo)",                   "<control>R", self.not_implemented, 0, None ),
                ("/_Viewers", None, None, 0, "<Branch>" ),
                ("/_Viewers/_Auto Import and HUD", "<control>A", self.tab_auto_import, 0, None ),
                ("/Viewers/_Graphs", "<control>G", self.tabGraphViewer, 0, None ),
                ("/Viewers/Hand _Replayer (todo)", None, self.not_implemented, 0, None ),
                ("/Viewers/Player _Details (todo)", None, self.not_implemented, 0, None ),
                ("/Viewers/_Player Stats (tabulated view)", None, self.tab_player_stats, 0, None ),
                ("/Viewers/Positional Stats (tabulated view)", None, self.tab_positional_stats, 0, None ),
                ("/Viewers/Starting _Hands (todo)", None, self.not_implemented, 0, None ),
                ("/Viewers/_Session Replayer (todo)", None, self.not_implemented, 0, None ),
                ("/Viewers/Poker_table Viewer (mostly obselete)", "<control>T", self.tab_table_viewer, 0, None ),
                #( "/Viewers/Tourney Replayer
                ( "/_Database",                             None,         None, 0, "<Branch>" ),
                ( "/Database/Create or Delete _Database (todo)",   None,         self.dia_create_del_database, 0, None ),
                ( "/Database/Create or Delete _User (todo)",       None,         self.dia_create_del_user, 0, None ),
                ( "/Database/Create or Recreate _Tables",   None,         self.dia_recreate_tables, 0, None ),
                ( "/Database/_Statistics (todo)",                  None,         self.dia_database_stats, 0, None ),
                ( "/D_ebugging",                            None,         None, 0, "<Branch>" ),
                ( "/Debugging/_Delete Parts of Database (todo)",   None,         self.dia_delete_db_parts, 0, None ),
                ( "/Debugging/_Export DB (todo)",                  None,         self.dia_export_db, 0, None ),
                ( "/Debugging/_Import DB (todo)",                  None,         self.dia_import_db, 0, None ),
                ( "/Debugging/_Regression test (todo)",            None,         self.dia_regression_test, 0, None ),
                ( "/_Help",                                 None,         None, 0, "<LastBranch>" ),
                ( "/Help/_Main Help",                       "<control>H", self.tab_main_help, 0, None ),
                ( "/Help/_Abbrevations (todo)",                    None,         self.tab_abbreviations, 0, None ),
                ( "/Help/sep1",                             None,         None, 0, "<Separator>" ),
                ( "/Help/A_bout (todo)",                           None,         self.dia_about, 0, None ),
                ( "/Help/_License and Copying (todo)",             None,         self.dia_licensing, 0, None )
        )

        self.main_vbox = gtk.VBox(False, 1)
        self.main_vbox.set_border_width(1)
        self.window.add(self.main_vbox)
        self.main_vbox.show()

        menubar = self.get_menu(self.window)
        self.main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        #done menubar

        self.tabs=[]
        self.tab_names=[]
        self.tab_buttons=[]
        self.tab_box = gtk.HBox(False,1)
        self.main_vbox.pack_start(self.tab_box, False, True, 0)
        self.tab_box.show()
        #done tab bar

        self.current_tab = gtk.VBox(False,1)
        self.current_tab.set_border_width(1)
        self.main_vbox.add(self.current_tab)
        self.current_tab.show()

        self.tab_main_help(None, None)

        self.status_bar = gtk.Label("Status: Connected to %s database named %s on host %s"%(self.db.get_backend_name(),self.db.database, self.db.host))
        self.main_vbox.pack_end(self.status_bar, False, True, 0)
        self.status_bar.show()

        self.window.show()
    #end def __init__

    def main(self):
        gtk.main()
        return 0
    #end def main

if __name__ == "__main__":
    me = fpdb()
    me.main()
