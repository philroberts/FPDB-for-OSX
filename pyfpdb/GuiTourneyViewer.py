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

class GuiTourneyViewer (threading.Thread):
    def __init__(self, config, db, sql, mainwin, debug=True):
        self.db = db
        
        self.mainVBox = gtk.VBox()
        self.interfaceHBox = gtk.HBox()
        self.mainVBox.pack_start(self.interfaceHBox, expand=False)
        
        self.siteBox = gtk.combo_box_new_text()
        for site in config.supported_sites:
            self.siteBox.append_text(site)
        self.siteBox.set_active(0)
        self.interfaceHBox.add(self.siteBox)
        
        label=gtk.Label("Enter the tourney number you want to display:")
        self.interfaceHBox.add(label)
        
        self.entryTourney = gtk.Entry()
        self.interfaceHBox.add(self.entryTourney)
        
        self.displayButton = gtk.Button("_Display")
        self.displayButton.connect('clicked', self.displayClicked)
        self.interfaceHBox.add(self.displayButton)
        
        self.entryPlayer = gtk.Entry()
        self.interfaceHBox.add(self.entryPlayer)
        
        self.playerButton = gtk.Button("Display _Player")
        self.playerButton.connect('clicked', self.displayPlayerClicked)
        self.interfaceHBox.add(self.playerButton)
        
        self.table = gtk.Table(columns=10, rows=9)
        self.mainVBox.add(self.table)
        
        self.mainVBox.show_all()
    #end def __init__
    
    def displayClicked(self, widget, data=None):
        tourneyNo=int(self.entryTourney.get_text())
        siteName=self.siteBox.get_active_text()
        
        self.table.destroy()
        self.table=gtk.Table(columns=10, rows=9)
        self.mainVBox.add(self.table)
        
        result=self.db.getTourneyInfo(siteName, tourneyNo)
        x=0
        y=0
        for i in range(1,len(result[0])):
            if y==9:
                x+=2
                y=0
            
            label=gtk.Label(result[0][i])
            self.table.attach(label,x,x+1,y,y+1)
            
            if result[1][i]==None:
                label=gtk.Label("N/A")
            else:
                label=gtk.Label(result[1][i])
            self.table.attach(label,x+1,x+2,y,y+1)
            
            y+=1
        self.mainVBox.show_all()
    #def displayClicked
    
    def displayPlayerClicked(self, widget, data=None):
        tourneyNo=int(self.entryTourney.get_text())
        siteName=self.siteBox.get_active_text()
        playerName=self.entryPlayer.get_text()
        
        self.table.destroy()
        self.table=gtk.Table(columns=4, rows=5)
        self.mainVBox.add(self.table)
        
        result=self.db.getTourneyPlayerInfo(siteName, tourneyNo, playerName)
        x=0
        y=0
        for i in range(1,len(result[0])):
            if y==5:
                x+=2
                y=0
            
            label=gtk.Label(result[0][i])
            self.table.attach(label,x,x+1,y,y+1)
            
            if result[1][i]==None:
                label=gtk.Label("N/A")
            else:
                label=gtk.Label(result[1][i])
            self.table.attach(label,x+1,x+2,y,y+1)
            
            y+=1
        self.mainVBox.show_all()
    #def displayPlayerClicked
    
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox
#end class GuiTourneyViewer
