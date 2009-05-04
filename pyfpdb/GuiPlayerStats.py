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
import pygtk
pygtk.require('2.0')
import gtk
import os
    
import fpdb_import
import fpdb_db
import Filters
import FpdbSQLQueries

class GuiPlayerStats (threading.Thread):
    def __init__(self, config, querylist, debug=True):
        self.debug=debug
        self.conf=config
        
        # create new db connection to avoid conflicts with other threads
        self.db = fpdb_db.fpdb_db()
        self.db.do_connect(self.conf)
        self.cursor=self.db.cursor
        self.sql = querylist

        settings = {}
        settings.update(config.get_db_parameters())
        settings.update(config.get_tv_parameters())
        settings.update(config.get_import_parameters())
        settings.update(config.get_default_paths())

        filters_display = { "Heroes"  :  True,
                            "Sites"   :  True,
                            "Games"   :  False,
                            "Limits"  :  False,
                            "Dates"   :  False,
                            "Button1" :  False,
                            "Button2" :  False
                          }

        self.filters = Filters.Filters(self.db, settings, config, querylist, display = filters_display)

        self.stat_table = None
        self.stats_frame = None
        
        self.main_hbox = gtk.HBox(False, 0)
        self.main_hbox.show()

        statsFrame = gtk.Frame("Stats:")
        statsFrame.set_label_align(0.0, 0.0)
        statsFrame.show()
        self.stats_frame = gtk.VBox(False, 0)
        self.stats_frame.show()

        self.fillStatsFrame(self.stats_frame)
        statsFrame.add(self.stats_frame)

        self.main_hbox.pack_start(self.filters.get_vbox())
        self.main_hbox.pack_start(statsFrame)

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def refreshStats(self, widget, data):
        try: self.stats_table.destroy()
        except AttributeError: pass
        self.fillStatsFrame(self.stats_frame)

    def fillStatsFrame(self, vbox):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        sitenos = []
        playerids = []

        # Which sites are selected?
        for site in sites:
            if sites[site] == True:
                sitenos.append(siteids[site])
                self.cursor.execute(self.sql.query['getPlayerId'], (heroes[site],))
                result = self.db.cursor.fetchall()
                if len(result) == 1:
                    playerids.append(result[0][0])

        if not sitenos:
            #Should probably pop up here.
            print "No sites selected - defaulting to PokerStars"
            sitenos = [2]
        if not playerids:
            print "No player ids found"
            return

        self.createStatsTable(vbox, playerids, sitenos)

    def createStatsTable(self, vbox, playerids, sitenos):
        tmp = self.sql.query['playerStats']

        nametest = str(tuple(playerids))
        nametest = nametest.replace("L", "")
        nametest = nametest.replace(",)",")")

        tmp = tmp.replace("<player_test>", nametest)

        self.cursor.execute(tmp)
        result = self.cursor.fetchall()
        cols = 18
        rows = len(result)+1 # +1 for title row
        self.stats_table = gtk.Table(rows, cols, False)
        self.stats_table.set_col_spacings(4)
        self.stats_table.show()
        vbox.add(self.stats_table)

        # Create header row
        titles = ("Game", "Hands", "VPIP", "PFR", "PF3", "Steals", "Saw_F", "SawSD", "WtSDwsF", "W$SD", "FlAFq", "TuAFq", "RvAFq", "PoFAFq", "Net($)", "BB/100", "$/hand", "Variance")

        col = 0
        row = 0
        for t in titles:
            l = gtk.Label(titles[col])
            l.show()
            self.stats_table.attach(l, col, col+1, row, row+1, yoptions=gtk.SHRINK)
            col +=1 

        for row in range(rows-1):
            if(row%2 == 0):
                bgcolor = "white"
            else:
                bgcolor = "lightgrey"
            for col in range(cols):
                eb = gtk.EventBox()
                eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bgcolor))
                if result[row][col]:
                    l = gtk.Label(result[row][col])
                else:
                    l = gtk.Label(' ')
                if col == 0:
                    l.set_alignment(xalign=0.0, yalign=0.5)
                else:
                    l.set_alignment(xalign=1.0, yalign=0.5)
                eb.add(l)
                self.stats_table.attach(eb, col, col+1, row+1, row+2, yoptions=gtk.SHRINK)
                l.show()
                eb.show()
        self.db.db.commit()
    #end def fillStatsFrame(self, vbox):
