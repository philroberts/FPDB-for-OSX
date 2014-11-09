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

#import os
#import sys
#from optparse import OptionParser
from time import gmtime, mktime, strftime, strptime
#import pokereval

import logging #logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("filter")

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (QDateEdit, QGroupBox, QPushButton)

#import Configuration
#import Database
#import SQL
import Charset
import Filters

class TourneyFilters(Filters.Filters):
    def __init__(self, db, config, qdict, display = {}, debug=True):
        Filters.Filters.__init__(self, db, config, qdict, display, debug)
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

        self.label = {}
        self.callback = {}

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
        self.start_date = QDateEdit(QDate(1970,1,1))
        self.end_date = QDateEdit(QDate(2100,1,1))

        # For use in groups etc
        #self.sbGroups = {}
        self.numTourneys = 0

        playerFrame = QGroupBox(self.filterText['playerstitle'])
        self.fillPlayerFrame(playerFrame, self.display)
        self.layout().addWidget(playerFrame)

        sitesFrame = QGroupBox(self.filterText['sitestitle'])
        self.fillSitesFrame(sitesFrame)
        self.layout().addWidget(sitesFrame)

        # Tourney types
        tourneyTypesFrame = QGroupBox(_('Tourney Type'))
        self.fillTourneyTypesFrame(tourneyTypesFrame)
        #self.layout().addWidget(tourneyTypesFrame)

        # Seats
        seatsFrame = QGroupBox(self.filterText['seatstitle'])
        self.layout().addWidget(seatsFrame)
        self.sbSeats = {}
        self.fillSeatsFrame(seatsFrame)

        # Date
        dateFrame = QGroupBox(self.filterText['datestitle'])
        self.layout().addWidget(dateFrame)
        self.fillDateFrame(dateFrame)

        # Buttons
        #self.Button1=gtk.Button("Unnamed 1")
        #self.Button1.set_sensitive(False)

        self.Button2=QPushButton("Unnamed 2")
        self.Button2.setEnabled(False)
        self.layout().addWidget(self.Button2)

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

if __name__ == '__main__':
    import Configuration
    config = Configuration.Config(file = "HUD_config.test.xml")
    import Database
    db = Database.Database(config)

    import SQL
    qdict = SQL.Sql(db_server = 'sqlite')

    filters_display = { "Heroes"    : True,
                        "Sites"     : True,
                        "Games"     : False,
                        "Cards"     : False,
                        "Currencies": False,
                        "Limits"    : False,
                        "LimitSep"  : False,
                        "LimitType" : False,
                        "Type"      : False,
                        "UseType"   : 'tour',
                        "Seats"     : True,
                        "SeatSep"   : False,
                        "Dates"     : True,
                        "GraphOps"  : False,
                        "Groups"    : False,
                        "Button1"   : False,
                        "Button2"   : True
                          }

    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication([])
    i = TourneyFilters(db, config, qdict, display = filters_display)
    main_window = QMainWindow()
    main_window.setCentralWidget(i)
    main_window.show()
    app.exec_()
