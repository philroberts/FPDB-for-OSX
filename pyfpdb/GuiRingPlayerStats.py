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

import traceback
import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
from time import time, strftime

import Card
import Database
import Filters
import Charset

from TreeViewTooltips import TreeViewTooltips


#colalias,colshowsumm,colshowposn,colheading,colxalign,colformat,coltype = 0,1,2,3,4,5,6
#new order in config file:
colalias,colheading,colshowsumm,colshowposn,colformat,coltype,colxalign = 0,1,2,3,4,5,6
ranks = {'x':0, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
fast_names = {'OnGame':'Strobe', 'PokerStars':'Zoom', 'Full Tilt Poker':'Rush', 'Bovada':'Zone'}
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
              'Std. Dev':_('Measure of uncertainty')
              } 



class DemoTips(TreeViewTooltips):

    def __init__(self, customer_column):
        # call base class init
        TreeViewTooltips.__init__(self)

    def get_tooltip(self, view, column, path):
        model = view.get_model()
        cards = model[path][0]
        title=column.get_title()
        if (title == 'Hand' or title == 'Game'): display=''     #no tooltips on headers                   
        else: display='<big>%s for %s</big>\n<i>%s</i>' % (title,cards,onlinehelp[title])
        return (display)

    def location(self, x, y, w, h):
        # this will place the tooltip above and to the right
        return x + 30, y - (h + 10)
        
        

class GuiRingPlayerStats:

    def __init__(self, config, querylist, mainwin, debug=True):
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

        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        self.filters.registerButton1Name(_("_Filters"))
        self.filters.registerButton1Callback(self.showDetailFilter)
        self.filters.registerButton2Name(_("_Refresh Stats"))
        self.filters.registerButton2Callback(self.refreshStats)

        # ToDo: store in config
        # ToDo: create popup to adjust column config
        # columns to display, keys match column name returned by sql, values in tuple are:
        #     is column displayed(summary then position), column heading, xalignment, formatting, celltype
        self.columns = self.conf.get_gui_cash_stat_params()

        # Detail filters:  This holds the data used in the popup window, extra values are
        # added at the end of these lists during processing
        #                  sql test,              screen description,        min, max
        self.handtests = [  # already in filter class : ['h.seats', 'Number of Players', 2, 10]
                          ['h.maxSeats',          'Size of Table',         2, 10]
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
        
        #self.main_hbox = gtk.HBox(False, 0)
        #self.main_hbox.show()
        self.main_hbox = gtk.HPaned()

        self.stats_frame = gtk.Frame()
        self.stats_frame.show()

        self.stats_vbox = gtk.VPaned()
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        self.top_pane_height = 0
        self.height_inc = None
        # self.fillStatsFrame(self.stats_vbox)

        #self.main_hbox.pack_start(self.filters.get_vbox())
        #self.main_hbox.pack_start(self.stats_frame, expand=True, fill=True)
        self.main_hbox.pack1(self.filters.get_vbox())
        self.main_hbox.pack2(self.stats_frame)
        self.main_hbox.show()

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

        self.last_pos = -1


    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox
    #end def get_vbox

    def refreshStats(self, widget, data):
        #self.last_pos = self.stats_vbox.get_position()
        self.height_inc = None
        #old_len = 0
        #if self.liststore:
        #    old_len = len(self.liststore[0])
        try: self.stats_vbox.destroy()
        except AttributeError: pass
        self.liststore = []
        self.listcols = []
        self.stats_vbox = gtk.VPaned()
        self.stats_vbox.show()
        self.stats_frame.add(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)

        # set height of top pane
        # (tried 2 ways, guesstimate using ratio of old to new number of rows and sum of
        #  heights of parts)
        new_len = 0
        if self.liststore:
            #new_len = len(self.liststore[0])
            #print "setting to", self.top_pane_height + self.height_inc
            self.stats_vbox.set_position(self.top_pane_height + self.height_inc)
        #if self.last_pos > 0:
        #    if old_len > 0 and new_len > 0 and new_len <= 10:
        #        self.stats_vbox.set_position(self.last_pos * (new_len+1.9)/(old_len+1.9))
        #    else:
        #        self.stats_vbox.set_position(self.last_pos)
    #end def refreshStats

    def fillStatsFrame(self, vbox):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        limits  = self.filters.getLimits()
        type   = self.filters.getType()
        seats  = self.filters.getSeats()
        groups = self.filters.getGroups()
        dates = self.filters.getDates()
        games = self.filters.getGames()
        currencies = self.filters.getCurrencies()
        sitenos = []
        playerids = []

        # Which sites are selected?
        for site in sites:
            if sites[site] == True:
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

        self.createStatsTable(vbox, playerids, sitenos, limits, type, seats, groups, dates, games, currencies)
    #end def fillStatsFrame

    def createStatsTable(self, vbox, playerids, sitenos, limits, type, seats, groups, dates, games, currencies):
        startTime = time()
        show_detail = True

        # Scrolled window for summary table
        swin = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack1(swin) #, resize=True)  don't use resize, self.height_inc relies on initial 
                         # height of pane being correct for one row

        # Display summary table at top of page
        # 3rd parameter passes extra flags, currently includes:
        #   holecards - whether to display card breakdown (True/False)
        #   numhands  - min number hands required when displaying all players
        #   gridnum   - index for grid data structures
        flags = [False, self.filters.getNumHands(), 0]
        self.addGrid(swin, 'playerDetailedStats', flags, playerids
                    ,sitenos, limits, type, seats, groups, dates, games, currencies)
        swin.show()

        if 'allplayers' in groups and groups['allplayers']:
            # can't currently do this combination so skip detailed table
            show_detail = False

        if show_detail: 
            # Separator
            vbox2 = gtk.VBox(False, 0)
            heading = gtk.Label(self.filterText['handhead'])
            heading.show()
            vbox2.pack_start(heading, expand=False, padding=3)

            # Scrolled window for detailed table (display by hand)
            swin2 = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
            swin2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            swin2.show()
            vbox2.pack_start(swin2, expand=True, padding=3)
            vbox.pack2(vbox2)
            vbox2.show()

            # Detailed table
            flags[0] = True
            flags[2] = 1
            self.addGrid(swin2, 'playerDetailedStats', flags, playerids
                        ,sitenos, limits, type, seats, groups, dates, games, currencies)

        if self.height_inc is None:
            self.height_inc = 0
            # need this to check whether scrollbar is visible:
            while gtk.events_pending(): # see http://faq.pygtk.org/index.py?req=index for more hints (3.7)
                gtk.main_iteration(False)
            hs = swin.get_hscrollbar()
            if hs is not None:
                #print "hs vis", hs.get_property('visible'), hs.get_property('visible').__class__
                if hs.get_property('visible'):
                    self.height_inc = hs.size_request()[1] + swin.style_get_property('scrollbar-spacing')
            #print "hh set to", self.height_inc
            self.stats_vbox.set_position(self.top_pane_height + self.height_inc)

        self.db.rollback()
        print (_("Stats page displayed in %4.2f seconds") % (time() - startTime))
    #end def createStatsTable

    def reset_style_render_func(self, treeviewcolumn, cell, model, iter):
        cell.set_property('foreground', None)
    #end def reset_style_render_func

    def ledger_style_render_func(self, tvcol, cell, model, iter):
        str = cell.get_property('text')
        if '-' in str:
            str = str.replace("-", "")
            str = "(%s)" %(str)
            cell.set_property('text', str)
            cell.set_property('foreground', 'red')
        else:
            cell.set_property('foreground', 'darkgreen')

        return

    def sortnums(self, model, iter1, iter2, nums):
        ret = 0
        (n, grid) = nums
        a = self.liststore[grid].get_value(iter1, n)
        b = self.liststore[grid].get_value(iter2, n)
        if 'f' in self.cols_to_show[n][4]:
            try:     a = float(a)
            except:  a = 0.0
            try:     b = float(b)
            except:  b = 0.0
        if n == 0 and grid == 1: #make sure it only works on the starting hands
            a1,a2,a3 = ranks[a[0]], ranks[a[1]], (a+'o')[2]
            b1,b2,b3 = ranks[b[0]], ranks[b[1]], (b+'o')[2]
            if a1 > b1 or ( a1 == b1 and (a2 > b2 or (a2 == b2 and a3 > b3) ) ):
                ret = 1
            else:
                ret = -1
        else:
            if a < b:
                ret = -1
            elif a == b:
                ret = 0
            else:
                ret = 1
        #print "n =", n, "iter1[n] =", self.liststore[grid].get_value(iter1,n), "iter2[n] =", self.liststore[grid].get_value(iter2,n), "ret =", ret

        return(ret)

    def sortcols(self, col, nums):
        try:
            #This doesn't actually work yet - clicking heading in top section sorts bottom section :-(
            (n, grid) = nums
            if not col.get_sort_indicator() or col.get_sort_order() == gtk.SORT_ASCENDING:
                col.set_sort_order(gtk.SORT_DESCENDING)
            else:
                col.set_sort_order(gtk.SORT_ASCENDING)
            self.liststore[grid].set_sort_column_id(n, col.get_sort_order())
            self.liststore[grid].set_sort_func(n, self.sortnums, (n,grid))
            for i in xrange(len(self.listcols[grid])):
                self.listcols[grid][i].set_sort_indicator(False)
            self.listcols[grid][n].set_sort_indicator(True)
            # use this   listcols[col].set_sort_indicator(True)
            # to turn indicator off for other cols
        except:
            err = traceback.extract_tb(sys.exc_info()[2])
            print ("***sortcols " + _("error") + ": " + str(sys.exc_info()[1]))
            print "\n".join( [e[0]+':'+str(e[1])+" "+e[2] for e in err] )
    #end def sortcols
    

    def addGrid(self, vbox, query, flags, playerids, sitenos, limits, type, seats, groups, dates, games, currencies):
        counter = 0
        row = 0
        sqlrow = 0
        if not flags:  holecards,grid = False,0
        else:          holecards,grid = flags[0],flags[2]

        tmp = self.sql.query[query]
        tmp = self.refineQuery(tmp, flags, playerids, sitenos, limits, type, seats, groups, dates, games, currencies)
        #print "DEBUG: query: %s" % tmp
        self.cursor.execute(tmp)
        result = self.cursor.fetchall()
        colnames = [desc[0].lower() for desc in self.cursor.description]

        # pre-fetch some constant values:
        colshow = colshowsumm
        if groups['posn']:  colshow = colshowposn 
        self.cols_to_show = [x for x in self.columns if x[colshow]]
        hgametypeid_idx = colnames.index('hgametypeid')

        assert len(self.liststore) == grid, "len(self.liststore)="+str(len(self.liststore))+" grid-1="+str(grid)
        self.liststore.append( gtk.ListStore(*([str] * len(self.cols_to_show))) )
        view = gtk.TreeView(model=self.liststore[grid])
        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        #vbox.pack_start(view, expand=False, padding=3)
        vbox.add(view)
        textcell = gtk.CellRendererText()
        textcell50 = gtk.CellRendererText()
        textcell50.set_property('xalign', 0.5)
        numcell = gtk.CellRendererText()
        numcell.set_property('xalign', 1.0)
        assert len(self.listcols) == grid
        self.listcols.append( [] )

        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
        for col, column in enumerate(self.cols_to_show):
            if column[colalias] == 'game' and holecards:
                s = [x for x in self.columns if x[colalias] == 'hand'][0][colheading]
            else:
                s = column[colheading]
            self.listcols[grid].append(gtk.TreeViewColumn(s))
            view.append_column(self.listcols[grid][col])
            if column[colformat] == '%s':
                if column[colxalign] == 0.0:
                    self.listcols[grid][col].pack_start(textcell, expand=True)
                    self.listcols[grid][col].add_attribute(textcell, 'text', col)
                    cellrend = textcell
                else:
                    self.listcols[grid][col].pack_start(textcell50, expand=True)
                    self.listcols[grid][col].add_attribute(textcell50, 'text', col)
                    cellrend = textcell50
                self.listcols[grid][col].set_expand(True)
            else:
                self.listcols[grid][col].pack_start(numcell, expand=True)
                self.listcols[grid][col].add_attribute(numcell, 'text', col)
                self.listcols[grid][col].set_expand(True)
                cellrend = numcell
                #self.listcols[grid][col].set_alignment(column[colxalign]) # no effect?
            self.listcols[grid][col].set_clickable(True)
            self.listcols[grid][col].connect("clicked", self.sortcols, (col,grid))
            if col == 0:
                self.listcols[grid][col].set_sort_order(gtk.SORT_DESCENDING)
                self.listcols[grid][col].set_sort_indicator(True)
            if column[coltype] == 'cash':
                self.listcols[grid][col].set_cell_data_func(numcell, self.ledger_style_render_func)
            else:
                self.listcols[grid][col].set_cell_data_func(cellrend, self.reset_style_render_func)

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
                                    + result[sqlrow][colnames.index('name')] + ' $'
                            if 100 * int(minbb/100.0) != minbb:
                                value += '%.2f' % (minbb/100.0)
                            else:
                                value += '%.0f' % (minbb/100.0)
                            if minbb != maxbb:
                                if 100 * int(maxbb/100.0) != maxbb:
                                    value += ' - $' + '%.2f' % (maxbb/100.0)
                                else:
                                    value += ' - $' + '%.0f' % (maxbb/100.0)
                            if result[sqlrow][colnames.index('fast')] == 1:
                                value += ' ' + fast_names[result[sqlrow][colnames.index('name')]]
                    else:
                        continue
                if value != None and value != -999:
                    treerow.append(column[colformat] % value)
                else:
                    treerow.append(' ')
            iter = self.liststore[grid].append(treerow)
            #print treerow
            sqlrow += 1
            row += 1
        tips = DemoTips(column[colformat])
        tips.add_view(view)     

        vbox.show_all()
        view.show()
        if len(self.liststore) == 1:
            #print "view hieght is ", view.get_allocation().height, view.size_request(), view.get_visible_rect().height, view.get_vadjustment().get_value()
            self.top_pane_height = view.size_request()[1]
            #print "saved ", self.top_pane_height
    #end def addGrid

    def refineQuery(self, query, flags, playerids, sitenos, limits, type, seats, groups, dates, games, currencies):
        having = ''
        if not flags:
            holecards = False
            numhands = 0
        else:
            holecards = flags[0]
            numhands = flags[1]
        colshow = colshowsumm
        if groups['posn']:  colshow = colshowposn 

        pname_column = (x for x in self.columns if x[0] == 'pname').next()
        if 'allplayers' in groups and groups['allplayers']:
            nametest = "(hp.playerId)"
            if holecards or groups['posn']:
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
        q = []
        for m in self.filters.display.items():
            if m[0] == 'Games' and m[1]:
                for n in games:
                    if games[n]:
                        q.append(n)
                if len(q) > 0:
                    gametest = str(tuple(q))
                    gametest = gametest.replace("L", "")
                    gametest = gametest.replace(",)",")")
                    gametest = gametest.replace("u'","'")
                    gametest = "and gt.category in %s" % gametest
                else:
                    gametest = "and gt.category IS NULL"
        query = query.replace("<game_test>", gametest)
        
        q = []
        for n in currencies:
            if currencies[n]:
                q.append(n)
        currencytest = str(tuple(q))
        currencytest = currencytest.replace(",)",")")
        currencytest = currencytest.replace("u'","'")
        currencytest = "AND gt.currency in %s" % currencytest
        query = query.replace("<currency_test>", currencytest)

        sitetest = ""
        q = []
        for m in self.filters.display.items():
            if m[0] == 'Sites' and m[1]:
                for n in sitenos:
                        q.append(n)
                if len(q) > 0:
                    sitetest = str(tuple(q))
                    sitetest = sitetest.replace("L", "")
                    sitetest = sitetest.replace(",)",")")
                    sitetest = sitetest.replace("u'","'")
                    sitetest = "and gt.siteId in %s" % sitetest
                else:
                    sitetest = "and gt.siteId IS NULL"
        query = query.replace("<site_test>", sitetest)
        
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
            groupLevels = "show" not in str(limits)
            if groupLevels:
                query = query.replace("<hgametypeId>", "p.name")  # need to use p.name for sqlite posn stats to work
            else:
                query = query.replace("<hgametypeId>", "h.gametypeId")

        # process self.detailFilters (a list of tuples)
        flagtest = ''
        #self.detailFilters = [('h.seats', 5, 6)]   # for debug
        if self.detailFilters:
            for f in self.detailFilters:
                if len(f) == 3:
                    # X between Y and Z
                    flagtest += ' and %s between %s and %s ' % (f[0], str(f[1]), str(f[2]))
        query = query.replace("<flagtest>", flagtest)
        if self.cardsFilters:
            cardstests = []

            for filter in self.cardsFilters:
                cardstests.append(filter)
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
        if groups['posn']:
            #query = query.replace("<position>", "case hp.position when '0' then 'Btn' else hp.position end")
            query = query.replace("<position>", "hp.position")
            plposition_column[colshow] = True
        else:
            query = query.replace("<position>", "gt.base")
            plposition_column[colshow] = False

        #print "query =\n", query
        return(query)
    #end def refineQuery

    def showDetailFilter(self, widget, data):
        detailDialog = gtk.Dialog(title=_("Detailed Filters"), parent=self.main_window
                                 ,flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                                 ,buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                           gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        handbox = gtk.VBox(True, 0)
        detailDialog.vbox.pack_start(handbox, False, False, 0)
        handbox.show()

        label = gtk.Label(_("Hand Filters:"))
        handbox.add(label)
        label.show()

        betweenFilters = []
        def add_hbox():
            hbox = gtk.HBox(False, 0)
            handbox.pack_start(hbox, False, False, 0)
            hbox.show()
            return hbox

        for htest in self.handtests:
            hbox = add_hbox()
            cb = gtk.CheckButton()
            lbl_from = gtk.Label(htest[1])
            lbl_from.set_alignment(xalign=0.0, yalign=0.5)
            lbl_tween = gtk.Label(_('between'))
            lbl_to   = gtk.Label(_('and'))
            adj1 = gtk.Adjustment(value=htest[2], lower=0, upper=10, step_incr=1, page_incr=1, page_size=0)
            sb1 = gtk.SpinButton(adjustment=adj1, climb_rate=0.0, digits=0)
            adj2 = gtk.Adjustment(value=htest[3], lower=2, upper=10, step_incr=1, page_incr=1, page_size=0)
            sb2 = gtk.SpinButton(adjustment=adj2, climb_rate=0.0, digits=0)

            for df in [x for x in self.detailFilters if x[0] == htest[0]]:
                cb.set_active(True)

            hbox.pack_start(cb, expand=False, padding=3)
            hbox.pack_start(lbl_from, expand=True, padding=3)
            hbox.pack_start(lbl_tween, expand=False, padding=3)
            hbox.pack_start(sb1, False, False, 0)
            hbox.pack_start(lbl_to, expand=False, padding=3)
            hbox.pack_start(sb2, False, False, 0)

            cb.show()
            lbl_from.show()
            lbl_tween.show()
            sb1.show()
            lbl_to.show()
            sb2.show()

            htest[4:7] = [cb,sb1,sb2]

        label = gtk.Label(_('Restrict to hand types:'))
        handbox.add(label)
        label.show()
        for ctest in self.cardstests:
            hbox = add_hbox()
            cb = gtk.CheckButton()
            if ctest[0] in self.cardsFilters:
                cb.set_active(True)
            label = gtk.Label(ctest[1])
            hbox.pack_start(cb, expand=False, padding=3)
            hbox.pack_start(label, expand=True, padding=3)
            cb.show()
            label.show()
            ctest[2:3] = [cb]
        response = detailDialog.run()

        if response == gtk.RESPONSE_ACCEPT:
            self.detailFilters = []
            for ht in self.handtests:
                if ht[4].get_active():
                    self.detailFilters.append( (ht[0], ht[5].get_value_as_int(), ht[6].get_value_as_int()) )
                ht[2],ht[3] = ht[5].get_value_as_int(), ht[6].get_value_as_int()
            print "detailFilters =", self.detailFilters
            self.cardsFilters = []
            for ct in self.cardstests:
                if ct[2].get_active():
                    self.cardsFilters.append(ct[0])
            print "cardsFilters =", self.cardsFilters
            self.refreshStats(None, None)

        detailDialog.destroy()





