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
        
        label=gtk.Label("To cancel just close this tab.")
        self.buttonsHBox.add(label)
        
        self.saveButton = gtk.Button("_Save")
        self.saveButton.connect('clicked', self.saveClicked)
        self.buttonsHBox.add(self.saveButton)
        
        self.importAllButton = gtk.Button("_Import All")
        self.importAllButton.connect('clicked', self.importAllClicked)
        self.buttonsHBox.add(self.importAllButton)
        
        self.statusLabel=gtk.Label("If you change the config you must save before importing")
        self.mainVBox.pack_end(self.statusLabel, expand=False, padding=4)

        
        self.displayConfig()
        
        self.mainVBox.show_all()
    #end def __init__
    
    def saveClicked(self, widget, data=None):
        row = self.rowVBox.get_children()
        columns=row[0].get_children() #TODO: make save capable of handling multiple email entries - not relevant yet as only one entry is useful atm. The rest of this tab works fine for multiple entries though
        
        siteName=columns[0].get_text()
        fetchType=columns[1].get_text()
        code=siteName+"_"+fetchType
        
        for email in self.config.emails:
            toSave=self.config.emails[email]
            break
        toSave.siteName=siteName
        toSave.fetchType=fetchType
        
        toSave.host=columns[2].get_text()
        toSave.username=columns[3].get_text()
        toSave.password=columns[4].get_text()
        toSave.folder=columns[5].get_text()
        
        if columns[6].get_active() == 0:
            toSave.useSsl="True"
        else:
            toSave.useSsl="False"
            
        self.config.editEmail(siteName, fetchType, toSave)
        self.config.save()
    #def saveClicked
    
    def importAllClicked(self, widget, data=None):
        self.statusLabel.set_label("Starting import. Please wait.") #FIXME: why doesnt this one show?
        for email in self.config.emails:
            result=ImapFetcher.run(self.config.emails[email], self.db)
        self.statusLabel.set_label("Finished import without error.")
    #def importAllClicked
    
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox
    
    def displayConfig(self):
        box=gtk.HBox(homogeneous=True)
        for text in ("Site", "Fetch Type", "Mailserver", "Username", "Password", "Mail Folder", "Use SSL"):
            label=gtk.Label(text)
            box.add(label)
        self.mainVBox.pack_start(box, expand=False)
        
        self.rowVBox = gtk.VBox()
        self.mainVBox.add(self.rowVBox)
        
        for email in self.config.emails:
            config=self.config.emails[email]
            box=gtk.HBox(homogeneous=True)
            
            for field in (config.siteName, config.fetchType):
                label=gtk.Label(field)
                box.add(label)
            
            for field in (config.host, config.username, config.password, config.folder):
                entry=gtk.Entry()
                entry.set_text(field)
                box.add(entry)
            
            sslBox = gtk.combo_box_new_text()
            sslBox.append_text("Yes")
            sslBox.append_text("No")
            sslBox.set_active(0)
            box.add(sslBox)
            
            #TODO: "run just this one" button
            
            self.rowVBox.pack_start(box, expand=False)
            #print 
        
        self.mainVBox.show_all()
    #end def displayConfig
#end class GuiImapFetcher
