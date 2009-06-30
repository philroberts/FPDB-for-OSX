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
from time import *
#import pokereval

try:
    import matplotlib
    matplotlib.use('GTK')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
    from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
    from numpy import arange, cumsum
    from pylab import *
except:
    print """Failed to load libs for graphing, graphing will not function. Please in
                 stall numpy and matplotlib if you want to use graphs."""
    print """This is of no consequence for other parts of the program, e.g. import 
         and HUD are NOT affected by this problem."""

import fpdb_import
import fpdb_db
import Filters

class GuiGraphViewer (threading.Thread):

    def __init__(self, db, settings, querylist, config, debug=True):
        """Constructor for GraphViewer"""
        self.debug=debug
        #print "start of GraphViewer constructor"
        self.db=db
        self.cursor=db.cursor
        self.settings=settings
        self.sql=querylist
        self.conf = config

        filters_display = { "Heroes"  :  True,
                            "Sites"   :  True,
                            "Games"   :  True,
                            "Limits"  :  True,
                            "Seats"   :  False,
                            "Dates"   :  True,
                            "Button1" :  True,
                            "Button2" :  True
                          }

        self.filters = Filters.Filters(db, settings, config, querylist, display = filters_display)
        self.filters.registerButton1Name("Refresh Graph")
        self.filters.registerButton1Callback(self.generateGraph)
        self.filters.registerButton2Name("Export to File")
        self.filters.registerButton2Callback(self.exportGraph)

        self.mainHBox = gtk.HBox(False, 0)
        self.mainHBox.show()

        self.leftPanelBox = self.filters.get_vbox()
        self.graphBox = gtk.VBox(False, 0)
        self.graphBox.show()

        self.hpane = gtk.HPaned()
        self.hpane.pack1(self.leftPanelBox)
        self.hpane.pack2(self.graphBox)
        self.hpane.show()

        self.mainHBox.add(self.hpane)

        self.fig = None
        #self.exportButton.set_sensitive(False)

        self.fig = Figure(figsize=(5,4), dpi=100)
        self.canvas = None


        self.db.db.rollback()

#################################
#
#        self.db.cursor.execute("""select UNIX_TIMESTAMP(handStart) as time, id from Hands ORDER BY time""")
#        THRESHOLD = 1800
#        hands = self.db.cursor.fetchall()
#
#        times = map(lambda x:long(x[0]), hands)
#        handids = map(lambda x:int(x[1]), hands)
#        print "DEBUG: len(times) %s" %(len(times))
#        diffs = diff(times)
#        print "DEBUG: len(diffs) %s" %(len(diffs))
#        index = nonzero(diff(times) > THRESHOLD)
#        print "DEBUG: len(index[0]) %s" %(len(index[0]))
#        print "DEBUG: index %s" %(index)
#        print "DEBUG: index[0][0] %s" %(index[0][0])
#
#        total = 0
#
#        last_idx = 0
#        for i in range(len(index[0])):
#            print "Hands in session %4s: %4s  Start: %s End: %s Total: %s" %(i, index[0][i] - last_idx, strftime("%d/%m/%Y %H:%M", localtime(times[last_idx])), strftime("%d/%m/%Y %H:%M", localtime(times[index[0][i]])), times[index[0][i]] - times[last_idx])
#            total = total + (index[0][i] - last_idx)
#            last_idx = index[0][i] + 1
#
#        print "Total: ", total
#################################


    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox
    #end def get_vbox

    def clearGraphData(self):
        self.fig.clf()
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
        limits  = self.filters.getLimits()
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
            return

        if not playerids:
            print "No player ids found"
            return

        if not limits:
            print "No limits found"
            return

        #Set graph properties
        self.ax = self.fig.add_subplot(111)

        #Get graph data from DB
        starttime = time()
        line = self.getRingProfitGraph(playerids, sitenos, limits)
        print "Graph generated in: %s" %(time() - starttime)

        self.ax.set_title("Profit graph for ring games")

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel("Hands", fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)
        if line == None or line == []:

            #TODO: Do something useful like alert user
            print "No hands returned by graph query"
        else:
#            text = "All Hands, " + sitename + str(name) + "\nProfit: $" + str(line[-1]) + "\nTotal Hands: " + str(len(line))
            text = "All Hands, " + "\nProfit: $" + str(line[-1]) + "\nTotal Hands: " + str(len(line))

            self.ax.annotate(text,
                             xy=(10, -10),
                             xycoords='axes points',
                             horizontalalignment='left', verticalalignment='top',
                             fontsize=10)

            #Draw plot
            self.ax.plot(line,)

            self.graphBox.add(self.canvas)
            self.canvas.show()
            #self.exportButton.set_sensitive(True)
    #end of def showClicked

    def getRingProfitGraph(self, names, sites, limits):
        tmp = self.sql.query['getRingProfitAllHandsPlayerIdSite']
#        print "DEBUG: getRingProfitGraph"
        start_date, end_date = self.filters.getDates()

        #Buggered if I can find a way to do this 'nicely' take a list of intergers and longs
        # and turn it into a tuple readale by sql.
        # [5L] into (5) not (5,) and [5L, 2829L] into (5, 2829)
        nametest = str(tuple(names))
        sitetest = str(tuple(sites))
        limittest = str(tuple(limits))
        nametest = nametest.replace("L", "")
        nametest = nametest.replace(",)",")")
        sitetest = sitetest.replace(",)",")")
        limittest = limittest.replace("L", "")
        limittest = limittest.replace(",)",")")

        #Must be a nicer way to deal with tuples of size 1 ie. (2,) - which makes sql barf
        tmp = tmp.replace("<player_test>", nametest)
        tmp = tmp.replace("<site_test>", sitetest)
        tmp = tmp.replace("<startdate_test>", start_date)
        tmp = tmp.replace("<enddate_test>", end_date)
        tmp = tmp.replace("<limit_test>", limittest)

        #print "DEBUG: sql query:"
        #print tmp
        self.cursor.execute(tmp)
        #returns (HandId,Winnings,Costs,Profit)
        winnings = self.db.cursor.fetchall()
        self.db.db.rollback()

        if(winnings == ()):
            return None

        y=map(lambda x:float(x[3]), winnings)
        line = cumsum(y)
        return line/100
        #end of def getRingProfitGraph

    def exportGraph (self, widget, data):
        if self.fig is None:
            return # Might want to disable export button until something has been generated.
        dia_chooser = gtk.FileChooserDialog(title="Please choose the directory you wish to export to:",
                                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        #TODO: Suggest path and filename to start with

        response = dia_chooser.run()
        if response == gtk.RESPONSE_OK:
            self.exportDir = dia_chooser.get_filename()
            print "DEBUG: self.exportDir = %s" %(self.exportDir)
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no graph exported'
        dia_chooser.destroy()
        #TODO: Check to see if file exists
        #NOTE: Dangerous - will happily overwrite any file we have write access too
        #TODO: This asks for a directory but will take a filename and overwrite it.
        self.fig.savefig(self.exportDir, format="png")


