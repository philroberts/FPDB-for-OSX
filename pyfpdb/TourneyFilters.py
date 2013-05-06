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

#TODO: migrate all of this into Filters.py

import L10n
_ = L10n.get_translation()

import pygtk
pygtk.require('2.0')
import gtk
import gobject
#import os
#import sys
#from optparse import OptionParser
from time import gmtime, mktime, strftime, strptime
#import pokereval

import logging #logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("filter")

#import Configuration
#import Database
#import SQL
import Charset
import Filters

class TourneyFilters(Filters.Filters):
    def __init__(self, db, config, qdict, display = {}, debug=True):
        self.debug = debug
        self.db = db
        self.cursor = db.cursor
        self.sql = db.sql
        self.conf = db.config
        self.display = display
        
        self.filterText = {'playerstitle':_('Hero:'), 'sitestitle':_('Sites:'), 'seatstitle':_('Number of Players:'),
                    'seatsbetween':_('Between:'), 'seatsand':_('And:'), 'datestitle':_('Date:'),
                    'tourneyTypesTitle':_('Tourney Type')}
        
        gen = self.conf.get_general_params()
        self.day_start = 0
        if 'day_start' in gen:
            self.day_start = float(gen['day_start'])

        self.sw = gtk.ScrolledWindow()
        self.sw.set_border_width(0)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_size_request(370, 300)

        # Outer Packing box
        self.mainVBox = gtk.VBox(False, 0)
        self.sw.add_with_viewport(self.mainVBox)
        self.sw.show()

        self.label = {}
        self.callback = {}

        self.make_filter()
    #end def __init__
    
    def __refresh(self, widget, entry): #identical with Filters
        for w in self.mainVBox.get_children():
            w.destroy()
        self.make_filter()
    #end def __refresh

    def make_filter(self):
        self.tourneyTypes = {}
        #self.tourneys = {}
        self.sites = {}
        self.seats = {}
        self.siteid = {}
        self.heroes = {}
        self.boxes = {}
        self.toggles  = {}

        for site in self.conf.get_supported_sites():
            #Get db site id for filtering later
            self.cursor.execute(self.sql.query['getSiteId'], (site,))
            result = self.db.cursor.fetchall()
            if len(result) == 1:
                self.siteid[site] = result[0][0]
            else:
                log.debug(_("Either 0 or more than one site matched for %s") % site)

        # For use in date ranges.
        self.start_date = gtk.Entry(max=12)
        self.end_date = gtk.Entry(max=12)
        self.start_date.set_property('editable', False)
        self.end_date.set_property('editable', False)

        # For use in groups etc
        #self.sbGroups = {}
        self.numTourneys = 0

        playerFrame = gtk.Frame()
        playerFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillPlayerFrame(vbox, self.display)
        playerFrame.add(vbox)

        sitesFrame = gtk.Frame()
        sitesFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillSitesFrame(vbox)
        sitesFrame.add(vbox)

        # Tourney types
        tourneyTypesFrame = gtk.Frame()
        tourneyTypesFrame.set_label_align(0.0, 0.0)
        tourneyTypesFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillTourneyTypesFrame(vbox)
        tourneyTypesFrame.add(vbox)

        # Seats
        seatsFrame = gtk.Frame()
        seatsFrame.show()
        vbox = gtk.VBox(False, 0)
        self.sbSeats = {}

        self.fillSeatsFrame(vbox, self.display)
        seatsFrame.add(vbox)

        # Date
        dateFrame = gtk.Frame()
        dateFrame.set_label_align(0.0, 0.0)
        dateFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillDateFrame(vbox)
        dateFrame.add(vbox)

        # Buttons
        #self.Button1=gtk.Button("Unnamed 1")
        #self.Button1.set_sensitive(False)

        self.Button2=gtk.Button("Unnamed 2")
        self.Button2.set_sensitive(False)

        expand = False
        self.mainVBox.pack_start(playerFrame, expand)
        self.mainVBox.pack_start(sitesFrame, expand)
        self.mainVBox.pack_start(seatsFrame, expand)
        self.mainVBox.pack_start(dateFrame, expand)
        self.mainVBox.pack_start(gtk.VBox(False, 0))
        #self.mainVBox.pack_start(self.Button1, expand)
        self.mainVBox.pack_start(self.Button2, expand)

        self.mainVBox.show_all()

        # Should do this cleaner
        if "Heroes" not in self.display or self.display["Heroes"] == False:
            playerFrame.hide()
        if "Sites" not in self.display or self.display["Sites"] == False:
            sitesFrame.hide()
        if "Seats" not in self.display or self.display["Seats"] == False:
            seatsFrame.hide()
        if "Dates" not in self.display or self.display["Dates"] == False:
            dateFrame.hide()
        #if "Button1" not in self.display or self.display["Button1"] == False:
        #    self.Button1.hide()
        if "Button2" not in self.display or self.display["Button2"] == False:
            self.Button2.hide()

        #if 'button1' in self.label and self.label['button1']:
        #    self.Button1.set_label( self.label['button1'] )
        if 'button2' in self.label and self.label['button2']:
            self.Button2.set_label( self.label['button2'] )
        #if 'button1' in self.callback and self.callback['button1']:
        #    self.Button1.connect("clicked", self.callback['button1'], "clicked")
        #    self.Button1.set_sensitive(True)
        if 'button2' in self.callback and self.callback['button2']:
            self.Button2.connect("clicked", self.callback['button2'], "clicked")
            self.Button2.set_sensitive(True)

        # make sure any locks on db are released:
        self.db.rollback()
    #end def make_filter
#end class TourneyFilters
