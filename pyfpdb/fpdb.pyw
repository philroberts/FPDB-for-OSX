#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Steffen Schaumburg
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
import re
import Queue

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
        if os.name=='nt':
            os.execvpe('pythonw.exe', ('pythonw.exe', 'fpdb.pyw', '-r'), os.environ) # first arg is ignored (name of program being run)
        else:
            os.execvpe('python', ('python', 'fpdb.pyw', '-r'), os.environ) # first arg is ignored (name of program being run)
    else:
        print "\npython 2.5 not found, please install python 2.5 or 2.6 for fpdb\n"
        raw_input("Press ENTER to continue.")
        exit()
else:
    pass
    #print "debug - not changing path"

if os.name == 'nt':
    try:
        import win32api
        import win32con
    except ImportError:
        print "We appear to be running in Windows, but the Windows Python Extensions are not loading. Please install the PYWIN32 package from http://sourceforge.net/projects/pywin32/"
        raw_input("Press ENTER to continue.")
        exit()

print "Python " + sys.version[0:3] + '...'

import traceback
import threading
import Options
import string
cl_options = string.join(sys.argv[1:])
(options, argv) = Options.fpdb_options()

import logging, logging.config
log = logging.getLogger("fpdb")

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
    import pango
except:
    print "Unable to load PYGTK modules required for GUI. Please install PyCairo, PyGObject, and PyGTK from www.pygtk.org."
    raw_input("Press ENTER to continue.")
    exit()

import interlocks

# these imports not required in this module, imported here to report version in About dialog
try:
    import matplotlib
    matplotlib_version = matplotlib.__version__
except:
    matplotlib_version = 'not found'
try:
    import numpy
    numpy_version = numpy.__version__
except:
    numpy_version = 'not found'
try:
    import sqlite3
    sqlite3_version = sqlite3.version
    sqlite_version = sqlite3.sqlite_version
except:
    sqlite3_version = 'not found'
    sqlite_version = 'not found'

import GuiPrefs
import GuiLogView
import GuiDatabase
import GuiBulkImport
import ImapFetcher
import GuiRingPlayerStats
import GuiTourneyPlayerStats
import GuiPositionalStats
import GuiTableViewer
import GuiAutoImport
import GuiGraphViewer
import GuiSessionViewer
import SQL
import Database
import Configuration
import Exceptions
import Stats

VERSION = "0.20 plus git"


class fpdb:
    def tab_clicked(self, widget, tab_name):
        """called when a tab button is clicked to activate that tab"""
        self.display_tab(tab_name)

    def add_and_display_tab(self, new_tab, new_tab_name):
        """just calls the component methods"""
        self.add_tab(new_tab, new_tab_name)
        self.display_tab(new_tab_name)

    def add_tab(self, new_page, new_tab_name):
        """adds a tab, namely creates the button and displays it and appends all the relevant arrays"""
        for name in self.nb_tab_names: #todo: check this is valid
            if name == new_tab_name:
                return # if tab already exists, just go to it

        used_before = False
        for i, name in enumerate(self.tab_names):
            if name == new_tab_name:
                used_before = True
                event_box = self.tabs[i]
                page = self.pages[i]
                break

        if not used_before:
            event_box = self.create_custom_tab(new_tab_name, self.nb)
            page = new_page
            self.pages.append(new_page)
            self.tabs.append(event_box)
            self.tab_names.append(new_tab_name)

        #self.nb.append_page(new_page, gtk.Label(new_tab_name))
        self.nb.append_page(page, event_box)
        self.nb_tab_names.append(new_tab_name)
        page.show()

    def display_tab(self, new_tab_name):
        """displays the indicated tab"""
        tab_no = -1
        for i, name in enumerate(self.nb_tab_names):
            if new_tab_name == name:
                tab_no = i
                break

        if tab_no < 0 or tab_no >= self.nb.get_n_pages():
            raise FpdbError("invalid tab_no " + str(tab_no))
        else:
            self.nb.set_current_page(tab_no)

    def create_custom_tab(self, text, nb):
        #create a custom tab for notebook containing a
        #label and a button with STOCK_ICON
        eventBox = gtk.EventBox()
        tabBox = gtk.HBox(False, 2)
        tabLabel = gtk.Label(text)
        tabBox.pack_start(tabLabel, False)
        eventBox.add(tabBox)

        if nb.get_n_pages() > 0:
            tabButton = gtk.Button()

            tabButton.connect('clicked', self.remove_tab, (nb, text))
            #Add a picture on a button
            self.add_icon_to_button(tabButton)
            tabBox.pack_start(tabButton, False)

        # needed, otherwise even calling show_all on the notebook won't
        # make the hbox contents appear.
        tabBox.show_all()
        return eventBox

    def add_icon_to_button(self, button):
        iconBox = gtk.HBox(False, 0)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        gtk.Button.set_relief(button, gtk.RELIEF_NONE)
        settings = gtk.Widget.get_settings(button);
        (w,h) = gtk.icon_size_lookup_for_settings(settings, gtk.ICON_SIZE_SMALL_TOOLBAR);
        gtk.Widget.set_size_request (button, w + 4, h + 4);
        image.show()
        iconBox.pack_start(image, True, False, 0)
        button.add(iconBox)
        iconBox.show()
        return

    # Remove a page from the notebook
    def remove_tab(self, button, data):
        (nb, text) = data
        page = -1
        #print "\n remove_tab: start", text
        for i, tab in enumerate(self.nb_tab_names):
            if text == tab:
                page = i
        #print "   page =", page
        if page >= 0 and page < self.nb.get_n_pages():
            #print "   removing page", page
            del self.nb_tab_names[page]
            nb.remove_page(page)
        # Need to refresh the widget --
        # This forces the widget to redraw itself.
        #nb.queue_draw_area(0,0,-1,-1) needed or not??

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        self.quit(widget)

    def dia_about(self, widget, data=None):
        #self.warning_box("About FPDB:\n\nFPDB was originally created by a guy named Steffen, sometime in 2008, \nand is mostly worked on these days by people named Eratosthenes, s0rrow, _mt, EricBlade, sqlcoder, and other strange people.\n\n", "ABOUT FPDB")
        dia = gtk.AboutDialog()
        dia.set_name("Free Poker Database (FPDB)")
        dia.set_version(VERSION)
        dia.set_copyright("Copyright 2008-2010, Steffen, Eratosthenes, Carl Gherardi, Eric Blade, _mt, sqlcoder, Bostik, and others")
        dia.set_comments("")
        dia.set_license("This program is licensed under the AGPL3, see agpl-3.0.txt in the fpdb installation directory")
        dia.set_website("http://fpdb.sourceforge.net/")
        
        dia.set_authors(['Steffen', 'Eratosthenes', 'Carl Gherardi',
            'Eric Blade', '_mt', 'sqlcoder', 'Bostik', 'and others'])
        dia.set_program_name("Free Poker Database (FPDB)")

        db_version = ""
        #if self.db is not None:
        #    db_version = self.db.get_version()
        nums = [ ('Operating System', os.name)
               , ('Python',           sys.version[0:3])
               , ('GTK+',             '.'.join([str(x) for x in gtk.gtk_version]))
               , ('PyGTK',            '.'.join([str(x) for x in gtk.pygtk_version]))
               , ('matplotlib',       matplotlib_version)
               , ('numpy',            numpy_version)
               , ('sqlite3',          sqlite3_version)
               , ('sqlite',           sqlite_version)
               , ('database',         self.settings['db-server'] + db_version)
               ]
        versions = gtk.TextBuffer()
        w = 20  # width used for module names and version numbers
        versions.set_text( '\n'.join( [x[0].rjust(w)+'  '+ x[1].ljust(w) for x in nums] ) )
        view = gtk.TextView(versions)
        view.set_editable(False)
        view.set_justification(gtk.JUSTIFY_CENTER)
        view.modify_font(pango.FontDescription('monospace 10'))
        view.show()
        dia.vbox.pack_end(view, True, True, 2)
        
        l = gtk.Label("Your config file is: "+self.config.file)
        l.set_alignment(0.5, 0.5)
        l.show()
        dia.vbox.pack_end(l, True, True, 2)

        l = gtk.Label('Version Information:')
        l.set_alignment(0.5, 0.5)
        l.show()
        dia.vbox.pack_end(l, True, True, 2)
        
        dia.run()
        dia.destroy()
        log.debug("Threads: ")
        for t in self.threads:
            log.debug("........." + str(t.__class__))

    def dia_preferences(self, widget, data=None):
        dia = gtk.Dialog("Preferences",
                         self.window,
                         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        dia.set_default_size(700, 500)

        prefs = GuiPrefs.GuiPrefs(self.config, self.window, dia.vbox, dia)
        response = dia.run()
        if response == gtk.RESPONSE_ACCEPT:
            # save updated config
            self.config.save()
            if len(self.nb_tab_names) == 1:
                # only main tab open, reload profile
                self.load_profile()
                dia.destroy()
            else:
                dia.destroy()  # destroy prefs before raising warning, otherwise parent is dia rather than self.window
                self.warning_box("Updated preferences have not been loaded because "
                                 + "windows are open. Re-start fpdb to load them.")
        else:
            dia.destroy()

    def dia_maintain_dbs(self, widget, data=None):
        self.warning_box("Unimplemented: Maintain Databases")
        return
        if len(self.tab_names) == 1:
            if self.obtain_global_lock("dia_maintain_dbs"):  # returns true if successful
                # only main tab has been opened, open dialog
                dia = gtk.Dialog("Maintain Databases",
                                 self.window,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                  gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
                dia.set_default_size(700, 320)

                prefs = GuiDatabase.GuiDatabase(self.config, self.window, dia)
                response = dia.run()
                if response == gtk.RESPONSE_ACCEPT:
                    # save updated config
                    self.config.save()

                self.release_global_lock()

            dia.destroy()
        else:
            self.warning_box("Cannot open Database Maintenance window because "
                             + "other windows have been opened. Re-start fpdb to use this option.")

    def dia_database_stats(self, widget, data=None):
        self.warning_box(str="Number of Hands: "+str(self.db.getHandCount())+
                    "\nNumber of Tourneys: "+str(self.db.getTourneyCount())+
                    "\nNumber of TourneyTypes: "+str(self.db.getTourneyTypeCount()),
                    diatitle="Database Statistics")
    #end def dia_database_stats

    def diaHudConfigurator(self, widget, data=None):
        self.hudConfiguratorRows=None
        self.hudConfiguratorColumns=None
        self.hudConfiguratorGame=None
        
        diaSelections = gtk.Dialog("HUD Configurator - choose category",
                                 self.window,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                                  gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        
        label=gtk.Label("Please select the game category for which you want to configure HUD stats:")
        diaSelections.vbox.add(label)
        label.show()
        
        #combo=gtk.ComboBox()
        
        comboGame = gtk.combo_box_new_text()
        comboGame.connect("changed", self.hudConfiguratorComboSelection)
        diaSelections.vbox.add(comboGame)
        games=self.config.get_supported_games()
        for game in games:
            comboGame.append_text(game)
        comboGame.set_active(0)
        comboGame.show()
        
        comboRows = gtk.combo_box_new_text()
        comboRows.connect("changed", self.hudConfiguratorComboSelection)
        diaSelections.vbox.add(comboRows)
        for i in range(1,8):
            comboRows.append_text(str(i)+" rows")
        comboRows.set_active(0)
        comboRows.show()
        
        comboColumns = gtk.combo_box_new_text()
        comboColumns.connect("changed", self.hudConfiguratorComboSelection)
        diaSelections.vbox.add(comboColumns)
        for i in range(1,8):
            comboColumns.append_text(str(i)+" columns")
        comboColumns.set_active(0)
        comboColumns.show()
        
        response=diaSelections.run()
        diaSelections.destroy()
        
        if response == gtk.RESPONSE_ACCEPT and self.hudConfiguratorRows!=None and self.hudConfiguratorColumns!=None and self.hudConfiguratorGame!=None:
            print "clicked ok and selected:", self.hudConfiguratorGame,"with", str(self.hudConfiguratorRows), "rows and", str(self.hudConfiguratorColumns), "columns"
            self.diaHudConfiguratorTable()
    #end def diaHudConfigurator

    def hudConfiguratorComboSelection(self, widget):
        result=widget.get_active_text()
        if result.endswith(" rows"):
            self.hudConfiguratorRows=int(result[0])
        elif result.endswith(" columns"):
            self.hudConfiguratorColumns=int(result[0])
        else:
            self.hudConfiguratorGame=result
    #end def hudConfiguratorComboSelection
    
    def diaHudConfiguratorTable(self):
        #TODO: show explanation of what each stat means
        diaHudTable = gtk.Dialog("HUD Configurator - please choose your stats",
                                 self.window,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT,
                                  gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        
        label=gtk.Label("Please choose the stats you wish to use")
        diaHudTable.vbox.add(label)
        label.show()
        
        self.hudConfiguratorTableContents=[]
        table= gtk.Table(rows=self.hudConfiguratorRows+1, columns=self.hudConfiguratorColumns+1, homogeneous=True)
        
        statDir=dir(Stats)
        statDict={}
        for attr in statDir:
            if attr.startswith('__'): continue
            if attr in ("Charset", "Configuration", "Database", "GInitiallyUnowned", "gtk", "pygtk",
                        "player", "c", "db_connection", "do_stat", "do_tip", "stat_dict",
                        "h", "re", "re_Percent", "re_Places", ): continue
            statDict[attr]=eval("Stats.%s.__doc__" % (attr))
        #print "statDict:",statDict
        
        for rowNumber in range(self.hudConfiguratorRows+1):
            newRow=[]
            
            for columnNumber in range(self.hudConfiguratorColumns+1):
                if rowNumber==0:
                    if columnNumber==0:
                        pass
                    else:
                        label=gtk.Label("column "+str(columnNumber))
                        table.attach(child=label, left_attach=columnNumber, right_attach=columnNumber+1, top_attach=rowNumber, bottom_attach=rowNumber+1)
                        label.show()
                elif columnNumber==0:
                    label=gtk.Label("row "+str(rowNumber))
                    table.attach(child=label, left_attach=columnNumber, right_attach=columnNumber+1, top_attach=rowNumber, bottom_attach=rowNumber+1)
                    label.show()
                else:
                    comboBox = gtk.combo_box_new_text()
                    
                    for stat in statDict.keys():
                        comboBox.append_text(stat)
                    comboBox.set_active(0)
                    
                    newRow.append(comboBox)
                    table.attach(child=comboBox, left_attach=columnNumber, right_attach=columnNumber+1, top_attach=rowNumber, bottom_attach=rowNumber+1)
                    
                    comboBox.show()
            self.hudConfiguratorTableContents.append(newRow)
        diaHudTable.vbox.add(table)
        table.show()
        
        response=diaHudTable.run()
        diaHudTable.destroy()
        
        if response == gtk.RESPONSE_ACCEPT:
            self.storeNewHudStatConfig()
    #end def diaHudConfiguratorTable
    
    def storeNewHudStatConfig(self):
        print "start of storeNewHudStatConfig"
        self.obtain_global_lock("diaHudConfiguratorTable")
        for row in self.hudConfiguratorTableContents:
            for column in row:
                print column.get_active_text()
        
        self.release_global_lock()
    #end def storeNewHudStatConfig
    
    def dia_dump_db(self, widget, data=None):
        self.db.dumpDatabase("database-dump.sql")
    #end def dia_database_stats

    def dia_licensing(self, widget, data=None):
        self.warning_box("Unimplemented: Licensing")

    def dia_load_profile(self, widget, data=None):
        """Dialogue to select a file to load a profile from"""
        if self.obtain_global_lock("fpdb.dia_load_profile"):  # returns true if successful
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

    def dia_recreate_tables(self, widget, data=None):
        """Dialogue that asks user to confirm that he wants to delete and recreate the tables"""
        if self.obtain_global_lock("fpdb.dia_recreate_tables"):  # returns true if successful

            #lock_released = False
            dia_confirm = gtk.MessageDialog(parent=self.window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_WARNING,
                    buttons=(gtk.BUTTONS_YES_NO), message_format="Confirm deleting and recreating tables")
            diastring = "Please confirm that you want to (re-)create the tables. If there already are tables in the database " \
                        +self.db.database+" on "+self.db.host+" they will be deleted.\nThis may take a while."
            dia_confirm.format_secondary_text(diastring)#todo: make above string with bold for db, host and deleted
            # disable windowclose, do not want the the underlying processing interrupted mid-process
            dia_confirm.set_deletable(False)

            response = dia_confirm.run()
            dia_confirm.destroy()
            if response == gtk.RESPONSE_YES:
                #if self.db.backend == self.fdb_lock.fdb.MYSQL_INNODB:
                    # mysql requires locks on all tables or none - easier to release this lock
                    # than lock all the other tables
                    # ToDo: lock all other tables so that lock doesn't have to be released
                #    self.release_global_lock()
                #    lock_released = True
                self.db.recreate_tables()
                self.release_global_lock()
                #else:
                    # for other dbs use same connection as holds global lock
                #    self.fdb_lock.fdb.recreate_tables()
                # TODO: figure out why this seems to be necessary
                dia_restart = gtk.MessageDialog(parent=self.window, flags=0, type=gtk.MESSAGE_WARNING,
                        buttons=(gtk.BUTTONS_OK), message_format="Restart fpdb")
                diastring = "Fpdb now needs to close. Please restart it."
                dia_restart.format_secondary_text(diastring)

                dia_restart.run()
                dia_restart.destroy()
                self.quit(None, None)
            elif response == gtk.RESPONSE_NO:
                self.release_global_lock()
                print 'User cancelled recreating tables'
            #if not lock_released:
    #end def dia_recreate_tables

    def dia_recreate_hudcache(self, widget, data=None):
        if self.obtain_global_lock("dia_recreate_hudcache"):
            self.dia_confirm = gtk.MessageDialog(parent=self.window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_WARNING, buttons=(gtk.BUTTONS_YES_NO), message_format="Confirm recreating HUD cache")
            diastring = "Please confirm that you want to re-create the HUD cache."
            self.dia_confirm.format_secondary_text(diastring)
            # disable windowclose, do not want the the underlying processing interrupted mid-process
            self.dia_confirm.set_deletable(False)

            hb1 = gtk.HBox(True, 1)
            self.h_start_date = gtk.Entry(max=12)
            self.h_start_date.set_text( self.db.get_hero_hudcache_start() )
            lbl = gtk.Label(" Hero's cache starts: ")
            btn = gtk.Button()
            btn.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
            btn.connect('clicked', self.__calendar_dialog, self.h_start_date)

            hb1.pack_start(lbl, expand=True, padding=3)
            hb1.pack_start(self.h_start_date, expand=True, padding=2)
            hb1.pack_start(btn, expand=False, padding=3)
            self.dia_confirm.vbox.add(hb1)
            hb1.show_all()

            hb2 = gtk.HBox(True, 1)
            self.start_date = gtk.Entry(max=12)
            self.start_date.set_text( self.db.get_hero_hudcache_start() )
            lbl = gtk.Label(" Villains' cache starts: ")
            btn = gtk.Button()
            btn.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
            btn.connect('clicked', self.__calendar_dialog, self.start_date)

            hb2.pack_start(lbl, expand=True, padding=3)
            hb2.pack_start(self.start_date, expand=True, padding=2)
            hb2.pack_start(btn, expand=False, padding=3)
            self.dia_confirm.vbox.add(hb2)
            hb2.show_all()

            response = self.dia_confirm.run()
            if response == gtk.RESPONSE_YES:
                lbl = gtk.Label(" Rebuilding HUD Cache ... ")
                self.dia_confirm.vbox.add(lbl)
                lbl.show()
                while gtk.events_pending():
                    gtk.main_iteration_do(False)

                self.db.rebuild_hudcache( self.h_start_date.get_text(), self.start_date.get_text() )
            elif response == gtk.RESPONSE_NO:
                print 'User cancelled rebuilding hud cache'

            self.dia_confirm.destroy()

        self.release_global_lock()

    def dia_rebuild_indexes(self, widget, data=None):
        if self.obtain_global_lock("dia_rebuild_indexes"):
            self.dia_confirm = gtk.MessageDialog(parent=self.window
                                                ,flags=gtk.DIALOG_DESTROY_WITH_PARENT
                                                ,type=gtk.MESSAGE_WARNING
                                                ,buttons=(gtk.BUTTONS_YES_NO)
                                                ,message_format="Confirm rebuilding database indexes")
            diastring = "Please confirm that you want to rebuild the database indexes."
            self.dia_confirm.format_secondary_text(diastring)
            # disable windowclose, do not want the the underlying processing interrupted mid-process
            self.dia_confirm.set_deletable(False)

            response = self.dia_confirm.run()
            if response == gtk.RESPONSE_YES:
                #FIXME these progress messages do not seem to work in *nix
                lbl = gtk.Label(" Rebuilding Indexes ... ")
                self.dia_confirm.vbox.add(lbl)
                lbl.show()
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
                self.db.rebuild_indexes()

                lbl.set_text(" Cleaning Database ... ")
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
                self.db.vacuumDB()

                lbl.set_text(" Analyzing Database ... ")
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
                self.db.analyzeDB()
            elif response == gtk.RESPONSE_NO:
                print 'User cancelled rebuilding db indexes'

            self.dia_confirm.destroy()

        self.release_global_lock()

    def dia_logs(self, widget, data=None):
        """opens the log viewer window"""

        #lock_set = False
        #if self.obtain_global_lock("dia_logs"):
        #    lock_set = True

        # remove members from self.threads if close messages received
        self.process_close_messages()

        viewer = None
        for i, t in enumerate(self.threads):
            if str(t.__class__) == 'GuiLogView.GuiLogView':
                viewer = t
                break

        if viewer is None:
            #print "creating new log viewer"
            new_thread = GuiLogView.GuiLogView(self.config, self.window, self.closeq)
            self.threads.append(new_thread)
        else:
            #print "showing existing log viewer"
            viewer.get_dialog().present()

        #if lock_set:
        #    self.release_global_lock()

    def addLogText(self, text):
        end_iter = self.logbuffer.get_end_iter()
        self.logbuffer.insert(end_iter, text)
        self.logview.scroll_to_mark(self.logbuffer.get_insert(), 0)


    def process_close_messages(self):
        # check for close messages
        try:
            while True:
                name = self.closeq.get(False)
                for i, t in enumerate(self.threads):
                    if str(t.__class__) == str(name):
                        # thread has ended so remove from list:
                        del self.threads[i]
                        break
        except Queue.Empty:
            # no close messages on queue, do nothing
            pass

    def __calendar_dialog(self, widget, entry):
# do not alter the modality of the parent
#        self.dia_confirm.set_modal(False)
        d = gtk.Window(gtk.WINDOW_TOPLEVEL)
        d.set_transient_for(self.dia_confirm)
        d.set_destroy_with_parent(True)
        d.set_modal(True)

        d.set_title('Pick a date')

        vb = gtk.VBox()
        cal = gtk.Calendar()
        vb.pack_start(cal, expand=False, padding=0)

        btn = gtk.Button('Done')
        btn.connect('clicked', self.__get_date, cal, entry, d)

        vb.pack_start(btn, expand=False, padding=4)

        d.add(vb)
        d.set_position(gtk.WIN_POS_MOUSE)
        d.show_all()

    def __get_dates(self):
        t1 = self.h_start_date.get_text()
        if t1 == '':
            t1 = '1970-01-01'
        t2 = self.start_date.get_text()
        if t2 == '':
            t2 = '1970-01-01'
        return (t1, t2)

    def __get_date(self, widget, calendar, entry, win):
        # year and day are correct, month is 0..11
        (year, month, day) = calendar.get_date()
        month += 1
        ds = '%04d-%02d-%02d' % (year, month, day)
        entry.set_text(ds)
        win.destroy()
        self.dia_confirm.set_modal(True)

    def dia_regression_test(self, widget, data=None):
        self.warning_box("Unimplemented: Regression Test")
        #self.obtain_global_lock("dia_regression_test")
        #self.release_global_lock()

    def dia_save_profile(self, widget, data=None):
        self.warning_box("Unimplemented: Save Profile (try saving a HUD layout, that should do it)")

    def diaSetupWizard(self, path):
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

    def get_menu(self, window):
        """returns the menu for this program"""
        fpdbmenu = """
            <ui>
              <menubar name="MenuBar">
                <menu action="main">
                  <menuitem action="LoadProf"/>
                  <menuitem action="SaveProf"/>
                  <menuitem action="hudConfigurator"/>
                  <menuitem action="Preferences"/>
                  <separator/>
                  <menuitem action="Quit"/>
                </menu>
                <menu action="import">
                  <menuitem action="sethharchive"/>
                  <menuitem action="bulkimp"/>
                  <menuitem action="imapsummaries"/>
                  <menuitem action="autoimp"/>
                </menu>
                <menu action="viewers">
                  <menuitem action="autoimp"/>
                  <menuitem action="hudConfigurator"/>
                  <menuitem action="graphs"/>
                  <menuitem action="ringplayerstats"/>
                  <menuitem action="tourneyplayerstats"/>
                  <menuitem action="posnstats"/>
                  <menuitem action="sessionstats"/>
                  <menuitem action="tableviewer"/>
                </menu>
                <menu action="database">
                  <menuitem action="maintaindbs"/>
                  <menuitem action="createtabs"/>
                  <menuitem action="rebuildhudcache"/>
                  <menuitem action="rebuildindexes"/>
                  <menuitem action="databasestats"/>
                  <menuitem action="dumptofile"/>
                </menu>
                <menu action="help">
                  <menuitem action="Logs"/>
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
                                 ('SaveProf', None, '_Save Profile (todo)', '<control>S', 'Save your profile', self.dia_save_profile),
                                 ('Preferences', None, 'Pre_ferences', '<control>F', 'Edit your preferences', self.dia_preferences),
                                 ('import', None, '_Import'),
                                 ('sethharchive', None, '_Set HandHistory Archive Directory', None, 'Set HandHistory Archive Directory', self.select_hhArchiveBase),
                                 ('bulkimp', None, '_Bulk Import', '<control>B', 'Bulk Import', self.tab_bulk_import),
                                 ('imapsummaries', None, '_Import Tourney Summaries through eMail/IMAP', '<control>I', 'Auto Import and HUD', self.import_imap_summaries),
                                 ('viewers', None, '_Viewers'),
                                 ('autoimp', None, '_Auto Import and HUD', '<control>A', 'Auto Import and HUD', self.tab_auto_import),
                                 ('hudConfigurator', None, '_HUD Configurator', '<control>H', 'HUD Configurator', self.diaHudConfigurator),
                                 ('graphs', None, '_Graphs', '<control>G', 'Graphs', self.tabGraphViewer),
                                 ('ringplayerstats', None, 'Ring _Player Stats (tabulated view)', '<control>P', 'Ring Player Stats (tabulated view)', self.tab_ring_player_stats),
                                 ('tourneyplayerstats', None, '_Tourney Player Stats (tabulated view)', '<control>T', 'Tourney Player Stats (tabulated view)', self.tab_tourney_player_stats),
                                 ('posnstats', None, 'P_ositional Stats (tabulated view)', '<control>O', 'Positional Stats (tabulated view)', self.tab_positional_stats),
                                 ('sessionstats', None, 'Session Stats', None, 'Session Stats', self.tab_session_stats),
                                 ('tableviewer', None, 'Poker_table Viewer (mostly obselete)', None, 'Poker_table Viewer (mostly obselete)', self.tab_table_viewer),
                                 ('database', None, '_Database'),
                                 ('maintaindbs', None, '_Maintain Databases (todo)', None, 'Maintain Databases', self.dia_maintain_dbs),
                                 ('createtabs', None, 'Create or Recreate _Tables', None, 'Create or Recreate Tables ', self.dia_recreate_tables),
                                 ('rebuildhudcache', None, 'Rebuild HUD Cache', None, 'Rebuild HUD Cache', self.dia_recreate_hudcache),
                                 ('rebuildindexes', None, 'Rebuild DB Indexes', None, 'Rebuild DB Indexes', self.dia_rebuild_indexes),
                                 ('databasestats', None, '_Statistics', None, 'View Database Statistics', self.dia_database_stats),
                                 ('dumptofile', None, 'Dump Database to Textfile (takes ALOT of time)', None, 'Dump Database to Textfile (takes ALOT of time)', self.dia_dump_db),
                                 ('help', None, '_Help'),
                                 ('Logs', None, '_Log Messages', None, 'Log and Debug Messages', self.dia_logs),
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
    
    def import_imap_summaries(self, widget, data=None):
        result=ImapFetcher.run(self.config, self.db)
        #print "import imap summaries result:", result
    #end def import_imap_summaries

    def load_profile(self, create_db = False):
        """Loads profile from the provided path name."""
        self.config = Configuration.Config(file=options.config, dbname=options.dbname)
        if self.config.file_error:
            self.warning_box( "There is an error in your config file\n" + self.config.file
                              + "\n\nError is:  " + str(self.config.file_error)
                            , diatitle="CONFIG FILE ERROR" )
            sys.exit()

        log = Configuration.get_logger("logging.conf", "fpdb", log_dir=self.config.dir_log)
        print "Logfile is " + os.path.join(self.config.dir_log, self.config.log_file) + "\n"
        if self.config.example_copy:
            self.info_box( "Config file"
                         , "has been created at:\n%s.\n" % self.config.file
                           + "Edit your screen_name and hand history path in the supported_sites "
                           + "section of the Preferences window (Main menu) before trying to import hands.")
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

        if self.db is not None and self.db.connected:
            self.db.disconnect()

        self.sql = SQL.Sql(db_server = self.settings['db-server'])
        err_msg = None
        try:
            self.db = Database.Database(self.config, sql = self.sql)
            if self.db.get_backend_name() == 'SQLite':
                # tell sqlite users where the db file is
                print "Connected to SQLite: %(database)s" % {'database':self.db.db_path}
        except Exceptions.FpdbMySQLAccessDenied:
            err_msg = "MySQL Server reports: Access denied. Are your permissions set correctly?"
        except Exceptions.FpdbMySQLNoDatabase:
            err_msg = "MySQL client reports: 2002 or 2003 error. Unable to connect - " \
                      + "Please check that the MySQL service has been started"
        except Exceptions.FpdbPostgresqlAccessDenied:
            err_msg = "Postgres Server reports: Access denied. Are your permissions set correctly?"
        except Exceptions.FpdbPostgresqlNoDatabase:
            err_msg = "Postgres client reports: Unable to connect - " \
                      + "Please check that the Postgres service has been started"
        if err_msg is not None:
            self.db = None
            self.warning_box(err_msg)

#        except FpdbMySQLFailedError:
#            self.warning_box("Unable to connect to MySQL! Is the MySQL server running?!", "FPDB ERROR")
#            exit()
#        except FpdbError:
#            #print "Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user'])
#            self.warning_box("Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user']), "FPDB ERROR")
#            err = traceback.extract_tb(sys.exc_info()[2])[-1]
#            print "*** Error: " + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])
#            sys.stderr.write("Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user']))
#        except:
#            #print "Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user'])
#            self.warning_box("Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user']), "FPDB ERROR")
#            err = traceback.extract_tb(sys.exc_info()[2])[-1]
#            print "*** Error: " + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1])
#            sys.stderr.write("Failed to connect to %s database with username %s." % (self.settings['db-server'], self.settings['db-user']))

        if self.db is not None and self.db.wrongDbVersion:
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

        if self.status_bar is None:
            self.status_bar = gtk.Label("")
            self.main_vbox.pack_end(self.status_bar, False, True, 0)
            self.status_bar.show()

        if self.db is not None and self.db.connected:
            self.status_bar.set_text("Status: Connected to %s database named %s on host %s"
                                     % (self.db.get_backend_name(),self.db.database, self.db.host))
            # rollback to make sure any locks are cleared:
            self.db.rollback()

        self.validate_config()

    def not_implemented(self, widget, data=None):
        self.warning_box("Unimplemented menu entry")

    def obtain_global_lock(self, source):
        ret = self.lock.acquire(source=source) # will return false if lock is already held
        if ret:
            print "\nGlobal lock taken by", source
            self.lockTakenBy=source
        else:
            print "\nFailed to get global lock, it is currently held by", source
        return ret
        # need to release it later:
        # self.lock.release()

    def quit(self, widget, data=None):
        # TODO: can we get some / all of the stuff done in this function to execute on any kind of abort?
        #FIXME  get two "quitting normally" messages, following the addition of the self.window.destroy() call
        #       ... because self.window.destroy() leads to self.destroy() which calls this!
        if not self.quitting:
            print "Quitting normally"
            self.quitting = True
        # TODO: check if current settings differ from profile, if so offer to save or abort
        
        if self.db!=None:
            if self.db.backend==self.db.MYSQL_INNODB:
                try:
                    if self.db is not None and self.db.connected():
                        self.db.disconnect()
                except _mysql_exceptions.OperationalError: # oh, damn, we're already disconnected
                    pass
            else:
                if self.db is not None and self.db.connected():
                    self.db.disconnect()
        else:
            pass
        self.statusIcon.set_visible(False)

        self.window.destroy() # explicitly destroy to allow child windows to close cleanly
        gtk.main_quit()

    def release_global_lock(self):
        self.lock.release()
        self.lockTakenBy=None
        print "Global lock released.\n"

    def tab_auto_import(self, widget, data=None):
        """opens the auto import tab"""
        new_aimp_thread = GuiAutoImport.GuiAutoImport(self.settings, self.config, self.sql, self.window)
        self.threads.append(new_aimp_thread)
        aimp_tab=new_aimp_thread.get_vbox()
        self.add_and_display_tab(aimp_tab, "Auto Import")

    def tab_bulk_import(self, widget, data=None):
        """opens a tab for bulk importing"""
        new_import_thread = GuiBulkImport.GuiBulkImport(self.settings, self.config, self.sql)
        self.threads.append(new_import_thread)
        bulk_tab=new_import_thread.get_vbox()
        self.add_and_display_tab(bulk_tab, "Bulk Import")

    def tab_ring_player_stats(self, widget, data=None):
        new_ps_thread = GuiRingPlayerStats.GuiRingPlayerStats(self.config, self.sql, self.window)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Ring Player Stats")

    def tab_tourney_player_stats(self, widget, data=None):
        new_ps_thread = GuiTourneyPlayerStats.GuiTourneyPlayerStats(self.config, self.db, self.sql, self.window)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Tourney Player Stats")

    def tab_positional_stats(self, widget, data=None):
        new_ps_thread = GuiPositionalStats.GuiPositionalStats(self.config, self.sql)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Positional Stats")

    def tab_session_stats(self, widget, data=None):
        new_ps_thread = GuiSessionViewer.GuiSessionViewer(self.config, self.sql, self.window)
        self.threads.append(new_ps_thread)
        ps_tab=new_ps_thread.get_vbox()
        self.add_and_display_tab(ps_tab, "Session Stats")

    def tab_main_help(self, widget, data=None):
        """Displays a tab with the main fpdb help screen"""
        mh_tab=gtk.Label("""Welcome to Fpdb!
To be notified of new snapshots and releases go to https://lists.sourceforge.net/lists/listinfo/fpdb-announce and subscribe.
If you want to follow development more closely go to https://lists.sourceforge.net/lists/listinfo/fpdb-main and subscribe.

This program is currently in an alpha-state, so our database format is still sometimes changed.
You should therefore always keep your hand history files so that you can re-import after an update, if necessary.

For documentation please visit our website at http://fpdb.sourceforge.net/.
If you need help click on Contact - Get Help on our website.
Please note that default.conf is no longer needed nor used, all configuration now happens in HUD_config.xml.

This program is free/libre open source software licensed partially under the AGPL3, and partially under GPL2 or later.
You can find the full license texts in agpl-3.0.txt, gpl-2.0.txt and gpl-3.0.txt in the fpdb installation directory.""")
        self.add_and_display_tab(mh_tab, "Help")

    def tab_table_viewer(self, widget, data=None):
        """opens a table viewer tab"""
        new_tv_thread = GuiTableViewer.GuiTableViewer(self.db, self.settings, self.config)
        self.threads.append(new_tv_thread)
        tv_tab = new_tv_thread.get_vbox()
        self.add_and_display_tab(tv_tab, "Table Viewer")

    def tabGraphViewer(self, widget, data=None):
        """opens a graph viewer tab"""
        new_gv_thread = GuiGraphViewer.GuiGraphViewer(self.sql, self.config, self.window)
        self.threads.append(new_gv_thread)
        gv_tab = new_gv_thread.get_vbox()
        self.add_and_display_tab(gv_tab, "Graphs")

    def __init__(self):
        # no more than 1 process can this lock at a time:
        self.lock = interlocks.InterProcessLock(name="fpdb_global_lock")
        self.db = None
        self.status_bar = None
        self.quitting = False

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_title("Free Poker DB - v%s" % (VERSION, ))
        self.window.set_border_width(1)
        defx, defy = 900, 720
        sx, sy = gtk.gdk.screen_width(), gtk.gdk.screen_height()
        if sx < defx:  defx = sx
        if sy < defy:  defy = sy
        self.window.set_default_size(defx, defy)
        self.window.set_resizable(True)

        self.main_vbox = gtk.VBox(False, 1)
        self.main_vbox.set_border_width(1)
        self.window.add(self.main_vbox)
        self.main_vbox.show()

        menubar = self.get_menu(self.window)
        self.main_vbox.pack_start(menubar, False, True, 0)
        menubar.show()
        #done menubar

        self.threads = []     # objects used by tabs - no need for threads, gtk handles it
        self.closeq = Queue.Queue(20)  # used to signal ending of a thread (only logviewer for now)

        self.nb = gtk.Notebook()
        self.nb.set_show_tabs(True)
        self.nb.show()
        self.main_vbox.pack_start(self.nb, True, True, 0)
        self.tabs=[]          # the event_boxes forming the actual tabs
        self.tab_names=[]     # names of tabs used since program started, not removed if tab is closed
        self.pages=[]         # the contents of the page, not removed if tab is closed
        self.nb_tab_names=[]  # list of tab names currently displayed in notebook

        self.tab_main_help(None, None)

        self.window.show()
        self.load_profile(create_db = True)

        if not options.errorsToConsole:
            fileName = os.path.join(self.config.dir_log, 'fpdb-errors.txt')
            print "\nNote: error output is being diverted to fpdb-errors.txt and HUD-errors.txt in:\n" \
                  + self.config.dir_log + "\nAny major error will be reported there _only_.\n"
            errorFile = open(fileName, 'w', 0)
            sys.stderr = errorFile

        self.statusIcon = gtk.StatusIcon()
        # use getcwd() here instead of sys.path[0] so that py2exe works:
        cards = os.path.join(os.getcwd(), '..','gfx','fpdb-cards.png')
        if os.path.exists(cards):
            self.statusIcon.set_from_file(cards)
        elif os.path.exists('/usr/share/pixmaps/fpdb-cards.png'):
            self.statusIcon.set_from_file('/usr/share/pixmaps/fpdb-cards.png')
        else:
            self.statusIcon.set_from_stock(gtk.STOCK_HOME)
        self.statusIcon.set_tooltip("Free Poker Database")
        self.statusIcon.connect('activate', self.statusicon_activate)
        self.statusMenu = gtk.Menu()
        menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menuItem.connect('activate', self.dia_about)
        self.statusMenu.append(menuItem)
 
        menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menuItem.connect('activate', self.quit)
        self.statusMenu.append(menuItem)

        self.statusIcon.connect('popup-menu', self.statusicon_menu, self.statusMenu)
        self.statusIcon.set_visible(True)

        self.window.connect('window-state-event', self.window_state_event_cb)
        sys.stderr.write("fpdb starting ...")

    def window_state_event_cb(self, window, event):
        if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
            # -20 = GWL_EXSTYLE can't find it in the pywin32 libs
            #bits = win32api.GetWindowLong(self.window.window.handle, -20)
            #bits = bits ^ (win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_APPWINDOW)

            #win32api.SetWindowLong(self.window.window.handle, -20, bits)

            if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
                self.window.hide()
                self.window.set_skip_taskbar_hint(True)
                self.window.set_skip_pager_hint(True)
            else:
                self.window.set_skip_taskbar_hint(False)
                self.window.set_skip_pager_hint(False)
        # Tell GTK not to propagate this signal any further
        return True

    def statusicon_menu(self, widget, button, time, data = None):
        # we don't need to pass data here, since we do keep track of most all
        # our variables .. the example code that i looked at for this
        # didn't use any long scope variables.. which might be an alright
        # idea too sometime
        if button == 3:
            if data:
                data.show_all()
                data.popup(None, None, None, 3, time)
        pass

    def statusicon_activate(self, widget, data = None):
        # Let's allow the tray icon to toggle window visibility, the way
        # most other apps work
        shown = self.window.get_property('visible')
        if shown:
            self.window.hide()
        else:
            self.window.show()
            self.window.present()

    def info_box(self, str1, str2):
        diapath = gtk.MessageDialog( parent=self.window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_INFO
                                   , buttons=(gtk.BUTTONS_OK), message_format=str1 )
        diapath.format_secondary_text(str2)
        response = diapath.run()
        diapath.destroy()
        return response

    def warning_box(self, str, diatitle="FPDB WARNING"):
        diaWarning = gtk.Dialog(title=diatitle, parent=self.window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))

        label = gtk.Label(str)
        diaWarning.vbox.add(label)
        label.show()

        response = diaWarning.run()
        diaWarning.destroy()
        return response

    def validate_config(self):
        if self.config.get_import_parameters().get('saveStarsHH'):
            hhbase    = self.config.get_import_parameters().get("hhArchiveBase")
            hhbase    = os.path.expanduser(hhbase)
            #hhdir     = os.path.join(hhbase,site)
            hhdir       = hhbase
            if not os.path.isdir(hhdir):
                diapath = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_WARNING, buttons=(gtk.BUTTONS_YES_NO), message_format="Setup hh dir")
                diastring = "WARNING: Unable to find output hh directory %s\n\n Press YES to create this directory, or NO to select a new one." % hhdir
                diapath.format_secondary_text(diastring)
                response = diapath.run()
                diapath.destroy()
                if response == gtk.RESPONSE_YES:
                    try:
                        os.makedirs(hhdir)
                    except:
                        self.warning_box("WARNING: Unable to create hand output directory. Importing is not likely to work until this is fixed.")
                elif response == gtk.RESPONSE_NO:
                    self.select_hhArchiveBase()

    def select_hhArchiveBase(self, widget=None):
        fc = gtk.FileChooserDialog(title="Select HH Output Directory", parent=None, action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons=(gtk.STOCK_OPEN,gtk.RESPONSE_OK), backend=None)
        fc.run()
        # TODO: We need to put in a Cancel button, and handle if the user presses that or the "Close" box without selecting anything as a cancel, and return to the prior setting
        #self.warning_box("You selected %s" % fc.get_filename())
        self.config.set_hhArchiveBase(fc.get_filename())
        self.config.save()
        self.load_profile() # we can't do this at the end of this func because load_profile calls this func
        fc.destroy() # TODO: loop this to make sure we get valid data back from it, because the open directory thing in GTK lets you select files and not select things and other stupid bullshit

    def main(self):
        gtk.main()
        return 0


if __name__ == "__main__":
    me = fpdb()
    me.main()
