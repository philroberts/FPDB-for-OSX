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

try:
	from matplotlib.figure import Figure
	from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
	from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
	from numpy import arange, sin, pi
except:
	print "Failed to load libs for graphing, graphing will not function. Please install numpy and matplotlib."

import fpdb_import
import fpdb_db

class GuiGraphViewer (threading.Thread):
	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def showClicked(self, widget, data):
		name=self.nameTBuffer.get_text(self.nameTBuffer.get_start_iter(), self.nameTBuffer.get_end_iter())
		
		site=self.siteTBuffer.get_text(self.siteTBuffer.get_start_iter(), self.siteTBuffer.get_end_iter())
		
		if site=="PS":
			site=1
		elif site=="FTP":
			site=2
		else:
			print "invalid text in site selection in graph, defaulting to PS"
			site=1
		
		self.fig = Figure(figsize=(5,4), dpi=100)
		self.ax = self.fig.add_subplot(111)

		self.cursor.execute("""SELECT handId, winnings FROM HandsPlayers
				INNER JOIN Players ON HandsPlayers.playerId = Players.id 
				INNER JOIN Hands ON Hands.id = HandsPlayers.handId
				WHERE Players.name = %s AND Players.siteId = %s
				ORDER BY siteHandNo""", (name, site))
		winnings = self.db.cursor.fetchall()
				
		profit=range(len(winnings))
		for i in profit:
			self.cursor.execute("""SELECT SUM(amount) FROM HandsActions
					INNER JOIN HandsPlayers ON HandsActions.handPlayerId = HandsPlayers.id
					INNER JOIN Players ON HandsPlayers.playerId = Players.id 
					WHERE Players.name = %s AND HandsPlayers.handId = %s AND Players.siteId = %s""", (name, winnings[i][0], site))
			spent = self.db.cursor.fetchone()
			profit[i]=(i, winnings[i][1]-spent[0])

		y=map(lambda x:float(x[1]), profit)
		line = range(len(y))

		for i in range(len(y)):
			line[i] = y[i] + line[i-1]

		self.ax.plot(line,)

		self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
		self.mainVBox.pack_start(self.canvas)
		self.canvas.show()
	#end of def showClicked

	def __init__(self, db, settings, debug=True):
		"""Constructor for GraphViewer"""
		self.debug=debug
		#print "start of GraphViewer constructor"
		self.db=db
		self.cursor=db.cursor
		self.settings=settings
        
		self.mainVBox = gtk.VBox(False, 0)
		self.mainVBox.show()
		
		self.settingsHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
		self.settingsHBox.show()
		
		self.nameLabel = gtk.Label("Name of the player to be graphed:")
		self.settingsHBox.pack_start(self.nameLabel)
		self.nameLabel.show()
		
		self.nameTBuffer=gtk.TextBuffer()
		self.nameTBuffer.set_text("name")
		self.nameTView=gtk.TextView(self.nameTBuffer)
		self.settingsHBox.pack_start(self.nameTView)
		self.nameTView.show()
		
		self.siteLabel = gtk.Label("Site (PS or FTP):")
		self.settingsHBox.pack_start(self.siteLabel)
		self.siteLabel.show()
		
		self.siteTBuffer=gtk.TextBuffer()
		self.siteTBuffer.set_text("PS")
		self.siteTView=gtk.TextView(self.siteTBuffer)
		self.settingsHBox.pack_start(self.siteTView)
		self.siteTView.show()
		
		self.showButton=gtk.Button("Show/Refresh")
		self.showButton.connect("clicked", self.showClicked, "show clicked")
		self.settingsHBox.pack_start(self.showButton)
 		self.showButton.show()
	#end of GuiGraphViewer.__init__
