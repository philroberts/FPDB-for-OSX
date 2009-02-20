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

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import sys
import time
import fpdb_import


class GuiAutoImport (threading.Thread):
    def __init__(self, settings, config):
        """Constructor for GuiAutoImport"""
        self.settings=settings
        self.config=config

        imp = self.config.get_import_parameters()

        print "Import parameters"
        print imp

        self.input_settings = {}
        self.pipe_to_hud = None

        self.importer = fpdb_import.Importer(self,self.settings, self.config)
        self.importer.setCallHud(True)
        self.importer.setMinPrint(30)
        self.importer.setQuiet(False)
        self.importer.setFailOnError(False)
        self.importer.setHandCount(0)
#        self.importer.setWatchTime()
        
        self.server=settings['db-host']
        self.user=settings['db-user']
        self.password=settings['db-password']
        self.database=settings['db-databaseName']

        self.mainVBox=gtk.VBox(False,1)
        self.mainVBox.show()

        self.settingsHBox = gtk.HBox(False, 0)
        self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
        self.settingsHBox.show()

        self.intervalLabel = gtk.Label("Interval (ie. break) between imports in seconds:")
        self.settingsHBox.pack_start(self.intervalLabel)
        self.intervalLabel.show()

        self.intervalEntry=gtk.Entry()
        self.intervalEntry.set_text(str(self.config.get_import_parameters().get("interval")))
        self.settingsHBox.pack_start(self.intervalEntry)
        self.intervalEntry.show()

        self.addSites(self.mainVBox)

        self.doAutoImportBool = False
        self.startButton=gtk.ToggleButton("Start Autoimport")
        self.startButton.connect("clicked", self.startClicked, "start clicked")
        self.mainVBox.add(self.startButton)
        self.startButton.show()


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
            print 'Closed, no files selected'
        dia_chooser.destroy()
    #end def GuiAutoImport.browseClicked

    def do_import(self):
        """Callback for timer to do an import iteration."""
        if self.doAutoImportBool:
            self.importer.runUpdated()
            print "GuiAutoImport.import_dir done"
            return True
        else:
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
            self.doAutoImportBool = True
            widget.set_label(u'Stop Autoimport')
            if self.pipe_to_hud is None:
                if os.name == 'nt':
                    command = "python HUD_run_me.py" + " %s" % (self.database)
                    bs = 0    # windows is not happy with line buffing here
                    self.pipe_to_hud = subprocess.Popen(command, bufsize = bs, stdin = subprocess.PIPE, 
                                                    universal_newlines=True)
                else:
                    command = self.config.execution_path('HUD_run_me.py')
                    bs = 1
                    self.pipe_to_hud = subprocess.Popen((command, self.database), bufsize = bs, stdin = subprocess.PIPE, 
                                                    universal_newlines=True)
    #            self.pipe_to_hud = subprocess.Popen((command, self.database), bufsize = bs, stdin = subprocess.PIPE,
    #                                                universal_newlines=True)
    #            command = command + " %s" % (self.database)
    #            print "command = ", command
    #            self.pipe_to_hud = os.popen(command, 'w')

    #            Add directories to importer object.
                for site in self.input_settings:
                    self.importer.addImportDirectory(self.input_settings[site][0], True, site, self.input_settings[site][1])
                    print "Adding import directories - Site: " + site + " dir: "+ str(self.input_settings[site][0])
                self.do_import()

                interval=int(self.intervalEntry.get_text())
                gobject.timeout_add(interval*1000, self.do_import)
        else: # toggled off
            self.doAutoImportBool = False # do_import will return this and stop the gobject callback timer
            print "Stopping autoimport"
            if self.pipe_to_hud.poll() is not None:
                print "HUD already terminated"
            else:
                #print >>self.pipe_to_hud.stdin, "\n"
                self.pipe_to_hud.communicate('\n') # waits for process to terminate
            self.pipe_to_hud = None
            self.startButton.set_label(u'Start Autoimport')
            
                

    #end def GuiAutoImport.startClicked

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    #Create the site line given required info and setup callbacks
    #enabling and disabling sites from this interface not possible
    #expects a box to layout the line horizontally
    def createSiteLine(self, hbox, site, iconpath, hhpath, filter_name, active = True):
        label = gtk.Label(site + " auto-import:")
        hbox.pack_start(label, False, False, 0)
        label.show()

        dirPath=gtk.Entry()
        dirPath.set_text(hhpath)
        hbox.pack_start(dirPath, False, True, 0)
        dirPath.show()

        browseButton=gtk.Button("Browse...")
        browseButton.connect("clicked", self.browseClicked, [site] + [dirPath])
        hbox.pack_start(browseButton, False, False, 0)
        browseButton.show()

        label = gtk.Label(site + " filter:")
        hbox.pack_start(label, False, False, 0)
        label.show()

        filter=gtk.Entry()
        filter.set_text(filter_name)
        hbox.pack_start(filter, False, True, 0)
        filter.show()

    def addSites(self, vbox):
        for site in self.config.supported_sites.keys():
            pathHBox = gtk.HBox(False, 0)
            vbox.pack_start(pathHBox, False, True, 0)
            pathHBox.show()

            paths = self.config.get_default_paths(site)
            params = self.config.get_site_parameters(site)
            self.createSiteLine(pathHBox, site, False, paths['hud-defaultPath'], params['converter'], params['enabled'])
            self.input_settings[site] = [paths['hud-defaultPath']] + [params['converter']]

if __name__== "__main__":
    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()

    settings = {}
    settings['db-host'] = "192.168.1.100"
    settings['db-user'] = "mythtv"
    settings['db-password'] = "mythtv"
    settings['db-databaseName'] = "fpdb"
    settings['hud-defaultInterval'] = 10
    settings['hud-defaultPath'] = 'C:/Program Files/PokerStars/HandHistory/nutOmatic'
    settings['callFpdbHud'] = True

    i = GuiAutoImport(settings)
    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    main_window.add(i.mainVBox)
    main_window.show()
    gtk.main()
