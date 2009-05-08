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
        self.MYSQL_INNODB   = 2
        self.PGSQL          = 3
        self.SQLITE         = 4
        
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

        filters_display = { "Heroes"   :  True,
                            "Sites"    :  True,
                            "Games"    :  False,
                            "Limits"   :  True,
                            "LimitSep" :  True,
                            "Dates"    :  False,
                            "Button1"  :  True,
                            "Button2"  :  False
                          }

        self.filters = Filters.Filters(self.db, settings, config, querylist, display = filters_display)
        self.filters.registerButton1Name("Refresh")
        self.filters.registerButton1Callback(self.refreshStats)

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
        limits  = self.filters.getLimits()
        seats  = self.filters.getSeats()
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
        if not limits:
            print "No limits found"
            return

        self.createStatsTable(vbox, playerids, sitenos, limits, seats)

    def createStatsTable(self, vbox, playerids, sitenos, limits, seats):
        tmp = self.sql.query['playerStats']
        tmp = self.refineQuery(tmp, playerids, sitenos, limits, seats)
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

    def refineQuery(self, query, playerids, sitenos, limits, seats):
        if playerids:
            nametest = str(tuple(playerids))
            nametest = nametest.replace("L", "")
            nametest = nametest.replace(",)",")")
            query = query.replace("<player_test>", nametest)
        else:
            query = query.replace("<player_test>", "1 = 2")

        if seats:
            query = query.replace('<seats_test>', 'between ' + str(seats['from']) + ' and ' + str(seats['to']))
            if 'show' in seats and seats['show']:
                query = query.replace('<groupbyseats>', ',hc.activeSeats')
                query = query.replace('<orderbyseats>', ',stats.AvgSeats')
            else:
                query = query.replace('<groupbyseats>', '')
                query = query.replace('<orderbyseats>', '')
        else:
            query = query.replace('<seats_test>', 'between 0 and 100')
            query = query.replace('<groupbyseats>', '')
            query = query.replace('<orderbyseats>', '')

        if [x for x in limits if str(x).isdigit()]:
            blindtest = str(tuple([x for x in limits if str(x).isdigit()]))
            blindtest = blindtest.replace("L", "")
            blindtest = blindtest.replace(",)",")")
            query = query.replace("<gtbigBlind_test>", "gt.bigBlind in " +  blindtest)
        else:
            query = query.replace("<gtbigBlind_test>", "gt.bigBlind = -1 ")

        groupLevels = "show" not in str(limits)
        if groupLevels:
            if self.db.backend == self.MYSQL_INNODB:
                bigblindselect = """concat(trim(leading ' ' from
                                                case when min(gt.bigBlind) < 100 
                                                     then format(min(gt.bigBlind)/100.0, 2)
                                                     else format(min(gt.bigBlind)/100.0, 0)
                                                end)
                                          ,' - '
                                          ,trim(leading ' ' from
                                                case when max(gt.bigBlind) < 100 
                                                     then format(max(gt.bigBlind)/100.0, 2)
                                                     else format(max(gt.bigBlind)/100.0, 0)
                                                end)
                                          ) """
            else:
                bigblindselect = """trim(leading ' ' from
                                         case when min(gt.bigBlind) < 100 
                                              then to_char(min(gt.bigBlind)/100.0,'90D00')
                                              else to_char(min(gt.bigBlind)/100.0,'999990')
                                         end)
                                    || ' - ' ||
                                    trim(leading ' ' from
                                         case when max(gt.bigBlind) < 100 
                                              then to_char(max(gt.bigBlind)/100.0,'90D00')
                                              else to_char(max(gt.bigBlind)/100.0,'999990')
                                         end) """
            bigblindselect = "cast('' as char)" # avoid odd effects when some posns and/or seats 
                                                # are missing from some limits (dunno why cast is
                                                # needed but it says "unknown type" otherwise?!
            query = query.replace("<selectgt.bigBlind>", bigblindselect)
            query = query.replace("<groupbygt.bigBlind>", "")
            query = query.replace("<hcgametypeId>", "-1")
            query = query.replace("<hgameTypeId>", "-1")
        else:
            if self.db.backend == self.MYSQL_INNODB:
                bigblindselect = """concat('$', trim(leading ' ' from
                                                     case when gt.bigBlind < 100 
                                                          then format(gt.bigBlind/100.0, 2)
                                                          else format(gt.bigBlind/100.0, 0)
                                                     end 
                                                    ) ) """
            else:
                bigblindselect = """'$' || trim(leading ' ' from
                                                case when gt.bigBlind < 100 
                                                     then to_char(gt.bigBlind/100.0,'90D00')
                                                     else to_char(gt.bigBlind/100.0,'999990')
                                                end 
                                               ) """
            query = query.replace("<selectgt.bigBlind>", bigblindselect)
            query = query.replace("<groupbygt.bigBlind>", ",gt.bigBlind")
            query = query.replace("<hcgametypeId>", "hc.gametypeId")
            query = query.replace("<hgameTypeId>", "h.gameTypeId")
        #print "query =\n", query
        return(query)
    #end def refineQuery(self, query, playerids, sitenos, limits):
