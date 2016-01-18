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

import os
from time import time, strftime
    
import Database
import Filters
import Charset

class GuiPositionalStats:
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
        settings.update(self.conf.get_import_parameters())
        settings.update(self.conf.get_default_paths())

        filters_display = { "Heroes"   :  True,
                            "Sites"    :  True,
                            "Games"    :  False,
                            "Limits"   :  True,
                            "LimitSep" :  True,
                            "Seats"    :  True,
                            "SeatSep"  :  True,
                            "Dates"    :  True,
                            "Button1"  :  True,
                            "Button2"  :  False
                          }

        self.filters = Filters.Filters(self.db, display = filters_display)
        self.filters.registerButton1Name(_("Refresh"))
        self.filters.registerButton1Callback(self.refreshStats)


        # ToDo: store in config
        # ToDo: create popup to adjust column config
        # columns to display, keys match column name returned by sql, values in tuple are:
        #     is column displayed, column heading, xalignment, formatting
        self.columns = [ ["game",       True,  "Game",     0.0, "%s"]
                       , ["hand",       False, "Hand",     0.0, "%s"]   # true not allowed for this line
                       , ["plposition", False, "Posn",     1.0, "%s"]   # true not allowed for this line (set in code)
                       , ["n",          True,  "Hds",      1.0, "%d"]
                       , ["avgseats",   True,  "Seats",    1.0, "%3.1f"]
                       , ["vpip",       True,  "VPIP",     1.0, "%3.1f"]
                       , ["pfr",        True,  "PFR",      1.0, "%3.1f"]
                       , ["pf3",        True,  "PF3",      1.0, "%3.1f"]
                       , ["steals",     True,  "Steals",   1.0, "%3.1f"]
                       , ["saw_f",      True,  "Saw_F",    1.0, "%3.1f"]
                       , ["sawsd",      True,  "SawSD",    1.0, "%3.1f"]
                       , ["wtsdwsf",    True,  "WtSDwsF",  1.0, "%3.1f"]
                       , ["wmsd",       True,  "W$SD",     1.0, "%3.1f"]
                       , ["flafq",      True,  "FlAFq",    1.0, "%3.1f"]
                       , ["tuafq",      True,  "TuAFq",    1.0, "%3.1f"]
                       , ["rvafq",      True,  "RvAFq",    1.0, "%3.1f"]
                       , ["pofafq",     False, "PoFAFq",   1.0, "%3.1f"]
                       , ["net",        True,  "Net($)",   1.0, "%6.2f"]
                       , ["bbper100",   True,  "bb/100",   1.0, "%4.2f"]
                       , ["rake",       True,  "Rake($)",  1.0, "%6.2f"]
                       , ["bb100xr",    True,  "bbxr/100", 1.0, "%4.2f"]
                       , ["variance",   True,  "Variance", 1.0, "%5.2f"]
                       , ["stddev",     True,  "Stddev",   1.0, "%5.2f"]
                       ]

        self.stat_table = None
        self.stats_frame = None
        self.stats_vbox = None

        self.main_hbox = gtk.HPaned()

        self.stats_frame = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.stats_frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.stats_frame.show()

        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add_with_viewport(self.stats_vbox)

        # This could be stored in config eventually, or maybe configured in this window somehow.
        # Each posncols element is the name of a column returned by the sql 
        # query (in lower case) and each posnheads element is the text to use as
        # the heading in the GUI. Both sequences should be the same length.
        # To miss columns out remove them from both tuples (the 1st 2 elements should always be included).
        # To change the heading just edit the second list element as required
        # If the first list element does not match a query column that pair is ignored
        self.posncols =  ( "game", "avgseats", "plposition", "vpip", "pfr", "pf3", "pf4", "pff3", "pff4", "steals"
                         , "saw_f", "sawsd", "wtsdwsf", "wmsd", "flafq", "tuafq", "rvafq"
                         , "pofafq", "net", "bbper100", "profitperhand", "variance", "stddev", "n"
                         )
        self.posnheads = ( "Game", "Seats", "Posn", "VPIP", "PFR", "PF3", "PF4", "PFF3", "PFF4", "Steals"
                         , "Saw_F", "SawSD", "WtSDwsF", "W$SD", "FlAFq", "TuAFq", "RvAFq"
                         , "PoFAFq", "Net($)", "bb/100", "$/hand", "Variance", "Stddev", "Hds"
                         )

        #self.fillStatsFrame(self.stats_vbox) #dont autoload, enter filters first (because of the bug that the tree is not scrollable, you cannot reach the refresh button with a lot of data)
        #self.stats_frame.add(self.stats_vbox)

        self.main_hbox.pack1(self.filters.get_vbox())
        self.main_hbox.pack2(self.stats_frame)
        self.main_hbox.show()


    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.main_hbox

    def toggleCallback(self, widget, data=None):
#        print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])
        self.activesite = data
        print (_("DEBUG:") + " " + _("activesite set to %s") % (self.activesite))

    def refreshStats(self, widget, data):
        try: self.stats_vbox.destroy()
        except AttributeError: pass
        self.stats_vbox = gtk.VBox(False, 0)
        self.stats_vbox.show()
        self.stats_frame.add_with_viewport(self.stats_vbox)
        self.fillStatsFrame(self.stats_vbox)

    def fillStatsFrame(self, vbox):
        sites = self.filters.getSites()
        heroes = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()
        limits  = self.filters.getLimits()
        seats = self.filters.getSeats()
        dates = self.filters.getDates()
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
        if not playerids:
            print _("No player ids found")
            return
        if not limits:
            print _("No limits found")
            return

        self.createStatsTable(vbox, playerids, sitenos, limits, seats, dates)

    def createStatsTable(self, vbox, playerids, sitenos, limits, seats, dates):

        starttime = time()
        colalias,colshow,colheading,colxalign,colformat = 0,1,2,3,4
        row = 0
        col = 0

        tmp = self.sql.query['playerStatsByPosition']
        tmp = self.refineQuery(tmp, playerids, sitenos, limits, seats, dates)
        #print "DEBUG:\n%s" % tmp
        self.cursor.execute(tmp)
        result = self.cursor.fetchall()
        colnames = [desc[0].lower() for desc in self.cursor.description]

        liststore = gtk.ListStore(*([str] * len(colnames)))
        view = gtk.TreeView(model=liststore)
        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        vbox.pack_start(view, expand=False, padding=3)
        # left-aligned cells:
        textcell = gtk.CellRendererText()
        # centred cells:
        textcell50 = gtk.CellRendererText()
        textcell50.set_property('xalign', 0.5)
        # right-aligned cells:
        numcell = gtk.CellRendererText()
        numcell.set_property('xalign', 1.0)
        listcols = []

        for t in self.posnheads:
            listcols.append(gtk.TreeViewColumn(self.posnheads[col]))
            view.append_column(listcols[col])
            if col == 0:
                listcols[col].pack_start(textcell, expand=True)
                listcols[col].add_attribute(textcell, 'text', col)
                listcols[col].set_expand(True)
            elif col in (1, 2):
                listcols[col].pack_start(textcell50, expand=True)
                listcols[col].add_attribute(textcell50, 'text', col)
                listcols[col].set_expand(True)
            else:
                listcols[col].pack_start(numcell, expand=True)
                listcols[col].add_attribute(numcell, 'text', col)
                listcols[col].set_expand(True)
            col +=1 

        # Code below to be used when full column data structures implemented like in player stats:
        
        # Create header row   eg column: ("game",     True, "Game",     0.0, "%s")
        #for col, column in enumerate(cols_to_show):
        #    if column[colalias] == 'game' and holecards:
        #        s = [x for x in self.columns if x[colalias] == 'hand'][0][colheading]
        #    else:
        #        s = column[colheading]
        #    listcols.append(gtk.TreeViewColumn(s))
        #    view.append_column(listcols[col])
        #    if column[colformat] == '%s':
        #        if column[colxalign] == 0.0:
        #            listcols[col].pack_start(textcell, expand=True)
        #            listcols[col].add_attribute(textcell, 'text', col)
        #        else:
        #            listcols[col].pack_start(textcell50, expand=True)
        #            listcols[col].add_attribute(textcell50, 'text', col)
        #        listcols[col].set_expand(True)
        #    else:
        #        listcols[col].pack_start(numcell, expand=True)
        #        listcols[col].add_attribute(numcell, 'text', col)
        #        listcols[col].set_expand(True)
        #        #listcols[col].set_alignment(column[colxalign]) # no effect?

        rows = len(result)

        last_game,last_seats,sqlrow = "","",0
        while sqlrow < rows:
            rowprinted=0
            treerow = []
            avgcol = colnames.index('avgseats')
            for col,colname in enumerate(self.posncols):
                if colname in colnames:
                    sqlcol = colnames.index(colname)
                else:
                    continue
                if result[sqlrow][sqlcol]:
                    if sqlrow == 0:
                        value = result[sqlrow][sqlcol]
                        rowprinted=1
                    elif result[sqlrow][0] != last_game:
                        value = ' '
#                    elif 'show' in seats and seats['show'] and result[sqlrow][avgcol] != last_seats: #FIXME 'show' in seats should now be 'show' in groups, but this class doesn't even use the group filters so it can never be set
#                        value = ' '
                    else:
                        value = result[sqlrow][sqlcol]
                        rowprinted=1
                else:
                    l = gtk.Label(' ')
                    value = ' '
                if value and value != -999:
                    treerow.append(value)
                else:
                    treerow.append(' ')
            iter = liststore.append(treerow)
            last_game = result[sqlrow][0]
            last_seats = result[sqlrow][avgcol]
            if rowprinted:
                sqlrow = sqlrow+1
            row = row + 1
        
        # show totals at bottom
        tmp = self.sql.query['playerStats']
        tmp = self.refineQuery(tmp, playerids, sitenos, limits, seats, dates)
        #print "DEBUG:\n%s" % tmp
        self.cursor.execute(tmp)
        result = self.cursor.fetchall()
        rows = len(result)
        colnames = [desc[0].lower() for desc in self.cursor.description]

        # blank row between main stats and totals:
        col = 0
        treerow = [' ' for x in self.posncols]
        iter = liststore.append(treerow)
        row = row + 1

        for sqlrow in range(rows):
            treerow = []
            for col,colname in enumerate(self.posncols):
                if colname in colnames:
                    sqlcol = colnames.index(colname)
                elif colname != "plposition":
                    continue
                if colname == 'plposition':
                    l = gtk.Label('Totals')
                    value = 'Totals'
                elif result[sqlrow][sqlcol]:
                    l = gtk.Label(result[sqlrow][sqlcol])
                    value = result[sqlrow][sqlcol]
                else:
                    l = gtk.Label(' ')
                    value = ' '
                if value and value != -999:
                    treerow.append(value)
                else:
                    treerow.append(' ')
            iter = liststore.append(treerow)
            row = row + 1
        vbox.show_all()

        self.db.rollback()
        print _("Positional Stats page displayed in %4.2f seconds") % (time() - starttime)
    #end def fillStatsFrame(self, vbox):

    def refineQuery(self, query, playerids, sitenos, limits, seats, dates):
        if playerids:
            nametest = str(tuple(playerids))
            nametest = nametest.replace("L", "")
            nametest = nametest.replace(",)",")")
            query = query.replace("<player_test>", nametest)
        else:
            query = query.replace("<player_test>", "1 = 2")

        if seats:
            query = query.replace('<seats_test>', 'between ' + str(seats['from']) + ' and ' + str(seats['to']))
            if False: #'show' in seats and seats['show']: should be 'show' in groups but we don't even show groups in filters
                query = query.replace('<groupbyseats>', ',hc.seats')
                query = query.replace('<orderbyseats>', ',stats.AvgSeats')
            else:
                query = query.replace('<groupbyseats>', '')
                query = query.replace('<orderbyseats>', '')
        else:
            query = query.replace('<seats_test>', 'between 0 and 100')
            query = query.replace('<groupbyseats>', '')
            query = query.replace('<orderbyseats>', '')

        bbtest = self.filters.get_limits_where_clause(limits)

        query = query.replace("<gtbigBlind_test>", bbtest)

        if self.db.backend == self.MYSQL_INNODB:
            bigblindselect = """concat('$', trim(leading ' ' from
                                                 case when gt.bigBlind < 100
                                                      then format(gt.bigBlind/100.0, 2)
                                                      else format(gt.bigBlind/100.0, 0)
                                                 end
                                                ) )"""
        elif self.db.backend == self.SQLITE:
            bigblindselect = """gt.bigBlind || gt.limitType || ' ' || gt.currency"""
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
        query = query.replace("<hgametypeId>", "h.gametypeId")

        # Filter on dates
        query = query.replace("<datestest>", " between '" + dates[0] + "' and '" + dates[1] + "'")

        #print "query =\n", query
        return(query)
    #end def refineQuery(self, query, playerids, sitenos, limits):
