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

#import traceback
import threading
import pygtk
pygtk.require('2.0')
import gtk
#import os
#import sys
#from time import time, strftime

#import Card
#import fpdb_import
#import Database
#import Charset
import TourneyFilters

class GuiTourneyPlayerStats (threading.Thread):
    def __init__(self, config, db, sql, mainwin, debug=True):
        self.conf = config
        self.db = db
        self.sql = sql
        self.main_window = mainwin
        self.debug = debug
        
        self.liststore = []   # gtk.ListStore[]         stores the contents of the grids
        self.listcols = []    # gtk.TreeViewColumn[][]  stores the columns in the grids
        
        filters_display = { "Heroes"    : True,
                            "Sites"     : True,
                            #"Games"     : True,
                            #"Limits"    : True,
                            #"LimitSep"  : True,
                            #"LimitType" : True,
                            #"Type"      : True,
                            "Seats"     : True,
                            #"SeatSep"   : True,
                            "Dates"     : True,
                            #"Groups"    : True,
                            #"GroupsAll" : True,
                            #"Button1"   : True,
                            "Button2"   : True}
        
        self.stats_frame = None
        self.stats_vbox = None
        self.detailFilters = []   # the data used to enhance the sql select

        self.main_hbox = gtk.HPaned()

        self.filters = TourneyFilters.TourneyFilters(self.db, self.conf, self.sql, display = filters_display)
        #self.filters.registerButton1Name("_Filters")
        #self.filters.registerButton1Callback(self.showDetailFilter)
        self.filters.registerButton2Name("_Refresh Stats")
        self.filters.registerButton2Callback(self.refreshStats)
        self.stats_frame = gtk.Frame()
        self.stats_frame.show()

        self.stats_vbox = gtk.VPaned()
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        # self.fillStatsFrame(self.stats_vbox)

        #self.main_hbox.pack_start(self.filters.get_vbox())
        #self.main_hbox.pack_start(self.stats_frame, expand=True, fill=True)
        self.main_hbox.pack1(self.filters.get_vbox())
        self.main_hbox.pack2(self.stats_frame)
        self.main_hbox.show()
    #end def __init__

    def createStatsTable(self, vbox, playerids, sitenos, limits, type, seats, groups, dates, games):
        starttime = time()
        show_detail = True

        # Scrolled window for summary table
        swin = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swin.show()
        vbox.pack1(swin)

        # Display summary table at top of page
        # 3rd parameter passes extra flags, currently includes:
        #   holecards - whether to display card breakdown (True/False)
        #   numhands  - min number hands required when displaying all players
        #   gridnum   - index for grid data structures
        flags = [False, self.filters.getNumHands(), 0]
        self.addGrid(swin, 'playerDetailedStats', flags, playerids
                    ,sitenos, limits, type, seats, groups, dates, games)

        if 'allplayers' in groups and groups['allplayers']:
            # can't currently do this combination so skip detailed table
            show_detail = False

        if show_detail: 
            # Separator
            vbox2 = gtk.VBox(False, 0)
            heading = gtk.Label(self.filterText['handhead'])
            heading.show()
            vbox2.pack_start(heading, expand=False, padding=3)

            # Scrolled window for detailed table (display by hand)
            swin = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
            swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            swin.show()
            vbox2.pack_start(swin, expand=True, padding=3)
            vbox.pack2(vbox2)
            vbox2.show()

            # Detailed table
            flags[0] = True
            flags[2] = 1
            self.addGrid(swin, 'playerDetailedStats', flags, playerids
                        ,sitenos, limits, type, seats, groups, dates, games)

        self.db.rollback()
        print "Stats page displayed in %4.2f seconds" % (time() - starttime)
    #end def createStatsTable

    def fillStatsFrame(self, vbox):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        seats  = self.filters.getSeats()
        dates = self.filters.getDates()
        games = self.filters.getGames()
        sitenos = []
        playerids = []

        # Which sites are selected?
        for site in sites:
            if sites[site] == True:
                sitenos.append(siteids[site])
                _hname = Charset.to_utf8(heroes[site])
                result = self.db.get_player_id(self.conf, site, _hname)
                if result is not None:
                    playerids.append(int(result))

        if not sitenos:
            #Should probably pop up here.
            print "No sites selected - defaulting to PokerStars"
            sitenos = [2]
        if not playerids:
            print "No player ids found"
            return
        if not limits:
            print "No limits found"
            return

        self.createStatsTable(vbox, playerids, sitenos, limits, type, seats, groups, dates, games)
    #end def fillStatsFrame

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox
    #end def get_vbox
    
    def refreshStats(self, widget, data):
        self.last_pos = self.stats_vbox.get_position()
        try: self.stats_vbox.destroy()
        except AttributeError: pass
        self.liststore = []
        self.listcols = []
        #self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox = gtk.VPaned()
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)
        if self.last_pos > 0:
            self.stats_vbox.set_position(self.last_pos)
    #end def refreshStats
#end class GuiTourneyPlayerStats
