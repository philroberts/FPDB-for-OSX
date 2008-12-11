#!/usr/bin/env python
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008, Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

#    to do

#    Standard Library modules
import sys

#    pyGTK modules
import pygtk
import gtk
import gobject

#    FreePokerTools modules
import Configuration
import Database

class Aux_Window:
    def __init__(self, parent, hud, config, db_name):
        self.config  = hud
        self.config  = config
        self.parent  = parent
        self.db_name = db_name

        self.vbox = gtk.VBox()
        self.parent.add(self.vbox)

    def update_data(self):
        pass

    def update_gui(self):
        pass

class Stud_mucked(Aux_Window):
    def __init__(self, parent, hud, config, db_name):

        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.parent  = parent    # parent container for this aux window widget
        self.db_name = db_name   # database for this aux window to use

        self.vbox = gtk.VBox()
        self.parent.add(self.vbox)

        self.mucked_list   = Stud_list(self.vbox, config, db_name)
        self.mucked_cards  = Stud_cards(self.vbox, config, db_name)
        self.mucked_list.mucked_cards = self.mucked_cards
        self.parent.show_all()

    def update_data(self, new_hand_id):
        self.mucked_cards.update_data(new_hand_id)
        self.mucked_list.update_data(new_hand_id)
        
    def update_gui(self, new_hand_id):
        self.mucked_cards.update_gui(new_hand_id)
        self.mucked_list.update_gui(new_hand_id)
        
class Stud_list:
    def __init__(self, parent, config, db_name):

        self.parent  = parent
        self.config  = config
        self.db_name = db_name

#       set up a scrolled window to hold the listbox
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.parent.add(self.scrolled_window)

#       create a ListStore to use as the model
        self.liststore = gtk.ListStore(str, str, str, str)
        self.treeview = gtk.TreeView(self.liststore)
        self.tvcolumn0 = gtk.TreeViewColumn('HandID')
        self.tvcolumn1 = gtk.TreeViewColumn('Cards')
        self.tvcolumn2 = gtk.TreeViewColumn('Net')
        self.tvcolumn3 = gtk.TreeViewColumn('Winner')

#       add tvcolumn to treeview
        self.treeview.append_column(self.tvcolumn0)
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        self.treeview.append_column(self.tvcolumn3)

#       create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn0.pack_start(self.cell, True)
        self.tvcolumn1.pack_start(self.cell, True)
        self.tvcolumn2.pack_start(self.cell, True)
        self.tvcolumn3.pack_start(self.cell, True)
        self.tvcolumn0.add_attribute(self.cell, 'text', 0)
        self.tvcolumn1.add_attribute(self.cell, 'text', 1)
        self.tvcolumn2.add_attribute(self.cell, 'text', 2)
        self.tvcolumn3.add_attribute(self.cell, 'text', 3)
#        resize the cols if nec
        self.tvcolumn0.set_resizable(True)
        self.tvcolumn1.set_resizable(True)
        self.tvcolumn2.set_resizable(True)
        self.tvcolumn3.set_resizable(True)
        self.treeview.connect("row-activated", self.activated_event)

        self.scrolled_window.add_with_viewport(self.treeview)

    def activated_event(self, path, column, data=None):
        sel = self.treeview.get_selection()
        (model, iter)  = sel.get_selected()
        self.mucked_cards.update_data(model.get_value(iter, 0))
        self.mucked_cards.update_gui(model.get_value(iter, 0))
        
    def update_data(self, new_hand_id):
        """Updates the data needed for the list box."""

        db_connection = Database.Database(self.config, 'fpdb', '')
        self.winners = db_connection.get_winners_from_hand(new_hand_id)
        db_connection.close_connection()
        pot = 0
        winners = ''
        for player in self.winners.keys():
            pot = pot + int(self.winners[player])
            if not winners == '':
                winners = winners + ", "
            winners = winners + player
        pot_dec = "%.2f" % (float(pot)/100)

        self.info_row = ((new_hand_id, "xxxx", pot_dec, winners), )

    def update_gui(self, new_hand_id):
        iter = self.liststore.append(self.info_row[0]) 
        sel = self.treeview.get_selection()
        sel.select_iter(iter)

        vadj = self.scrolled_window.get_vadjustment()
        vadj.set_value(vadj.upper)

class Stud_cards:
    def __init__(self, parent, config, db_name = 'fpdb'):

        self.parent  = parent    #this is the parent of the mucked cards widget
        self.config  = config
        self.db_name = db_name

        self.card_images = self.get_card_images()
        self.seen_cards = {}
        self.grid_contents = {}
        self.eb = {}

        self.rows = 8
        self.cols = 7
        self.grid = gtk.Table(self.rows, self.cols + 4, homogeneous = False)

        for r in range(0, self.rows):
            for c in range(0, self.cols):
                self.seen_cards[(c, r)] = gtk.image_new_from_pixbuf(self.card_images[('B', 'S')])
                self.eb[(c, r)]= gtk.EventBox()

#    set up the contents for the cells
        for r in range(0, self.rows):
            self.grid_contents[( 0, r)] = gtk.Label("%d" % (r + 1))
            self.grid_contents[( 1, r)] = gtk.Label("player %d" % (r + 1))
            self.grid_contents[( 1, r)].set_property("width-chars", 12)
            self.grid_contents[( 4, r)] = gtk.Label("-")
            self.grid_contents[( 9, r)] = gtk.Label("-")
            self.grid_contents[( 2, r)] = self.eb[( 0, r)]
            self.grid_contents[( 3, r)] = self.eb[( 1, r)]
            self.grid_contents[( 5, r)] = self.eb[( 2, r)]
            self.grid_contents[( 6, r)] = self.eb[( 3, r)]
            self.grid_contents[( 7, r)] = self.eb[( 4, r)]
            self.grid_contents[( 8, r)] = self.eb[( 5, r)]
            self.grid_contents[(10, r)] = self.eb[( 6, r)]
            for c in range(0, self.cols):
                self.eb[(c, r)].add(self.seen_cards[(c, r)])
            
#    add the cell contents to the table
        for c in range(0, self.cols + 4):
            for r in range(0, self.rows):
                self.grid.attach(self.grid_contents[(c, r)], c, c+1, r, r+1, xpadding = 1, ypadding = 1)
                
        self.parent.add(self.grid)

    def translate_cards(self, old_cards):
        ranks = ('', '', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')

        for c in old_cards.keys():
            for i in range(1, 8):
                rank = 'card' + str(i) + 'Value'
                suit = 'card' + str(i) + 'Suit'
                key = 'hole_card_' + str(i)
                if old_cards[c][rank] == 0:
                    old_cards[c][key] = 'xx'
                else:
                    old_cards[c][key] = ranks[old_cards[c][rank]] + old_cards[c][suit]
        return old_cards

    def update_data(self, new_hand_id):
        db_connection = Database.Database(self.config, 'fpdb', '')
        cards = db_connection.get_cards(new_hand_id)
        self.clear()
        self.cards = self.translate_cards(cards)

        self.tips = []
        action = db_connection.get_action_from_hand(new_hand_id)
        for street in action:
            temp = ''
            for act in street:
                temp = temp + act[0] + " " + act[1] + "s "
                if act[2] > 0:
                    if act[2]%100 > 0:
                        temp = temp + "%4.2f\n" % (float(act[2])/100)
                    else:
                        temp = temp + "%d\n" % (act[2]/100) 
                else:
                    temp = temp + "\n"
            self.tips.append(temp)
        db_connection.close_connection()

    def update_gui(self, new_hand_id):
        for c in self.cards.keys():
            self.grid_contents[(1, self.cards[c]['seat_number'] - 1)].set_text(self.cards[c]['screen_name'])
            for i in ((0, 'hole_card_1'), (1, 'hole_card_2'), (2, 'hole_card_3'), (3, 'hole_card_4'), 
                      (4, 'hole_card_5'), (5, 'hole_card_6'), (6, 'hole_card_7')):
                if not self.cards[c][i[1]] == "xx":
                    self.seen_cards[(i[0], self.cards[c]['seat_number'] - 1)]. \
                        set_from_pixbuf(self.card_images[self.split_cards(self.cards[c][i[1]])])
##    action in tool tips for 3rd street cards
        for c in (0, 1, 2):
            for r in range(0, self.rows):
                self.eb[(c, r)].set_tooltip_text(self.tips[0])

#    action in tools tips for later streets
        round_to_col = (0, 3, 4, 5, 6)
        for round in range(1, len(self.tips)):
            for r in range(0, self.rows):
                self.eb[(round_to_col[round], r)].set_tooltip_text(self.tips[round])

    def split_cards(self, card):
        return (card[0], card[1].upper())

    def clear(self):
        for r in range(0, self.rows):
            self.grid_contents[(1, r)].set_text("             ")
            for c in range(0, 7):
                self.seen_cards[(c, r)].set_from_pixbuf(self.card_images[('B', 'S')])
                self.eb[(c, r)].set_tooltip_text('')
    def get_card_images(self):
        card_images = {}
        suits = ('S', 'H', 'D', 'C')
        ranks = ('A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2', 'B')
        pb  = gtk.gdk.pixbuf_new_from_file("Cards01.png")
        
        for j in range(0, 14):
            for i in range(0, 4):
                temp_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(), pb.get_bits_per_sample(),  30,  42)
                pb.copy_area(30*j, 42*i, 30, 42, temp_pb, 0, 0)
                card_images[(ranks[j], suits[i])] = temp_pb
        return(card_images)

#   cards are 30 wide x 42 high

if __name__== "__main__":
    
    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()             # used only for testing

    def process_new_hand(source, condition):  #callback from stdin watch -- testing only
#    there is a new hand_id to be processed
#    just read it and pass it to update
        new_hand_id = sys.stdin.readline()
        new_hand_id = new_hand_id.rstrip()  # remove trailing whitespace
        m.update_data(new_hand_id)
        m.update_gui(new_hand_id)
        return(True)

    config = Configuration.Config()
#    db_connection = Database.Database(config, 'fpdb', '')
    main_window = gtk.Window()
    main_window.set_keep_above(True)
    main_window.connect("destroy", destroy)

    aux_to_call = "Stud_mucked"
    m = eval("%s(main_window, None, config, 'fpdb')" % aux_to_call)
    main_window.show_all()
    
    s_id = gobject.io_add_watch(sys.stdin, gobject.IO_IN, process_new_hand)
    gtk.main()
