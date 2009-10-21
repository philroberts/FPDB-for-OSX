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

import sys
import threading
import pygtk
pygtk.require('2.0')
import gtk
import os
from time import time, strftime, localtime
try:
    from numpy import diff, nonzero, sum
#    from matplotlib.dates import  DateFormatter, WeekdayLocator, HourLocator, \
#     DayLocator, MONDAY, timezone

except:
    print """Failed to load numpy in Session Viewer"""
    print """This is of no consequence as the module currently doesn't do anything."""

import Card
import fpdb_import
import Database
import Filters
import FpdbSQLQueries

class GuiSessionViewer (threading.Thread):
    def __init__(self, config, querylist, mainwin, debug=True):
        self.debug = debug
        self.conf = config
        self.sql = querylist

        self.liststore = None

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

        filters_display = { "Heroes"    : True,
                            "Sites"     : True,
                            "Games"     : False,
                            "Limits"    : True,
                            "LimitSep"  : True,
                            "LimitType" : True,
                            "Type"      : True,
                            "Seats"     : True,
                            "SeatSep"   : True,
                            "Dates"     : True,
                            "Groups"    : True,
                            "GroupsAll" : True,
                            "Button1"   : True,
                            "Button2"   : True
                          }

        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        self.filters.registerButton1Name("_Refresh")
        self.filters.registerButton1Callback(self.refreshStats)

        # ToDo: store in config
        # ToDo: create popup to adjust column config
        # columns to display, keys match column name returned by sql, values in tuple are:
        #     is column displayed, column heading, xalignment, formatting
        self.columns = [ ("sid",      True,  "SID",      0.0, "%s")
                       , ("hand",     False, "Hand",     0.0, "%s")   # true not allowed for this line
                       , ("n",        True,  "Hds",      1.0, "%d")
                       , ("start",    True,  "Start",    1.0, "%d")
                       , ("end",      True,  "End",      1.0, "%d")
                       , ("hph",      True,  "Hands/h",  1.0, "%d")
                       , ("profit",   True,  "Profit",   1.0, "%s")
                       #, ("avgseats", True,  "Seats",    1.0, "%3.1f")
                       #, ("vpip",     True,  "VPIP",     1.0, "%3.1f")
                       #, ("pfr",      True,  "PFR",      1.0, "%3.1f")
                       #, ("pf3",      True,  "PF3",      1.0, "%3.1f")
                       #, ("steals",   True,  "Steals",   1.0, "%3.1f")
                       #, ("saw_f",    True,  "Saw_F",    1.0, "%3.1f")
                       #, ("sawsd",    True,  "SawSD",    1.0, "%3.1f")
                       #, ("wtsdwsf",  True,  "WtSDwsF",  1.0, "%3.1f")
                       #, ("wmsd",     True,  "W$SD",     1.0, "%3.1f")
                       #, ("flafq",    True,  "FlAFq",    1.0, "%3.1f")
                       #, ("tuafq",    True,  "TuAFq",    1.0, "%3.1f")
                       #, ("rvafq",    True,  "RvAFq",    1.0, "%3.1f")
                       #, ("pofafq",   False, "PoFAFq",   1.0, "%3.1f")
                       #, ("net",      True,  "Net($)",   1.0, "%6.2f")
                       #, ("bbper100", True,  "BB/100",   1.0, "%4.2f")
                       #, ("rake",     True,  "Rake($)",  1.0, "%6.2f")
                       #, ("variance", True,  "Variance", 1.0, "%5.2f")
                       ]

        self.stats_frame = None
        self.stats_vbox = None
        self.detailFilters = []   # the data used to enhance the sql select

        #self.main_hbox = gtk.HBox(False, 0)
        #self.main_hbox.show()
        self.main_hbox = gtk.HPaned()

        self.stats_frame = gtk.Frame()
        self.stats_frame.show()

        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        # self.fillStatsFrame(self.stats_vbox)

        #self.main_hbox.pack_start(self.filters.get_vbox())
        #self.main_hbox.pack_start(self.stats_frame, expand=True, fill=True)
        self.main_hbox.pack1(self.filters.get_vbox())
        self.main_hbox.pack2(self.stats_frame)
        self.main_hbox.show()

        # make sure Hand column is not displayed
        #[x for x in self.columns if x[0] == 'hand'][0][1] = False

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def generateGraph(self):
        fig = figure()
        fig.subplots_adjust(bottom=0.2)
        ax = fig.add_subplot(111)
        ax.xaxis.set_major_locator(mondays)
        ax.xaxis.set_minor_locator(alldays)
        ax.xaxis.set_major_formatter(weekFormatter)
        #ax.xaxis.set_minor_formatter(dayFormatter)
        #plot_day_summary(ax, quotes, ticksize=3)
#        candlestick(ax, quotes, width=0.6)
#        candlestick2(ax, opens, closes, highs, lows, width=4, colorup='k', colordown='r', alpha=0.75)
#    Represent the open, close as a bar line and high low range as a vertical line.
#    ax          : an Axes instance to plot to
#    width       : the bar width in points
#    colorup     : the color of the lines where close >= open
#    colordown   : the color of the lines where close <  open
#    alpha       : bar transparency
#    return value is lineCollection, barCollection
        ax.xaxis_date()
        ax.autoscale_view()
        setp( gca().get_xticklabels(), rotation=45, horizontalalignment='right')

        show()


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

        # pre-fetch some constant values:
        cols_to_show = [x for x in self.columns if x[colshow]]

        self.liststore = gtk.ListStore(*([str] * len(cols_to_show)))

        view = gtk.TreeView(model=self.liststore)
        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        vbox.add(view)
        textcell = gtk.CellRendererText()
        textcell50 = gtk.CellRendererText()
        textcell50.set_property('xalign', 0.5)
        numcell = gtk.CellRendererText()
        numcell.set_property('xalign', 1.0)
        listcols = []

        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
        for col, column in enumerate(cols_to_show):
            s = column[colheading]
            listcols.append(gtk.TreeViewColumn(s))
            view.append_column(listcols[col])
            if column[colformat] == '%s':
                if column[colxalign] == 0.0:
                    listcols[col].pack_start(textcell, expand=True)
                    listcols[col].add_attribute(textcell, 'text', col)
                else:
                    listcols[col].pack_start(textcell50, expand=True)
                    listcols[col].add_attribute(textcell50, 'text', col)
                listcols[col].set_expand(True)
            else:
                listcols[col].pack_start(numcell, expand=True)
                listcols[col].add_attribute(numcell, 'text', col)
                listcols[col].set_expand(True)

        # Get a list of all handids and their timestampts
        # FIXME: Will probably want to be able to filter this list eventually
        # FIXME: Join on handsplayers for Hero to get other useful stuff like total profit?
        q = """
select UNIX_TIMESTAMP(h.handStart) as time, hp.handId, hp.startCash, hp.winnings, hp.totalProfit
from HandsPlayers hp
     inner join Hands h       on  (h.id = hp.handId)
     inner join Gametypes gt  on  (gt.Id = h.gameTypeId)
     inner join Sites s       on  (s.Id = gt.siteId)
     inner join Players p     on  (p.Id = hp.playerId)
where hp.playerId in (2)
order by time
"""
        self.db.cursor.execute(q)
        THRESHOLD = 1800
        hands = self.db.cursor.fetchall()

        # Take that list and create an array of the time between hands
        times = map(lambda x:long(x[0]), hands)
        handids = map(lambda x:int(x[1]), hands)
        winnings = map(lambda x:int(x[4]), hands)
        print "DEBUG: len(times) %s" %(len(times))
        diffs = diff(times) # This array is the difference in starttime between consecutive hands
        index = nonzero(diff(times) > THRESHOLD) # This array represents the indexes into 'times' for start/end times of sessions
                                                 # ie. times[index[0][0]] is the end of the first session
        #print "DEBUG: len(index[0]) %s" %(len(index[0]))
        #print "DEBUG: index %s" %(index)
        #print "DEBUG: index[0][0] %s" %(index[0][0])

        total = 0
        last_idx = 0
        lowidx = 0
        uppidx = 0
        results = []
        # Take all results and format them into a list for feeding into gui model.
        for i in range(len(index[0])):
            sid = i                                                             # Session id
            hds = index[0][i] - last_idx                                        # Number of hands in session
            stime = strftime("%d/%m/%Y %H:%M", localtime(times[last_idx]))      # Formatted start time
            etime = strftime("%d/%m/%Y %H:%M", localtime(times[index[0][i]]))   # Formatted end time
            hph = (times[index[0][i]] - times[last_idx])/60                     # Hands per hour
            won = sum(winnings[last_idx:index[0][i]])
            print "DEBUG: range: %s - %s" %(last_idx, index[0][i])
            
            results.append([sid, hds, stime, etime, hph, won])
            print "Hands in session %4s: %4s  Start: %s End: %s HPH: %s Profit: %s" %(sid, hds, stime, etime, hph, won)
            total = total + (index[0][i] - last_idx)
            last_idx = index[0][i] + 1

        for row in results:
            iter = self.liststore.append(row)

        vbox.show_all()

def main(argv=None):
    config = Configuration.Config()
    i = GuiBulkImport(settings, config)

if __name__ == '__main__':
    sys.exit(main())

