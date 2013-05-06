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
import pygtk
pygtk.require('2.0')
import gtk
import os
import traceback
from time import time, strftime, localtime, gmtime
try:
    calluse = not 'matplotlib' in sys.modules
    import matplotlib
    if calluse:
        matplotlib.use('GTKCairo')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
    from matplotlib.finance import candlestick

    from numpy import diff, nonzero, sum, cumsum, max, min, append

except ImportError, inst:
    print _("""Failed to load numpy and/or matplotlib in Session Viewer""")
    print "ImportError: %s" % inst.args

import Card
import Database
import Filters
import Charset

import GuiHandViewer

DEBUG = False

class GuiSessionViewer:
    def __init__(self, config, querylist, mainwin, owner, debug=True):
        self.debug = debug
        self.conf = config
        self.sql = querylist
        self.window = mainwin
        self.owner = owner

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
                            "Games"     : True,
                            "Currencies": True,
                            "Limits"    : True,
                            "LimitSep"  : True,
                            "LimitType" : True,
                            "Type"      : False,
                            "Seats"     : True,
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
        self.columns = [ (1.0, "SID"   )
                       , (1.0, "Hands" )
                       , (0.5, "Start" )
                       , (0.5, "End"   )
                       , (1.0, "Rate"  )
                       , (1.0, "Open"  )
                       , (1.0, "Close" )
                       , (1.0, "Low"   )
                       , (1.0, "High"  )
                       , (1.0, "Range" )
                       , (1.0, "Profit")
                       ]

        self.detailFilters = []   # the data used to enhance the sql select

        self.main_hbox = gtk.HPaned()

        self.stats_frame = gtk.Frame()
        self.stats_frame.show()

        main_vbox = gtk.VPaned()
        main_vbox.show()
        self.graphBox = gtk.VBox(False, 0)
        self.graphBox.set_size_request(400,400)
        self.graphBox.show()
        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)

        self.main_hbox.pack1(self.filters.get_vbox())
        self.main_hbox.pack2(main_vbox)
        main_vbox.pack1(self.graphBox)
        main_vbox.pack2(self.stats_frame)
        self.main_hbox.show()

        # make sure Hand column is not displayed
        #[x for x in self.columns if x[0] == 'hand'][0][1] = False
        # if DEBUG == False:
        #     warning_string = _("Session Viewer is proof of concept code only, and contains many bugs.\n")
        #     warning_string += _("Feel free to use the viewer, but there is no guarantee that the data is accurate.\n")
        #     warning_string += _("If you are interested in developing the code further please contact us via the usual channels.\n")
        #     warning_string += _("Thank you")
        #     self.warning_box(warning_string)

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
        games  = self.filters.getGames()
        currencies = self.filters.getCurrencies()
        limits  = self.filters.getLimits()
        seats  = self.filters.getSeats()
        sitenos = []
        playerids = []

        for i in ('show', 'none'):
            if i in limits:
                limits.remove(i)

        # Which sites are selected?
        for site in sites:
            if sites[site] == True:
                sitenos.append(siteids[site])
                _hname = Charset.to_utf8(heroes[site])
                result = self.db.get_player_id(self.conf, site, _hname)
                if result is not None:
                    playerids.append(result)

        if not sitenos:
            #Should probably pop up here.
            print _("No sites selected - defaulting to PokerStars")
            sitenos = [2]
        if not games:
            print _("No games found")
            return
        if not currencies:
            print _("No currencies found")
            return
        if not playerids:
            print _("No player ids found")
            return
        if not limits:
            print _("No limits found")
            return

        self.createStatsPane(vbox, playerids, sitenos, games, currencies, limits, seats)

    def createStatsPane(self, vbox, playerids, sitenos, games, currencies, limits, seats):
        starttime = time()

        (results, quotes) = self.generateDatasets(playerids, sitenos, games, currencies, limits, seats)

        if DEBUG:
            for x in quotes:
                print "start %s\tend %s  \thigh %s\tlow %s" % (x[1], x[2], x[3], x[4])

        self.generateGraph(quotes)

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

    def generateDatasets(self, playerids, sitenos, games, currencies, limits, seats):
        if (DEBUG): print "DEBUG: Starting generateDatasets"
        THRESHOLD = 1800     # Min # of secs between consecutive hands before being considered a new session
        PADDING   = 5        # Additional time in minutes to add to a session, session startup, shutdown etc

        # Get a list of timestamps and profits

        q = self.sql.query['sessionStats']
        start_date, end_date = self.filters.getDates()
        q = q.replace("<datestest>", " BETWEEN '" + start_date + "' AND '" + end_date + "'")

        l = []
        for m in self.filters.display.items():
            if m[0] == 'Games' and m[1]:
                for n in games:
                    if games[n]:
                        l.append(n)
                if len(l) > 0:
                    gametest = str(tuple(l))
                    gametest = gametest.replace("L", "")
                    gametest = gametest.replace(",)",")")
                    gametest = gametest.replace("u'","'")
                    gametest = "AND gt.category in %s" % gametest
                else:
                    gametest = "AND gt.category IS NULL"
        q = q.replace("<game_test>", gametest)

        limittest = self.filters.get_limits_where_clause(limits)
        q = q.replace("<limit_test>", limittest)

        l = []
        for n in currencies:
            if currencies[n]:
                l.append(n)
        currencytest = str(tuple(l))
        currencytest = currencytest.replace(",)",")")
        currencytest = currencytest.replace("u'","'")
        currencytest = "AND gt.currency in %s" % currencytest
        q = q.replace("<currency_test>", currencytest)


        if seats:
            q = q.replace('<seats_test>',
                          'AND h.seats BETWEEN ' + str(seats['from']) +
                          ' AND ' + str(seats['to']))
        else:
            q = q.replace('<seats_test>', 'AND h.seats BETWEEN 0 AND 100')

        nametest = str(tuple(playerids))
        nametest = nametest.replace("L", "")
        nametest = nametest.replace(",)",")")
        q = q.replace("<player_test>", nametest)
        q = q.replace("<ampersand_s>", "%s")

        if DEBUG:
            hands = [ 
                ( u'10000',  10), ( u'10000',  20), ( u'10000',  30),
                ( u'20000', -10), ( u'20000', -20), ( u'20000', -30),
                ( u'30000',  40),
                ( u'40000',   0),
                ( u'50000', -40),
                ( u'60000',  10), ( u'60000',  30), ( u'60000', -20),
                ( u'70000', -20), ( u'70000',  10), ( u'70000',  30),
                ( u'80000', -10), ( u'80000', -30), ( u'80000',  20),
                ( u'90000',  20), ( u'90000', -10), ( u'90000', -30),
                (u'100000',  30), (u'100000', -50), (u'100000',  30),
                (u'110000', -20), (u'110000',  50), (u'110000', -20),
                (u'120000', -30), (u'120000',  50), (u'120000', -30),
                (u'130000',  20), (u'130000', -50), (u'130000',  20),
                (u'140000',  40), (u'140000', -40),
                (u'150000', -40), (u'150000',  40),
                (u'160000', -40), (u'160000',  80), (u'160000', -40),
                ]
        else:
            self.db.cursor.execute(q)
            hands = self.db.cursor.fetchall()

        #fixme - nasty hack to ensure that the hands.insert() works 
        # for mysql data.  mysql returns tuples which can't be inserted
        # into so convert explicity to list.
        hands = list(hands)

        if (not hands):
            return ([], [])

        hands.insert(0, (hands[0][0], 0))

        # Take that list and create an array of the time between hands
        times = map(lambda x:long(x[0]), hands)
        profits = map(lambda x:float(x[1]), hands)
        #print "DEBUG: times   : %s" % times
        #print "DEBUG: profits: %s" % profits
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

        first_idx = 1
        quotes = []
        results = []
        cum_sum = cumsum(profits) / 100
        sid = 1

        total_hands = 0
        total_time = 0
        global_open = None
        global_lwm = None
        global_hwm = None

        self.times = []
        # Take all results and format them into a list for feeding into gui model.
        #print "DEBUG: range(len(index[0]): %s" % range(len(index[0]))
        for i in range(len(index[0])):
            last_idx = index[0][i]
            hds = last_idx - first_idx + 1                                           # Number of hands in session
            if hds > 0:
                stime = strftime("%d/%m/%Y %H:%M", localtime(times[first_idx]))      # Formatted start time
                etime = strftime("%d/%m/%Y %H:%M", localtime(times[last_idx]))       # Formatted end time
                self.times.append((times[first_idx], times[last_idx]))
                minutesplayed = (times[last_idx] - times[first_idx])/60
                minutesplayed = minutesplayed + PADDING
                if minutesplayed == 0:
                    minutesplayed = 1
                hph = hds*60/minutesplayed # Hands per hour
                end_idx = last_idx+1
                won = sum(profits[first_idx:end_idx])/100.0
                #print "DEBUG: profits[%s:%s]: %s" % (first_idx, end_idx, profits[first_idx:end_idx])
                hwm = max(cum_sum[first_idx-1:end_idx]) # include the opening balance,
                lwm = min(cum_sum[first_idx-1:end_idx]) # before we win/lose first hand
                open = (sum(profits[:first_idx]))/100
                close = (sum(profits[:end_idx]))/100
                #print "DEBUG: range: (%s, %s) - (min, max): (%s, %s) - (open,close): (%s, %s)" %(first_idx, end_idx, lwm, hwm, open, close)
            
                total_hands = total_hands + hds
                total_time = total_time + minutesplayed
                if (global_lwm == None or global_lwm > lwm):
                    global_lwm = lwm
                if (global_hwm == None or global_hwm < hwm):
                    global_hwm = hwm
                if (global_open == None):
                    global_open = open
                    global_stime = stime

                results.append([sid, hds, stime, etime, hph,
                                "%.2f" % open,
                                "%.2f" % close,
                                "%.2f" % lwm,
                                "%.2f" % hwm,
                                "%.2f" % (hwm - lwm),
                                "%.2f" % won])
                quotes.append((sid, open, close, hwm, lwm))
                #print "DEBUG: Hands in session %4s: %4s  Start: %s End: %s HPH: %s Profit: %s" %(sid, hds, stime, etime, hph, won)
                first_idx = end_idx
                sid = sid+1
            else:
                print "hds <= 0"
        global_close = close
        global_etime = etime
        results.append([''] * 11)
        results.append([_("all"), total_hands, global_stime, global_etime,
                        total_hands * 60 / total_time,
                        "%.2f" % global_open,
                        "%.2f" % global_close,
                        "%.2f" % global_lwm,
                        "%.2f" % global_hwm,
                        "%.2f" % (global_hwm - global_lwm),
                        "%.2f" % (global_close - global_open)])

        return (results, quotes)

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


    def generateGraph(self, quotes):
        self.clearGraphData()

        #print "DEBUG:"
        #print "\tquotes = %s" % quotes

        #for i in range(len(highs)):
        #    print "DEBUG: (%s, %s, %s, %s)" %(lows[i], opens[i], closes[i], highs[i])
        #    print "DEBUG: diffs h/l: %s o/c: %s" %(lows[i] - highs[i], opens[i] - closes[i])

        self.ax = self.fig.add_subplot(111)

        self.ax.set_title(_("Session candlestick graph"))

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel(_("Sessions"), fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)

        candlestick(self.ax, quotes, width=0.50, colordown='r', colorup='g', alpha=1.00)
        self.graphBox.add(self.canvas)
        self.canvas.show()
        self.canvas.draw()

    def addTable(self, vbox, results):
        row = 0
        sqlrow = 0
        colxalign,colheading = range(2)

        self.liststore = gtk.ListStore(*([str] * len(self.columns)))
        for row in results:
            iter = self.liststore.append(row)

        view = gtk.TreeView(model=self.liststore)
        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        vbox.add(view)
        print view.connect("row-activated", self.row_activated)
        cell05 = gtk.CellRendererText()
        cell05.set_property('xalign', 0.5)
        cell10 = gtk.CellRendererText()
        cell10.set_property('xalign', 1.0)
        listcols = []

        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
        for col, column in enumerate(self.columns):
            treeviewcolumn = gtk.TreeViewColumn(column[colheading])
            listcols.append(treeviewcolumn)
            treeviewcolumn.set_alignment(column[colxalign])
            view.append_column(listcols[col])
            if (column[colxalign] == 0.5):
                cell = cell05
            else:
                cell = cell10
            listcols[col].pack_start(cell, expand=True)
            listcols[col].add_attribute(cell, 'text', col)
            listcols[col].set_expand(True)

        vbox.show_all()

    def row_activated(self, view, path, column):
        if path[0] < len(self.times):
            replayer = None
            for tabobject in self.owner.threads:
                if isinstance(tabobject, GuiHandViewer.GuiHandViewer):
                    replayer = tabobject
                    self.owner.tab_hand_viewer(None)
                    break
            if replayer is None:
                self.owner.tab_hand_viewer(None)
                for tabobject in self.owner.threads:
                    if isinstance(tabobject, GuiHandViewer.GuiHandViewer):
                        replayer = tabobject
                        break
            # added the timezone offset ('+00:00') to make the db query work. Otherwise the hands
            # at the edges of the date range are not included. A better solution may be possible.
            # Optionally the end date in the call below, which is a Long gets a '+1'.
            reformat = lambda t: strftime("%Y-%m-%d %H:%M:%S+00:00", gmtime(t))
            handids = replayer.get_hand_ids_from_date_range(reformat(self.times[path[0]][0]), reformat(self.times[path[0]][1]), save_date = True)
            replayer.reload_hands(handids)

def main(argv=None):
    Configuration.set_logfile("fpdb-log.txt")
    config = Configuration.Config()
    i = GuiBulkImport(settings, config)

if __name__ == '__main__':
    sys.exit(main())

