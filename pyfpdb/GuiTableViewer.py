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

import fpdb_import
import fpdb_db
from Exceptions import *


class GuiTableViewer (threading.Thread):
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
            tmp=("Name", "HDs", "VPIP", "PFR", "PF3B", "ST")
            
            tmp+=("FS", "FB")
            
            tmp+=("CB", )
            
            tmp+=("2B", "3B")
            
            tmp+=("AF", "FF", "AT", "FT", "AR", "FR")
            
            tmp+=("WtSD", "W$wsF", "W$SD")
        else:
            raise FpdbError("reimplement stud")
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
                FpdbError("invalid seatCount")
            
            self.cursor.execute("SELECT * FROM HudCache WHERE gametypeId=%s AND playerId=%s AND activeSeats>=%s AND activeSeats<=%s", (self.gametype_id, self.player_ids[player][0], minSeats, maxSeats))
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
                            #print "in prep data, row_no:",row_no,"field_no:",field_no
                            row[field_no]+=rows[row_no][field_no]
            
            tmp.append(str(row[6]))#Hands
            tmp.append(self.hudDivide(row[7],row[6])) #VPIP
            tmp.append(self.hudDivide(row[8],row[6])) #PFR
            tmp.append(self.hudDivide(row[10],row[9])+" ("+str(row[9])+")") #PF3B
            
            tmp.append(self.hudDivide(row[31],row[30])+" ("+str(row[30])+")") #ST
            
            tmp.append(self.hudDivide(row[35],row[34])+" ("+str(row[34])+")") #FS
            tmp.append(self.hudDivide(row[33],row[32])+" ("+str(row[32])+")") #FB
            
            tmp.append(self.hudDivide(row[37],row[36])+" ("+str(row[36])+")") #CB
            
            tmp.append(self.hudDivide(row[39],row[38])+" ("+str(row[38])+")") #2B
            tmp.append(self.hudDivide(row[41],row[40])+" ("+str(row[40])+")") #3B
            
            tmp.append(self.hudDivide(row[16],row[11])+" ("+str(row[11])+")") #AF
            tmp.append(self.hudDivide(row[24],row[20])+" ("+str(row[20])+")") #FF
            tmp.append(self.hudDivide(row[17],row[12])+" ("+str(row[12])+")") #AT
            tmp.append(self.hudDivide(row[25],row[21])+" ("+str(row[21])+")") #FT
            tmp.append(self.hudDivide(row[18],row[13])+" ("+str(row[13])+")") #AR
            tmp.append(self.hudDivide(row[26],row[22])+" ("+str(row[22])+")") #FR
            
            tmp.append(self.hudDivide(row[15],row[11])) #WtSD
            tmp.append(self.hudDivide(row[28],row[11])) #W$wSF
            tmp.append(self.hudDivide(row[29],row[15])+" ("+str(row[15])+")") #W$@SD
            
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
                #style = eventBox.get_style()
                #style.font.height=8
                #eventBox.set_style(style)

                eventBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bg_col))
                eventBox.add(new_label)
                self.data_table.attach(child=eventBox, left_attach=column, right_attach=column+1, top_attach=row, bottom_attach=row+1)
                eventBox.show()
                new_label.show()
    #end def table_viewer.refresh_clicked

    def read_names_clicked(self, widget, data):
        """runs when user clicks read names"""
        #print "start of table_viewer.read_names_clicked"
        self.db.reconnect()
        self.cursor=self.db.get_cursor()
        #self.hands_id=self.last_read_hand_id

        self.cursor.execute("SELECT gametypeId FROM Hands WHERE id=%s", (self.hands_id, ))
        self.gametype_id=self.cursor.fetchone()[0]
        self.cursor.execute("SELECT category FROM Gametypes WHERE id=%s", (self.gametype_id, ))
        self.category=self.cursor.fetchone()[0]
        #print "self.gametype_id", self.gametype_id,"  category:", self.category, "  self.hands_id:", self.hands_id
        
        self.cursor.execute("""SELECT DISTINCT Players.id FROM HandsPlayers
                INNER JOIN Players ON HandsPlayers.playerId=Players.id
                WHERE handId=%s""", (self.hands_id, ))
        self.player_ids=self.cursor.fetchall()
        #print "self.player_ids:",self.player_ids
        
        self.cursor.execute("""SELECT DISTINCT Players.name FROM HandsPlayers
                INNER JOIN Players ON HandsPlayers.playerId=Players.id
                WHERE handId=%s""", (self.hands_id, ))
        self.player_names=self.cursor.fetchall()
        #print "self.player_names:",self.player_names
    #end def table_viewer.read_names_clicked

    def import_clicked(self, widget, data):
        """runs when user clicks import"""
        #print "start of table_viewer.import_clicked"
        self.inputFile=self.filename_tbuffer.get_text(self.filename_tbuffer.get_start_iter(), self.filename_tbuffer.get_end_iter())

        self.importer = fpdb_import.Importer(self, self.settings, self.config)
        self.importer.setMinPrint(0)
        self.importer.setQuiet(False)
        self.importer.setFailOnError(False)
        self.importer.setHandCount(0)

        self.importer.addImportFile(self.inputFile)
        self.importer.runImport()
        self.hands_id=self.importer.handsId
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
    
    def __init__(self, db, settings, config=None, debug=True):
        """Constructor for table_viewer"""
        self.debug=debug
        #print "start of table_viewer constructor"
        self.db = db
        self.cursor = db.get_cursor()
        self.settings = settings
        self.config = config
        
        self.main_vbox = gtk.VBox(False, 0)
        self.main_vbox.show()

        self.settings_hbox = gtk.HBox(False, 0)
        self.main_vbox.pack_end(self.settings_hbox, False, True, 0)
        self.settings_hbox.show()
        
        self.filename_label = gtk.Label("Path of history file")
        self.settings_hbox.pack_start(self.filename_label, False, False)
        self.filename_label.show()
        
        self.filename_tbuffer=gtk.TextBuffer()
        self.filename_tbuffer.set_text(self.settings['hud-defaultPath'])
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
