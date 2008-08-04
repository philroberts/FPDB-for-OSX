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
import MySQLdb
import fpdb_import
import fpdb_db

class table_viewer (threading.Thread):
	def browse_clicked(self, widget, data):
		"""runs when user clicks browse on tv tab"""
		print "start of table_viewer.browser_clicked"
		current_path=self.filename_tbuffer.get_text(self.filename_tbuffer.get_start_iter(), self.filename_tbuffer.get_end_iter())
		
		dia_chooser = gtk.FileChooserDialog(title="Please choose the file for which you want to open the Table Viewer",
				action=gtk.FILE_CHOOSER_ACTION_OPEN,
				buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		#dia_chooser.set_current_folder(pathname)
		dia_chooser.set_filename(current_path)
		#dia_chooser.set_select_multiple(select_multiple) #not in tv, but want this in bulk import
		
		response = dia_chooser.run()
		if response == gtk.RESPONSE_OK:
			#print dia_chooser.get_filename(), 'selected'
			self.filename_tbuffer.set_text(dia_chooser.get_filename())
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
		dia_chooser.destroy()		
	#end def table_viewer.browse_clicked
	
	def prepare_data(self):
		"""prepares the data for display by refresh_clicked, returns a 2D array"""
		print "start of prepare_data"
		arr=[]
		#first prepare the header row
		if (self.category=="holdem" or self.category=="omahahi" or self.category=="omahahilo"):
			tmp=("Name", "Hands", "VPIP", "PFR", "AF", "FF", "AT", "FT", "AR", "FR")
			streets=(1,2,3)
		else:
			tmp=("Name", "Hands", "VPI3", "A3", "A4", "F4", "A5", "F5", "A6", "F6", "A7", "F7")
			streets=(4,5,6,7)#todo: change this once table has been changed
		arr.append(tmp)
		
		#then the data rows
		for i in range(len(self.player_names)):
			tmp=[]
			tmp.append(self.player_names[i][0])
			
			self.cursor.execute("""SELECT DISTINCT hands.id FROM hands
				INNER JOIN hands_players ON hands_players.hand_id = hands.id
				WHERE hands.gametype_id=%s AND hands_players.player_id=%s""", (self.gametype_id, self.player_ids[i][0]))
			hand_count=self.cursor.rowcount
			tmp.append(str(hand_count))
			
			self.cursor.execute("""SELECT DISTINCT hands.id FROM hands_players 
				INNER JOIN hands_players_flags ON hands_players.id = hands_players_flags.hand_player_id 
				INNER JOIN hands ON hands_players.hand_id = hands.id
				WHERE hands.gametype_id=%s AND hands_players.player_id=%s 
				AND street0_vpi=True""", (self.gametype_id, self.player_ids[i][0]))
			vpi_count=self.cursor.rowcount
			vpi_percent=int(vpi_count/float(hand_count)*100)
			tmp.append(str(vpi_percent))
			
			
			self.cursor.execute("""SELECT DISTINCT hands.id FROM hands_players 
				INNER JOIN hands_players_flags ON hands_players.id = hands_players_flags.hand_player_id 
				INNER JOIN hands ON hands_players.hand_id = hands.id
				WHERE hands.gametype_id=%s AND hands_players.player_id=%s 
				AND street0_raise=True""", (self.gametype_id, self.player_ids[i][0]))
			raise_count=self.cursor.rowcount
			raise_percent=int(raise_count/float(hand_count)*100)
			tmp.append(str(raise_percent))
			
			######start of flop/4th street######
			hand_count
			
			play_counts=[]
			raise_counts=[]
			fold_counts=[]
			self.cursor.execute("""SELECT DISTINCT hands.id FROM hands_players 
				INNER JOIN hands_players_flags ON hands_players.id = hands_players_flags.hand_player_id 
				INNER JOIN hands ON hands_players.hand_id = hands.id
				WHERE hands.gametype_id=%s AND hands_players.player_id=%s 
				AND folded_on=0""", (self.gametype_id, self.player_ids[i][0]))
			preflop_fold_count=self.cursor.rowcount
			last_play_count=hand_count-preflop_fold_count
			play_counts.append(last_play_count)
				
			for street in streets:
				self.cursor.execute("""SELECT DISTINCT hands.id FROM hands_players 
					INNER JOIN hands_players_flags ON hands_players.id = hands_players_flags.hand_player_id 
					INNER JOIN hands ON hands_players.hand_id = hands.id
					WHERE hands.gametype_id=%s AND hands_players.player_id=%s 
					AND folded_on="""+str(street), (self.gametype_id, self.player_ids[i][0]))
				fold_count=self.cursor.rowcount
				fold_counts.append(fold_count)
				last_play_count-=fold_count
				play_counts.append(last_play_count)
				
				self.cursor.execute("""SELECT DISTINCT hands.id FROM hands_players 
					INNER JOIN hands_players_flags ON hands_players.id = hands_players_flags.hand_player_id 
					INNER JOIN hands ON hands_players.hand_id = hands.id
					WHERE hands.gametype_id=%s AND hands_players.player_id=%s 
					AND street"""+str(street)+"_raise=True""", (self.gametype_id, self.player_ids[i][0]))
				raise_counts.append(self.cursor.rowcount)
			
			for street in range (len(streets)):
				if play_counts[street]>0:
					raise_percent=int(raise_counts[street]/float(play_counts[street])*100)
					tmp.append(str(raise_percent))
					fold_percent=int(fold_counts[street]/float(play_counts[street])*100)
					tmp.append(str(fold_percent))
				else:
					tmp.append("n/a")
					tmp.append("n/a")
			
			arr.append(tmp)
		return arr
	#end def table_viewer.prepare_data
	
	def refresh_clicked(self, widget, data):
		"""runs when user clicks refresh"""
		if self.debug: print "start of table_viewer.refresh_clicked"
		arr=self.prepare_data()
		
		try: self.data_table.destroy()
		except AttributeError: pass
		self.data_table=gtk.Table(rows=len(arr), columns=len(arr[0]), homogeneous=False)
		self.main_vbox.pack_start(self.data_table)
		self.data_table.show()
		
		for row in range(len(arr)):
			for column in range (len(arr[row])):
				new_label=gtk.Label(arr[row][column])
				self.data_table.attach(child=new_label, left_attach=column, right_attach=column+1, top_attach=row, bottom_attach=row+1)
				new_label.show()
	#end def table_viewer.refresh_clicked

	def read_names_clicked(self, widget, data):
		"""runs when user clicks read names"""
		print "start of table_viewer.read_names_clicked"
		print "self.last_read_hand:",self.last_read_hand
		self.db.reconnect()
		self.cursor=self.db.cursor
		self.cursor.execute("""SELECT id FROM hands WHERE site_hand_no=%s""", (self.last_read_hand))
		hands_id_tmp=self.db.cursor.fetchone()
		print "tmp:",hands_id_tmp
		self.hands_id=hands_id_tmp[0]

		self.db.cursor.execute("SELECT gametype_id FROM hands WHERE id=%s", (self.hands_id, ))
		self.gametype_id=self.db.cursor.fetchone()[0]
		self.cursor.execute("SELECT category FROM gametypes WHERE id=%s", (self.gametype_id, ))
		self.category=self.db.cursor.fetchone()[0]
		print "self.gametype_id", self.gametype_id,"  category:", self.category, "  self.hands_id:", self.hands_id
		
		self.db.cursor.execute("""SELECT DISTINCT players.id FROM hands_players
				INNER JOIN players ON hands_players.player_id=players.id
				WHERE hand_id=%s""", (self.hands_id, ))
		self.player_ids=self.db.cursor.fetchall()
		print "self.player_ids:",self.player_ids
		
		self.db.cursor.execute("""SELECT DISTINCT players.name FROM hands_players
				INNER JOIN players ON hands_players.player_id=players.id
				WHERE hand_id=%s""", (self.hands_id, ))
		self.player_names=self.db.cursor.fetchall()
		print "self.player_names:",self.player_names
	#end def table_viewer.read_names_clicked

	def import_clicked(self, widget, data):
		"""runs when user clicks import"""
		print "start of table_viewer.import_clicked"
		self.inputFile=self.filename_tbuffer.get_text(self.filename_tbuffer.get_start_iter(), self.filename_tbuffer.get_end_iter())
		
		self.server=self.db.host
		self.database=self.db.database
		self.user=self.db.user
		self.password=self.db.password

		self.quiet=False
		self.failOnError=False
		self.minPrint=0
		self.handCount=0
		
		self.last_read_hand=fpdb_import.import_file_dict(self)
	#end def table_viewer.import_clicked

	def all_clicked(self, widget, data):
		"""runs when user clicks all"""
		print "start of table_viewer.all_clicked"
		self.import_clicked(widget, data)
		self.read_names_clicked(widget, data)
		self.refresh_clicked(widget, data)
	#end def table_viewer.all_clicked

	def get_vbox(self):
		"""returns the vbox of this thread"""
		return self.main_vbox
	#end def get_vbox
	
	def __init__(self, db, debug=True):
		"""Constructor for table_viewer"""
		self.debug=debug
		if self.debug: print "start of table_viewer constructor"
		self.db=db
		self.cursor=db.cursor
        
		self.main_vbox = gtk.VBox(False, 0)
		self.main_vbox.show()

		self.settings_hbox = gtk.HBox(False, 0)
		self.main_vbox.pack_end(self.settings_hbox, False, True, 0)
		self.settings_hbox.show()
		
		self.filename_label = gtk.Label("Path of history file")
		self.settings_hbox.add(self.filename_label)
		self.filename_label.show()
		
		self.filename_tbuffer=gtk.TextBuffer()
		self.filename_tbuffer.set_text("/home/sycamore/ps-history/HH20080726 Meliboea - $0.10-$0.20 - Limit Hold'em.txt")
		self.filename_tview=gtk.TextView(self.filename_tbuffer)
		self.settings_hbox.add(self.filename_tview)
		self.filename_tview.show()
		
		self.browse_button=gtk.Button("Browse...")
		self.browse_button.connect("clicked", self.browse_clicked, "Browse clicked")
		self.settings_hbox.add(self.browse_button)
 		self.browse_button.show()
		

		self.button_hbox = gtk.HBox(False, 0)
		self.main_vbox.pack_end(self.button_hbox, False, True, 0)
		self.button_hbox.show()
		
		#self.import_button = gtk.Button("Import")
		#self.import_button.connect("clicked", self.import_clicked, "Import clicked")
		#self.button_hbox.add(self.import_button)
 		#self.import_button.show()
        
		#self.read_names_button = gtk.Button("Read Names")
		#self.read_names_button.connect("clicked", self.read_names_clicked, "Read clicked")
		#self.button_hbox.add(self.read_names_button)
		#self.read_names_button.show()
		
		#self.refresh_button = gtk.Button("Show/Refresh data")
		#self.refresh_button.connect("clicked", self.refresh_clicked, "Refresh clicked")
		#self.button_hbox.add(self.refresh_button)
		#self.refresh_button.show()
		
		self.all_button = gtk.Button("Import&Read&Refresh")
		self.all_button.connect("clicked", self.all_clicked, "All clicked")
		self.button_hbox.add(self.all_button)
		self.all_button.show()
	#end of table_viewer.__init__
