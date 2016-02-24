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

import os
import sys

import logging

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QLineEdit, QTextEdit, QCheckBox, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor

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


class GuiAutoImport(QWidget):
    def __init__(self, settings, config, sql = None, parent = None, cli = False):
        QWidget.__init__(self, parent)
        self.importtimer = None
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
        self.setLayout(QVBoxLayout())

        hbox = QHBoxLayout()

        self.intervalLabel = QLabel(_("Time between imports in seconds:"))

        self.intervalEntry = QSpinBox()
        self.intervalEntry.setValue(int(self.config.get_import_parameters().get("interval")))
        hbox.addWidget(self.intervalLabel)
        hbox.addWidget(self.intervalEntry)
        self.layout().addLayout(hbox)

        hbox = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        self.layout().addLayout(hbox)

        self.addSites(vbox1, vbox2)

        self.textview = QTextEdit()
        self.textview.setReadOnly(True)

        self.doAutoImportBool = False
        self.startButton = QCheckBox(_("Start Auto Import"))
        self.startButton.stateChanged.connect(self.startClicked)
        self.layout().addWidget(self.startButton)
        self.layout().addWidget(self.textview)

        self.addText(_("Auto Import Ready."))

    def addText(self, text):
        self.textview.moveCursor(QTextCursor.End)
        self.textview.insertPlainText(text)


    #end of GuiAutoImport.__init__
    def browseClicked(self):
        """runs when user clicks one of the browse buttons in the auto import tab"""
#       Browse is not valid while hud is running, so return immediately
        if (self.pipe_to_hud):
            return
        data = self.sender().hackdata
        current_path=data[1].text()

        newdir = QFileDialog.getExistingDirectory(self, caption=_("Please choose the path that you want to Auto Import"),
                                        directory=current_path)
        if newdir:
            #print dia_chooser.get_filename(), 'selected'
            data[1].setText(newdir)
            self.input_settings[data[0]][0] = newdir
    #end def GuiAutoImport.browseClicked

    def do_import(self):
        """Callback for timer to do an import iteration."""
        if self.doAutoImportBool:
            self.importer.autoSummaryGrab()
            self.importer.runUpdated()
            self.addText(".")
            return True
        return False

    def reset_startbutton(self):
        if self.pipe_to_hud is not None:
            self.startButton.set_label(_(u'Stop Auto Import'))
        else:
            self.startButton.set_label(_(u'Start Auto Import'))

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

    def startClicked(self):
        """runs when user clicks start on auto import tab"""

        # Check to see if we have an open file handle to the HUD and open one if we do not.
        # bufsize = 1 means unbuffered
        # We need to close this file handle sometime.

        # TODO:  Allow for importing from multiple dirs - REB 29AUG2008
        # As presently written this function does nothing if there is already a pipe open.
        # That is not correct.  It should open another dir for importing while piping the
        # results to the same pipe.  This means that self.path should be a a list of dirs
        # to watch.
        
        if self.startButton.isChecked():
            # - Does the lock acquisition need to be more sophisticated for multiple dirs?
            # (see comment above about what to do if pipe already open)
            # - Ideally we want to release the lock if the auto-import is killed by some
            # kind of exception - is this possible?
            if self.settings['global_lock'].acquire(wait=False, source="AutoImport"):   # returns false immediately if lock not acquired
                self.addText("\n" + _("Global lock taken ... Auto Import Started.")+"\n")
                self.doAutoImportBool = True
                self.intervalEntry.setEnabled(False)
                if self.pipe_to_hud is None:
                    if self.config.install_method == "exe":    # if py2exe, run hud_main.exe
                        path = self.config.pyfpdb_path
                        command = "HUD_main.exe"
                        bs = 0
                    elif self.config.install_method == "app":
                        command = os.path.join(sys.path[0], "HUD_main")
                        bs = 1
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
                            self.addText("\n * " + _("Add %s import directory %s") % (site, self.input_settings[(site,type)][0]))
                            self.do_import()
                    interval = self.intervalEntry.value()
                    self.importtimer = QTimer()
                    self.importtimer.timeout.connect(self.do_import)
                    self.importtimer.start(interval * 1000)

            else:
                self.addText("\n" + _("Auto Import aborted.") + _("Global lock not available."))
        else: # toggled off
            self.doAutoImportBool = False # do_import will return this and stop the gobject callback timer
            self.importtimer = None
            self.importer.autoSummaryGrab(True)
            self.settings['global_lock'].release()
            self.addText("\n" + _("Stopping Auto Import.") + _("Global lock released."))
            if self.pipe_to_hud.poll() is not None:
                self.addText("\n * " + _("Stop Auto Import") + ": " + _("HUD already terminated."))
            else:
                self.pipe_to_hud.terminate()
                #print >>self.pipe_to_hud.stdin, "\n"
                # self.pipe_to_hud.communicate('\n') # waits for process to terminate
            self.pipe_to_hud = None
            self.intervalEntry.setEnabled(True)

    #end def GuiAutoImport.startClicked

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    #Create the site line given required info and setup callbacks
    #enabling and disabling sites from this interface not possible
    #expects a box to layout the line horizontally
    def createSiteLine(self, hbox1, hbox2, site, iconpath, type, path, filter_name, active = True):
        label = QLabel(_("%s auto-import:") % site)
        hbox1.addWidget(label)

        dirPath=QLineEdit()
        dirPath.setText(path)
        hbox1.addWidget(dirPath)
#       Anything typed into dirPath was never recognised (only the browse button works)
#       so just prevent entry to avoid user confusion
        dirPath.setReadOnly(True)

        browseButton=QPushButton(_("Browse..."))
        browseButton.hackdata = [(site, type)] + [dirPath]
        browseButton.clicked.connect(self.browseClicked)#, [(site,type)] + [dirPath])
        hbox2.addWidget(browseButton)

        label = QLabel("filter:")
        hbox2.addWidget(label)

#       Anything typed into filter was never recognised
#       so just grey it out to avoid user confusion
        filterLine = QLineEdit()
        filterLine.setText(filter_name)
        filterLine.setEnabled(False)
        hbox2.addWidget(filterLine)

    def addSites(self, vbox1, vbox2):
        the_sites = self.config.get_supported_sites()
        #log.debug("addSites: the_sites="+str(the_sites))
        for site in the_sites:
            pathHBox1 = QHBoxLayout()
            vbox1.addLayout(pathHBox1)
            pathHBox2 = QHBoxLayout()
            vbox2.addLayout(pathHBox2)

            params = self.config.get_site_parameters(site)
            paths = self.config.get_default_paths(site)
            
            self.createSiteLine(pathHBox1, pathHBox2, site, False, 'hh', paths['hud-defaultPath'], params['converter'], params['enabled'])
            self.input_settings[(site, 'hh')] = [paths['hud-defaultPath']] + [params['converter']]
            
            if 'hud-defaultTSPath' in paths:
                pathHBox1 = QHBoxLayout()
                vbox1.addLayout(pathHBox1)
                pathHBox2 = QHBoxLayout()
                vbox2.addLayout(pathHBox2)
                self.createSiteLine(pathHBox1, pathHBox2, site, False, 'ts', paths['hud-defaultTSPath'], params['summaryImporter'], params['enabled'])
                self.input_settings[(site, 'ts')] = [paths['hud-defaultTSPath']] + [params['summaryImporter']]
        #log.debug("addSites: input_settings="+str(self.input_settings))

if __name__== "__main__":
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
        from PyQt5.QtWidgets import QApplication, QMainWindow
        app = QApplication([])
        i = GuiAutoImport(settings, config, None, None)
        main_window = QMainWindow()
        main_window.setCentralWidget(i)
        main_window.show()
        app.exec_()
    else:
        i = GuiAutoImport(settings, config, cli = True)
