#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aux_Base.py

Some base classes for Aux_Hud, Mucked, and other aux-handlers.
These classes were previously in Mucked, and have been split away
for clarity
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
_ = L10n.get_translation()
#    to do

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QWidget

#   FPDB
import Card


# This holds all card images in a nice lookup table. One instance is
# populated on the first run of Aux_Window.get_card_images() and all
# subsequent uses will have the same instance available.
deck = None

# This allows for a performance gain. Loading and parsing 53 SVG cards
# takes some time. If that is done at the first access of
# Aux_Window.get_card_images(), it can add a delay of several seconds.
# A pre-populated deck on the other hand grants instant access.


class Aux_Window(object):
    def __init__(self, hud, params, config):
        self.hud     = hud
        self.params  = params
        self.config  = config

#   Override these methods as needed
    def update_data(self, *args): pass
    def update_gui(self, *args):  pass
    def create(self, *args):      pass
    def save_layout(self, *args): pass
    def move_windows(self, *args): pass
    def destroy(self):
        try:
            self.container.destroy()
        except:
            pass

############################################################################
#    Some utility routines useful for Aux_Windows
#
    # Returns the number of places where cards were shown. This can be N
    # players + common cards
    # XXX XXX: AAAAAGGGGGGHHHHHHHHHHHHHH!
    # XXX XXX: 'cards' is a dictionary with EVERY INVOLVED SEAT included;
    # XXX XXX: in addition, the unknown/unshown cards are marked with
    # zeroes, not None
    def count_seats_with_cards(self, cards):
        """Returns the number of seats with shown cards in the list."""
        n = 0
        for seat, cards_tuple in cards.items():
            if seat != 'common' and cards_tuple[0] != 0:
                n += 1
        return n

    def get_id_from_seat(self, seat):
        """Determine player id from seat number, given stat_dict."""
        
        # hh_seats is a list of the actual seat numbers used in the hand history.
        #  Some sites (e.g. iPoker) miss out some seat numbers if max is <10,
        #  e.g. iPoker 6-max uses seats 1,3,5,6,8,10 NOT 1,2,3,4,5,6
        seat = self.hud.layout.hh_seats[seat]
        for id, dict in self.hud.stat_dict.iteritems():
            if seat == dict['seat']:
                return id
        return None
        
class Seat_Window(QWidget):
    def __init__(self, aw = None, seat = None):
        super(Seat_Window, self).__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus) # FIXME acceptfocus?  splashscreen?
        self.lastPos = None
        self.aw = aw
        self.seat = seat
        self.resize(10,10)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.button_press_left(event)
        elif event.button() == Qt.MiddleButton:
            self.button_press_middle(event)
        elif event.button() == Qt.RightButton:
            self.button_press_right(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.button_release_left(event)
        elif event.button() == Qt.MiddleButton:
            self.button_release_middle(event)
        elif event.button() == Qt.RightButton:
            self.button_release_right(event)

    def button_press_left(self, event):
        self.lastPos = event.globalPos()
    def button_press_middle(self, event): pass #subclass will define this
    def button_press_right(self, event):  pass #subclass will define this

    def mouseMoveEvent(self, event):
        if self.lastPos is not None:
            self.move(self.pos() + event.globalPos() - self.lastPos)
            self.lastPos = event.globalPos()

    def button_release_left(self, event):
        self.lastPos = None
        self.aw.configure_event_cb(self, self.seat)
    def button_release_middle(self, event): pass #subclass will define this
    def button_release_right(self, event):  pass #subclass will define this
    
    def create_contents(self, *args): pass
    def update_contents(self, *args): pass
    
class Aux_Seats(Aux_Window):
    """A super class to display an aux_window or a stat block at each seat."""

    def __init__(self, hud, config, params):
        super(Aux_Seats, self).__init__(hud, params, config)
        self.positions = {}      # dict of window positions. normalised for favourite seat and offset
                                 # but _not_ offset to the absolute screen position
        self.displayed = False   # the seat windows are displayed
        self.uses_timer = False  # the Aux_seats object uses a timer to control hiding
        self.timer_on = False    # bool = Ture if the timeout for removing the cards is on

        self.aw_class_window = Seat_Window # classname to be used by the aw_class_window

#    placeholders that should be overridden--so we don't throw errors
    def create_contents(self): pass
    def create_common(self, x, y): pass
    def update_contents(self): pass
    
    def resize_windows(self): 
        #Resize calculation has already happened in HUD_main&hud.py
        # refresh our internal map to reflect these changes
        for i in (range(1, self.hud.max + 1)):
            self.positions[i] = self.hud.layout.location[self.adj[i]]
        self.positions["common"] = self.hud.layout.common
        # and then move everything to the new places
        self.move_windows()

    def move_windows(self):
        for i in (range(1, self.hud.max + 1)):
            self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                            self.positions[i][1] + self.hud.table.y)

        self.m_windows["common"].move(self.hud.layout.common[0] + self.hud.table.x,
                                self.hud.layout.common[1] + self.hud.table.y)
        
    def create(self):
        
        self.adj = self.adj_seats()
        self.m_windows = {}      # windows to put the card/hud items in

        for i in (range(1, self.hud.max + 1) + ['common']):   
            if i == 'common':
                #    The common window is different from the others. Note that it needs to 
                #    get realized, shown, topified, etc. in create_common
                #    self.hud.layout.xxxxx is updated here after scaling, to ensure
                #    layout and positions are in sync
                (x, y) = self.hud.layout.common
                self.m_windows[i] = self.create_common(x, y)
                self.hud.layout.common = self.create_scale_position(x, y)
            else:
                (x, y) = self.hud.layout.location[self.adj[i]]
                self.m_windows[i] = self.aw_class_window(self, i)
                self.positions[i] = self.create_scale_position(x, y)
                self.m_windows[i].move(self.positions[i][0] + self.hud.table.x,
                                self.positions[i][1] + self.hud.table.y)
                self.hud.layout.location[self.adj[i]] = self.positions[i]
                if self.params.has_key('opacity'):
                    self.m_windows[i].setWindowOpacity(float(self.params['opacity']))

            # main action below - fill the created window with content
            #    the create_contents method is supplied by the subclass
            #      for hud's this is probably Aux_Hud.stat_window
            self.create_contents(self.m_windows[i], i)

            self.m_windows[i].create() # ensure there is a native window handle for topify
            self.hud.table.topify(self.m_windows[i])
            if not self.uses_timer:
                self.m_windows[i].show()
                
        self.hud.layout.height = self.hud.table.height
        self.hud.layout.width = self.hud.table.width
        

    def create_scale_position(self, x, y):
        # for a given x/y, scale according to current height/wid vs. reference
        # height/width
        # This method is needed for create (because the table may not be 
        # the same size as the layout in config)
        
        # any subsequent resizing of this table will be handled through
        # hud_main.idle_resize

        x_scale = (1.0 * self.hud.table.width / self.hud.layout.width)
        y_scale = (1.0 * self.hud.table.height / self.hud.layout.height)
        return (int(x * x_scale), int(y * y_scale))

        
    def update_gui(self, new_hand_id):
        """Update the gui, LDO."""
        for i in self.m_windows.keys():
            self.update_contents(self.m_windows[i], i)
        #reload latest block positions, in case another aux has changed them
        #these lines allow the propagation of block-moves across
        #the hud and mucked handlers for this table
        self.resize_windows()

#   Methods likely to be of use for any Seat_Window implementation
    def destroy(self):
        """Destroy all of the seat windows."""
        try:
            for i in self.m_windows.keys():
                self.m_windows[i].destroy()
                del(self.m_windows[i])
        except AttributeError:
            pass

#   Methods likely to be useful for mucked card windows (or similar) only
    def hide(self):
        """Hide the seat windows."""
        for (i, w) in self.m_windows.iteritems():
            if w is not None: w.hide()
        self.displayed = False

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""
        """ this method is  overridden in the specific aux because
        the HUD's controlling stat boxes set the seat positions and
        the mucked card aux's control the common location
        This class method would only be valid for an aux which has full control
        over all seat and common locations
        """

        log.error(_("Aux_Seats.save_layout called - this shouldn't happen"))
        log.error(_("save_layout method should be handled in the aux"))


    def configure_event_cb(self, widget, i):
        """
        This method updates the current location for each statblock.
        This method is needed to record moves for an individual block.
        Move/resize also end up in here due to it being a configure.
        This is not optimal, but isn't easy to work around. fixme.
        """
        if (i): 
            new_abs_position = widget.pos() #absolute value of the new position
            new_position = (new_abs_position.x()-self.hud.table.x, new_abs_position.y()-self.hud.table.y)
            self.positions[i] = new_position     #write this back to our map
            if i != "common":
                self.hud.layout.location[self.adj[i]] = new_position #update the hud-level dict, so other aux can be told
            else:
                self.hud.layout.common = new_position

    def adj_seats(self):
        # determine how to adjust seating arrangements, if a "preferred seat" is set in the hud layout configuration
        #  Need range here, not xrange -> need the actual list
    
        adj = range(0, self.hud.max + 1) # default seat adjustments = no adjustment
        
        #   does the user have a fav_seat? if so, just get out now
        if self.hud.site_parameters["fav_seat"][self.hud.max] == 0:
            return adj

        # find the hero's actual seat
        
        actual_seat = None
        for key in self.hud.stat_dict:
            if self.hud.stat_dict[key]['screen_name'] == self.config.supported_sites[self.hud.site].screen_name:
                # Seat from stat_dict is the seat num recorded in the hand history and database
                # For tables <10-max, some sites omit some seat nums (e.g. iPoker 6-max uses 1,3,5,6,8,10)
                # The seat nums in the hh from the site are recorded in config file for each layout, and available
                # here as the self.layout.hh_seats list
                #    (e.g. for iPoker - [None,1,3,5,6,8,10];
                #      for most sites-  [None, 1,2,3,4,5,6]
                # we need to match 'seat' from hand history with the postion in the list, as the hud
                #  always numbers its stat_windows using consecutive numbers (e.g. 1-6)

                for i in range(1, self.hud.max + 1):
                    if self.hud.layout.hh_seats[i] == self.hud.stat_dict[key]['seat']:
                        actual_seat = i
                        break

        if not actual_seat: # this shouldn't happen because we don't create huds if the hero isn't seated.
            log.error(_("Error finding hero seat."))
            return adj
                
        for i in xrange(0, self.hud.max + 1):
            j = actual_seat + i
            if j > self.hud.max:
                j = j - self.hud.max
            adj[j] = self.hud.site_parameters["fav_seat"][self.hud.max] + i
            if adj[j] > self.hud.max:
                adj[j] = adj[j] - self.hud.max

        return adj
