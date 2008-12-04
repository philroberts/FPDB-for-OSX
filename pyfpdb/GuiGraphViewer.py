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
from time import time
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

class GuiGraphViewer (threading.Thread):
    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox
    #end def get_vbox

    def generateGraph(self, widget, data):
        try: self.canvas.destroy()
        except AttributeError: pass

        # Whaich sites are selected?
        # TODO:
        # What hero names for the selected site?
        # TODO:

        name = self.heroes[self.sites]

        if self.sites == "PokerStars":
            site=2
            sitename="PokerStars: "
        elif self.sites=="Full Tilt":
            site=1
            sitename="Full Tilt: "
        else:
            print "invalid text in site selection in graph, defaulting to PS"
            site=2

        self.fig = Figure(figsize=(5,4), dpi=100)

        #Set graph properties
        self.ax = self.fig.add_subplot(111)

        #Get graph data from DB
        starttime = time()
        line = self.getRingProfitGraph(name, site)
        print "Graph generated in: %s" %(time() - starttime)

        self.ax.set_title("Profit graph for ring games")

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel("Hands", fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)
        text = "All Hands, " + sitename + str(name) + "\nProfit: $" + str(line[-1]) + "\nTotal Hands: " + str(len(line))

        self.ax.annotate(text, 
                        xy=(10, -10),
                        xycoords='axes points',
                        horizontalalignment='left', verticalalignment='top',
                        fontsize=10)


        #Draw plot
        self.ax.plot(line,)

        self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
        self.graphBox.add(self.canvas)
        self.canvas.show()
    #end of def showClicked

    def getRingProfitGraph(self, name, site):
        self.cursor.execute(self.sql.query['getRingProfitAllHandsPlayerIdSite'], (name, site))
        #returns (HandId,Winnings,Costs,Profit)
        winnings = self.db.cursor.fetchall()

        y=map(lambda x:float(x[3]), winnings)
        line = cumsum(y)
        return line/100
        #end of def getRingProfitGraph

    def createPlayerLine(self, hbox, site, player):
        label = gtk.Label(site +" id:")
        hbox.pack_start(label, False, False, 0)
        label.show()

        pname = gtk.Entry()
        pname.set_text(player)
        pname.set_width_chars(20)
        hbox.pack_start(pname, False, True, 0)
        #TODO: Need to connect a callback here
        pname.connect("changed", self.__set_hero_name, site)
        #TODO: Look at GtkCompletion - to fill out usernames
        pname.show()

        self.__set_hero_name(pname, site)

    def __set_hero_name(self, w, site):
        self.heroes[site] = w.get_text()
        print "DEBUG: settings heroes[%s]: %s"%(site, self.heroes[site])

    def createSiteLine(self, hbox, site):
        cb = gtk.CheckButton(site)
        cb.connect('clicked', self.__set_site_select, site)
        hbox.pack_start(cb, False, False, 0)
        cb.show()

    def __set_site_select(self, w, site):
        # This doesn't behave as intended - self.site only allows 1 site for the moment.
        self.sites = site
        print "self.sites set to %s" %(self.sites)

    def fillPlayerFrame(self, vbox):
        for site in self.conf.supported_sites.keys():
            pathHBox = gtk.HBox(False, 0)
            vbox.pack_start(pathHBox, False, True, 0)
            pathHBox.show()

            player = self.conf.supported_sites[site].screen_name
            self.createPlayerLine(pathHBox, site, player)

    def fillSitesFrame(self, vbox):
        for site in self.conf.supported_sites.keys():
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, True, 0)
            hbox.show()
            self.createSiteLine(hbox, site)

    def fillDateFrame(self, vbox):
        # Hat tip to Mika Bostrom - calendar code comes from PokerStats
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)
        hbox.show()

        lbl_start = gtk.Label('From:')
        lbl_start.show()

        btn_start = gtk.Button()
        btn_start.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_start.connect('clicked', self.__calendar_dialog, self.start_date)
        btn_start.show()

        hbox.pack_start(lbl_start, expand=False, padding=3)
        hbox.pack_start(btn_start, expand=False, padding=3)
        hbox.pack_start(self.start_date, expand=False, padding=2)
        self.start_date.show()

        #New row for end date
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)
        hbox.show()

        lbl_end = gtk.Label('  To:')
        lbl_end.show()
        btn_end = gtk.Button()
        btn_end.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_end.connect('clicked', self.__calendar_dialog, self.end_date)
        btn_end.show()

        btn_clear = gtk.Button(label=' Clear Dates ')
        btn_clear.connect('clicked', self.__clear_dates)
        btn_clear.show()

        hbox.pack_start(lbl_end, expand=False, padding=3)
        hbox.pack_start(btn_end, expand=False, padding=3)
        hbox.pack_start(self.end_date, expand=False, padding=2)
        self.end_date.show()

        hbox.pack_start(btn_clear, expand=False, padding=15)

    def __calendar_dialog(self, widget, entry):
        d = gtk.Window(gtk.WINDOW_TOPLEVEL)
        d.set_title('Pick a date')

        vb = gtk.VBox()
        cal = gtk.Calendar()
        vb.pack_start(cal, expand=False, padding=0)

        btn = gtk.Button('Done')
        btn.connect('clicked', self.__get_date, cal, entry, d)

        vb.pack_start(btn, expand=False, padding=4)

        d.add(vb)
        d.set_position(gtk.WIN_POS_MOUSE)
        d.show_all()

    def __clear_dates(self, w):
        self.start_date.set_text('')
        self.end_date.set_text('')

    def __get_dates(self):
        t1 = self.start_date.get_text()
        t2 = self.end_date.get_text()
        return (t1, t2)

    def __get_date(self, widget, calendar, entry, win):
# year and day are correct, month is 0..11
        (year, month, day) = calendar.get_date()
        month += 1
        ds = '%04d-%02d-%02d' % (year, month, day)
        entry.set_text(ds)
        win.destroy()

    def __init__(self, db, settings, querylist, config, debug=True):
        """Constructor for GraphViewer"""
        self.debug=debug
        #print "start of GraphViewer constructor"
        self.db=db
        self.cursor=db.cursor
        self.settings=settings
        self.sql=querylist
        self.conf = config

        self.sites = "PokerStars"
        self.heroes = {}

        # For use in date ranges.
        self.start_date = gtk.Entry(max=12)
        self.end_date = gtk.Entry(max=12)
        self.start_date.set_property('editable', False)
        self.end_date.set_property('editable', False)
        
        self.mainHBox = gtk.HBox(False, 0)
        self.mainHBox.show()

        self.leftPanelBox = gtk.VBox(False, 0)
        self.graphBox = gtk.VBox(False, 0)

        self.hpane = gtk.HPaned()
        self.hpane.pack1(self.leftPanelBox)
        self.hpane.pack2(self.graphBox)
        self.hpane.show()

        self.mainHBox.add(self.hpane)

        playerFrame = gtk.Frame("Hero:")
        playerFrame.set_label_align(0.0, 0.0)
        playerFrame.show()
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.fillPlayerFrame(vbox)
        playerFrame.add(vbox)

        sitesFrame = gtk.Frame("Sites:")
        sitesFrame.set_label_align(0.0, 0.0)
        sitesFrame.show()
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.fillSitesFrame(vbox)
        sitesFrame.add(vbox)

        dateFrame = gtk.Frame("Date:")
        dateFrame.set_label_align(0.0, 0.0)
        dateFrame.show()
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.fillDateFrame(vbox)
        dateFrame.add(vbox)

        graphButton=gtk.Button("Generate Graph")
        graphButton.connect("clicked", self.generateGraph, "cliced data")
        graphButton.show()

        self.exportButton=gtk.Button("Export to File")
#@      self.exportButton.connect("clicked", self.exportGraph, "show clicked")
        self.exportButton.show()

        self.leftPanelBox.add(playerFrame)
        self.leftPanelBox.add(sitesFrame)
        self.leftPanelBox.add(dateFrame)
        self.leftPanelBox.add(graphButton)
        self.leftPanelBox.add(self.exportButton)

        self.leftPanelBox.show()
        self.graphBox.show()

