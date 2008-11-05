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
import subprocess

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import time
import fpdb_import

class GuiAutoImport (threading.Thread):
	def starsBrowseClicked(self, widget, data):
		"""runs when user clicks browse on auto import tab"""
		#print "start of GuiAutoImport.starsBrowseClicked"
		current_path=self.starsDirPath.get_text()
		
		dia_chooser = gtk.FileChooserDialog(title="Please choose the path that you want to auto import",
				action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
				buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		#dia_chooser.set_current_folder(pathname)
		dia_chooser.set_filename(current_path)
		#dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import

		response = dia_chooser.run()
		if response == gtk.RESPONSE_OK:
			#print dia_chooser.get_filename(), 'selected'
			self.starsDirPath.set_text(dia_chooser.get_filename())
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
		dia_chooser.destroy()		
	#end def GuiAutoImport.starsBrowseClicked

	def tiltBrowseClicked(self, widget, data):
		"""runs when user clicks browse on auto import tab"""
		#print "start of GuiAutoImport.tiltBrowseClicked"
		current_path=self.tiltDirPath.get_text()

		dia_chooser = gtk.FileChooserDialog(title="Please choose the path that you want to auto import",
				action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
				buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		#dia_chooser.set_current_folder(pathname)
		dia_chooser.set_filename(current_path)
		#dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import

		response = dia_chooser.run()
		if response == gtk.RESPONSE_OK:
			#print dia_chooser.get_filename(), 'selected'
			self.tiltDirPath.set_text(dia_chooser.get_filename())
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
		dia_chooser.destroy()
	#end def GuiAutoImport.tiltBrowseClicked

	def do_import(self):
		"""Callback for timer to do an import iteration."""
		self.importer.runUpdated()
		print "GuiAutoImport.import_dir done"
		return True

	def startClicked(self, widget, data):
		"""runs when user clicks start on auto import tab"""

#	Check to see if we have an open file handle to the HUD and open one if we do not.
#	bufsize = 1 means unbuffered
#	We need to close this file handle sometime.

#	TODO:  Allow for importing from multiple dirs - REB 29AUG2008
#	As presently written this function does nothing if there is already a pipe open.
#	That is not correct.  It should open another dir for importing while piping the
#	results to the same pipe.  This means that self.path should be a a list of dirs
#	to watch.
		try:      #uhhh, I don't this this is the best way to check for the existence of an attr
			getattr(self, "pipe_to_hud")
		except AttributeError:
			if os.name == 'nt':
				command = "python HUD_main.py" + " %s" % (self.database)
				bs = 0    # windows is not happy with line buffing here
				self.pipe_to_hud = subprocess.Popen(command, bufsize = bs, stdin = subprocess.PIPE, 
											    universal_newlines=True)
			else:
				cwd = os.getcwd()
				command = os.path.join(cwd, 'HUD_main.py')
				bs = 1
				self.pipe_to_hud = subprocess.Popen((command, self.database), bufsize = bs, stdin = subprocess.PIPE, 
											    universal_newlines=True)
#			self.pipe_to_hud = subprocess.Popen((command, self.database), bufsize = bs, stdin = subprocess.PIPE, 
#											    universal_newlines=True)
#			command = command + " %s" % (self.database)
#			print "command = ", command
#			self.pipe_to_hud = os.popen(command, 'w')
			self.starspath=self.starsDirPath.get_text()
			self.tiltpath=self.tiltDirPath.get_text()

#			Add directory to importer object.
			self.importer.addImportDirectory(self.starspath, True, "PokerStars", "passthrough")
			self.importer.addImportDirectory(self.tiltpath, True, "FullTilt", "passthrough")
			self.do_import()
		
			interval=int(self.intervalEntry.get_text())
			gobject.timeout_add(interval*1000, self.do_import)
	#end def GuiAutoImport.startClicked

	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def __init__(self, settings, config, debug=True):
		"""Constructor for GuiAutoImport"""
		self.settings=settings
		self.config=config
		self.importer = fpdb_import.Importer(self,self.settings)
		self.importer.setCallHud(True)
		self.importer.setMinPrint(30)
		self.importer.setQuiet(False)
		self.importer.setFailOnError(False)
		self.importer.setHandCount(0)
#		self.importer.setWatchTime()
		
		self.server=settings['db-host']
		self.user=settings['db-user']
		self.password=settings['db-password']
		self.database=settings['db-databaseName']
		
		self.mainVBox=gtk.VBox(False,1)
		self.mainVBox.show()
		
		self.settingsHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.settingsHBox, False, True, 0)
		self.settingsHBox.show()
		
		self.intervalLabel = gtk.Label("Interval (ie. break) between imports in seconds:")
		self.settingsHBox.pack_start(self.intervalLabel)
		self.intervalLabel.show()
		
		self.intervalEntry=gtk.Entry()
		self.intervalEntry.set_text(str(self.settings['hud-defaultInterval']))
		self.settingsHBox.pack_start(self.intervalEntry)
		self.intervalEntry.show()
		
		self.pathHBox = gtk.HBox(False, 0)
		self.mainVBox.pack_start(self.pathHBox, False, True, 0)
		self.pathHBox.show()
		
		self.pathStarsLabel = gtk.Label("Path to PokerStars auto-import:")
		self.pathHBox.pack_start(self.pathStarsLabel, False, False, 0)
		self.pathStarsLabel.show()
		
		self.starsDirPath=gtk.Entry()
		paths = self.config.get_default_paths("PokerStars")
		self.starsDirPath.set_text(paths['hud-defaultPath'])
		self.pathHBox.pack_start(self.starsDirPath, False, True, 0)
		self.starsDirPath.show()

		self.browseButton=gtk.Button("Browse...")
		self.browseButton.connect("clicked", self.starsBrowseClicked, "Browse clicked")
		self.pathHBox.pack_start(self.browseButton, False, False, 0)
 		self.browseButton.show()
		
		self.pathTiltLabel = gtk.Label("Path to Full Tilt auto-import:")
		self.pathHBox.pack_start(self.pathTiltLabel, False, False, 0)
		self.pathTiltLabel.show()

		self.tiltDirPath=gtk.Entry()
		paths = self.config.get_default_paths("Full Tilt")
		self.tiltDirPath.set_text(paths['hud-defaultPath'])
		self.pathHBox.pack_start(self.tiltDirPath, False, True, 0)
		self.tiltDirPath.show()

		self.browseButton=gtk.Button("Browse...")
		self.browseButton.connect("clicked", self.tiltBrowseClicked, "Browse clicked")
		self.pathHBox.pack_start(self.browseButton, False, False, 0)
 		self.browseButton.show()

		self.startButton=gtk.Button("Start Autoimport")
		self.startButton.connect("clicked", self.startClicked, "start clicked")
		self.mainVBox.add(self.startButton)
 		self.startButton.show()
	#end of GuiAutoImport.__init__
if __name__== "__main__":
    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()

    settings = {}
    settings['db-host'] = "192.168.1.100"
    settings['db-user'] = "mythtv"
    settings['db-password'] = "mythtv"
    settings['db-databaseName'] = "fpdb"
    settings['hud-defaultInterval'] = 10
    settings['hud-defaultPath'] = 'C:/Program Files/PokerStars/HandHistory/nutOmatic'
    settings['imp-callFpdbHud'] = True

    i = GuiAutoImport(settings)
    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    main_window.add(i.mainVBox)
    main_window.show()
    gtk.main()
