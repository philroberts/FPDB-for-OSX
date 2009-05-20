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
    def __init__(self, config, querylist, mainwin, debug=True):
        self.debug=debug
        self.conf=config
        self.main_window=mainwin
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
                            "Seats"    :  True,
                            "SeatSep"  :  True,
                            "Dates"    :  False,
                            "Button1"  :  True,
                            "Button2"  :  False
                          }

        self.filters = Filters.Filters(self.db, settings, config, querylist, display = filters_display)
        self.filters.registerButton1Name("Refresh")
        self.filters.registerButton1Callback(self.refreshStats)

        # TODO: these probably be a dict keyed on colAlias and the headings loop should use colAlias ...
        # This could be stored in config eventually, or maybe configured in this window somehow.
        # Each colAlias element is the name of a column returned by the sql 
        # query (in lower case) and each colHeads element is the text to use as
        # the heading in the GUI. Both sequences should be the same length.
        # To miss columns out remove them from both tuples (the 1st 2 elements should always be included).
        # To change the heading just edit the second list element as required
        # If the first list element does not match a query column that pair is ignored
        self.colAlias =  ( "game", "n", "avgseats", "vpip", "pfr", "pf3", "steals" 
                         , "saw_f", "sawsd", "wtsdwsf", "wmsd", "flafq", "tuafq", "rvafq"
                         , "pofafq", "net", "bbper100", "rake", "variance"
                         )
        self.colHeads = ( "Game", "Hds", "Seats", "VPIP", "PFR", "PF3", "Steals"
                        , "Saw_F", "SawSD", "WtSDwsF", "W$SD", "FlAFq", "TuAFq", "RvAFq"
                        , "PoFAFq", "Net($)", "BB/100", "Rake($)", "Variance"
                        )
        self.colXAligns = ( 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
                          , 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
                          , 1.0, 1.0, 1.0, 1.0, 1.0
                          )
        self.colFormats = ( "%s", "%d", "%3.1f", "%3.1f", "%3.1f", "%3.1f", "%3.1f"
                          , "%3.1f", "%3.1f", "%3.1f", "%3.1f", "%3.1f", "%3.1f", "%3.1f"
                          , "%3.1f", "%6.2f", "%4.2f", "%6.2f", "%5.2f"
                          )

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
        self.stats_table = gtk.Table(1, 1, False)
        self.stats_table.set_col_spacings(4)
        self.stats_table.show()
        vbox.add(self.stats_table)

        # Create header row
        row = 0
        col = 0
        for t in self.colHeads:
            l = gtk.Label(self.colHeads[col])
            l.set_alignment(xalign=self.colXAligns[col], yalign=0.5)
            l.show()
            self.stats_table.attach(l, col, col+1, row, row+1, yoptions=gtk.SHRINK)
            col +=1 

        tmp = self.sql.query['playerDetailedStats']
        tmp = self.refineQuery(tmp, playerids, sitenos, limits, seats)
        self.cursor.execute(tmp)
        result = self.cursor.fetchall()

        #cols = 19
        rows = len(result) # +1 for title row
        colnames = [desc[0].lower() for desc in self.cursor.description]

        col = 0
        for row in range(rows):
            if(row%2 == 0):
                bgcolor = "white"
            else:
                bgcolor = "lightgrey"
            for col,colname in enumerate(self.colAlias):
                if colname in colnames:
                    value = result[row][colnames.index(colname)]
                else:
                    if colname == 'game':
                        minbb = result[row][colnames.index('minbigblind')]
                        maxbb = result[row][colnames.index('maxbigblind')]
                        value = result[row][colnames.index('limittype')] + ' ' \
                                + result[row][colnames.index('category')].title() + ' ' \
                                + result[row][colnames.index('name')] + ' $'
                        if 100 * int(minbb/100.0) != minbb:
                            value += '%.2f' % (minbb/100.0)
                        else:
                            value += '%.0f' % (minbb/100.0)
                        if minbb != maxbb:
                            if 100 * int(maxbb/100.0) != maxbb:
                                value += ' - $' + '%.2f' % (maxbb/100.0)
                            else:
                                value += ' - $' + '%.0f' % (maxbb/100.0)
                    else:
                        continue
                eb = gtk.EventBox()
                eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bgcolor))
                if value and value != -999:
                    l = gtk.Label(self.colFormats[col] % value)
                else:
                    l = gtk.Label(' ')
                l.set_alignment(xalign=self.colXAligns[col], yalign=0.5)
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
                query = query.replace('<groupbyseats>', ',h.seats')
                query = query.replace('<orderbyseats>', ',h.seats')
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
            query = query.replace("<groupbygt.bigBlind>", "")
            query = query.replace("<hcgametypeId>", "-1")
            query = query.replace("<hgameTypeId>", "-1")
        else:
            query = query.replace("<groupbygt.bigBlind>", ",gt.bigBlind")
            query = query.replace("<hcgametypeId>", "hc.gametypeId")
            query = query.replace("<hgameTypeId>", "h.gameTypeId")

        if self.db.backend == self.MYSQL_INNODB:
            query = query.replace("<signed>", 'signed ')
        else:
            query = query.replace("<signed>", '')

        #print "query =\n", query
        return(query)
    #end def refineQuery(self, query, playerids, sitenos, limits):
