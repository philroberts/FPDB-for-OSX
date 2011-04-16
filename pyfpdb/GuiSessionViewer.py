#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

import L10n
_ = L10n.get_translation()

import sys
import threading
import pygtk
pygtk.require('2.0')
import gtk
import os
import traceback
from time import time, strftime, localtime
try:
    calluse = not 'matplotlib' in sys.modules
    import matplotlib
    if calluse:
        matplotlib.use('GTKCairo')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
    from matplotlib.finance import candlestick2

    from numpy import diff, nonzero, sum, cumsum, max, min, append

except ImportError, inst:
    print _("""Failed to load numpy and/or matplotlib in Session Viewer""")
    print "ImportError: %s" % inst.args

import Card
import fpdb_import
import Database
import Filters
import Charset

DEBUG = False

class GuiSessionViewer (threading.Thread):
    def __init__(self, config, querylist, mainwin, debug=True):
        self.debug = debug
        self.conf = config
        self.sql = querylist
        self.window = mainwin

        self.liststore = None

        self.MYSQL_INNODB   = 2
        self.PGSQL          = 3
        self.SQLITE         = 4

        self.fig = None
        self.canvas = None
        self.ax = None
        self.graphBox = None
        
        # create new db connection to avoid conflicts with other threads
        self.db = Database.Database(self.conf, sql=self.sql)
        self.cursor = self.db.cursor

        settings = {}
        settings.update(self.conf.get_db_parameters())
        settings.update(self.conf.get_import_parameters())
        settings.update(self.conf.get_default_paths())

        # text used on screen stored here so that it can be configured
        self.filterText = {'handhead':_('Hand Breakdown for all levels listed above')}

        filters_display = { "Heroes"    : True,
                            "Sites"     : True,
                            "Games"     : False,
                            "Limits"    : False,
                            "LimitSep"  : False,
                            "LimitType" : False,
                            "Type"      : True,
                            "Seats"     : False,
                            "SeatSep"   : False,
                            "Dates"     : True,
                            "Groups"    : False,
                            "GroupsAll" : False,
                            "Button1"   : True,
                            "Button2"   : False
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
        if DEBUG == False:
            warning_string = _("Session Viewer is proof of concept code only, and contains many bugs.\n")
            warning_string += _("Feel free to use the viewer, but there is no guarantee that the data is accurate.\n")
            warning_string += _("If you are interested in developing the code further please contact us via the usual channels.\n")
            warning_string += _("Thankyou")
            self.warning_box(warning_string)

    def warning_box(self, str, diatitle=_("FPDB WARNING")):
        diaWarning = gtk.Dialog(title=diatitle, parent=self.window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))

        label = gtk.Label(str)
        diaWarning.vbox.add(label)
        label.show()

        response = diaWarning.run()
        diaWarning.destroy()
        return response

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
                _q = self.sql.query['getPlayerId']
                _name = Charset.to_utf8(heroes[site])
                #print 'DEBUG(_name) :: %s' % _name
                self.cursor.execute(_q, (_name,)) # arg = tuple
                result = self.db.cursor.fetchall()
                if len(result) == 1:
                    playerids.append(result[0][0])

        if not sitenos:
            #Should probably pop up here.
            print _("No sites selected - defaulting to PokerStars")
            sitenos = [2]
        if not playerids:
            print _("No player ids found")
            return
        if not limits:
            print _("No limits found")
            return

        self.createStatsPane(vbox, playerids, sitenos, limits, seats)

    def createStatsPane(self, vbox, playerids, sitenos, limits, seats):
        starttime = time()

        (results, opens, closes, highs, lows) = self.generateDatasets(playerids, sitenos, limits, seats)



        self.graphBox = gtk.VBox(False, 0)
        self.graphBox.show()
        self.generateGraph(opens, closes, highs, lows)

        vbox.pack_start(self.graphBox)
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

        self.addTable(vbox1, results)

        self.db.rollback()
        print _("Stats page displayed in %4.2f seconds") % (time() - starttime)
    #end def fillStatsFrame(self, vbox):

    def generateDatasets(self, playerids, sitenos, limits, seats):
        print "DEBUG: Starting generateDatasets"
        THRESHOLD = 1800     # Min # of secs between consecutive hands before being considered a new session
        PADDING   = 5        # Additional time in minutes to add to a session, session startup, shutdown etc

        # Get a list of all handids and their timestampts
        #FIXME: Query still need to filter on blind levels

        q = self.sql.query['sessionStats']
        start_date, end_date = self.filters.getDates()
        q = q.replace("<datestest>", " between '" + start_date + "' and '" + end_date + "'")

        nametest = str(tuple(playerids))
        nametest = nametest.replace("L", "")
        nametest = nametest.replace(",)",")")
        q = q.replace("<player_test>", nametest)
        q = q.replace("<ampersand_s>", "%s")

        self.db.cursor.execute(q)
        hands = self.db.cursor.fetchall()

        hands.insert(0, (hands[0][0], 0, 0, 0, 0))

        # Take that list and create an array of the time between hands
        times = map(lambda x:long(x[0]), hands)
        handids = map(lambda x:int(x[1]), hands)
        winnings = map(lambda x:float(x[4]), hands)
        #print "DEBUG: times   : %s" % times
        #print "DEBUG: handids : %s" % handids
        #print "DEBUG: winnings: %s" % winnings
        #print "DEBUG: len(times) %s" %(len(times))
        diffs = diff(times)                      # This array is the difference in starttime between consecutive hands
        diffs2 = append(diffs,THRESHOLD + 1)     # Append an additional session to the end of the diffs, so the next line
                                                 # includes an index into the last 'session'
        index = nonzero(diffs2 > THRESHOLD)      # This array represents the indexes into 'times' for start/end times of sessions
                                                 # times[index[0][0]] is the end of the first session,
        #print "DEBUG: len(index[0]) %s" %(len(index[0]))
        if len(index[0]) > 0:
            #print "DEBUG: index[0][0] %s" %(index[0][0])
            #print "DEBUG: index %s" %(index)
            pass
        else:
            index = [[0]]
            #print "DEBUG: index %s" %(index)
            #print "DEBUG: index[0][0] %s" %(index[0][0])
            pass

        total = 0
        first_idx = 0
        lowidx = 0
        uppidx = 0
        opens = []
        closes = []
        highs = []
        lows = []
        results = []
        cum_sum = cumsum(winnings)
        cum_sum = cum_sum/100
        sid = 1
        # Take all results and format them into a list for feeding into gui model.
        #print "DEBUG: range(len(index[0]): %s" % range(len(index[0]))
        for i in range(len(index[0])):
            hds = index[0][i] - first_idx                                       # Number of hands in session
            if hds > 0:
                stime = strftime("%d/%m/%Y %H:%M", localtime(times[first_idx]))      # Formatted start time
                etime = strftime("%d/%m/%Y %H:%M", localtime(times[index[0][i]]))   # Formatted end time
                minutesplayed = (times[index[0][i]] - times[first_idx])/60
                if minutesplayed == 0:
                    minutesplayed = 1
                minutesplayed = minutesplayed + PADDING
                hph = hds*60/minutesplayed # Hands per hour
                end_idx = first_idx+hds+1
                won = sum(winnings[first_idx:end_idx])/100.0
                #print "DEBUG: winnings[%s:%s]: %s" % (first_idx, end_idx, winnings[first_idx:end_idx])
                hwm = max(cum_sum[first_idx:end_idx])
                lwm = min(cum_sum[first_idx:end_idx])
                open = (sum(winnings[:first_idx]))/100
                close = (sum(winnings[:end_idx]))/100
                #print "DEBUG: range: (%s, %s) - (min, max): (%s, %s) - (open,close): (%s, %s)" %(first_idx, end_idx, lwm, hwm, open, close)
            
                results.append([sid, hds, stime, etime, hph, won])
                opens.append(open)
                closes.append(close)
                highs.append(hwm)
                lows.append(lwm)
                #print "DEBUG: Hands in session %4s: %4s  Start: %s End: %s HPH: %s Profit: %s" %(sid, hds, stime, etime, hph, won)
                total = total + (index[0][i] - first_idx)
                first_idx = index[0][i] + 1
                sid = sid+1
            else:
                print "hds <= 0"

        return (results, opens, closes, highs, lows)

    def clearGraphData(self):

        try:
            try:
                if self.canvas:
                    self.graphBox.remove(self.canvas)
            except:
                pass

            if self.fig is not None:
                self.fig.clear()
            self.fig = Figure(figsize=(5,4), dpi=100)
            if self.canvas is not None:
                self.canvas.destroy()

            self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("Error:")+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
            raise


    def generateGraph(self, opens, closes, highs, lows):
        self.clearGraphData()

        #print "DEBUG:"
        #print "\thighs = %s" % highs
        #print "\tlows = %s" % lows
        #print "\topens = %s" % opens
        #print "\tcloses = %s" % closes
        #print "\tlen(highs): %s == len(lows): %s" %(len(highs), len(lows))
        #print "\tlen(opens): %s == len(closes): %s" %(len(opens), len(closes))

        #for i in range(len(highs)):
        #    print "DEBUG: (%s, %s, %s, %s)" %(lows[i], opens[i], closes[i], highs[i])
        #    print "DEBUG: diffs h/l: %s o/c: %s" %(lows[i] - highs[i], opens[i] - closes[i])

        self.ax = self.fig.add_subplot(111)

        self.ax.set_title(_("Session candlestick graph"))

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel(_("Sessions"), fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)

        candlestick2(self.ax, opens, closes, highs, lows, width=0.50, colordown='r', colorup='g', alpha=1.00)
        self.graphBox.add(self.canvas)
        self.canvas.show()
        self.canvas.draw()

    def addTable(self, vbox, results):
        row = 0
        sqlrow = 0
        colalias,colshow,colheading,colxalign,colformat = 0,1,2,3,4

        # pre-fetch some constant values:
        cols_to_show = [x for x in self.columns if x[colshow]]

        self.liststore = gtk.ListStore(*([str] * len(cols_to_show)))
        for row in results:
            iter = self.liststore.append(row)

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

        vbox.show_all()

def main(argv=None):
    config = Configuration.Config()
    i = GuiBulkImport(settings, config)

if __name__ == '__main__':
    sys.exit(main())

