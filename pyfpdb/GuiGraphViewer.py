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

try:
	import MySQLdb
except:
	diaSQLLibMissing = gtk.Dialog(title="Fatal Error - SQL interface library missing", parent=None, flags=0, buttons=(gtk.STOCK_QUIT,gtk.RESPONSE_OK))

	label = gtk.Label("Please note that the table viewer only works with MySQL, if you use PostgreSQL this error is expected.")
	diaSQLLibMissing.vbox.add(label)
	label.show()
		
	label = gtk.Label("Since the HUD now runs on all supported plattforms I do not see any point in table viewer anymore, if you disagree please send a message to steffen@sycamoretest.info")
	diaSQLLibMissing.vbox.add(label)
	label.show()

	response = diaSQLLibMissing.run()
	#sys.exit(1)
	
import fpdb_import
import fpdb_db

class GuiGraphViewer (threading.Thread):
	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.main_vbox
	#end def get_vbox
	
	def __init__(self, db, settings, debug=True):
		"""Constructor for table_viewer"""
		self.debug=debug
		#print "start of table_viewer constructor"
		self.db=db
		self.cursor=db.cursor
		self.settings=settings
        
		self.main_vbox = gtk.VBox(False, 0)
		self.main_vbox.show()
		
		self.fig = Figure(figsize=(5,4), dpi=100)
		self.ax = self.fig.add_subplot(111)
#		x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
#		y = [2.7, 2.8, 31.4, 38.1, 58.0, 76.2, 100.5, 130.0, 149.3, 180.0]

		self.db.reconnect()
                self.cursor=self.db.cursor

		self.db.cursor.execute("SELECT handId, winnings FROM HandsPlayers WHERE playerId=1 ORDER BY handId")

		self.results = self.db.cursor.fetchall()

#		x=map(lambda x:float(x[0]),self.results)
	        y=map(lambda x:float(x[1]),self.results)
		line = range(len(y))

		for i in range(len(y)):
			line[i] = y[i] + line[i-1]

		self.ax.plot(line,)

		self.canvas = FigureCanvas(self.fig)  # a gtk.DrawingArea
		self.main_vbox.pack_start(self.canvas)
		self.canvas.show()

	#end of table_viewer.__init__
