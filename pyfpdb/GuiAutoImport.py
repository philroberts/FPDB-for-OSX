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
import fpdb_import

class GuiAutoImport (threading.Thread):
	def browseClicked(self, widget, data):
		"""runs when user clicks browse on auto import tab"""
		#print "start of GuiAutoImport.browseClicked"
		current_path=self.pathTBuffer.get_text(self.pathTBuffer.get_start_iter(), self.pathTBuffer.get_end_iter())
		
		dia_chooser = gtk.FileChooserDialog(title="Please choose the path that you want to auto import",
				action=gtk.FILE_CHOOSER_ACTION_OPEN,
				buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		#dia_chooser.set_current_folder(pathname)
		dia_chooser.set_filename(current_path)
		#dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import
		
		response = dia_chooser.run()
		if response == gtk.RESPONSE_OK:
			#print dia_chooser.get_filename(), 'selected'
			self.pathTBuffer.set_text(dia_chooser.get_filename())
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
		dia_chooser.destroy()		
	#end def GuiAutoImport.browseClicked

	def startClicked(self, widget, data):
		"""runs when user clicks start on auto import tab"""
		print "implement GuiAutoImport.startClicked"
	#end def GuiAutoImport.browseClicked

	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def __init__(self, settings, debug=True):
		"""Constructor for GuiAutoImport"""
		self.settings=settings
		
		self.mainVBox=gtk.VBox(False,1)
		self.mainVBox.show()
		
		self.settingsHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
		self.settingsHBox.show()
		
		self.intervalLabel = gtk.Label("Interval (ie. break) between imports in seconds:")
		self.settingsHBox.pack_start(self.intervalLabel)
		self.intervalLabel.show()
		
		self.intervalTBuffer=gtk.TextBuffer()
		self.intervalTBuffer.set_text(str(self.settings['hud-defaultInterval']))
		self.intervalTView=gtk.TextView(self.intervalTBuffer)
		self.settingsHBox.pack_start(self.intervalTView)
		self.intervalTView.show()
		
		
		self.pathHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.pathHBox, False, True, 0)
		self.pathHBox.show()
		
		self.pathLabel = gtk.Label("Path to auto-import:")
		self.pathHBox.pack_start(self.pathLabel, False, False, 0)
		self.pathLabel.show()
		
		self.pathTBuffer=gtk.TextBuffer()
		self.pathTBuffer.set_text(self.settings['hud-defaultPath'])
		self.pathTView=gtk.TextView(self.pathTBuffer)
		self.pathHBox.pack_start(self.pathTView, False, True, 0)
		self.pathTView.show()
		
		self.browseButton=gtk.Button("Browse...")
		self.browseButton.connect("clicked", self.browseClicked, "Browse clicked")
		self.pathHBox.pack_end(self.browseButton, False, False, 0)
 		self.browseButton.show()
		
		
		self.startButton=gtk.Button("Start Autoimport")
		self.startButton.connect("clicked", self.startClicked, "start clicked")
		self.mainVBox.add(self.startButton)
 		self.startButton.show()
	#end of GuiAutoImport.__init__
