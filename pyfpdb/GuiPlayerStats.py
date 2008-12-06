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

class GuiPlayerStats (threading.Thread):
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def toggleCallback(self, widget, data=None):
        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])

    def fillStatsFrame(self, vbox):
        self.cursor.execute(self.sql.query['playerStats'])
        result = self.db.cursor.fetchall()
        print result
        print "Length result: %s" %(len(result))
        cols = 18
        rows = len(result)+1 # +1 for title row
        table = gtk.Table(rows, cols, False)
        table.show()
        vbox.add(table)

        # Create header row
        titles = ("gametypeId", "base", "limitType", "name", "BigBlind", "n", "vpip", "pfr", "saw_f", "sawsd", "wtsdwsf", "wmsd", "FlAFq", "TuAFq", "RvAFq", "PFAFq", "Net", "BBlPer100")

        col = 0
        row = 0
        for t in titles:
            l = gtk.Label(titles[col])
            l.show()
            table.attach(l, col, col+1, row, row+1)
            col +=1 

        for row in range(rows-1):
            for col in range(cols):
                print "result[%s][%s]: %s" %(row-1, col, result[row-1][col])
                l = gtk.Label(result[row-1][col])
                l.show()
                table.attach(l, col, col+1, row+1, row+2)


    def fillPlayerFrame(self, vbox):
        for site in self.conf.supported_sites.keys():
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, True, 0)
            hbox.show()

            player = self.conf.supported_sites[site].screen_name
            self.createPlayerLine(hbox, site, player)

    def createPlayerLine(self, hbox, site, player):
        button = gtk.RadioButton(None, site + " id:")
        hbox.pack_start(button, True, True, 0)
        button.connect("toggled", self.toggleCallback, site)
        button.set_active(True)
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
        print "DEBUG: settings heroes[%s]: %s"%(site, self.heroes[site])
    
    def __init__(self, db, config, querylist, debug=True):
        """Constructor for table_viewer"""
        self.debug=debug
        self.db=db
        self.cursor=db.cursor
        self.conf=config

        self.sql = querylist

        self.heroes = {}
        
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
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.fillStatsFrame(vbox)
        statsFrame.add(vbox)

        self.main_hbox.pack_start(playerFrame)
        self.main_hbox.pack_start(statsFrame)

