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
#import pokereval

try:
	from matplotlib.figure import Figure
	from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
	from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
	from numpy import arange, cumsum
	from pylab import *
except:
	print "Failed to load libs for graphing, graphing will not function. Please install numpy and matplotlib if you want to use graphs."
	print "This is of no consequence for other parts of the program, e.g. import and HUD are NOT affected by this problem."

import fpdb_import
import fpdb_db

class GuiGraphViewer (threading.Thread):
	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def showClicked(self, widget, data):
		try: self.canvas.destroy()
		except AttributeError: pass

		name=self.nameEntry.get_text()
		
		site=self.siteEntry.get_text()
		
		if site=="PS":
			site=2
			sitename="PokerStars: "
		elif site=="FTP":
			site=1
			sitename="Full Tilt: "
		else:
			print "invalid text in site selection in graph, defaulting to PS"
			site=2
		
		self.fig = Figure(figsize=(5,4), dpi=100)

		#Set graph properties
		self.ax = self.fig.add_subplot(111)

		#Get graph data from DB
		line = self.getRingProfitGraph(name, site)

		self.ax.set_title("Profit graph for ring games")

		#Set axis labels and grid overlay properites
		self.ax.set_xlabel("Hands", fontsize = 12)
		self.ax.set_ylabel("$", fontsize = 12)
		self.ax.grid(color='g', linestyle=':', linewidth=0.2)
		text = "All Hands, " + sitename + str(name) + "\nProfit: $" + str(line[-1]) + "\nTotal Hands: " + str(len(line))

		self.ax.annotate(text, xy=(10, -10),
                xycoords='axes points',
                horizontalalignment='left', verticalalignment='top',
                fontsize=10)


		#Draw plot
		self.ax.plot(line,)

		self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
		self.mainVBox.pack_start(self.canvas)
		self.canvas.show()
	#end of def showClicked

	def getRingProfitGraph(self, name, site):
                self.cursor.execute(self.sql.query['getRingWinningsAllGamesPlayerIdSite'], (name, site))
                winnings = self.db.cursor.fetchall()

                profit=range(len(winnings))
                for i in profit:
                        self.cursor.execute(self.sql.query['getRingProfitFromHandId'], (name, winnings[i][0], site))
                        spent = self.db.cursor.fetchone()
                        profit[i]=(i, winnings[i][1]-spent[0])

                y=map(lambda x:float(x[1]), profit)
                line = cumsum(y)
                return line/100
        #end of def getRingProfitGraph

	def __init__(self, db, settings, querylist, config, debug=True):
		"""Constructor for GraphViewer"""
		self.debug=debug
		#print "start of GraphViewer constructor"
		self.db=db
		self.cursor=db.cursor
		self.settings=settings
		self.sql=querylist
        
		self.mainVBox = gtk.VBox(False, 0)
		self.mainVBox.show()
		
		self.settingsHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
		self.settingsHBox.show()
		
		self.nameLabel = gtk.Label("Name of the player to be graphed:")
		self.settingsHBox.pack_start(self.nameLabel)
		self.nameLabel.show()
		
		self.nameEntry=gtk.Entry()
		self.nameEntry.set_text("name")
		self.settingsHBox.pack_start(self.nameEntry)
		self.nameEntry.show()
		
		self.siteLabel = gtk.Label("Site (PS or FTP):")
		self.settingsHBox.pack_start(self.siteLabel)
		self.siteLabel.show()
		
		self.siteEntry=gtk.Entry()
		self.siteEntry.set_text("PS")
		self.settingsHBox.pack_start(self.siteEntry)
		self.siteEntry.show()

		#Note: Assumes PokerStars is in the config
		self.nameEntry.set_text(config.supported_sites["PokerStars"].screen_name)
		
		self.showButton=gtk.Button("Show/Refresh")
		self.showButton.connect("clicked", self.showClicked, "show clicked")
		self.settingsHBox.pack_start(self.showButton)
 		self.showButton.show()
	#end of GuiGraphViewer.__init__
