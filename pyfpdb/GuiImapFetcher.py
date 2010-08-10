#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2010 Steffen Schaumburg
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

import threading
import pygtk
pygtk.require('2.0')
import gtk
import ImapFetcher

class GuiImapFetcher (threading.Thread):
    def __init__(self, config, db, sql, mainwin, debug=True):
        self.config = config
        self.db = db
        self.mainVBox = gtk.VBox()
        
        
        self.buttonsHBox = gtk.HBox()
        self.mainVBox.pack_end(self.buttonsHBox, expand=False)
        
        label=gtk.Label("To cancel just close this tab")
        self.buttonsHBox.add(label)
        
        self.saveButton = gtk.Button("_Save Configuration")
        self.saveButton.connect('clicked', self.saveClicked)
        self.buttonsHBox.add(self.saveButton)
        
        self.runAllButton = gtk.Button("_Run All")
        self.runAllButton.connect('clicked', self.runAllClicked)
        self.buttonsHBox.add(self.runAllButton)
        
        self.statusLabel=gtk.Label("Please edit your config if you wish and then click Run All")
        self.mainVBox.pack_end(self.statusLabel, expand=False, padding=4)

        self.rowVBox = gtk.VBox()
        self.mainVBox.add(self.rowVBox)
        
        self.displayConfig()
        
        self.mainVBox.show_all()
    #end def __init__
    
    def saveClicked(self, widget, data=None):
        pass
    #def saveClicked
    
    def runAllClicked(self, widget, data=None):
        self.statusLabel.set_label("Starting import. Please wait.") #FIXME: why doesnt this one show?
        for email in self.config.emails:
            result=ImapFetcher.run(self.config.emails[email], self.db)
        self.statusLabel.set_label("Finished import without error.")
    #def runAllClicked
    
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox
    
    def displayConfig(self):
        print self.config.emails
        for email in self.config.emails:
            print self.config.emails[email]
        
    #end def displayConfig
#end class GuiImapFetcher
