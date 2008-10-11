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
	def browseClicked(self, widget, data):
		"""runs when user clicks browse on auto import tab"""
		#print "start of GuiAutoImport.browseClicked"
		current_path=self.pathTBuffer.get_text(self.pathTBuffer.get_start_iter(), self.pathTBuffer.get_end_iter())
		
		dia_chooser = gtk.FileChooserDialog(title="Please choose the path that you want to auto import",
				action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
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

	def do_import(self):
		"""Callback for timer to do an import iteration."""
		for file in os.listdir(self.path):
			if os.path.isdir(file):
				print "AutoImport is not recursive - please select the final directory in which the history files are"
			else:
				self.inputFile = os.path.join(self.path, file)
				stat_info = os.stat(self.inputFile)
				if not self.import_files.has_key(self.inputFile) or stat_info.st_mtime > self.import_files[self.inputFile]:
				    self.importer.import_file_dict()
				    self.import_files[self.inputFile] = stat_info.st_mtime

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
			self.path=self.pathTBuffer.get_text(self.pathTBuffer.get_start_iter(), self.pathTBuffer.get_end_iter())

#	Iniitally populate the self.import_files dict, which keeps mtimes for the files watched

			self.import_files = {}
			for file in os.listdir(self.path):
				if os.path.isdir(file):
					pass   # skip subdirs for now
				else:
					inputFile = os.path.join(self.path, file)
					stat_info = os.stat(inputFile)
					self.import_files[inputFile] = stat_info.st_mtime 

			self.do_import()
		
			interval=int(self.intervalTBuffer.get_text(self.intervalTBuffer.get_start_iter(), self.intervalTBuffer.get_end_iter()))
			gobject.timeout_add(interval*1000, self.do_import)
	#end def GuiAutoImport.browseClicked

	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.mainVBox
	#end def get_vbox
	
	def __init__(self, settings, debug=True):
		"""Constructor for GuiAutoImport"""
		self.settings=settings
		self.importer = fpdb_import.Importer(self,self.settings)
		self.importer.setCallHud(True)
		self.importer.setMinPrint(30)
		
		self.server=settings['db-host']
		self.user=settings['db-user']
		self.password=settings['db-password']
		self.database=settings['db-databaseName']
		self.quiet=False
		self.failOnError=False
		self.handCount=0
		
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
