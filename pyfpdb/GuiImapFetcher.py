#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Steffen Schaumburg
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

from imaplib import IMAP4
from socket import gaierror

import ImapFetcher

class GuiImapFetcher:
    def __init__(self, config, db, sql, mainwin, debug=True):
        self.config = config
        self.db = db
        self.mainVBox = gtk.VBox()
        
        
        self.buttonsHBox = gtk.HBox()
        self.mainVBox.pack_end(self.buttonsHBox, expand=False)
        
        label=gtk.Label(_("To cancel just close this tab."))
        self.buttonsHBox.add(label)
        
        self.saveButton = gtk.Button(_("Save"))
        self.saveButton.connect('clicked', self.saveClicked)
        self.buttonsHBox.add(self.saveButton)
        
        self.importAllButton = gtk.Button(_("Import All"))
        self.importAllButton.connect('clicked', self.importAllClicked)
        self.buttonsHBox.add(self.importAllButton)
        
        self.statusLabel=gtk.Label(_("If you change the config you must save before importing"))
        self.mainVBox.pack_end(self.statusLabel, expand=False, padding=4)

        self.passwords={}
        self.displayConfig()
        
        self.mainVBox.show_all()
    #end def __init__
    
    def saveClicked(self, widget, data=None):
        row = self.rowVBox.get_children()
        columns=row[0].get_children() #TODO: make save capable of handling multiple email entries - not relevant yet as only one entry is useful atm. The rest of this tab works fine for multiple entries though
        
        siteName=columns[0].get_text()
        fetchType=columns[1].get_text()
        
        toSave=self.config.supported_sites[siteName].emails[fetchType]
        
        toSave.host=columns[2].get_text()
        toSave.username=columns[3].get_text()
        
        if columns[4].get_text()=="***":
            toSave.password=self.passwords[siteName+fetchType]
        else:
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
        self.statusLabel.set_label(_("Starting import. Please wait.")) #FIXME: why doesnt this one show?
        for siteName in self.config.supported_sites:
            for fetchType in self.config.supported_sites[siteName].emails:
                try:
                    result=ImapFetcher.run(self.config.supported_sites[siteName].emails[fetchType], self.db)
                    self.statusLabel.set_label(_("Finished import without error."))
                except IMAP4.error as error:
                    if str(error)=="[AUTHENTICATIONFAILED] Authentication failed.":
                        self.statusLabel.set_label(_("Login to mailserver failed: please check mailserver, username and password"))
                except gaierror as error:
                    if str(error)=="[Errno -2] Name or service not known":
                        self.statusLabel.set_label(_("Could not connect to mailserver: check mailserver and use SSL settings and internet connectivity"))
    #def importAllClicked
    
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox
    
    def displayConfig(self):
        box=gtk.HBox(homogeneous=True)
        for text in (_("Site"), _("Fetch Type"), _("Mail Server"), _("Username"), _("Password"), _("Mail Folder"), _("Use SSL")):
            label=gtk.Label(text)
            box.add(label)
        self.mainVBox.pack_start(box, expand=False)
        
        self.rowVBox = gtk.VBox()
        self.mainVBox.add(self.rowVBox)
        
        for siteName in self.config.supported_sites:
            for fetchType in self.config.supported_sites[siteName].emails:
                config=self.config.supported_sites[siteName].emails[fetchType]
                box=gtk.HBox(homogeneous=True)
                
                for field in (siteName, config.fetchType):
                    label=gtk.Label(field)
                    box.add(label)
                
                for field in (config.host, config.username):
                    entry=gtk.Entry()
                    entry.set_text(field)
                    box.add(entry)
                
                entry=gtk.Entry()
                self.passwords[siteName+fetchType]=config.password
                entry.set_text("***")
                box.add(entry)
                
                entry=gtk.Entry()
                entry.set_text(config.folder)
                box.add(entry)
                
                sslBox = gtk.combo_box_new_text()
                sslBox.append_text(_("Yes"))
                sslBox.append_text(_("No"))
                if config.useSsl:
                    sslBox.set_active(0)
                else:
                    sslBox.set_active(1)
                box.add(sslBox)
                
                #TODO: "run just this one" button
                
                self.rowVBox.pack_start(box, expand=False)
                #print 
        
        self.mainVBox.show_all()
    #end def displayConfig
#end class GuiImapFetcher
