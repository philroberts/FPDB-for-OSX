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
	def hudDivide (self, a, b):
		if b==0:
			return "n/a"
		else:
			return str(int((a/float(b))*100))+"%"
	#end def hudDivide
	
	def browse_clicked(self, widget, data):
		"""runs when user clicks browse on tv tab"""
		#print "start of table_viewer.browser_clicked"
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
		#print "start of prepare_data"
		arr=[]
		#first prepare the header row
		if (self.category=="holdem" or self.category=="omahahi" or self.category=="omahahilo"):
			tmp=("Name", "Hands", "VPIP", "PFR", "PF3B4B", "AF", "FF", "AT", "FT", "AR", "FR", "SD/F", "W$wSF", "W$@SD")
		else:
			raise fpdb_simple.FpdbError("reimplement stud")
			tmp=("Name", "Hands", "VPI3", "A3", "3B4B_3" "A4", "F4", "A5", "F5", "A6", "F6", "A7", "F7", "SD/4")
		arr.append(tmp)
		
		#then the data rows
		for player in range(len(self.player_names)):
			tmp=[]
			tmp.append(self.player_names[player][0])
			
			seatCount=len(self.player_names)
			if seatCount>=8:
				minSeats,maxSeats=7,10
			elif seatCount==7:
				minSeats,maxSeats=6,10
			elif seatCount==6 or seatCount==5:
				minSeats,maxSeats=seatCount-1,seatCount+1
			elif seatCount==4:
				minSeats,maxSeats=4,5
			elif seatCount==2 or seatCount==3:
				minSeats,maxSeats=seatCount,seatCount
			else:
				fpdb_simple.FpdbError("invalid seatCount")
			
			self.cursor.execute("SELECT * FROM HudDataHoldemOmaha WHERE gametypeId=%s AND playerId=%s AND activeSeats>=%s AND activeSeats<=%s", (self.gametype_id, self.player_ids[player][0], minSeats, maxSeats))
			rows=self.cursor.fetchall()
			
			row=[]
			for field_no in range(len(rows[0])):
				row.append(rows[0][field_no])
			
			for row_no in range(len(rows)):
				if row_no==0:
					pass
				else:
					for field_no in range(len(rows[row_no])):
						if field_no<=3:
							pass
						else:
							row[field_no]+=rows[row_no][field_no]
			
			tmp.append(str(row[4]))#Hands
			tmp.append(self.hudDivide(row[5],row[4])) #VPIP
			tmp.append(self.hudDivide(row[6],row[4])) #PFR
			tmp.append(self.hudDivide(row[8],row[7])+" ("+str(row[7])+")") #PF3B4B
			tmp.append(self.hudDivide(row[13],row[9])+" ("+str(row[9])+")") #AF
			tmp.append(self.hudDivide(row[17],row[16])+" ("+str(row[16])+")") #FF
			tmp.append(self.hudDivide(row[14],row[10])+" ("+str(row[10])+")") #AT
			tmp.append(self.hudDivide(row[19],row[18])+" ("+str(row[18])+")") #FT
			tmp.append(self.hudDivide(row[15],row[11])+" ("+str(row[11])+")") #AR
			tmp.append(self.hudDivide(row[21],row[20])+" ("+str(row[20])+")") #FR
			tmp.append(self.hudDivide(row[12],row[9])+" ("+str(row[9])+")") #SD/F
			tmp.append(self.hudDivide(row[22],row[9])+" ("+str(row[9])+")") #W$wSF
			tmp.append(self.hudDivide(row[23],row[12])+" ("+str(row[12])+")") #W$@SD
			
			arr.append(tmp)
		return arr
	#end def table_viewer.prepare_data
	
	def refresh_clicked(self, widget, data):
		"""runs when user clicks refresh"""
		#print "start of table_viewer.refresh_clicked"
		arr=self.prepare_data()
		
		try: self.data_table.destroy()
		except AttributeError: pass
		self.data_table=gtk.Table(rows=len(arr), columns=len(arr[0]), homogeneous=False)
		self.main_vbox.pack_start(self.data_table)
		self.data_table.show()
		
		for row in range(len(arr)):
			for column in range (len(arr[row])):
				eventBox=gtk.EventBox()
				new_label=gtk.Label(arr[row][column])
				if row%2==0: #
					bg_col="white"
					if column==0 or (column>=5 and column<=10):
						bg_col="lightgrey"
				else:
					bg_col="lightgrey"
					if column==0 or (column>=5 and column<=10):
						bg_col="grey"
				eventBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bg_col))
				eventBox.add(new_label)
				self.data_table.attach(child=eventBox, left_attach=column, right_attach=column+1, top_attach=row, bottom_attach=row+1)
				eventBox.show()
				new_label.show()
	#end def table_viewer.refresh_clicked

	def read_names_clicked(self, widget, data):
		"""runs when user clicks read names"""
		#print "start of table_viewer.read_names_clicked"
		#print "self.last_read_hand:",self.last_read_hand
		self.db.reconnect()
		self.cursor=self.db.cursor
		self.cursor.execute("""SELECT id FROM hands WHERE site_hand_no=%s""", (self.last_read_hand))
		hands_id_tmp=self.db.cursor.fetchone()
		#print "tmp:",hands_id_tmp
		self.hands_id=hands_id_tmp[0]

		self.db.cursor.execute("SELECT gametype_id FROM hands WHERE id=%s", (self.hands_id, ))
		self.gametype_id=self.db.cursor.fetchone()[0]
		self.cursor.execute("SELECT category FROM gametypes WHERE id=%s", (self.gametype_id, ))
		self.category=self.db.cursor.fetchone()[0]
		#print "self.gametype_id", self.gametype_id,"  category:", self.category, "  self.hands_id:", self.hands_id
		
		self.db.cursor.execute("""SELECT DISTINCT players.id FROM hands_players
				INNER JOIN players ON hands_players.player_id=players.id
				WHERE hand_id=%s""", (self.hands_id, ))
		self.player_ids=self.db.cursor.fetchall()
		#print "self.player_ids:",self.player_ids
		
		self.db.cursor.execute("""SELECT DISTINCT players.name FROM hands_players
				INNER JOIN players ON hands_players.player_id=players.id
				WHERE hand_id=%s""", (self.hands_id, ))
		self.player_names=self.db.cursor.fetchall()
		#print "self.player_names:",self.player_names
	#end def table_viewer.read_names_clicked

	def import_clicked(self, widget, data):
		"""runs when user clicks import"""
		#print "start of table_viewer.import_clicked"
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
		#print "start of table_viewer.all_clicked"
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
		#print "start of table_viewer constructor"
		self.db=db
		self.cursor=db.cursor
        
		self.main_vbox = gtk.VBox(False, 0)
		self.main_vbox.show()

		self.settings_hbox = gtk.HBox(False, 0)
		self.main_vbox.pack_end(self.settings_hbox, False, True, 0)
		self.settings_hbox.show()
		
		self.filename_label = gtk.Label("Path of history file")
		self.settings_hbox.pack_start(self.filename_label, False, False)
		self.filename_label.show()
		
		self.filename_tbuffer=gtk.TextBuffer()
		self.filename_tbuffer.set_text("/home/sycamore/ps-history/HH20080726 Meliboea - $0.10-$0.20 - Limit Hold'em.txt")
		self.filename_tview=gtk.TextView(self.filename_tbuffer)
		self.settings_hbox.pack_start(self.filename_tview, True, True, padding=5)
		self.filename_tview.show()
		
		self.browse_button=gtk.Button("Browse...")
		self.browse_button.connect("clicked", self.browse_clicked, "Browse clicked")
		self.settings_hbox.pack_start(self.browse_button, False, False)
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
