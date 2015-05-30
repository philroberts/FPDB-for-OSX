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

import L10n
_ = L10n.init_translation()

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

from PyQt5.QtCore import QObject
from PyQt5.QtGui import (QPainter, QPixmap, QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QGridLayout, QLabel, QTableView,
                             QVBoxLayout, QWidget)

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

        self.container = QWidget()
        self.vbox = QVBoxLayout()
        self.container.setLayout(self.vbox)
        self.container.setWindowTitle(self.hud.table.name)

        self.mucked_list.create(self.vbox)
        self.mucked_cards.create(self.vbox)
        self.container.show()

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
        self.container  = container

        self.treeview = QTableView()
        self.liststore = QStandardItemModel(0, 4, self.treeview)
        self.treeview.setModel(self.liststore)
        self.liststore.setHorizontalHeaderLabels(['HandID', 'Cards', 'Net', 'Winner'])
        self.treeview.verticalHeader().hide()
        self.container.addWidget(self.treeview)
        
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

        hero_cards = self.get_hero_cards(self.parent.hero)
        self.info_row = ((new_hand_id, hero_cards, pot_dec, winners), )

    def get_hero_cards(self, hero):
        """Formats the hero cards for inclusion in the table."""
        if hero == '':
            return "xxxxxx"
        else:
            # find the hero's seat from the stat_dict
            for stat in self.parent.hud.stat_dict.itervalues():
                if stat['screen_name'] == hero:
                    return Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][0]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][1]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][2])
        return "xxxxxx"
            
    def update_gui(self, new_hand_id):
        self.liststore.appendRow(map(QStandardItem, self.info_row[0]))
        self.treeview.resizeColumnsToContents()
        self.treeview.horizontalHeader().setStretchLastSection(True)

class Stud_cards:
    def __init__(self, parent, params, config):

        self.parent    = parent
        self.params  = params
        self.config  = config

        self.card_images = self.parent.hud.parent.deck.get_all_card_images()
        self.grid_contents = {}
        self.eb = {}

        self.rows = 8
        self.cols = 7

    def create(self, container):
        self.container  = container
        self.grid = QGridLayout()

        for r in range(0, self.rows):
            for c in range(0, self.cols):
                # Start by creating a box of nothing but card backs
                self.eb[(c, r)]= QLabel()
                self.eb[(c, r)].setPixmap(self.card_images[0])

#    set up the contents for the cells
        for r in range(0, self.rows):
            self.grid_contents[( 0, r)] = QLabel("%d" % (r + 1))
            self.grid_contents[( 1, r)] = QLabel("player %d" % (r + 1))
            self.grid_contents[( 4, r)] = QLabel("-")
            self.grid_contents[( 9, r)] = QLabel("-")
            self.grid_contents[( 2, r)] = self.eb[( 0, r)]
            self.grid_contents[( 3, r)] = self.eb[( 1, r)]
            self.grid_contents[( 5, r)] = self.eb[( 2, r)]
            self.grid_contents[( 6, r)] = self.eb[( 3, r)]
            self.grid_contents[( 7, r)] = self.eb[( 4, r)]
            self.grid_contents[( 8, r)] = self.eb[( 5, r)]
            self.grid_contents[(10, r)] = self.eb[( 6, r)]
            
#    add the cell contents to the table
        for c in range(0, self.cols + 4):
            for r in range(0, self.rows):
                self.grid.addWidget(self.grid_contents[(c, r)], r, c)

        self.container.addLayout(self.grid)

    def update_data(self, new_hand_id, db_connection):
        self.tips = []
        action = db_connection.get_action_from_hand(new_hand_id)
        print action
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
            self.grid_contents[(1, c - 1)].setText(self.get_screen_name(c))
            for i in ((0, cards[0]), (1, cards[1]), (2, cards[2]), (3, cards[3]), 
                      (4, cards[4]), (5, cards[5]), (6, cards[6])):
                if not i[1] == 0:
                    # Pixmaps are stored in dict with rank+suit keys
                    (_rank, _suit) = Card.valueSuitFromCard(i[1])
                    _rank = Card.card_map[_rank]
                    self.eb[(i[0], c - 1)].setPixmap(self.card_images[_suit][_rank])
        #    action in tool tips for 3rd street cards
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
            self.grid_contents[(1, r)].setText("             ")
            for c in range(0, 7):
                # Start by creating a box of nothing but card backs
                self.eb[(c, r)].setPixmap(self.card_images[0])

class Flop_Mucked(Aux_Base.Aux_Seats, QObject):
    """Aux_Window class for displaying mucked cards for flop games."""

    def __init__(self, hud, config, params):
        super(Flop_Mucked, self).__init__(hud, config, params)
        QObject.__init__(self)
        self.card_images = self.hud.parent.deck.get_all_card_images()
        self.card_height = self.hud.parent.hud_params["card_ht"]
        self.card_width = self.hud.parent.hud_params["card_wd"]
        self.uses_timer = True  # this Aux_seats object uses a timer to control hiding

    def create_common(self, x, y):
        "Create the window for the board cards and do the initial population."
        w = self.aw_class_window(self, "common")
        self.positions["common"] = self.create_scale_position(x, y)
        w.move(self.positions["common"][0]+ self.hud.table.x,
                self.positions["common"][1]+ self.hud.table.y)
        if 'opacity' in self.params:
            w.setWindowOpacity(float(self.params['opacity']))
        return w

    def create_contents(self, container, i):
        """Create the widgets for showing the contents of the Aux_seats window."""
        container.seen_cards = QLabel()
        container.seen_cards.setPixmap(self.card_images[0])
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().addWidget(container.seen_cards)

    # NOTE: self.hud.cards is a dictionary of:
    # { seat_num: (card, card, [...]) }
    #
    # Thus the individual hands (cards for seat) are tuples
    def update_contents(self, container, i):
        if type(i) is int:
            hist_seat = self.hud.layout.hh_seats[i]
        else:
            hist_seat = i
        if hist_seat not in self.hud.cards: return
        
        cards = self.hud.cards[hist_seat]
        # Here we want to know how many cards the given seat showed;
        # board is considered a seat, and has the id 'common'
        # 'cards' on the other hand is a tuple. The format is:
        # (card_num, card_num, ...)
        n_cards = valid_cards(cards)
        if n_cards > 1:
            # scratch is a working pixmap, used to assemble the image
            scratch = QPixmap(int(self.card_width) * n_cards,
                              int(self.card_height))
            painter = QPainter(scratch)
            x = 0 # x coord where the next card starts in scratch
            for card in cards:
                # concatenate each card image to scratch
                # flop game never(?) has unknown cards.
                # FIXME: if "show one and fold" ever becomes an option,
                # this needs to be changed
                if card is None or card == 0:
                    break

                # This gives us the card symbol again
                (_rank, _suit) = Card.valueSuitFromCard(card)
                _rank = Card.card_map[_rank]
                px = self.card_images[_suit][_rank]
                painter.drawPixmap(x, 0, px)
                x += px.width()
                
            painter.end()
            if container is not None:
                container.seen_cards.setPixmap(scratch)
                container.resize(1,1)
                container.move(self.positions[i][0] + self.hud.table.x,
                            self.positions[i][1] + self.hud.table.y)   # here is where I move back
                container.show()

            self.displayed = True
            if i != "common":
                id = self.get_id_from_seat(i)
                if id is not None:
                    self.m_windows[i].setToolTip(self.hud.stat_dict[id]['screen_name'])
                    
    def save_layout(self, *args):
        """Save new common position back to the layout element in the config file."""
        new_locs = {}
        for (i, pos) in self.positions.iteritems():
            if i == 'common':
                new_locs[i] = ((pos[0]), (pos[1]))
            else:
                # seat positions are owned by the aux controlling the stat block
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
            self.startTimer(int(1000*float(self.params['timeout'])))

    def timerEvent(self, event):
        self.killTimer(event.timerId())
        if self.timer_on:
            self.hide()

    def button_press_cb(self, widget, event, i, *args):
        """Handle button clicks in the event boxes."""

        if event.button == 2:   # middle button event, hold display (do not timeout)
            if self.timer_on:  self.timer_on = False
            else: self.timer_on = False;  self.hide()
        elif event.button == 1 and i == "common":   # left button event (move)
            # firstly, cancel timer, otherwise block becomes locked if move event
            #   is happening when timer eventually times-out
            if self.timer_on:  self.timer_on = False
            # only allow move on "common" element - seat block positions are
            # determined by aux_hud, not mucked card display
            window = widget.get_parent()
            window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def expose_all(self):
        for i in self.hud.cards:
            self.m_windows[i].show()
            self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                                   self.positions[i][1] + self.hud.table.y)
            self.displayed = True

