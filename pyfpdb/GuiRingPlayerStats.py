#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2008-2011 Steffen Schaumburg
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# In the "official" distribution you can find the license in agpl-3.0.txt.

import L10n
_ = L10n.get_translation()

from time import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                             QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QScrollArea, QSpinBox, QSplitter,
                             QTableView, QVBoxLayout, QWidget)

import Card
import Database
import Filters
import Charset

colalias,colheading,colshowsumm,colshowposn,colformat,coltype,colxalign = 0,1,2,3,4,5,6
ranks = {'x':0, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
fast_names = {'OnGame':'Strobe', 'PokerStars':'Zoom', 'Full Tilt Poker':'Rush', 'Bovada':'Zone', 'PacificPoker': 'Snap'}
onlinehelp = {'Game':_('Type of Game'),
              'Hand':_('Hole Cards'),
              'Posn':_('Position'),
              'Name':_('Player Name'),
              'Hds':_('Number of hands seen'),
              'Seats':_('Number of Seats'),
              'VPIP':_('Voluntarily put in preflop/3rd street %'),
              'PFR':_('Preflop/3rd street raise %'),
              'PF3':_('% 3 bet preflop/3rd street'),
              'PF4':_('% 4 bet preflop/3rd street'),
              'PFF3':_('% fold to 3 bet preflop/3rd street'),
              'PFF4':_('% fold to 4 bet preflop/3rd street'),
              'AggFac':_('Aggression factor')+("\n"),
              'AggFreq':_('Post-flop aggression frequency'),
              'ContBet':_('% continuation bet'),
              'RFI':_('% Raise First In / % Raise when first to bet'),
              'Steals':_('% steal attempted'),
              'CARpre':_('% called a raise preflop'),
              'Saw_F':_('Flop/4th street seen %'),
              'SawSD':_('Saw Showdown / River'),
              'WtSDwsF':_('% went to showdown when seen flop/4th street'),
              'W$wsF':_("% won money when seen flop/4th street"),
              'W$SD':_('% won some money at showdown'),
              'FlAFq':_('Aggression frequency flop/4th street'),
              'TuAFq':_('Aggression frequency turn/5th street'),
              'RvAFq':_('Aggression frequency river/6th street'),
              #'PoFAFq':_('Total % agression'), TODO
              'Net($)':_('Total Profit'),
              'bb/100':_('Big blinds won per 100 hands'),
              'Rake($)':_('Amount of rake paid'),
              'bbxr/100':_('Big blinds won per 100 hands when excluding rake'),
              'Variance':_('Measure of uncertainty'),
              'Std. Dev.':_('Measure of uncertainty')
              } 


class GuiRingPlayerStats(QSplitter):

    def __init__(self, config, querylist, mainwin, debug=True):
        QSplitter.__init__(self, None)
        self.debug = debug
        self.conf = config
        self.main_window = mainwin
        self.sql = querylist
        
        self.liststore = []   # gtk.ListStore[]         stores the contents of the grids
        self.listcols = []    # gtk.TreeViewColumn[][]  stores the columns in the grids

        self.MYSQL_INNODB   = 2
        self.PGSQL          = 3
        self.SQLITE         = 4

        # create new db connection to avoid conflicts with other threads
        self.db = Database.Database(self.conf, sql=self.sql)
        self.cursor = self.db.cursor

        settings = {}
        settings.update(self.conf.get_db_parameters())
        settings.update(self.conf.get_import_parameters())
        settings.update(self.conf.get_default_paths())

        # text used on screen stored here so that it can be configured
        self.filterText = {'handhead':_('Hand Breakdown for all levels listed above')
                          }

        filters_display = { "Heroes"    : True,
                            "Sites"     : True,
                            "Games"     : True,
                            "Currencies": True,
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

        self.filters = Filters.Filters(self.db, display = filters_display)
        self.filters.registerButton1Name(_("Filters"))
        self.filters.registerButton1Callback(self.showDetailFilter)
        self.filters.registerButton2Name(_("Refresh Stats"))
        self.filters.registerButton2Callback(self.refreshStats)

        scroll = QScrollArea()
        scroll.setWidget(self.filters)

        # ToDo: store in config
        # ToDo: create popup to adjust column config
        # columns to display, keys match column name returned by sql, values in tuple are:
        #     is column displayed(summary then position), column heading, xalignment, formatting, celltype
        self.columns = self.conf.get_gui_cash_stat_params()

        # Detail filters:  This holds the data used in the popup window, extra values are
        # added at the end of these lists during processing
        #                  sql test,              screen description,        min, max
        self.handtests = [  # already in filter class : ['h.seats', 'Number of Players', 2, 10]
                          ['gt.maxSeats',         'Size of Table',         2, 10]
                         ,['h.playersVpi',        'Players who VPI',       0, 10]
                         ,['h.playersAtStreet1',  'Players at Flop',       0, 10]
                         ,['h.playersAtStreet2',  'Players at Turn',       0, 10]
                         ,['h.playersAtStreet3',  'Players at River',      0, 10]
                         ,['h.playersAtStreet4',  'Players at Street7',    0, 10]
                         ,['h.playersAtShowdown', 'Players at Showdown',   0, 10]
                         ,['h.street0Raises',     'Bets to See Flop',      0,  5]
                         ,['h.street1Raises',     'Bets to See Turn',      0,  5]
                         ,['h.street2Raises',     'Bets to See River',     0,  5]
                         ,['h.street3Raises',     'Bets to See Street7',   0,  5]
                         ,['h.street4Raises',     'Bets to See Showdown',  0,  5]
                         ]

        self.cardstests = [
            [Card.DATABASE_FILTERS['pair'], _('Pocket pairs')],
            [Card.DATABASE_FILTERS['suited'], _('Suited')],
            [Card.DATABASE_FILTERS['suited_connectors'], _('Suited connectors')],
            [Card.DATABASE_FILTERS['offsuit'], _('Offsuit')],
            [Card.DATABASE_FILTERS['offsuit_connectors'], _('Offsuit connectors')],
        ]
        self.stats_frame = None
        self.stats_vbox = None
        self.detailFilters = []   # the data used to enhance the sql select
        self.cardsFilters = []
        
        self.stats_frame = QFrame()
        self.stats_frame.setLayout(QVBoxLayout())

        self.stats_vbox = QSplitter(Qt.Vertical)
        self.stats_frame.layout().addWidget(self.stats_vbox)

        self.addWidget(scroll)
        self.addWidget(self.stats_frame)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

        # Make sure Hand column is not displayed.
        hand_column = (x for x in self.columns if x[0] == 'hand').next()
        hand_column[colshowsumm] = hand_column[colshowposn] = False

        # If rfi and steal both on for summaries, turn rfi off.
        rfi_column = (x for x in self.columns if x[0] == 'rfi').next()
        steals_column = (x for x in self.columns if x[0] == 'steals').next()
        if rfi_column[colshowsumm] and steals_column[colshowsumm]:
            rfi_column[colshowsumm] = False

        # If rfi and steal both on for position breakdowns, turn steals off.
        if rfi_column[colshowposn] and steals_column[colshowposn]:
            steals_column[colshowposn] = False

    def refreshStats(self, checkState):
        self.liststore = []
        self.listcols = []
        self.stats_frame.layout().removeWidget(self.stats_vbox)
        self.stats_vbox.setParent(None)
        self.stats_vbox = QSplitter(Qt.Vertical)
        self.stats_frame.layout().addWidget(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)

        if self.liststore:
            topsize = self.stats_vbox.widget(0).sizeHint().height()
            self.stats_vbox.setSizes([topsize, self.stats_vbox.height() - topsize])
            self.stats_vbox.setStretchFactor(0, 0)
            self.stats_vbox.setStretchFactor(1, 1)

    def fillStatsFrame(self, vbox):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        limits  = self.filters.getLimits()
        seats  = self.filters.getSeats()
        groups = self.filters.getGroups()
        dates = self.filters.getDates()
        games = self.filters.getGames()
        currencies = self.filters.getCurrencies()
        sitenos = []
        playerids = []

        # Which sites are selected?
        for site in sites:
            sitenos.append(siteids[site])
            _hname = Charset.to_utf8(heroes[site])
            result = self.db.get_player_id(self.conf, site, _hname)
            if result is not None:
                playerids.append(int(result))

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

        self.createStatsTable(vbox, playerids, sitenos, limits, seats, groups, dates, games, currencies)

    def createStatsTable(self, vbox, playerids, sitenos, limits, seats, groups, dates, games, currencies):
        startTime = time()
        show_detail = True

#        # Display summary table at top of page
#        # 3rd parameter passes extra flags, currently includes:
#        #   holecards - whether to display card breakdown (True/False)
#        #   numhands  - min number hands required when displaying all players
#        #   gridnum   - index for grid data structures
        flags = [False, self.filters.getNumHands(), 0]
        self.addGrid(vbox, 'playerDetailedStats', flags, playerids
                    ,sitenos, limits, seats, groups, dates, games, currencies)

        if 'allplayers' in groups:
            # can't currently do this combination so skip detailed table
            show_detail = False

        if show_detail: 
            # Separator
            frame = QWidget()
            vbox2 = QVBoxLayout()
            vbox2.setContentsMargins(0,0,0,0)
            frame.setLayout(vbox2)
            vbox.addWidget(frame)
            heading = QLabel(self.filterText['handhead'])
            heading.setAlignment(Qt.AlignHCenter)
            vbox2.addWidget(heading)

            # Detailed table
            flags[0] = True
            flags[2] = 1
            self.addGrid(vbox2, 'playerDetailedStats', flags, playerids
                        ,sitenos, limits, seats, groups, dates, games, currencies)

        self.db.rollback()
        print (_("Stats page displayed in %4.2f seconds") % (time() - startTime))

    def addGrid(self, vbox, query, flags, playerids, sitenos, limits, seats, groups, dates, games, currencies):
        sqlrow = 0
        if not flags:  holecards,grid = False,0
        else:          holecards,grid = flags[0],flags[2]

        tmp = self.sql.query[query]
        tmp = self.refineQuery(tmp, flags, playerids, sitenos, limits, seats, groups, dates, games, currencies)
        self.cursor.execute(tmp)
        result = self.cursor.fetchall()
        colnames = [desc[0].lower() for desc in self.cursor.description]

        # pre-fetch some constant values:
        colshow = colshowsumm
        if 'posn' in groups:  colshow = colshowposn
        self.cols_to_show = [x for x in self.columns if x[colshow]]
        hgametypeid_idx = colnames.index('hgametypeid')

        assert len(self.liststore) == grid, "len(self.liststore)="+str(len(self.liststore))+" grid-1="+str(grid)
        view = QTableView()
        self.liststore.append(QStandardItemModel(0, len(self.cols_to_show), view))
        self.liststore[grid].setSortRole(Qt.UserRole)
        view.setModel(self.liststore[grid])
        view.verticalHeader().hide()
        vbox.addWidget(view)
        self.listcols.append( [] )

        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
        for col, column in enumerate(self.cols_to_show):
            if column[colalias] == 'game' and holecards:
                s = [x for x in self.columns if x[colalias] == 'hand'][0][colheading]
            else:
                s = column[colheading]
            self.listcols[grid].append(s)
        self.liststore[grid].setHorizontalHeaderLabels(self.listcols[grid])

        rows = len(result) # +1 for title row

        while sqlrow < rows:
            treerow = []
            for col,column in enumerate(self.cols_to_show):
                if column[colalias] in colnames:
                    value = result[sqlrow][colnames.index(column[colalias])]
                    if column[colalias] == 'plposition':
                        if value == 'B':
                            value = 'BB'
                        elif value == 'S':
                            value = 'SB'
                        elif value == '0':
                            value = 'Btn'
                else:
                    if column[colalias] == 'game':
                        if holecards:
                            value = Card.decodeStartHandValue(result[sqlrow][colnames.index('category')], result[sqlrow][hgametypeid_idx] )
                        else:
                            minbb = result[sqlrow][colnames.index('minbigblind')]
                            maxbb = result[sqlrow][colnames.index('maxbigblind')]
                            value = result[sqlrow][colnames.index('limittype')] + ' ' \
                                    + result[sqlrow][colnames.index('category')].title() + ' ' \
                                    + result[sqlrow][colnames.index('name')] + ' ' \
                                    + result[sqlrow][colnames.index('currency')] + ' '
                            if 100 * int(minbb/100.0) != minbb:
                                value += '%.2f' % (minbb/100.0)
                            else:
                                value += '%.0f' % (minbb/100.0)
                            if minbb != maxbb:
                                if 100 * int(maxbb/100.0) != maxbb:
                                    value += ' - %.2f' % (maxbb/100.0)
                                else:
                                    value += ' - %.0f' % (maxbb/100.0)
                            ante = result[sqlrow][colnames.index('ante')]
                            if ante > 0:
                                value += ' ante: %.2f' % (ante/100.0)
                            if result[sqlrow][colnames.index('fast')] == 1:
                                value += ' ' + fast_names[result[sqlrow][colnames.index('name')]]
                    else:
                        continue
                item = QStandardItem('')
                sortValue = -1e9
                if value is not None and value != -999:
                    item = QStandardItem(column[colformat] % value)
                    if column[colalias] == 'game' and holecards:
                        if result[sqlrow][colnames.index('category')] == 'holdem':
                            sortValue = 1000 * ranks[value[0]] + 10 * ranks[value[1]] + (1 if len(value) == 3 and value[2] == 's' else 0)
                        else:
                            sortValue = -1
                    elif column[colalias] in ('game', 'pname'):
                        sortValue = value
                    elif column[colalias] == 'plposition':
                        sortValue = ['BB', 'SB', 'Btn', '1', '2', '3', '4', '5', '6', '7'].index(value)
                    else:
                        sortValue = float(value)
                item.setData(sortValue, Qt.UserRole)
                item.setEditable(False)
                if col != 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if column[colalias] != 'game':
                    item.setToolTip('<big>%s for %s</big><br/><i>%s</i>' % (column[colheading],treerow[0].text(),onlinehelp[column[colheading]]))
                treerow.append(item)
            self.liststore[grid].appendRow(treerow)
            sqlrow += 1

        view.resizeColumnsToContents()
        view.setSortingEnabled(True) # do this after resizing columns, otherwise it leaves room for the sorting triangle in every heading
        view.resizeColumnToContents(0) # we want room for the sorting triangle in column 0 where it starts.
        view.resizeRowsToContents()

    def refineQuery(self, query, flags, playerids, sitenos, limits, seats, groups, dates, games, currencies):
        having = ''
        if not flags:
            holecards = False
            numhands = 0
        else:
            holecards = flags[0]
            numhands = flags[1]
        colshow = colshowsumm
        if 'posn' in groups:  colshow = colshowposn

        pname_column = (x for x in self.columns if x[0] == 'pname').next()
        if 'allplayers' in groups:
            nametest = "(hp.playerId)"
            if holecards or 'posn' in groups:
                pname = "'all players'"
                # set flag in self.columns to not show player name column
                pname_column[colshow] = False
                # can't do this yet (re-write doing more maths in python instead of sql?)
                if numhands:
                    nametest = "(-1)"
            else:
                pname = "p.name"
                # set flag in self.columns to show player name column
                pname_column[colshow] = True
                if numhands:
                    having = ' and count(1) > %d ' % (numhands,)
        else:
            if playerids:
                nametest = str(tuple(playerids))
                nametest = nametest.replace("L", "")
                nametest = nametest.replace(",)",")")
            else:
                nametest = "1 = 2"
            pname = "p.name"
            # set flag in self.columns to not show player name column
            pname_column[colshow] = False
        query = query.replace("<player_test>", nametest)
        query = query.replace("<playerName>", pname)
        query = query.replace("<havingclause>", having)

        gametest = ""
        for m in self.filters.display.items():
            if m[0] == 'Games' and m[1]:
                if len(games) > 0:
                    gametest = str(tuple(games))
                    gametest = gametest.replace("L", "")
                    gametest = gametest.replace(",)",")")
                    gametest = gametest.replace("u'","'")
                    gametest = "and gt.category in %s" % gametest
                else:
                    gametest = "and gt.category IS NULL"
        query = query.replace("<game_test>", gametest)
        
        currencytest = str(tuple(currencies))
        currencytest = currencytest.replace(",)",")")
        currencytest = currencytest.replace("u'","'")
        currencytest = "AND gt.currency in %s" % currencytest
        query = query.replace("<currency_test>", currencytest)

        sitetest = ""
        for m in self.filters.display.items():
            if m[0] == 'Sites' and m[1]:
                if len(sitenos) > 0:
                    sitetest = str(tuple(sitenos))
                    sitetest = sitetest.replace("L", "")
                    sitetest = sitetest.replace(",)",")")
                    sitetest = sitetest.replace("u'","'")
                    sitetest = "and gt.siteId in %s" % sitetest
                else:
                    sitetest = "and gt.siteId IS NULL"
        query = query.replace("<site_test>", sitetest)
        
        if seats:
            query = query.replace('<seats_test>', 'between ' + str(seats['from']) + ' and ' + str(seats['to']))
            if 'seats' in groups:
                query = query.replace('<groupbyseats>', ',h.seats')
                query = query.replace('<orderbyseats>', ',h.seats')
            else:
                query = query.replace('<groupbyseats>', '')
                query = query.replace('<orderbyseats>', '')
        else:
            query = query.replace('<seats_test>', 'between 0 and 100')
            query = query.replace('<groupbyseats>', '')
            query = query.replace('<orderbyseats>', '')

        bbtest = self.filters.get_limits_where_clause(limits)

        query = query.replace("<gtbigBlind_test>", bbtest)

        if holecards:  # re-use level variables for hole card query
            query = query.replace("<hgametypeId>", "hp.startcards")
            query = query.replace("<orderbyhgametypeId>"
                                 , ",case when floor((hp.startcards-1)/13) >= mod((hp.startcards-1),13) then hp.startcards + 0.1 "
                                   +    " else 13*mod((hp.startcards-1),13) + floor((hp.startcards-1)/13) + 1 "
                                   +    " end desc ")
        else:
            query = query.replace("<orderbyhgametypeId>", "")
            groupLevels = 'limits' not in groups
            if groupLevels:
                query = query.replace("<hgametypeId>", "p.name")  # need to use p.name for sqlite posn stats to work
            else:
                query = query.replace("<hgametypeId>", "h.gametypeId")

        # process self.detailFilters (a list of tuples)
        flagtest = ''
        if self.detailFilters:
            for f in self.detailFilters:
                if len(f) == 3:
                    # X between Y and Z
                    flagtest += ' and %s between %s and %s ' % (f[0], str(f[1]), str(f[2]))
        query = query.replace("<flagtest>", flagtest)
        if self.cardsFilters:
            cardstests = []

            for cardFilter in self.cardsFilters:
                cardstests.append(cardFilter)
            cardstests = ''.join(('and (', ' or '.join(cardstests), ')'))
        else:
            cardstests = ''
        query = query.replace("<cardstest>", cardstests)
        # allow for differences in sql cast() function:
        if self.db.backend == self.MYSQL_INNODB:
            query = query.replace("<signed>", 'signed ')
        else:
            query = query.replace("<signed>", '')

        # Filter on dates
        query = query.replace("<datestest>", " between '" + dates[0] + "' and '" + dates[1] + "'")

        # Group by position?
        plposition_column = (x for x in self.columns if x[0] == 'plposition').next()
        if 'posn' in groups:
            query = query.replace("<position>", "hp.position")
            plposition_column[colshow] = True
        else:
            query = query.replace("<position>", "gt.base")
            plposition_column[colshow] = False

        return(query)

    def showDetailFilter(self, checkState):
        detailDialog = QDialog(self.main_window)
        detailDialog.setWindowTitle(_("Detailed Filters"))

        handbox = QVBoxLayout()
        detailDialog.setLayout(handbox)

        label = QLabel(_("Hand Filters:"))
        handbox.addWidget(label)
        label.setAlignment(Qt.AlignCenter)

        grid = QGridLayout()
        handbox.addLayout(grid)
        for row, htest in enumerate(self.handtests):
            cb = QCheckBox()
            lbl_from = QLabel(htest[1])
            lbl_tween = QLabel(_('between'))
            lbl_to   = QLabel(_('and'))
            sb1 = QSpinBox()
            sb1.setRange(0, 10)
            sb1.setValue(htest[2])
            sb2 = QSpinBox()
            sb2.setRange(2, 10)
            sb2.setValue(htest[3])

            for df in self.detailFilters:
                if df[0] == htest[0]:
                    cb.setChecked(True)
                    break

            grid.addWidget(cb, row, 0)
            grid.addWidget(lbl_from, row, 1, Qt.AlignLeft)
            grid.addWidget(lbl_tween, row, 2)
            grid.addWidget(sb1, row, 3)
            grid.addWidget(lbl_to, row, 4)
            grid.addWidget(sb2, row, 5)

            htest[4:7] = [cb,sb1,sb2]

        label = QLabel(_('Restrict to hand types:'))
        handbox.addWidget(label)
        for ctest in self.cardstests:
            hbox = QHBoxLayout()
            handbox.addLayout(hbox)
            cb = QCheckBox()
            if ctest[0] in self.cardsFilters:
                cb.setChecked(True)
            label = QLabel(ctest[1])
            hbox.addWidget(cb)
            hbox.addWidget(label)
            ctest[2:3] = [cb]
        btnBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        handbox.addWidget(btnBox)
        btnBox.accepted.connect(detailDialog.accept)
        btnBox.rejected.connect(detailDialog.reject)
        response = detailDialog.exec_()

        if response:
            self.detailFilters = []
            for ht in self.handtests:
                if ht[4].isChecked():
                    self.detailFilters.append( (ht[0], ht[5].value(), ht[6].value()) )
                ht[2],ht[3] = ht[5].value(), ht[6].value()
            self.cardsFilters = []
            for ct in self.cardstests:
                if ct[2].isChecked():
                    self.cardsFilters.append(ct[0])
            self.refreshStats(None)

if __name__ == "__main__":
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
    main_window = QMainWindow()
    i = GuiRingPlayerStats(config, sql, main_window)
    main_window.setCentralWidget(i)
    main_window.show()
    main_window.resize(1400, 800)
    app.exec_()
