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

import threading
import subprocess
import traceback

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import sys
import time
import fpdb_import
from optparse import OptionParser
import Configuration
import string

class GuiAutoImport (threading.Thread):
    def __init__(self, settings, config, sql):
        self.importtimer = 0
        self.settings = settings
        self.config = config
        self.sql = sql

        imp = self.config.get_import_parameters()

#        print "Import parameters"
#        print imp

        self.input_settings = {}
        self.pipe_to_hud = None

        self.importer = fpdb_import.Importer(self, self.settings, self.config, self.sql)
        self.importer.setCallHud(True)
        self.importer.setMinPrint(settings['minPrint'])
        self.importer.setQuiet(False)
        self.importer.setFailOnError(False)
        self.importer.setHandCount(0)
#        self.importer.setWatchTime()

        self.server = settings['db-host']
        self.user = settings['db-user']
        self.password = settings['db-password']
        self.database = settings['db-databaseName']

        self.mainVBox = gtk.VBox(False,1)

        hbox = gtk.HBox(True, 0) # contains 2 equal vboxes
        self.mainVBox.pack_start(hbox, False, False, 0)

        vbox1 = gtk.VBox(True, 0)
        hbox.pack_start(vbox1, True, True, 0)
        vbox2 = gtk.VBox(True, 0)
        hbox.pack_start(vbox2, True, True, 0)

        self.intervalLabel = gtk.Label("Time between imports in seconds:")
        self.intervalLabel.set_alignment(xalign=1.0, yalign=0.5)
        vbox1.pack_start(self.intervalLabel, False, True, 0)

        hbox = gtk.HBox(False, 0)
        vbox2.pack_start(hbox, False, True, 0)
        self.intervalEntry = gtk.Entry()
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
        self.startButton = gtk.ToggleButton("  _Start Autoimport  ")
        self.startButton.connect("clicked", self.startClicked, "start clicked")
        hbox.pack_start(self.startButton, expand=False, fill=False)


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
        self.addText("AutoImport Ready.")

    def addText(self, text):
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, text)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0)


    #end of GuiAutoImport.__init__
    def browseClicked(self, widget, data):
        """runs when user clicks one of the browse buttons in the auto import tab"""
        current_path=data[1].get_text()

        dia_chooser = gtk.FileChooserDialog(title="Please choose the path that you want to auto import",
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        #dia_chooser.set_current_folder(pathname)
        dia_chooser.set_filename(current_path)
        #dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import

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
            self.startButton.set_label(u' I M P O R T I N G  ')
            self.importer.runUpdated()
            self.addText(".")
            #sys.stdout.write(".")
            #sys.stdout.flush()
            gobject.timeout_add(1000, self.reset_startbutton)
            return True
        return False

    def reset_startbutton(self):
        if self.pipe_to_hud is not None:
            self.startButton.set_label(u'  _Stop Autoimport  ')
        else:
            self.startButton.set_label(u'  _Start Autoimport  ')

        return False


    def startClicked(self, widget, data):
        """runs when user clicks start on auto import tab"""

#    Check to see if we have an open file handle to the HUD and open one if we do not.
#    bufsize = 1 means unbuffered
#    We need to close this file handle sometime.

#    TODO:  Allow for importing from multiple dirs - REB 29AUG2008
#    As presently written this function does nothing if there is already a pipe open.
#    That is not correct.  It should open another dir for importing while piping the
#    results to the same pipe.  This means that self.path should be a a list of dirs
#    to watch.
        if widget.get_active(): # toggled on
            # - Does the lock acquisition need to be more sophisticated for multiple dirs?
            # (see comment above about what to do if pipe already open)
            # - Ideally we want to release the lock if the auto-import is killed by some
            # kind of exception - is this possible?
            if self.settings['global_lock'].acquire(False):   # returns false immediately if lock not acquired
                self.addText("\nGlobal lock taken ... Auto Import Started.\n")
                self.doAutoImportBool = True
                widget.set_label(u'  _Stop Autoimport  ')
                if self.pipe_to_hud is None:
                    if Configuration.FROZEN:
                        path = Configuration.EXEC_PATH
                        command = "HUD_main.exe"
                        bs = 0
                    elif os.name == 'nt':
                        path = sys.path[0].replace('\\','\\\\')
                        command = 'pythonw "'+path+'\\HUD_main.pyw" ' + self.settings['cl_options']
                        bs = 0
                    else:
                        command = os.path.join(sys.path[0], 'HUD_main.pyw')
                        command = [command, ] + string.split(self.settings['cl_options'])
                        bs = 1

                    try:
                        print "opening pipe to HUD"
                        self.pipe_to_hud = subprocess.Popen(command, bufsize=bs,
                                                            stdin=subprocess.PIPE,
                                                            stdout=subprocess.PIPE,  # only needed for py2exe
                                                            stderr=subprocess.PIPE,  # only needed for py2exe
                                                            universal_newlines=True
                                                           )
                        #self.pipe_to_hud.stdout.close()
                        #self.pipe_to_hud.stderr.close()
                    except:
                        err = traceback.extract_tb(sys.exc_info()[2])[-1]
                        #self.addText( "\n*** GuiAutoImport Error opening pipe: " + err[2] + "(" + str(err[1]) + "): " + str(sys.exc_info()[1]))
                        self.addText( "\n*** GuiAutoImport Error opening pipe: " + traceback.format_exc() )
                    else:
                        for site in self.input_settings:
                            self.importer.addImportDirectory(self.input_settings[site][0], True, site, self.input_settings[site][1])
                            self.addText("\n * Add "+ site+ " import directory "+ str(self.input_settings[site][0]))
                            self.do_import()
                            interval = int(self.intervalEntry.get_text())
                    if self.importtimer != 0:
                        gobject.source_remove(self.importtimer)
                    self.importtimer = gobject.timeout_add(interval * 1000, self.do_import)

            else:
                self.addText("\nauto-import aborted - global lock not available")
        else: # toggled off
            gobject.source_remove(self.importtimer)
            self.settings['global_lock'].release()
            self.doAutoImportBool = False # do_import will return this and stop the gobject callback timer
            self.addText("\nStopping autoimport - global lock released.")
            if self.pipe_to_hud.poll() is not None:
                self.addText("\n * Stop Autoimport: HUD already terminated")
            else:
                #print >>self.pipe_to_hud.stdin, "\n"
                self.pipe_to_hud.communicate('\n') # waits for process to terminate
            self.pipe_to_hud = None
            self.startButton.set_label(u'  _Start Autoimport  ')

    #end def GuiAutoImport.startClicked

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    #Create the site line given required info and setup callbacks
    #enabling and disabling sites from this interface not possible
    #expects a box to layout the line horizontally
    def createSiteLine(self, hbox1, hbox2, site, iconpath, hhpath, filter_name, active = True):
        label = gtk.Label("%s auto-import:" % site)
        hbox1.pack_start(label, False, False, 3)
        label.show()

        dirPath=gtk.Entry()
        dirPath.set_text(hhpath)
        hbox1.pack_start(dirPath, True, True, 3)
        dirPath.show()

        browseButton=gtk.Button("Browse...")
        browseButton.connect("clicked", self.browseClicked, [site] + [dirPath])
        hbox2.pack_start(browseButton, False, False, 3)
        browseButton.show()

        label = gtk.Label("%s filter:" % site)
        hbox2.pack_start(label, False, False, 3)
        label.show()

        filter=gtk.Entry()
        filter.set_text(filter_name)
        hbox2.pack_start(filter, True, True, 3)
        filter.show()

    def addSites(self, vbox1, vbox2):
        the_sites = self.config.get_supported_sites()
        for site in the_sites:
            pathHBox1 = gtk.HBox(False, 0)
            vbox1.pack_start(pathHBox1, False, True, 0)
            pathHBox2 = gtk.HBox(False, 0)
            vbox2.pack_start(pathHBox2, False, True, 0)

            params = self.config.get_site_parameters(site)
            paths = self.config.get_default_paths(site)
            self.createSiteLine(pathHBox1, pathHBox2, site, False, paths['hud-defaultPath'], params['converter'], params['enabled'])
            self.input_settings[site] = [paths['hud-defaultPath']] + [params['converter']]

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
    parser.add_option("-m", "--minPrint", "--status", dest="minPrint", default="0", type="int",
                    help="How often to print a one-line status report (0 (default) means never)")
    (options, argv) = parser.parse_args()

    config = Configuration.Config()

    settings = {}
    settings['minPrint'] = options.minPrint
    if os.name == 'nt': settings['os'] = 'windows'
    else:               settings['os'] = 'linuxmac'

    settings.update(config.get_db_parameters('fpdb'))
    settings.update(config.get_tv_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    if(options.gui == True):
        i = GuiAutoImport(settings, config)
        main_window = gtk.Window()
        main_window.connect('destroy', destroy)
        main_window.add(i.mainVBox)
        main_window.show()
        gtk.main()
    else:
        pass
