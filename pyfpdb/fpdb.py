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
import re

# if path is set to use an old version of python look for a new one:
# (does this work in linux?)
if os.name == 'nt' and sys.version[0:3] not in ('2.5', '2.6') and '-r' not in sys.argv:
    #print "old path =", os.environ['PATH']
    dirs = re.split(os.pathsep, os.environ['PATH'])
    # remove any trailing / or \ chars from dirs:
    dirs = [re.sub('[\\/]$','',p) for p in dirs]
    # remove any dirs containing 'python' apart from those ending in 'python25', 'python26' or 'python':
    dirs = [p for p in dirs if not re.search('python', p, re.I) or re.search('python25$', p, re.I) or re.search('python26$', p, re.I)]
    tmppath = ";".join(dirs)
    #print "new path =", tmppath
    if re.search('python', tmppath, re.I):
        os.environ['PATH'] = tmppath
        print "Python " + sys.version[0:3] + ' - press return to continue\n'
        sys.stdin.readline()
        os.execvpe('python.exe', ('python.exe', 'fpdb.py', '-r'), os.environ) # first arg is ignored (name of program being run)
    else:
        print "\npython 2.5 not found, please install python 2.5 or 2.6 for fpdb\n"
        exit
else:
    pass
    #print "debug - not changing path"

print "Python " + sys.version[0:3] + '...\n'

import threading
import Options
import string
cl_options = string.join(sys.argv[1:])
(options, sys.argv) = Options.fpdb_options()

if not options.errorsToConsole:
    print "Note: error output is being diverted to fpdb-error-log.txt and HUD-error.txt. Any major error will be reported there _only_."
    errorFile = open('fpdb-error-log.txt', 'w', 0)
    sys.stderr = errorFile

import logging

import pygtk
pygtk.require('2.0')
import gtk

import interlocks


import fpdb_simple
import GuiBulkImport
import GuiPlayerStats
import GuiPositionalStats
import GuiTableViewer
import GuiAutoImport
import GuiGraphViewer
import GuiSessionViewer
import SQL
import Database
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
        self.quit(widget)
    #end def destroy

    def dia_about(self, widget, data=None):
        print "todo: implement dia_about",
        print " version = %s, requires database version %s" % (VERSION, "118")
    #end def dia_about

    def dia_create_del_database(self, widget, data=None):
        print "todo: implement dia_create_del_database"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_create_del_database

    def dia_create_del_user(self, widget, data=None):
        print "todo: implement dia_create_del_user"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_create_del_user

    def dia_database_stats(self, widget, data=None):
        print "todo: implement dia_database_stats"
        #string=fpdb_db.getDbStats(db, cursor)
    #end def dia_database_stats

    def dia_database_sessions(self, widget, data=None):
        new_sessions_thread=GuiSessionViewer.GuiSessionViewer(self.config, self.sql)
        self.threads.append(new_sessions_thread)
        sessions_tab=new_sessions_thread.get_vbox()
        self.add_and_display_tab(sessions_tab, "Sessions")

    def dia_delete_db_parts(self, widget, data=None):
        print "todo: implement dia_delete_db_parts"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_delete_db_parts

    def dia_edit_profile(self, widget=None, data=None, create_default=False, path=None):
        print "todo: implement dia_edit_profile"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_edit_profile

    def dia_export_db(self, widget, data=None):
        print "todo: implement dia_export_db"
        self.obtain_global_lock()
        self.release_global_lock()
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

    def dia_import_db(self, widget, data=None):
        print "todo: implement dia_import_db"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_import_db

    def dia_licensing(self, widget, data=None):
        print "todo: implement dia_licensing"
    #end def dia_licensing

    def dia_load_profile(self, widget, data=None):
        """Dialogue to select a file to load a profile from"""
        if self.obtain_global_lock():  # returns true if successful
            #try:
            #    chooser = gtk.FileChooserDialog(title="Please select a profile file to load",
            #            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            #            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
            #    chooser.set_filename(self.profile)

            #    response = chooser.run()
            #    chooser.destroy()    
            #    if response == gtk.RESPONSE_OK:
            #        self.load_profile(chooser.get_filename())
            #    elif response == gtk.RESPONSE_CANCEL:
            #        print 'User cancelled loading profile'
            #except:
            #    pass
            #try:
            self.load_profile()
            #except:
            #    pass
            self.release_global_lock()
    #end def dia_load_profile

    def dia_recreate_tables(self, widget, data=None):
        """Dialogue that asks user to confirm that he wants to delete and recreate the tables"""
        if self.obtain_global_lock():  # returns true if successful

            #lock_released = False
            try:
                dia_confirm = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_WARNING,
                        buttons=(gtk.BUTTONS_YES_NO), message_format="Confirm deleting and recreating tables")
                diastring = "Please confirm that you want to (re-)create the tables. If there already are tables in the database " \
                            +self.db.fdb.database+" on "+self.db.fdb.host+" they will be deleted."
                dia_confirm.format_secondary_text(diastring)#todo: make above string with bold for db, host and deleted

                response = dia_confirm.run()
                dia_confirm.destroy()
                if response == gtk.RESPONSE_YES:
                    #if self.db.fdb.backend == self.fdb_lock.fdb.MYSQL_INNODB:
                        # mysql requires locks on all tables or none - easier to release this lock 
                        # than lock all the other tables
                        # ToDo: lock all other tables so that lock doesn't have to be released
                    #    self.release_global_lock()
                    #    lock_released = True
                    self.db.recreate_tables()
                    #else:
                        # for other dbs use same connection as holds global lock
                    #    self.fdb_lock.fdb.recreate_tables()
                elif response == gtk.RESPONSE_NO:
                    print 'User cancelled recreating tables'
            except:
                pass
            #if not lock_released:
            self.release_global_lock()
    #end def dia_recreate_tables
    
    def dia_recreate_hudcache(self, widget, data=None):
        if self.obtain_global_lock():
            dia_confirm = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_WARNING, buttons=(gtk.BUTTONS_YES_NO), message_format="Confirm recreating HUD cache")
            diastring = "Please confirm that you want to re-create the HUD cache."
            dia_confirm.format_secondary_text(diastring)
            
            response = dia_confirm.run()
            dia_confirm.destroy()
            if response == gtk.RESPONSE_YES:
                self.db.rebuild_hudcache()
            elif response == gtk.REPSONSE_NO:
                print 'User cancelled rebuilding hud cache'
        self.release_global_lock()
    

    def dia_regression_test(self, widget, data=None):
        print "todo: implement dia_regression_test"
        self.obtain_global_lock()
        self.release_global_lock()
    #end def dia_regression_test

    def dia_save_profile(self, widget, data=None):
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
        fpdbmenu = """
            <ui>
              <menubar name="MenuBar">
                <menu action="main">
                  <menuitem action="LoadProf"/>
                  <menuitem action="EditProf"/>
                  <menuitem action="SaveProf"/>
                  <separator/>
                  <menuitem action="Quit"/>
                </menu>
                <menu action="import">
                  <menuitem action="bulkimp"/>
                  <menuitem action="autoimp"/>
                  <menuitem action="autorate"/>
                </menu>
                <menu action="viewers">
                  <menuitem action="autoimp"/>
                  <menuitem action="graphs"/>
                  <menuitem action="handreplay"/>
                  <menuitem action="playerdetails"/>
                  <menuitem action="playerstats"/>
                  <menuitem action="posnstats"/>
                  <menuitem action="sessionreplay"/>
                  <menuitem action="tableviewer"/>
                </menu>
                <menu action="database">
                  <menuitem action="createdb"/>
                  <menuitem action="createuser"/>
                  <menuitem action="createtabs"/>
                  <menuitem action="rebuildhudcache"/>
                  <menuitem action="stats"/>
                  <menuitem action="sessions"/>
                </menu>
                <menu action="help">
                  <menuitem action="Abbrev"/>
                  <separator/>
                  <menuitem action="About"/>
                  <menuitem action="License"/>
                </menu>
              </menubar>
            </ui>"""

        uimanager = gtk.UIManager()
        accel_group = uimanager.get_accel_group()
        actiongroup = gtk.ActionGroup('UIManagerExample')

        # Create actions
        actiongroup.add_actions([('main', None, '_Main'),
                                 ('Quit', gtk.STOCK_QUIT, '_Quit', None, 'Quit the Program', self.quit),
                                 ('LoadProf', None, '_Load Profile (broken)', '<control>L', 'Load your profile', self.dia_load_profile),
                                 ('EditProf', None, '_Edit Profile (todo)', '<control>E', 'Edit your profile', self.dia_edit_profile),
                                 ('SaveProf', None, '_Save Profile (todo)', '<control>S', 'Save your profile', self.dia_save_profile),
                                 ('import', None, '_Import'),
                                 ('bulkimp', None, '_Bulk Import', '<control>B', 'Bulk Import', self.tab_bulk_import),
                                 ('autorate', None, 'Auto _Rating (todo)', '<control>R', 'Auto Rating (todo)', self.not_implemented),
                                 ('viewers', None, '_Viewers'),
                                 ('autoimp', None, '_Auto Import and HUD', '<control>A', 'Auto Import and HUD', self.tab_auto_import),
                                 ('graphs', None, '_Graphs', '<control>G', 'Graphs', self.tabGraphViewer),
                                 ('handreplay', None, 'Hand _Replayer (todo)', None, 'Hand Replayer (todo)', self.not_implemented),
                                 ('playerdetails', None, 'Player _Details (todo)', None, 'Player Details (todo)', self.not_implemented),
                                 ('playerstats', None, '_Player Stats (tabulated view)', '<control>P', 'Player Stats (tabulated view)', self.tab_player_stats),
                                 ('posnstats', None, 'P_ositional Stats (tabulated view)', '<control>O', 'Positional Stats (tabulated view)', self.tab_positional_stats),
                                 ('sessionreplay', None, '_Session Replayer (todo)', None, 'Session Replayer (todo)', self.not_implemented),
                                 ('tableviewer', None, 'Poker_table Viewer (mostly obselete)', None, 'Poker_table Viewer (mostly obselete)', self.tab_table_viewer),
                                 ('database', None, '_Database'),
                                 ('createdb', None, 'Create or Delete _Database (todo)', None, 'Create or Delete Database', self.dia_create_del_database),
                                 ('createuser', None, 'Create or Delete _User (todo)', None, 'Create or Delete User', self.dia_create_del_user),
                                 ('createtabs', None, 'Create or Recreate _Tables', None, 'Create or Recreate Tables ', self.dia_recreate_tables),
                                 ('rebuildhudcache', None, 'Rebuild HUD Cache', None, 'Rebuild HUD Cache', self.dia_recreate_hudcache),
                                 ('stats', None, '_Statistics (todo)', None, 'View Database Statistics', self.dia_database_stats),
                                 ('sessions', None, 'Sessions', None, 'View Sessions', self.dia_database_sessions),
                                 ('help', None, '_Help'),
                                 ('Abbrev', None, '_Abbrevations (todo)', None, 'List of Abbrevations', self.tab_abbreviations),
                                 ('About', None, 'A_bout', None, 'About the program', self.dia_about),
                                 ('License', None, '_License and Copying (todo)', None, 'License and Copying', self.dia_licensing),
                                ])
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')

        uimanager.insert_action_group(actiongroup, 0)
        merge_id = uimanager.add_ui_from_string(fpdbmenu)

        # Create a MenuBar
        menubar = uimanager.get_widget('/MenuBar')
        window.add_accel_group(accel_group)
        return menubar
    #end def get_menu

    def load_profile(self):
        """Loads profile from the provided path name."""
        self.config = Configuration.Config(file=options.config, dbname=options.dbname)
        self.settings = {}
        self.settings['global_lock'] = self.lock
        if (os.sep=="/"):
            self.settings['os']="linuxmac"
        else:
            self.settings['os']="windows"

        self.settings.update({'cl_options': cl_options})
        self.settings.update(self.config.get_db_parameters())
        self.settings.update(self.config.get_tv_parameters())
        self.settings.update(self.config.get_import_parameters())
        self.settings.update(self.config.get_default_paths())

        if self.db != None and self.db.fdb != None:
            self.db.disconnect()

        self.sql = SQL.Sql(type = self.settings['db-type'], db_server = self.settings['db-server'])
        self.db = Database.Database(self.config, sql = self.sql)

        if self.db.fdb.wrongDbVersion:
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

        if self.status_bar == None:
            self.status_bar = gtk.Label("Status: Connected to %s database named %s on host %s"%(self.db.get_backend_name(),self.db.fdb.database, self.db.fdb.host))
            self.main_vbox.pack_end(self.status_bar, False, True, 0)
            self.status_bar.show()
        else:
            self.status_bar.set_text("Status: Connected to %s database named %s on host %s" % (self.db.get_backend_name(),self.db.fdb.database, self.db.fdb.host))

        # Database connected to successfully, load queries to pass on to other classes
        self.db.connection.rollback()
    #end def load_profile

    def not_implemented(self, widget, data=None):
        print "todo: called unimplemented menu entry (users: pls ignore this)"#remove this once more entries are implemented
    #end def not_implemented

    def obtain_global_lock(self):
        ret = self.lock.acquire(False) # will return false if lock is already held
        if ret:
            print "\nGlobal lock taken ..."
        else:
            print "\nFailed to get global lock."
        return ret
        # need to release it later:
        # self.lock.release()

    #end def obtain_global_lock

    def quit(self, widget, data=None):
        print "Quitting normally"
        #check if current settings differ from profile, if so offer to save or abort
        self.db.disconnect()
        gtk.main_quit()
    #end def quit_cliecked

    def release_global_lock(self):
        self.lock.release()
        print "Global lock released.\n"
    #end def release_global_lock

    def tab_abbreviations(self, widget, data=None):
        print "todo: implement tab_abbreviations"
    #end def tab_abbreviations

    def tab_auto_import(self, widget, data=None):
        """opens the auto import tab"""
        new_aimp_thread=GuiAutoImport.GuiAutoImport(self.settings, self.config)
        self.threads.append(new_aimp_thread)
        aimp_tab=new_aimp_thread.get_vbox()
        self.add_and_display_tab(aimp_tab, "Auto Import")
    #end def tab_auto_import

    def tab_bulk_import(self, widget, data=None):
        """opens a tab for bulk importing"""
        #print "start of tab_bulk_import"
        new_import_thread = GuiBulkImport.GuiBulkImport(self.settings, self.config, self.sql)
        self.threads.append(new_import_thread)
        bulk_tab=new_import_thread.get_vbox()
        self.add_and_display_tab(bulk_tab, "Bulk Import")
    #end def tab_bulk_import

    def tab_player_stats(self, widget, data=None):
        new_ps_thread=GuiPlayerStats.GuiPlayerStats(self.config, self.sql, self.window)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Player Stats")

    def tab_positional_stats(self, widget, data=None):
        new_ps_thread = GuiPositionalStats.GuiPositionalStats(self.config, self.sql)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Positional Stats")

    def tab_main_help(self, widget, data=None):
        """Displays a tab with the main fpdb help screen"""
        #print "start of tab_main_help"
        mh_tab=gtk.Label("""Welcome to Fpdb!
For documentation please visit our website at http://fpdb.sourceforge.net/ or check the docs directory in the fpdb folder.
Please note that default.conf is no longer needed nor used, all configuration now happens in HUD_config.xml
This program is licensed under the AGPL3, see docs"""+os.sep+"agpl-3.0.txt")
        self.add_and_display_tab(mh_tab, "Help")
    #end def tab_main_help

    def tab_table_viewer(self, widget, data=None):
        """opens a table viewer tab"""
        #print "start of tab_table_viewer"
        new_tv_thread=GuiTableViewer.GuiTableViewer(self.db.fdb, self.settings)
        self.threads.append(new_tv_thread)
        tv_tab=new_tv_thread.get_vbox()
        self.add_and_display_tab(tv_tab, "Table Viewer")
    #end def tab_table_viewer

    def tabGraphViewer(self, widget, data=None):
        """opens a graph viewer tab"""
        #print "start of tabGraphViewer"
        new_gv_thread = GuiGraphViewer.GuiGraphViewer(self.sql, self.config)
        self.threads.append(new_gv_thread)
        gv_tab=new_gv_thread.get_vbox()
        self.add_and_display_tab(gv_tab, "Graphs")
    #end def tabGraphViewer

    def __init__(self):
        self.threads = []
        # no more than 1 process can this lock at a time:
        self.lock = interlocks.InterProcessLock(name="fpdb_global_lock")
        self.db = None
        self.status_bar = None

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_title("Free Poker DB - v%s or higher" % (VERSION, ))
        self.window.set_border_width(1)
        self.window.set_default_size(900,720)
        self.window.set_resizable(True)

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
        self.tab_box = gtk.HBox(True,1)
        self.main_vbox.pack_start(self.tab_box, False, True, 0)
        self.tab_box.show()
        #done tab bar

        self.current_tab = gtk.VBox(False,1)
        self.current_tab.set_border_width(1)
        self.main_vbox.add(self.current_tab)
        self.current_tab.show()

        self.tab_main_help(None, None)

        self.window.show()
        self.load_profile()
        sys.stderr.write("fpdb starting ...")
    #end def __init__

    def main(self):
        gtk.main()
        return 0
    #end def main

if __name__ == "__main__":
    me = fpdb()
    me.main()
