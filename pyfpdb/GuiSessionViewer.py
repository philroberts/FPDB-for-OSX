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
from time import time, strftime, localtime
from numpy import diff, nonzero

import Card
import fpdb_import
import Database
import Filters
import FpdbSQLQueries

class GuiSessionViewer (threading.Thread):
    def __init__(self, config, querylist, debug=True):
        self.debug = debug
        self.conf = config
        self.sql = querylist
        self.MYSQL_INNODB   = 2
        self.PGSQL          = 3
        self.SQLITE         = 4
        
        # create new db connection to avoid conflicts with other threads
        self.db = Database.Database(self.conf, sql=self.sql)
        self.cursor = self.db.cursor

        settings = {}
        settings.update(self.conf.get_db_parameters())
        settings.update(self.conf.get_tv_parameters())
        settings.update(self.conf.get_import_parameters())
        settings.update(self.conf.get_default_paths())

        # text used on screen stored here so that it can be configured
        self.filterText = {'handhead':'Hand Breakdown for all levels listed above'
                          }

        filters_display = { "Heroes"   :  True,
                            "Sites"    :  True,
                            "Games"    :  False,
                            "Limits"   :  True,
                            "LimitSep" :  True,
                            "Seats"    :  True,
                            "SeatSep"  :  True,
                            "Dates"    :  False,
                            "Groups"   :  True,
                            "Button1"  :  True,
                            "Button2"  :  True
                          }

        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        self.filters.registerButton2Name("_Refresh")
        self.filters.registerButton2Callback(self.refreshStats)

        # ToDo: store in config
        # ToDo: create popup to adjust column config
        # columns to display, keys match column name returned by sql, values in tuple are:
        #     is column displayed, column heading, xalignment, formatting
        self.columns = [ ("game",     True,  "Game",     0.0, "%s")
                       , ("hand",     False, "Hand",     0.0, "%s")   # true not allowed for this line
                       , ("n",        True,  "Hds",      1.0, "%d")
                       , ("avgseats", True,  "Seats",    1.0, "%3.1f")
                       , ("vpip",     True,  "VPIP",     1.0, "%3.1f")
                       , ("pfr",      True,  "PFR",      1.0, "%3.1f")
                       , ("pf3",      True,  "PF3",      1.0, "%3.1f")
                       , ("steals",   True,  "Steals",   1.0, "%3.1f")
                       , ("saw_f",    True,  "Saw_F",    1.0, "%3.1f")
                       , ("sawsd",    True,  "SawSD",    1.0, "%3.1f")
                       , ("wtsdwsf",  True,  "WtSDwsF",  1.0, "%3.1f")
                       , ("wmsd",     True,  "W$SD",     1.0, "%3.1f")
                       , ("flafq",    True,  "FlAFq",    1.0, "%3.1f")
                       , ("tuafq",    True,  "TuAFq",    1.0, "%3.1f")
                       , ("rvafq",    True,  "RvAFq",    1.0, "%3.1f")
                       , ("pofafq",   False, "PoFAFq",   1.0, "%3.1f")
                       , ("net",      True,  "Net($)",   1.0, "%6.2f")
                       , ("bbper100", True,  "BB/100",   1.0, "%4.2f")
                       , ("rake",     True,  "Rake($)",  1.0, "%6.2f")
                       , ("variance", True,  "Variance", 1.0, "%5.2f")
                       ]

        self.stats_frame = None
        self.stats_vbox = None
        self.detailFilters = []   # the data used to enhance the sql select
        
        self.main_hbox = gtk.HBox(False, 0)
        self.main_hbox.show()

        self.stats_frame = gtk.Frame()
        self.stats_frame.show()

        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)

        self.main_hbox.pack_start(self.filters.get_vbox())
        self.main_hbox.pack_start(self.stats_frame, expand=True, fill=True)

################################


        # make sure Hand column is not displayed
        [x for x in self.columns if x[0] == 'hand'][0][1] == False

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def refreshStats(self, widget, data):
        try: self.stats_vbox.destroy()
        except AttributeError: pass
        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)

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
        starttime = time()

        # Display summary table at top of page
        # 3rd parameter passes extra flags, currently includes:
        # holecards - whether to display card breakdown (True/False)
        flags = [False]
        self.addTable(vbox, 'playerDetailedStats', flags, playerids, sitenos, limits, seats)

        # Separator
        sep = gtk.HSeparator()
        vbox.pack_start(sep, expand=False, padding=3)
        sep.show_now()
        vbox.show_now()
        heading = gtk.Label(self.filterText['handhead'])
        heading.show()
        vbox.pack_start(heading, expand=False, padding=3)

        # Scrolled window for detailed table (display by hand)
        swin = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swin.show()
        vbox.pack_start(swin, expand=True, padding=3)

        vbox1 = gtk.VBox(False, 0)
        vbox1.show()
        swin.add_with_viewport(vbox1)

        # Detailed table
        flags = [True]
        self.addTable(vbox1, 'playerDetailedStats', flags, playerids, sitenos, limits, seats)

        self.db.rollback()
        print "Stats page displayed in %4.2f seconds" % (time() - starttime)
    #end def fillStatsFrame(self, vbox):

    def addTable(self, vbox, query, flags, playerids, sitenos, limits, seats):
        row = 0
        sqlrow = 0
        colalias,colshow,colheading,colxalign,colformat = 0,1,2,3,4
        if not flags:  holecards = False
        else:          holecards = flags[0]


        self.stats_table = gtk.Table(1, 1, False)
        self.stats_table.set_col_spacings(4)
        self.stats_table.show()
        
        self.db.cursor.execute("""select UNIX_TIMESTAMP(handStart) as time, id from Hands ORDER BY time""")
        THRESHOLD = 1800
        hands = self.db.cursor.fetchall()

        times = map(lambda x:long(x[0]), hands)
        handids = map(lambda x:int(x[1]), hands)
        print "DEBUG: len(times) %s" %(len(times))
        diffs = diff(times)
        print "DEBUG: len(diffs) %s" %(len(diffs))
        index = nonzero(diff(times) > THRESHOLD)
        print "DEBUG: len(index[0]) %s" %(len(index[0]))
        print "DEBUG: index %s" %(index)
        print "DEBUG: index[0][0] %s" %(index[0][0])

        total = 0

        last_idx = 0
        for i in range(len(index[0])):
            print "Hands in session %4s: %4s  Start: %s End: %s Total: %s" %(i, index[0][i] - last_idx, strftime("%d/%m/%Y %H:%M", localtime(times[last_idx])), strftime("%d/%m/%Y %H:%M", localtime(times[index[0][i]])), times[index[0][i]] - times[last_idx])
            total = total + (index[0][i] - last_idx)
            last_idx = index[0][i] + 1

        print "Total: ", total
#
#        colnames = [desc[0].lower() for desc in self.cursor.description]
#
#        # pre-fetch some constant values:
#        cols_to_show = [x for x in self.columns if x[colshow]]
#        hgametypeid_idx = colnames.index('hgametypeid')
#
#        liststore = gtk.ListStore(*([str] * len(cols_to_show)))
#        view = gtk.TreeView(model=liststore)
#        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
#        vbox.pack_start(view, expand=False, padding=3)
#        textcell = gtk.CellRendererText()
#        numcell = gtk.CellRendererText()
#        numcell.set_property('xalign', 1.0)
#        listcols = []
#
#        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
#        for col, column in enumerate(cols_to_show):
#            if column[colalias] == 'game' and holecards:
#                s = [x for x in self.columns if x[colalias] == 'hand'][0][colheading]
#            else:
#                s = column[colheading]
#            listcols.append(gtk.TreeViewColumn(s))
#            view.append_column(listcols[col])
#            if column[colformat] == '%s':
#                if col == 1 and holecards:
#                    listcols[col].pack_start(textcell, expand=True)
#                else:
#                    listcols[col].pack_start(textcell, expand=False)
#                listcols[col].add_attribute(textcell, 'text', col)
#            else:
#                listcols[col].pack_start(numcell, expand=False)
#                listcols[col].add_attribute(numcell, 'text', col)
#
#        rows = len(result) # +1 for title row
#
#        while sqlrow < rows:
#            treerow = []
#            if(row%2 == 0):
#                bgcolor = "white"
#            else:
#                bgcolor = "lightgrey"
#            for col,column in enumerate(cols_to_show):
#                if column[colalias] in colnames:
#                    value = result[sqlrow][colnames.index(column[colalias])]
#                else:
#                    if column[colalias] == 'game':
#                        if holecards:
#                            value = Card.twoStartCardString( result[sqlrow][hgametypeid_idx] )
#                        else:
#                            minbb = result[sqlrow][colnames.index('minbigblind')]
#                            maxbb = result[sqlrow][colnames.index('maxbigblind')]
#                            value = result[sqlrow][colnames.index('limittype')] + ' ' \
#                                    + result[sqlrow][colnames.index('category')].title() + ' ' \
#                                    + result[sqlrow][colnames.index('name')] + ' $'
#                            if 100 * int(minbb/100.0) != minbb:
#                                value += '%.2f' % (minbb/100.0)
#                            else:
#                                value += '%.0f' % (minbb/100.0)
#                            if minbb != maxbb:
#                                if 100 * int(maxbb/100.0) != maxbb:
#                                    value += ' - $' + '%.2f' % (maxbb/100.0)
#                                else:
#                                    value += ' - $' + '%.0f' % (maxbb/100.0)
#                    else:
#                        continue
#                if value and value != -999:
#                    treerow.append(column[colformat] % value)
#                else:
#                    treerow.append(' ')
#            iter = liststore.append(treerow)
#            sqlrow += 1
#            row += 1
        vbox.show_all()
