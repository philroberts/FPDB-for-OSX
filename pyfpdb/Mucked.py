#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008-2012,  Ray E. Barker
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
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import gtk
import gobject

#    FreePokerTools modules
import Card
import Aux_Base



# Utility routine to get the number of valid cards in the card tuple
def valid_cards(ct):
    n = 0
    for c in ct:
        if c != 0:
            n += 1
    return n

        
class Stud_mucked(Aux_Base.Aux_Window):
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

        self.container = gtk.Window() 
        self.vbox = gtk.VBox()
        self.container.add(self.vbox)
        self.container.set_title(self.hud.table.name)

        self.mucked_list.create(self.vbox)
        self.mucked_cards.create(self.vbox)
        self.container.show_all()

    def update_data(self, new_hand_id, db_connection):
#    uncomment next line when action is available in the db
#        self.mucked_cards.update_data(new_hand_id, db_connection)
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
                    return Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][0]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][1]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][2])
        return "xxxxxx"
            
    def update_gui(self, new_hand_id):
        iter = self.liststore.append(self.info_row[0]) 
        sel = self.treeview.get_selection()
        #sel.select_iter(iter)

        vadj = self.scrolled_window.get_vadjustment()
        #vadj.set_value(vadj.upper)

class Stud_cards:
    def __init__(self, parent, params, config):

        self.parent    = parent
        self.params  = params
        self.config  = config
#        self.db_name = db_name

        self.card_images = self.parent.hud.parent.deck.get_all_card_images()
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
                # Start by creating a box of nothing but card backs
                self.seen_cards[(c, r)] = gtk.image_new_from_pixbuf(self.card_images[0].copy())
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
            if c == 'common': continue
            self.grid_contents[(1, c - 1)].set_text(self.get_screen_name(c))
            for i in ((0, cards[0]), (1, cards[1]), (2, cards[2]), (3, cards[3]), 
                      (4, cards[4]), (5, cards[5]), (6, cards[6])):
                if not i[1] == 0:
                    # Pixmaps are stored in dict with rank+suit keys
                    (_rank, _suit) = Card.valueSuitFromCard(i[1])
                    _rank = Card.card_map[_rank]
                    px = self.card_images[_suit][_rank].copy()
                    self.seen_cards[(i[0], c - 1)].set_from_pixbuf(px)
##    action in tool tips for 3rd street cards
        for c in (0, 1, 2):
            for r in range(0, self.rows):
                #self.eb[(c, r)].set_tooltip_text(self.tips[0])
                pass

#    action in tools tips for later streets
        round_to_col = (0, 3, 4, 5, 6)
        #for round in range(1, len(self.tips)):
        #    for r in range(0, self.rows):
        #        self.eb[(round_to_col[round], r)].set_tooltip_text(self.tips[round])

    def get_screen_name(self, seat_no):
        """Gets and returns the screen name from stat_dict, given seat number."""
        for k in self.parent.hud.stat_dict.keys():
            if self.parent.hud.stat_dict[k]['seat'] == seat_no:
                return self.parent.hud.stat_dict[k]['screen_name']
        return _("No Name")

    def clear(self):
        for r in range(0, self.rows):
            self.grid_contents[(1, r)].set_text("             ")
            for c in range(0, 7):
                # Start by creating a box of nothing but card backs
                self.seen_cards[(c, r)].set_from_pixbuf(self.card_images[0].copy())
                self.eb[(c, r)].set_tooltip_text('')

class Flop_Mucked(Aux_Base.Aux_Seats):
    """Aux_Window class for displaying mucked cards for flop games."""

    def __init__(self, hud, config, params):
        super(Flop_Mucked, self).__init__(hud, config, params)
        self.card_images = self.hud.parent.deck.get_all_card_images()
        self.card_height = self.hud.parent.hud_params["card_ht"]
        self.card_width = self.hud.parent.hud_params["card_wd"]
        self.uses_timer = True  # this Aux_seats object uses a timer to control hiding

    def create_common(self, x, y):
        "Create the window for the board cards and do the initial population."
        w = self.aw_class_window(self, "common")
        w.set_decorated(False)
        w.set_property("skip-taskbar-hint", True)
        w.set_focus_on_map(False)
        w.set_focus(None)
        w.set_accept_focus(False)
        w.connect("configure_event", self.configure_event_cb, "common")
        self.positions["common"] = self.create_scale_position(x, y)
        w.move(self.positions["common"][0]+ self.hud.table.x,
                self.positions["common"][1]+ self.hud.table.y)
        if self.params.has_key('opacity'):
            w.set_opacity(float(self.params['opacity']))
        return w

    def create_contents(self, container, i):
        """Create the widgets for showing the contents of the Aux_seats window."""
        container.eb = gtk.EventBox()
        container.eb.connect("button_press_event", self.button_press_cb, i)
        container.add(container.eb)
        container.seen_cards = gtk.image_new_from_pixbuf(self.card_images[0].copy())
        container.eb.add(container.seen_cards)

    # NOTE: self.hud.cards is a dictionary of:
    # { seat_num: (card, card, [...]) }
    #
    # Thus the individual hands (cards for seat) are tuples
    def update_contents(self, container, i):

        if not self.hud.cards.has_key(i): return
        
        cards = self.hud.cards[i]
        # Here we want to know how many cards the given seat showed;
        # board is considered a seat, and has the id 'common'
        # 'cards' on the other hand is a tuple. The format is:
        # (card_num, card_num, ...)
        n_cards = valid_cards(cards)
        if n_cards > 1:
#    scratch is a working pixbuf, used to assemble the image
            scratch = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,
                                        has_alpha=True, bits_per_sample=8,
                                        width=int(self.card_width)*n_cards,
                                        height=int(self.card_height))
            x = 0 # x coord where the next card starts in scratch
            for card in cards:
#    concatenate each card image to scratch
                # flop game never(?) has unknown cards.
                # FIXME: if "show one and fold" ever becomes an option,
                # this needs to be changed
                if card == None or card ==0:
                    break

                # This gives us the card symbol again
                (_rank, _suit) = Card.valueSuitFromCard(card)
                _rank = Card.card_map[_rank]
                # We copy the image data. Technically we __could__ use
                # the pixmap directly but it seems there are some subtle
                # races and explicitly creating a new pixbuf seems to
                # work around most of them.
                #
                # We also should not use copy_area() but it is far
                # easier to work with than _render_to_drawable()
                px = self.card_images[_suit][_rank].copy()
                px.copy_area(0, 0,
                        px.get_width(), px.get_height(),
                        scratch, x, 0)
                x += px.get_width()
                
            if container is not None:
                container.seen_cards.set_from_pixbuf(scratch)
                container.resize(1,1)
                container.move(self.positions[i][0] + self.hud.table.x,
                            self.positions[i][1] + self.hud.table.y)   # here is where I move back
                container.show()

            self.displayed = True
            if i != "common":
                id = self.get_id_from_seat(i)
                # sc: had KeyError here with new table so added id != None test as a guess:
                if id is not None:
                    self.m_windows[i].eb.set_tooltip_text(self.hud.stat_dict[id]['screen_name'])
                    
    def save_layout(self, *args):
        """Save new common position back to the layout element in the config file."""
        new_locs = {}
        for (i, pos) in self.positions.iteritems():
            if i == 'common':
                new_locs[i] = ((pos[0]), (pos[1]))
            else:
                #seat positions are owned by the aux controlling the stat block
                # we share the locations from that aux, so don't write-back their
                # locations here
                pass

        self.config.save_layout_set(self.hud.layout_set, self.hud.max, new_locs, width=None, height=None)

    def update_gui(self, new_hand_id):
        """Prepare and show the mucked cards."""
        if self.displayed: self.hide()
#   See how many players showed a hand. Skip if only 1 shows (= hero)
        n_sd = self.count_seats_with_cards(self.hud.cards)
        if n_sd < 2: 
            return

        super(Flop_Mucked, self).update_gui(new_hand_id)

        if self.displayed and float(self.params['timeout']) > 0:
            self.timer_on = True
            gobject.timeout_add(int(1000*float(self.params['timeout'])), self.timed_out)

    def timed_out(self):
#    this is the callback from the timeout
#    if timer_on is False the user has cancelled the timer with a click
#    so just return False to cancel the timer
        if not self.timer_on:
            return False
        else:
            self.hide()
            return False

    def button_press_cb(self, widget, event, i, *args):
        """Handle button clicks in the event boxes."""

        if event.button == 2:   # middle button event, hold display (do not timeout)
            if self.timer_on == True:  self.timer_on = False
            else: self.timer_on = False;  self.hide()
        elif event.button == 1 and i == "common":   # left button event (move)
            # firstly, cancel timer, otherwise block becomes locked if move event
            #   is happening when timer eventually times-out
            if self.timer_on == True:  self.timer_on = False
            #only allow move on "common" element - seat block positions are 
            # determined by aux_hud, not mucked card display
            window = widget.get_parent()
            window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def expose_all(self):
        for (i, cards) in self.hud.cards.iteritems():
            self.m_windows[i].show()
            self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                                self.positions[i][1] + self.hud.table.y)   # here is where I move back
            self.displayed = True

