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

class GuiGraphViewer (threading.Thread):
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

        # Which sites are selected?
        for site in self.sites:
            if self.sites[site] == True:
                sitenos.append(self.siteid[site])
                self.cursor.execute(self.sql.query['getPlayerId'], (self.heroes[site],))
                result = self.db.cursor.fetchall()
                if len(result) == 1:
                    playerids.append(result[0][0])

        if sitenos == []:
            #Should probably pop up here.
            print "No sites selected - defaulting to PokerStars"
            sitenos = [2]


        if playerids == []:
            print "No player ids found"
            return


        #Set graph properties
        self.ax = self.fig.add_subplot(111)

        #Get graph data from DB
        starttime = time()
        line = self.getRingProfitGraph(playerids, sitenos)
        print "Graph generated in: %s" %(time() - starttime)

        self.ax.set_title("Profit graph for ring games")

        #Set axis labels and grid overlay properites
        self.ax.set_xlabel("Hands", fontsize = 12)
        self.ax.set_ylabel("$", fontsize = 12)
        self.ax.grid(color='g', linestyle=':', linewidth=0.2)
        if(line == None):
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
    #end of def showClicked

    def getRingProfitGraph(self, names, sites):
        tmp = self.sql.query['getRingProfitAllHandsPlayerIdSite']
#        print "DEBUG: getRingProfitGraph"
        start_date, end_date = self.__get_dates()

        if start_date == '':
            start_date = '1970-01-01'
        if end_date == '':
            end_date = '2020-12-12'

        #Buggered if I can find a way to do this 'nicely' take a list of intergers and longs
        # and turn it into a tuple readale by sql.
        # [5L] into (5) not (5,) and [5L, 2829L] into (5, 2829)
        nametest = str(tuple(names))
        sitetest = str(tuple(sites))
        nametest = nametest.replace("L", "")
        nametest = nametest.replace(",)",")")
        sitetest = sitetest.replace(",)",")")

        #Must be a nicer way to deal with tuples of size 1 ie. (2,) - which makes sql barf
        tmp = tmp.replace("<player_test>", nametest)
        tmp = tmp.replace("<site_test>", sitetest)
        tmp = tmp.replace("<startdate_test>", start_date)
        tmp = tmp.replace("<enddate_test>", end_date)

#        print "DEBUG: sql query:"
#        print tmp
        self.cursor.execute(tmp)
        #returns (HandId,Winnings,Costs,Profit)
        winnings = self.db.cursor.fetchall()

        if(winnings == ()):
            return None

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
        pname.connect("changed", self.__set_hero_name, site)
        #TODO: Look at GtkCompletion - to fill out usernames
        pname.show()

        self.__set_hero_name(pname, site)

    def __set_hero_name(self, w, site):
        self.heroes[site] = w.get_text()
#        print "DEBUG: settings heroes[%s]: %s"%(site, self.heroes[site])

    def createSiteLine(self, hbox, site):
        cb = gtk.CheckButton(site)
        cb.connect('clicked', self.__set_site_select, site)
        hbox.pack_start(cb, False, False, 0)
        cb.show()

    def __set_site_select(self, w, site):
        # This doesn't behave as intended - self.site only allows 1 site for the moment.
        print w.get_active()
        self.sites[site] = w.get_active()
        print "self.sites[%s] set to %s" %(site, self.sites[site])

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
            #Get db site id for filtering later
            self.cursor.execute(self.sql.query['getSiteId'], (site,))
            result = self.db.cursor.fetchall()
            if len(result) == 1:
                self.siteid[site] = result[0][0]
            else:
                print "Either 0 or more than one site matched - EEK"

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

    def __init__(self, db, settings, querylist, config, debug=True):
        """Constructor for GraphViewer"""
        self.debug=debug
        #print "start of GraphViewer constructor"
        self.db=db
        self.cursor=db.cursor
        self.settings=settings
        self.sql=querylist
        self.conf = config

        self.sites = {}
        self.siteid = {}
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

        self.fig = None
        self.exportButton=gtk.Button("Export to File")
        self.exportButton.connect("clicked", self.exportGraph, "show clicked")
        self.exportButton.show()

        self.leftPanelBox.add(playerFrame)
        self.leftPanelBox.add(sitesFrame)
        self.leftPanelBox.add(dateFrame)
        self.leftPanelBox.add(graphButton)
        self.leftPanelBox.add(self.exportButton)

        self.leftPanelBox.show()
        self.graphBox.show()

        self.fig = Figure(figsize=(5,4), dpi=100)
        self.canvas = None

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

