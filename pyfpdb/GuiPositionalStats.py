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
import FpdbSQLQueries

class GuiPositionalStats (threading.Thread):
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def toggleCallback(self, widget, data=None):
#        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])
        self.activesite = data
        print "DEBUG: activesite set to %s" %(self.activesite)

    def refreshStats(self, widget, data):
        try: self.stats_table.destroy()
        except AttributeError: pass
        self.fillStatsFrame(self.stats_frame)

    def fillStatsFrame(self, vbox):
        # Get currently active site and grab playerid
        print "DEBUG: attempting to fill stats frame"
        tmp = self.sql.query['playerStatsByPosition']

        result = self.cursor.execute(self.sql.query['getPlayerId'], (self.heroes[self.activesite],))
        result = self.cursor.fetchall()
        if not result == ():
                pid = result[0][0]
                pid = result[0][0]
                tmp = tmp.replace("<player_test>", "(" + str(pid) + ")")
                self.cursor.execute(tmp)
                result = self.cursor.fetchall()
                cols = 16
                rows = len(result)+1 # +1 for title row
                self.stats_table = gtk.Table(rows, cols, False)
                self.stats_table.set_col_spacings(4)
                self.stats_table.show()
                vbox.add(self.stats_table)

                # Create header row
                titles = ("Game", "Position", "#", "VPIP", "PFR", "Saw_F", "SawSD", "WtSDwsF", "W$SD", "FlAFq", "TuAFq", "RvAFq", "PoFAFq", "Net($)", "BB/100", "$/hand", "Variance")

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
        self.fdb.db.commit()
    #end def fillStatsFrame(self, vbox):

    def fillPlayerFrame(self, vbox):
        for site in self.conf.supported_sites.keys():
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, True, 0)
            hbox.show()

            player = self.conf.supported_sites[site].screen_name
            self.createPlayerLine(hbox, site, player)
        hbox = gtk.HBox(False, 0)
        button = gtk.Button("Refresh")
        button.connect("clicked", self.refreshStats, False)
        button.show()
        hbox.add(button)
        vbox.pack_start(hbox, False, True, 0)
        hbox.show()

    def createPlayerLine(self, hbox, site, player):
        if(self.buttongroup == None):
            button = gtk.RadioButton(None, site + " id:")
            button.set_active(True)
            self.buttongroup = button
            self.activesite = site
        else:
            button = gtk.RadioButton(self.buttongroup, site + " id:")
        hbox.pack_start(button, True, True, 0)
        button.connect("toggled", self.toggleCallback, site)
        button.show()

        pname = gtk.Entry()
        pname.set_text(player)
        pname.set_width_chars(20)
        hbox.pack_start(pname, False, True, 0)
        pname.connect("changed", self.__set_hero_name, site)
        #TODO: Look at GtkCompletion - to fill out usernames
        pname.show()
        self.__set_hero_name(pname, site)

    def __set_hero_name(self, w, site):
        self.heroes[site] = w.get_text()
    
    def __init__(self, db, config, querylist, debug=True):
        self.debug=debug
        self.conf=config
        
        # create new db connection to avoid conflicts with other threads
        self.fdb = fpdb_db.fpdb_db()
        self.fdb.do_connect(self.conf)
        self.cursor=self.fdb.cursor

        self.sql = querylist

        self.activesite = None
        self.buttongroup = None

        self.heroes = {}
        self.stat_table = None
        self.stats_frame = None
        
        self.main_hbox = gtk.HBox(False, 0)
        self.main_hbox.show()

        playerFrame = gtk.Frame("Hero:")
        playerFrame.set_label_align(0.0, 0.0)
        playerFrame.show()
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.fillPlayerFrame(vbox)
        playerFrame.add(vbox)

        statsFrame = gtk.Frame("Stats:")
        statsFrame.set_label_align(0.0, 0.0)
        statsFrame.show()
        self.stats_frame = gtk.VBox(False, 0)
        self.stats_frame.show()

        self.fillStatsFrame(self.stats_frame)
        statsFrame.add(self.stats_frame)

        self.main_hbox.pack_start(playerFrame)
        self.main_hbox.pack_start(statsFrame)

