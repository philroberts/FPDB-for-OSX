#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

import subprocess
import traceback

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import sys

import logging


import Importer
from optparse import OptionParser
import Configuration
import string
import interlocks

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")

if os.name == "nt":
    import win32console


class GuiAutoImport:
    def __init__(self, settings, config, sql = None, parent = None, cli = False):
        self.importtimer = 0
        self.settings = settings
        self.config = config
        self.sql = sql
        self.parent = parent

        self.input_settings = {}
        self.pipe_to_hud = None

        self.importer = Importer.Importer(self, self.settings, self.config, self.sql)
        self.importer.setCallHud(True)
        self.importer.setQuiet(False)
        self.importer.setHandCount(0)
        self.importer.setMode('auto')

        self.server = settings['db-host']
        self.user = settings['db-user']
        self.password = settings['db-password']
        self.database = settings['db-databaseName']

        if cli == False:
            self.setupGui()
        else:
            # TODO: Separate the code that grabs the directories from config
            #       Separate the calls to the Importer API
            #       Create a timer interface that doesn't rely on GTK
            pass

    def setupGui(self):
        self.mainVBox = gtk.VBox(False,1)

        hbox = gtk.HBox(True, 0) # contains 2 equal vboxes
        self.mainVBox.pack_start(hbox, False, False, 0)

        vbox1 = gtk.VBox(True, 0)
        hbox.pack_start(vbox1, True, True, 0)
        vbox2 = gtk.VBox(True, 0)
        hbox.pack_start(vbox2, True, True, 0)

        self.intervalLabel = gtk.Label(_("Time between imports in seconds:"))
        self.intervalLabel.set_alignment(xalign=1.0, yalign=0.5)
        vbox1.pack_start(self.intervalLabel, False, True, 0)

        hbox = gtk.HBox(False, 0)
        vbox2.pack_start(hbox, False, True, 0)
        self.intervalEntry = gtk.Entry()
        self.intervalEntry.set_width_chars(4)
        self.intervalEntry.set_text(str(self.config.get_import_parameters().get("interval")))
        hbox.pack_start(self.intervalEntry, False, False, 0)
        lbl1 = gtk.Label()
        hbox.pack_start(lbl1, expand=False, fill=True)

        lbl = gtk.Label('')
        vbox1.pack_start(lbl, expand=False, fill=True)
        lbl = gtk.Label('')
        vbox2.pack_start(lbl, expand=False, fill=True)

        self.addSites(vbox1, vbox2)
        self.textbuffer = gtk.TextBuffer()
        self.textview = gtk.TextView(self.textbuffer)

        hbox = gtk.HBox(False, 0)
        self.mainVBox.pack_start(hbox, expand=True, padding=3)

        hbox = gtk.HBox(False, 0)
        self.mainVBox.pack_start(hbox, expand=False, padding=3)

        lbl1 = gtk.Label()
        hbox.pack_start(lbl1, expand=True, fill=False)

        self.doAutoImportBool = False
        self.startButton = gtk.ToggleButton(_("Start _Auto Import"))
        self.startButton.connect("clicked", self.startClicked, "start clicked")
        hbox.pack_start(self.startButton, expand=False, fill=False)

        self.DetectButton = gtk.Button(_("Detect Directories"))
        self.DetectButton.connect("clicked", self.detect_hh_dirs, "detect")
        #hbox.pack_start(self.DetectButton, expand=False, fill=False)


        lbl2 = gtk.Label()
        hbox.pack_start(lbl2, expand=True, fill=False)

        hbox = gtk.HBox(False, 0)
        hbox.show()

        self.mainVBox.pack_start(hbox, expand=True, padding=3)

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.mainVBox.pack_end(scrolledwindow, expand=True)
        scrolledwindow.add(self.textview)

        self.mainVBox.show_all()
        self.addText(_("Auto Import Ready."))

    def addText(self, text):
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, text)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0)


    #end of GuiAutoImport.__init__
    def browseClicked(self, widget, data):
        """runs when user clicks one of the browse buttons in the auto import tab"""
#       Browse is not valid while hud is running, so return immediately
        if (self.pipe_to_hud):
            return
            
        current_path=data[1].get_text()

        dia_chooser = gtk.FileChooserDialog(title=_("Please choose the path that you want to Auto Import"),
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        #dia_chooser.set_current_folder(pathname)
        dia_chooser.set_filename(current_path)
        #dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import
        dia_chooser.set_show_hidden(True)
        dia_chooser.set_destroy_with_parent(True)
        dia_chooser.set_transient_for(self.parent)

        response = dia_chooser.run()
        if response == gtk.RESPONSE_OK:
            #print dia_chooser.get_filename(), 'selected'
            data[1].set_text(dia_chooser.get_filename())
            self.input_settings[data[0]][0] = dia_chooser.get_filename()
        elif response == gtk.RESPONSE_CANCEL:
            #print 'Closed, no files selected'
            pass
        dia_chooser.destroy()
    #end def GuiAutoImport.browseClicked

    def do_import(self):
        """Callback for timer to do an import iteration."""
        if self.doAutoImportBool:
            self.importer.autoSummaryGrab()
            self.startButton.set_label(_(u'_Auto Import Running'))
            self.importer.runUpdated()
            self.addText(".")
            #sys.stdout.write(".")
            #sys.stdout.flush()
            gobject.timeout_add(1000, self.reset_startbutton)
            return True
        return False

    def reset_startbutton(self):
        if self.pipe_to_hud is not None:
            self.startButton.set_label(_(u'Stop _Auto Import'))
        else:
            self.startButton.set_label(_(u'Start _Auto Import'))

        return False

    def detect_hh_dirs(self, widget, data):
        """Attempt to find user hand history directories for enabled sites"""
        the_sites = self.config.get_supported_sites()
        for site in the_sites:
            params = self.config.get_site_parameters(site)
            if params['enabled'] == True:
                print (_("DEBUG:") + " " + _("Detecting hand history directory for site: '%s'") % site)
                if os.name == 'posix':
                    if self.posix_detect_hh_dirs(site):
                        #data[1].set_text(dia_chooser.get_filename())
                        self.input_settings[(site, 'hh')][0]
                        pass
                elif os.name == 'nt':
                    # Sorry
                    pass

    def posix_detect_hh_dirs(self, site):
        defaults = {
                    'PokerStars': '~/.wine/drive_c/Program Files/PokerStars/HandHistory',
                   }
        if site == 'PokerStars':
            directory = os.path.expanduser(defaults[site])
            for file in [file for file in os.listdir(directory) if not file in [".",".."]]:
                print file
        return False

    def startClicked(self, widget, data):
        """runs when user clicks start on auto import tab"""

        # Check to see if we have an open file handle to the HUD and open one if we do not.
        # bufsize = 1 means unbuffered
        # We need to close this file handle sometime.

        # TODO:  Allow for importing from multiple dirs - REB 29AUG2008
        # As presently written this function does nothing if there is already a pipe open.
        # That is not correct.  It should open another dir for importing while piping the
        # results to the same pipe.  This means that self.path should be a a list of dirs
        # to watch.
        
        if data == "autostart" or (widget == self.startButton and self.startButton.get_active()):
            self.startButton.set_active(True)
            # - Does the lock acquisition need to be more sophisticated for multiple dirs?
            # (see comment above about what to do if pipe already open)
            # - Ideally we want to release the lock if the auto-import is killed by some
            # kind of exception - is this possible?
            if self.settings['global_lock'].acquire(wait=False, source="AutoImport"):   # returns false immediately if lock not acquired
                self.addText("\n" + _("Global lock taken ... Auto Import Started.")+"\n")
                self.doAutoImportBool = True
                self.startButton.set_label(_(u'Stop _Auto Import'))
                self.intervalEntry.set_sensitive(False)
                while gtk.events_pending(): # change the label NOW don't wait for the pipe to open
                    gtk.main_iteration(False)
                if self.pipe_to_hud is None:
                    if self.config.install_method == "exe":    # if py2exe, run hud_main.exe
                        path = self.config.pyfpdb_path
                        command = "HUD_main.exe"
                        bs = 0
                    elif os.name == 'nt':
                        path = sys.path[0].replace('\\','\\\\')
                        if win32console.GetConsoleWindow() == 0:
                            command = 'pythonw "'+path+'\\HUD_main.pyw" ' + self.settings['cl_options']
                        else:
                            command = 'python "'+path+'\\HUD_main.pyw" ' + self.settings['cl_options']
                        bs = 0
                    else:
                        command = os.path.join(sys.path[0], 'HUD_main.pyw')
                        if not os.path.isfile(command):
                            self.addText("\n" + _('*** %s was not found') % (command))
                        command = [command, ] + string.split(self.settings['cl_options'])
                        bs = 1

                        print _("opening pipe to HUD")
                    try:
                        if self.config.install_method == "exe" or (os.name == "nt" and win32console.GetConsoleWindow() == 0):
                            self.pipe_to_hud = subprocess.Popen(command, bufsize=bs,
                                                                stdin=subprocess.PIPE,
                                                                stdout=subprocess.PIPE,  # needed for pythonw / py2exe
                                                                stderr=subprocess.PIPE,  # needed for pythonw / py2exe
                                                                universal_newlines=True
                                                               )
                        else:
                            self.pipe_to_hud = subprocess.Popen(command, bufsize=bs, stdin=subprocess.PIPE, universal_newlines=True)
                    except:
                        self.addText("\n" + _("*** GuiAutoImport Error opening pipe:") + " " + traceback.format_exc() )
                    else:
                        for (site,type) in self.input_settings:
                            self.importer.addImportDirectory(self.input_settings[(site,type)][0], monitor = True, site=(site,type))
                            self.addText("\n * " + _("Add %s import directory %s") % (site, str(self.input_settings[(site,type)][0])))
                            self.do_import()
                    interval = int(self.intervalEntry.get_text())
                    if self.importtimer != 0:
                        gobject.source_remove(self.importtimer)
                    self.importtimer = gobject.timeout_add(interval * 1000, self.do_import)

            else:
                self.addText("\n" + _("Auto Import aborted.") + _("Global lock not available."))
        else: # toggled off
            self.doAutoImportBool = False # do_import will return this and stop the gobject callback timer
            self.importer.autoSummaryGrab(True)
            gobject.source_remove(self.importtimer)
            self.settings['global_lock'].release()
            self.addText("\n" + _("Stopping Auto Import.") + _("Global lock released."))
            if self.pipe_to_hud.poll() is not None:
                self.addText("\n * " + _("Stop Auto Import") + ": " + _("HUD already terminated."))
            else:
                self.pipe_to_hud.terminate()
                #print >>self.pipe_to_hud.stdin, "\n"
                # self.pipe_to_hud.communicate('\n') # waits for process to terminate
            self.pipe_to_hud = None
            self.intervalEntry.set_sensitive(True)
            self.startButton.set_label(_(u'Start _Auto Import'))

    #end def GuiAutoImport.startClicked

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    #Create the site line given required info and setup callbacks
    #enabling and disabling sites from this interface not possible
    #expects a box to layout the line horizontally
    def createSiteLine(self, hbox1, hbox2, site, iconpath, type, path, filter_name, active = True):
        label = gtk.Label(_("%s auto-import:") % site)
        hbox1.pack_start(label, False, False, 3)
        label.show()

        dirPath=gtk.Entry()
        dirPath.set_text(path)
        hbox1.pack_start(dirPath, True, True, 3)
#       Anything typed into dirPath was never recognised (only the browse button works)
#       so just prevent entry to avoid user confusion
        dirPath.set_editable(False)
        
        dirPath.show()

        browseButton=gtk.Button(_("Browse..."))
        browseButton.connect("clicked", self.browseClicked, [(site,type)] + [dirPath])
        hbox2.pack_start(browseButton, False, False, 3)
        browseButton.show()

        label = gtk.Label("filter:")
        hbox2.pack_start(label, False, False, 3)
        label.show()

#       Anything typed into filter was never recognised
#       so just grey it out to avoid user confusion
        filter=gtk.Entry()
        filter.set_text(filter_name)
        hbox2.pack_start(filter, True, True, 3)
        filter.set_sensitive(False)
        filter.show()

    def addSites(self, vbox1, vbox2):
        the_sites = self.config.get_supported_sites()
        #log.debug("addSites: the_sites="+str(the_sites))
        for site in the_sites:
            pathHBox1 = gtk.HBox(False, 0)
            vbox1.pack_start(pathHBox1, False, True, 0)
            pathHBox2 = gtk.HBox(False, 0)
            vbox2.pack_start(pathHBox2, False, True, 0)

            params = self.config.get_site_parameters(site)
            paths = self.config.get_default_paths(site)
            
            self.createSiteLine(pathHBox1, pathHBox2, site, False, 'hh', paths['hud-defaultPath'], params['converter'], params['enabled'])
            self.input_settings[(site, 'hh')] = [paths['hud-defaultPath']] + [params['converter']]
            
            if 'hud-defaultTSPath' in paths:
                pathHBox1 = gtk.HBox(False, 0)
                vbox1.pack_start(pathHBox1, False, True, 0)
                pathHBox2 = gtk.HBox(False, 0)
                vbox2.pack_start(pathHBox2, False, True, 0)
                self.createSiteLine(pathHBox1, pathHBox2, site, False, 'ts', paths['hud-defaultTSPath'], params['summaryImporter'], params['enabled'])
                self.input_settings[(site, 'ts')] = [paths['hud-defaultTSPath']] + [params['summaryImporter']]
        #log.debug("addSites: input_settings="+str(self.input_settings))

if __name__== "__main__":
    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()

#    settings = {}
#    settings['db-host'] = "192.168.1.100"
#    settings['db-user'] = "mythtv"
#    settings['db-password'] = "mythtv"
#    settings['db-databaseName'] = "fpdb"
#    settings['hud-defaultInterval'] = 10
#    settings['hud-defaultPath'] = 'C:/Program Files/PokerStars/HandHistory/nutOmatic'
#    settings['callFpdbHud'] = True

    parser = OptionParser()
    parser.add_option("-q", "--quiet", action="store_false", dest="gui", default=True, help="don't start gui")
    (options, argv) = parser.parse_args()

    config = Configuration.Config()

    settings = {}
    if os.name == 'nt': settings['os'] = 'windows'
    else:               settings['os'] = 'linuxmac'

    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    settings['global_lock'] = interlocks.InterProcessLock(name="fpdb_global_lock")
    settings['cl_options'] = string.join(sys.argv[1:])

    if(options.gui == True):
        i = GuiAutoImport(settings, config, None, None)
        main_window = gtk.Window()
        main_window.connect('destroy', destroy)
        main_window.add(i.mainVBox)
        main_window.show()
        gtk.main()
    else:
        i = GuiAutoImport(settings, config, cli = True)
