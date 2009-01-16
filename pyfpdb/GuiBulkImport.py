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
import fpdb_simple
import fpdb_import
import pygtk
pygtk.require('2.0')
import gtk
import os #todo: remove this once import_dir is in fpdb_import
from time import time

class GuiBulkImport (threading.Thread):
	def import_dir(self):
		"""imports a directory, non-recursive. todo: move this to fpdb_import so CLI can use it"""
		self.path=self.inputFile
		self.importer.addImportDirectory(self.path)
		self.importer.setCallHud(False)
		starttime = time()
		(stored, dups, partial, errs, ttime) = self.importer.runImport()
		print "GuiBulkImport.import_dir done: Stored: %d Dupllicates: %d Partial: %d Errors: %d in %s" %(stored, dups, partial, errs, time() - starttime)
		
	def load_clicked(self, widget, data=None):
		self.inputFile=self.chooser.get_filename()
		
		self.handCount=self.hand_count_tbuffer.get_text(self.hand_count_tbuffer.get_start_iter(), self.hand_count_tbuffer.get_end_iter())
		if (self.handCount=="unlimited" or self.handCount=="Unlimited"):
			self.importer.setHandCount(0)
		else:
			self.importer.setHandCount(int(self.handCount))

		self.errorFile="failed.txt"
		
		self.minPrint=self.min_print_tbuffer.get_text(self.min_print_tbuffer.get_start_iter(), self.min_print_tbuffer.get_end_iter())
		if (self.minPrint=="never" or self.minPrint=="Never"):
			self.importer.setMinPrint(0)
		else:
			self.importer.setMinPrint=int(self.minPrint)
		
		self.quiet=self.info_tbuffer.get_text(self.info_tbuffer.get_start_iter(), self.info_tbuffer.get_end_iter())
		if (self.quiet=="yes"):
			self.importer.setQuiet(False)
		else:
			self.importer.setQuiet(True)
			
		self.failOnError=self.fail_error_tbuffer.get_text(self.fail_error_tbuffer.get_start_iter(), self.fail_error_tbuffer.get_end_iter())
		if (self.failOnError=="no"):
			self.importer.setFailOnError(False)
		else:
			self.importer.setFailOnError(True)
		
		if os.path.isdir(self.inputFile):
			self.import_dir()
		else:
			self.importer.addImportFile(self.inputFile)
			self.importer.setCallHud(False)
			self.importer.runImport()
			self.importer.clearFileList()
	
	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.vbox
	#end def get_vbox
	
	def run (self):
		print "todo: implement bulk import thread"
	#end def run
	
	def __init__(self, db, settings, config):
		self.db=db
		self.settings=settings
		self.config=config
		self.importer = fpdb_import.Importer(self,self.settings, config)
		
		self.vbox=gtk.VBox(False,1)
		self.vbox.show()
		
		self.chooser = gtk.FileChooserWidget()
		self.chooser.set_filename(self.settings['bulkImport-defaultPath'])
		#chooser.set_default_response(gtk.RESPONSE_OK)
		#self.filesel.ok_button.connect_object("clicked", gtk.Widget.destroy, self.filesel)
		self.vbox.add(self.chooser)
		self.chooser.show()
		
		
		self.settings_hbox = gtk.HBox(False, 0)
		self.vbox.pack_end(self.settings_hbox, False, True, 0)
		self.settings_hbox.show()
		
		self.hand_count_label = gtk.Label("Hands to import per file")
		self.settings_hbox.add(self.hand_count_label)
		self.hand_count_label.show()
		
		self.hand_count_tbuffer=gtk.TextBuffer()
		self.hand_count_tbuffer.set_text("unlimited")
		self.hand_count_tview=gtk.TextView(self.hand_count_tbuffer)
		self.settings_hbox.add(self.hand_count_tview)
		self.hand_count_tview.show()
		
		self.min_hands_label = gtk.Label("Status every")
		self.settings_hbox.add(self.min_hands_label)
		self.min_hands_label.show()
		
		self.min_print_tbuffer=gtk.TextBuffer()
		self.min_print_tbuffer.set_text("never")
		self.min_print_tview=gtk.TextView(self.min_print_tbuffer)
		self.settings_hbox.add(self.min_print_tview)
		self.min_print_tview.show()

		
		self.toggles_hbox = gtk.HBox(False, 0)
		self.vbox.pack_end(self.toggles_hbox, False, True, 0)
		self.toggles_hbox.show()

		self.info_label = gtk.Label("Print start/end info:")
		self.toggles_hbox.add(self.info_label)
		self.info_label.show()
		
		self.info_tbuffer=gtk.TextBuffer()
		self.info_tbuffer.set_text("yes")
		self.info_tview=gtk.TextView(self.info_tbuffer)
		self.toggles_hbox.add(self.info_tview)
		self.info_tview.show()
		
		self.fail_error_label = gtk.Label("Fail on error:")
		self.toggles_hbox.add(self.fail_error_label)
		self.fail_error_label.show()
		
		self.fail_error_tbuffer=gtk.TextBuffer()
		self.fail_error_tbuffer.set_text("no")
		self.fail_error_tview=gtk.TextView(self.fail_error_tbuffer)
		self.toggles_hbox.add(self.fail_error_tview)
		self.fail_error_tview.show()

		self.load_button = gtk.Button("Import") #todo: rename variables to import too
		self.load_button.connect("clicked", self.load_clicked, "Import clicked")
		self.toggles_hbox.add(self.load_button)
		self.load_button.show()

		threading.Thread.__init__ ( self )
		print "initialised new bulk import thread (not actually a thread yet)"
#end class import_threaded
