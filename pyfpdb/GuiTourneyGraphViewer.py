#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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

import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
import traceback
from time import *
from datetime import datetime
#import pokereval

import Database
import Filters
import Charset

try:
    calluse = not 'matplotlib' in sys.modules
    import matplotlib
    if calluse:
        matplotlib.use('GTKCairo')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
    from matplotlib.font_manager import FontProperties
    from numpy import arange, cumsum
    from pylab import *
except ImportError, inst:
    print _("""Failed to load libs for graphing, graphing will not function. Please install numpy and matplotlib if you want to use graphs.""")
    print _("""This is of no consequence for other parts of the program, e.g. import and HUD are NOT affected by this problem.""")
    print "ImportError: %s" % inst.args

class GuiTourneyGraphViewer:

    def __init__(self, querylist, config, parent, debug=True):
        """Constructor for GraphViewer"""
        self.sql = querylist
        self.conf = config
        self.debug = debug
        self.parent = parent
        #print "start of GraphViewer constructor"
        self.db = Database.Database(self.conf, sql=self.sql)


        filters_display = { "Heroes"    : True,
                            "Sites"     : True,
                            "Games"     : False,
                            "Limits"    : False,
                            "LimitSep"  : False,
                            "LimitType" : False,
                            "Type"      : False,
                            "UseType"   : 'tour',
                            "Seats"     : False,
                            "SeatSep"   : False,
                            "Dates"     : True,
                            "Groups"    : False,
                            "Button1"   : True,
                            "Button2"   : True
                          }

        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        self.filters.registerButton1Name(_("Refresh _Graph"))
        self.filters.registerButton1Callback(self.generateGraph)
        self.filters.registerButton2Name(_("_Export to File"))
        self.filters.registerButton2Callback(self.exportGraph)

        self.mainHBox = gtk.HBox(False, 0)
        self.mainHBox.show()

        self.leftPanelBox = self.filters.get_vbox()

        self.hpane = gtk.HPaned()
        self.hpane.pack1(self.leftPanelBox)
        self.mainHBox.add(self.hpane)
        # hierarchy:  self.mainHBox / self.hpane / self.graphBox / self.canvas / self.fig / self.ax

        self.graphBox = gtk.VBox(False, 0)
        self.graphBox.show()
        self.hpane.pack2(self.graphBox)
        self.hpane.show()

        self.fig = None
        #self.exportButton.set_sensitive(False)
        self.canvas = None


        self.db.rollback()

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox
    #end def get_vbox

    def clearGraphData(self):
        try:
            if self.canvas:
                self.graphBox.remove(self.canvas)
        except:
            pass

        if self.fig != None:
            self.fig.clear()
        self.fig = Figure(figsize=(5,4), dpi=100)
        if self.canvas is not None:
            self.canvas.destroy()

        self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea

    def generateGraph(self, widget, data):
        self.clearGraphData()

        sitenos = []
        playerids = []

        sites   = self.filters.getSites()
        heroes  = self.filters.getHeroes()
        siteids = self.filters.getSiteIds()

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
            self.db.rollback()
            return

        if not playerids:
            print _("No player ids found")
            self.db.rollback()
            return

        #Set graph properties
        self.ax = self.fig.add_subplot(111)

        #Get graph data from DB
        starttime = time()
        green = self.getData(playerids, sitenos)
        print _("Graph generated in: %s") %(time() - starttime)


        #Set axis labels and grid overlay properites
        self.ax.set_xlabel(_("Tournaments"), fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)
        if green == None or green == []:
            self.ax.set_title(_("No Data for Player(s) Found"))
            green = ([    0.,     0.,     0.,     0.,   500.,  1000.,   900.,   800.,
                        700.,   600.,   500.,   400.,   300.,   200.,   100.,     0.,
                        500.,  1000.,  1000.,  1000.,  1000.,  1000.,  1000.,  1000.,
                        1000., 1000.,  1000.,  1000.,  1000.,  1000.,   875.,   750.,
                        625.,   500.,   375.,   250.,   125.,     0.,     0.,     0.,
                        0.,   500.,  1000.,   900.,   800.,   700.,   600.,   500.,
                        400.,   300.,   200.,   100.,     0.,   500.,  1000.,  1000.])
            red   =  ([    0.,     0.,     0.,     0.,   500.,  1000.,   900.,   800.,
                        700.,   600.,   500.,   400.,   300.,   200.,   100.,     0.,
                        0.,   0.,     0.,     0.,     0.,     0.,   125.,   250.,
                        375.,   500.,   500.,   500.,   500.,   500.,   500.,   500.,
                        500.,   500.,   375.,   250.,   125.,     0.,     0.,     0.,
                        0.,   500.,  1000.,   900.,   800.,   700.,   600.,   500.,
                        400.,   300.,   200.,   100.,     0.,   500.,  1000.,  1000.])
            blue =    ([    0.,     0.,     0.,     0.,   500.,  1000.,   900.,   800.,
                          700.,   600.,   500.,   400.,   300.,   200.,   100.,     0.,
                          0.,     0.,     0.,     0.,     0.,     0.,   125.,   250.,
                          375.,   500.,   625.,   750.,   875.,  1000.,   875.,   750.,
                          625.,   500.,   375.,   250.,   125.,     0.,     0.,     0.,
                        0.,   500.,  1000.,   900.,   800.,   700.,   600.,   500.,
                        400.,   300.,   200.,   100.,     0.,   500.,  1000.,  1000.])

            self.ax.plot(green, color='green', label=_('Tournaments') + ': %d\n' % len(green) + _('Profit') + ': $%.2f' % green[-1])
            self.graphBox.add(self.canvas)
            self.canvas.show()
            self.canvas.draw()

            #TODO: Do something useful like alert user
        else:
            self.ax.set_title(_("Tournament Results")+" (USD)")

            #Draw plot
            self.ax.plot(green, color='green', label=_('Tournaments') + ': %d\n' % len(green) + _('Profit') + ': $%.2f' % green[-1])

            legend = self.ax.legend(loc='upper left', fancybox=True, shadow=True, prop=FontProperties(size='smaller'))
            legend.draggable(True)
            
            self.graphBox.add(self.canvas)
            self.canvas.show()
            self.canvas.draw()
            #self.exportButton.set_sensitive(True)

    #end of def showClicked

    def getData(self, names, sites):
        tmp = self.sql.query['tourneyGraph']
        #print "DEBUG: getData"
        start_date, end_date = self.filters.getDates()

        #Buggered if I can find a way to do this 'nicely' take a list of integers and longs
        # and turn it into a tuple readale by sql.
        # [5L] into (5) not (5,) and [5L, 2829L] into (5, 2829)
        nametest = str(tuple(names))
        sitetest = str(tuple(sites))

        #Must be a nicer way to deal with tuples of size 1 ie. (2,) - which makes sql barf
        tmp = tmp.replace("<player_test>", nametest)
        tmp = tmp.replace("<site_test>", sitetest)
        tmp = tmp.replace("<startdate_test>", start_date)
        tmp = tmp.replace("<enddate_test>", end_date)
        tmp = tmp.replace(",)", ")")

        #print "DEBUG: sql query:", tmp

        self.db.cursor.execute(tmp)
        #returns (HandId,Winnings,Costs,Profit)
        winnings = self.db.cursor.fetchall()
        self.db.rollback()

        if len(winnings) == 0:
            return None

        green = map(lambda x:float(x[1]), winnings)
        #blue  = map(lambda x: float(x[1]) if x[2] == True  else 0.0, winnings)
        #red   = map(lambda x: float(x[1]) if x[2] == False else 0.0, winnings)
        greenline = cumsum(green)
        #blueline  = cumsum(blue)
        #redline   = cumsum(red)
        return (greenline/100)

    def exportGraph (self, widget, data):
        if self.fig is None:
            return # Might want to disable export button until something has been generated.

        dia_chooser = gtk.FileChooserDialog(title=_("Please choose the directory you wish to export to:"),
                                            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        dia_chooser.set_destroy_with_parent(True)
        dia_chooser.set_transient_for(self.parent)
        try: 
            dia_chooser.set_filename(self.exportFile) # use previously chosen export path as default
        except:
            pass

        response = dia_chooser.run()
        
        if response <> gtk.RESPONSE_OK:
            print _('Closed, no graph exported')
            dia_chooser.destroy()
            return
            
        # generate a unique filename for export
        now = datetime.now()
        now_formatted = now.strftime("%Y%m%d%H%M%S")
        self.exportFile = dia_chooser.get_filename() + "/fpdb" + now_formatted + ".png"
        dia_chooser.destroy()
        
        #print "DEBUG: self.exportFile = %s" %(self.exportFile)
        self.fig.savefig(self.exportFile, format="png")

        #display info box to confirm graph created
        diainfo = gtk.MessageDialog(parent=self.parent,
                                flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                type=gtk.MESSAGE_INFO,
                                buttons=gtk.BUTTONS_OK,
                                message_format=_("Graph created"))
        diainfo.format_secondary_text(self.exportFile)          
        diainfo.run()
        diainfo.destroy()
        
    #end of def exportGraph
