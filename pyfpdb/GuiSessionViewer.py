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
import os
import traceback
from time import time, strftime, localtime, gmtime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                             QSplitter, QTableView, QVBoxLayout, QWidget)

try:
    calluse = not 'matplotlib' in sys.modules
    import matplotlib
    if calluse:
        try:
            matplotlib.use('qt5agg')
        except ValueError, e:
            print e
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvas
    from matplotlib.finance import candlestick_ochl

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

class GuiSessionViewer(QSplitter):
    def __init__(self, config, querylist, mainwin, owner, debug=True):
        QSplitter.__init__(self, mainwin)
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

        self.filters = Filters.Filters(self.db, display = filters_display)
        self.filters.registerButton1Name("_Refresh")
        self.filters.registerButton1Callback(self.refreshStats)

        scroll = QScrollArea()
        scroll.setWidget(self.filters)

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

        self.stats_frame = QFrame()
        self.stats_frame.setLayout(QVBoxLayout())
        self.view = None
        heading = QLabel(self.filterText['handhead'])
        heading.setAlignment(Qt.AlignCenter)
        self.stats_frame.layout().addWidget(heading)


        self.main_vbox = QSplitter(Qt.Vertical)

        self.graphBox = QFrame()
        self.graphBox.setLayout(QVBoxLayout())

        self.addWidget(scroll)
        self.addWidget(self.main_vbox)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.main_vbox.addWidget(self.graphBox)
        self.main_vbox.addWidget(self.stats_frame)

    def refreshStats(self, checkState):
        if self.view:
            self.stats_frame.layout().removeWidget(self.view)
            self.view.setParent(None)
        self.fillStatsFrame(self.stats_frame)

    def fillStatsFrame(self, frame):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        games  = self.filters.getGames()
        currencies = self.filters.getCurrencies()
        limits  = self.filters.getLimits()
        seats  = self.filters.getSeats()
        sitenos = []
        playerids = []

        # Which sites are selected?
        for site in sites:
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

        self.createStatsPane(frame, playerids, sitenos, games, currencies, limits, seats)

    def createStatsPane(self, frame, playerids, sitenos, games, currencies, limits, seats):
        starttime = time()

        (results, quotes) = self.generateDatasets(playerids, sitenos, games, currencies, limits, seats)

        if DEBUG:
            for x in quotes:
                print "start %s\tend %s  \thigh %s\tlow %s" % (x[1], x[2], x[3], x[4])

        self.generateGraph(quotes)

        self.addTable(frame, results)

        self.db.rollback()
        print _("Stats page displayed in %4.2f seconds") % (time() - starttime)

    def generateDatasets(self, playerids, sitenos, games, currencies, limits, seats):
        if (DEBUG): print "DEBUG: Starting generateDatasets"
        THRESHOLD = 1800     # Min # of secs between consecutive hands before being considered a new session
        PADDING   = 5        # Additional time in minutes to add to a session, session startup, shutdown etc

        # Get a list of timestamps and profits

        q = self.sql.query['sessionStats']
        start_date, end_date = self.filters.getDates()
        q = q.replace("<datestest>", " BETWEEN '" + start_date + "' AND '" + end_date + "'")

        for m in self.filters.display.items():
            if m[0] == 'Games' and m[1]:
                if len(games) > 0:
                    gametest = str(tuple(games))
                    gametest = gametest.replace("L", "")
                    gametest = gametest.replace(",)",")")
                    gametest = gametest.replace("u'","'")
                    gametest = "AND gt.category in %s" % gametest
                else:
                    gametest = "AND gt.category IS NULL"
        q = q.replace("<game_test>", gametest)

        limittest = self.filters.get_limits_where_clause(limits)
        q = q.replace("<limit_test>", limittest)

        currencytest = str(tuple(currencies))
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
                self.times.append((times[first_idx] - PADDING * 60, times[last_idx] + PADDING * 60))
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
                    self.graphBox.layout().removeWidget(self.canvas)
                    self.canvas.setParent(None)
            except:
                pass

            if self.fig is not None:
                self.fig.clear()
            self.fig = Figure(figsize=(5,4), dpi=100)
            if self.canvas is not None:
                self.canvas.destroy()

            self.canvas = FigureCanvas(self.fig)
            self.canvas.setParent(self)
        except:
            err = traceback.extract_tb(sys.exc_info()[2])[-1]
            print _("Error:")+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
            raise


    def generateGraph(self, quotes):
        self.clearGraphData()

        self.ax = self.fig.add_subplot(111)

        self.ax.set_title(_("Session candlestick graph"))

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel(_("Sessions"), fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)

        candlestick_ochl(self.ax, quotes, width=0.50, colordown='r', colorup='g', alpha=1.00)
        self.graphBox.layout().addWidget(self.canvas)
        self.canvas.draw()

    def addTable(self, frame, results):
        colxalign,colheading = range(2)

        self.liststore = QStandardItemModel(0, len(self.columns))
        self.liststore.setHorizontalHeaderLabels([column[colheading] for column in self.columns])
        for row in results:
            listrow = [QStandardItem(str(r)) for r in row]
            for item in listrow:
                item.setEditable(False)
            self.liststore.appendRow(listrow)

        self.view = QTableView()
        self.view.setModel(self.liststore)
        self.view.verticalHeader().hide()
        self.view.setSelectionBehavior(QTableView.SelectRows)
        frame.layout().addWidget(self.view)
        self.view.doubleClicked.connect(self.row_activated)

    def row_activated(self, index):
        if index.row() < len(self.times):
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
            handids = replayer.get_hand_ids_from_date_range(reformat(self.times[index.row()][0]), reformat(self.times[index.row()][1]))
            replayer.reload_hands(handids)

if __name__ == '__main__':
    import Configuration
    config = Configuration.Config()

    settings = {}

    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication([])
    import SQL
    sql = SQL.Sql(db_server=settings['db-server'])
    i = GuiSessionViewer(config, sql, None, None)
    main_window = QMainWindow()
    main_window.setCentralWidget(i)
    main_window.show()
    main_window.resize(1400, 800)
    app.exec_()

