#!/usr/bin/env python
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008, 2009,  Ray E. Barker
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
import pprint

#    pyGTK modules
import pygtk
import gtk
import gobject

#    FreePokerTools modules
import Configuration
import Database

class Aux_Window:
    def __init__(self, hud, params, config):
        self.hud     = hud
        self.config  = config

    def update_data(self, *parms):
        pass

    def update_gui(self, *parms):
        pass

    def create(self, *parms):
        pass

    def save_layout(self, *args):
        pass

    def destroy(self):
        try:
            self.container.destroy()
        except:
            pass

############################################################################
#    Some utility routines useful for Aux_Windows
#
    def get_card_images(self):
        card_images = {}
        suits = ('S', 'H', 'D', 'C')
        ranks = ('A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2', 'B')
        pb  = gtk.gdk.pixbuf_new_from_file(self.config.execution_path(self.params['deck']))
        
        for j in range(0, 14):
            for i in range(0, 4):
                temp_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(), pb.get_bits_per_sample(),  30,  42)
                pb.copy_area(30*j, 42*i, 30, 42, temp_pb, 0, 0)
                card_images[(ranks[j], suits[i])] = temp_pb
        return(card_images)
#   cards are 30 wide x 42 high

    def split_cards(self, card):
        if card == 'xx': return ('B', 'S')
        return (card[0], card[1].upper())

    def has_cards(self, cards):
        for c in cards:
            if c in set('shdc'): return True
        return False

class Stud_mucked(Aux_Window):
    def __init__(self, hud, config, params):

        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.params  = params    # hash aux params from config

        try:
            site_params = self.config.get_site_parameters(self.hud.site)
            self.hero = site_params['screen_name']
        except:
            self.hero = ''

        self.mucked_list   = Stud_list(self, params, config, self.hero)
        self.mucked_cards  = Stud_cards(self, params, config)
        self.mucked_list.mucked_cards = self.mucked_cards

    def create(self):

        self.container =gtk.Window() 
        self.vbox = gtk.VBox()
        self.container.add(self.vbox)

        self.mucked_list.create(self.vbox)
        self.mucked_cards.create(self.vbox)
        self.container.show_all()

    def update_data(self, new_hand_id, db_connection):
        self.mucked_cards.update_data(new_hand_id, db_connection)
        self.mucked_list.update_data(new_hand_id, db_connection)
        
    def update_gui(self, new_hand_id):
        self.mucked_cards.update_gui(new_hand_id)
        self.mucked_list.update_gui(new_hand_id)
        
class Stud_list:
    def __init__(self, parent, params, config, hero):

        self.parent     = parent
        self.params  = params
        self.config  = config
        self.hero    = hero

    def create(self, container):
#       set up a scrolled window to hold the listbox
        self.container  = container
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.container.add(self.scrolled_window)

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
        pass
#        sel = self.treeview.get_selection()
#        (model, iter)  = sel.get_selected()
#        self.mucked_cards.update_data(model.get_value(iter, 0))
#        self.mucked_cards.update_gui(model.get_value(iter, 0))
        
    def update_data(self, new_hand_id, db_connection):
        """Updates the data needed for the list box."""

#        db_connection = Database.Database(self.config, 'fpdb', '')
        self.winners = db_connection.get_winners_from_hand(new_hand_id)
        pot = 0
        winners = ''
        for player in self.winners.keys():
            pot = pot + int(self.winners[player])
            if not winners == '':
                winners = winners + ", "
            winners = winners + player
        pot_dec = "%.2f" % (float(pot)/100)

        hero_cards = self.get_hero_cards(self.parent.hero, self.parent.hud.cards)
        self.info_row = ((new_hand_id, hero_cards, pot_dec, winners), )

    def get_hero_cards(self, hero, cards):
        """Formats the hero cards for inclusion in the tree."""
        trans = ('0', 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        if hero == '':
            return "xxxxxx"
        else:
#    find the hero's seat from the stat_dict
            for stat in self.parent.hud.stat_dict.itervalues():
                if stat['screen_name'] == hero:
                    return self.parent.hud.cards[stat['seat']][0:6]
        return "xxxxxx"
            
    def update_gui(self, new_hand_id):
        iter = self.liststore.append(self.info_row[0]) 
        sel = self.treeview.get_selection()
        sel.select_iter(iter)

        vadj = self.scrolled_window.get_vadjustment()
        vadj.set_value(vadj.upper)

class Stud_cards:
    def __init__(self, parent, params, config):

        self.parent    = parent
        self.params  = params
        self.config  = config
#        self.db_name = db_name

        self.card_images = self.parent.get_card_images()
        self.seen_cards = {}
        self.grid_contents = {}
        self.eb = {}

        self.rows = 8
        self.cols = 7

    def create(self, container):
        self.container  = container
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
                
        self.container.add(self.grid)

    def update_data(self, new_hand_id, db_connection):
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

    def update_gui(self, new_hand_id):
        self.clear()
        for c, cards in self.parent.hud.cards.iteritems():
            self.grid_contents[(1, c - 1)].set_text(self.get_screen_name(c))
            for i in ((0, cards[0:2]), (1, cards[2:4]), (2, cards[4:6]), (3, cards[6:8]), 
                      (4, cards[8:10]), (5, cards[10:12]), (6, cards[12:14])):
                if not i[1] == "xx":
                    self.seen_cards[(i[0], c - 1)]. \
                        set_from_pixbuf(self.card_images[self.parent.split_cards(i[1])])
##    action in tool tips for 3rd street cards
        for c in (0, 1, 2):
            for r in range(0, self.rows):
                self.eb[(c, r)].set_tooltip_text(self.tips[0])

#    action in tools tips for later streets
        round_to_col = (0, 3, 4, 5, 6)
        for round in range(1, len(self.tips)):
            for r in range(0, self.rows):
                self.eb[(round_to_col[round], r)].set_tooltip_text(self.tips[round])

    def get_screen_name(self, seat_no):
        """Gets and returns the screen name from stat_dict, given seat number."""
        for k in self.parent.hud.stat_dict.keys():
            if self.parent.hud.stat_dict[k]['seat'] == seat_no:
                return self.parent.hud.stat_dict[k]['screen_name']
        return "No Name"

    def clear(self):
        for r in range(0, self.rows):
            self.grid_contents[(1, r)].set_text("             ")
            for c in range(0, 7):
                self.seen_cards[(c, r)].set_from_pixbuf(self.card_images[('B', 'S')])
                self.eb[(c, r)].set_tooltip_text('')

class Flop_Mucked(Aux_Window):
    """Aux_Window class for displaying mucked cards for flop games."""

    def __init__(self, hud, config, params):
        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.params  = params    # dict aux params from config
        self.positions = {}      # dict of window positions
        self.displayed_cards = False
        self.timer_on = False    # bool = Ture if the timeout for removing the cards is on
        self.card_images = self.get_card_images()

    def create(self):
        self.adj = self.hud.adj_seats(0, self.config)
        loc = self.config.get_aux_locations(self.params['name'], int(self.hud.max))
        
        self.m_windows = {}      # windows to put the card images in
        self.eb = {}             # event boxes so we can interact with the mucked cards
        self.seen_cards = {}     # image objects to stash the cards in

        for i in (range(1, self.hud.max + 1) + ['common']):           
            if i == 'common':
                (x, y) = self.params['layout'][self.hud.max].common
            else:
                (x, y) = loc[self.adj[i]]
            self.m_windows[i] = gtk.Window()
            self.m_windows[i].set_decorated(False)
            self.m_windows[i].set_property("skip-taskbar-hint", True)
            self.m_windows[i].set_transient_for(self.hud.main_window)
            self.m_windows[i].set_focus_on_map(False)
            self.eb[i] = gtk.EventBox()
            self.eb[i].connect("button_press_event", self.button_press_cb)
            self.m_windows[i].add(self.eb[i])
            self.seen_cards[i] = gtk.image_new_from_pixbuf(self.card_images[('B', 'H')])
            self.eb[i].add(self.seen_cards[i])
            self.m_windows[i].move(int(x) + self.hud.table.x, int(y) + self.hud.table.y)
            self.positions[i] = (int(x) + self.hud.table.x, int(y) + self.hud.table.y)
            self.m_windows[i].set_opacity(float(self.params['opacity']))
            self.m_windows[i].show_all()
            self.m_windows[i].hide()

    def update_gui(self, new_hand_id):
        """Prepare and show the mucked cards."""
        if self.displayed_cards:
            self.hide_mucked_cards()
            self.displayed_cards = False
        for (i, cards) in self.hud.cards.iteritems():
            if self.has_cards(cards):
#    scratch is a working pixbuf, used to assemble the image
                scratch = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8,
                                         int(self.params['card_wd'])*len(cards)/2,
                                         int(self.params['card_ht']))
                x = 0 # x coord where the next card starts in scratch
                for card in [cards[k:k+2] for k in xrange(0, len(cards), 2)]:
#    concatenate each card image to scratch
                    self.card_images[self.split_cards(card)].copy_area(0, 0, 
                                            int(self.params['card_wd']), int(self.params['card_ht']),
                                            scratch, x, 0)
                    x = x + int(self.params['card_wd'])
                self.seen_cards[i].set_from_pixbuf(scratch)
#                self.m_windows[i].show_all()
                self.m_windows[i].resize(1,1)
                self.m_windows[i].present()
                self.m_windows[i].move(self.positions[i][0], self.positions[i][1])   # here is where I move back
                self.displayed_cards = True

        for stats in self.hud.stat_dict.itervalues():
            self.eb[stats['seat']].set_tooltip_text(stats['screen_name'])

        if self.displayed_cards and float(self.params['timeout']) > 0:
            self.timer_on = True
            gobject.timeout_add(int(1000*float(self.params['timeout'])), self.timed_out)

    def destroy(self):
        """Destroy all of the mucked windows."""
        for w in self.m_windows.values():
            w.destroy()

    def timed_out(self):
#    this is the callback from the timeout

#    if timer_on is False the user has cancelled the timer with a click
#    so just return False to cancel the timer
        if not self.timer_on:
            return False
        else:
            self.hide_mucked_cards()
            return False

    def hide_mucked_cards(self):
        """Hide the mucked card windows."""
        for (i, w) in self.m_windows.iteritems():
            self.positions[i] = w.get_position()
            w.hide()
            self.displayed_cards = False

    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the event boxes."""

#    shift-any button exposes all the windows and turns off the timer
        if event.state & gtk.gdk.SHIFT_MASK:
            self.timer_on = False
            self.expose_all()
            return

        if event.button == 3:   # right button event
            pass

        elif event.button == 2:   # middle button event
            if self.timer_on == True:
                self.timer_on = False
            else:
                self.timer_on = False
                self.hide_mucked_cards()

        elif event.button == 1:   # left button event
            window = widget.get_parent()
            window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def expose_all(self):
        for (i, cards) in self.hud.cards.iteritems():
            self.m_windows[i].present()
            self.m_windows[i].move(self.positions[i][0], self.positions[i][1])   # here is where I move back
            self.displayed_cards = True

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""
        new_locs = {}
        print "adj =", self.adj
        for (i, pos) in self.positions.iteritems():
            if i != 'common':
                new_locs[self.adj[int(i)]] = (pos[0] - self.hud.table.x, pos[1] - self.hud.table.y)
            else:
                new_locs[i] = (pos[0] - self.hud.table.x, pos[1] - self.hud.table.y)
        print "old locations =", self.params['layout'][self.hud.max]
        print "saving locations =", new_locs
        self.config.edit_aux_layout(self.params['name'], self.hud.max, locations = new_locs)

if __name__== "__main__":
    
    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()             # used only for testing

    def process_new_hand(source, condition, db_connection):  #callback from stdin watch -- testing only
#    there is a new hand_id to be processed
#    just read it and pass it to update
        new_hand_id = sys.stdin.readline()
        new_hand_id = new_hand_id.rstrip()  # remove trailing whitespace
        m.update_data(new_hand_id, db_connection)
        m.update_gui(new_hand_id)
        return(True)

    config = Configuration.Config()
    db_connection = Database.Database(config, 'fpdb', '')
    main_window = gtk.Window()
    main_window.set_keep_above(True)
    main_window.connect("destroy", destroy)

    aux_to_call = "stud_mucked"
    aux_params = config.get_aux_parameters(aux_to_call)
    m = eval("%s(main_window, None, config, aux_params)" % aux_params['class'])
    
    s_id = gobject.io_add_watch(sys.stdin, gobject.IO_IN, process_new_hand, db_connection)
    gtk.main()
