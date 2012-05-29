#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hello.py

Hello World demostration for Aux_Window.
"""
#    Copyright 2009-2012, Ray E. Barker
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
#    add another class that demonstrates querying the db

# when actually used all user-visible strings should be surrounded by _() as usual

#    Standard Library modules
import sys

#    pyGTK modules
import pygtk
import gtk
import gobject
import L10n
_ = L10n.get_translation()

#    FreePokerTools modules
from Aux_Base import Aux_Window
from Aux_Base import Seat_Window
from Aux_Base import Aux_Seats

class Hello(Aux_Window):
    """A 'Hello World' Aux_Window demo."""
    def create(self):
        print ("creating Hello")
#    This demo simply creates a label in a window.
        self.container = gtk.Window()
        self.container.add(gtk.Label("Hello World"))
#    and shows it. There is no functionality.
        self.container.show_all()

class Hello_plus(Aux_Window):
    """A slightly more complex 'Hello World demo."""
    def __init__(self, hud, config, params):
        """Initialize a new aux_window object."""
#    Initialize the aux_window object. Do not interact with the gui
#    in this function.
        self.hud        = hud          # hud object that this aux window supports
        self.config     = config       # configuration object for this aux window to use
        self.params     = params       # hash aux params from config

        self.hands_played = 0          # initialize the hands played counter

#    get the site we are playing from the HUD
        self.site = hud.site
        print "site =", hud.site # print it to the terminal, to make sure

#    now get our screen name for that site from the configuration
#    wrap it in a try/except in case screen name isn't set up in the config file
        try:
            site_params = self.config.get_site_parameters(self.hud.site)
            self.hero = site_params['screen_name']
        except:
            self.hero = 'YOUR NAME HERE'
        print "hero =", self.hero


    def create(self):
        """Creates the gui."""
        self.container = gtk.Window()               # create a gtk window for our container
        self.label = gtk.Label("")                  # create a blank label to write in update_gui
        self.container.add(self.label)              # add it to our container
        self.container.show_all()                   # show the container and its contents

    def update_data(self, new_hand_id, db_connection):
        """Increment the hands.played attribute."""
#    This function will be called from the main program, in a thread separate from 
#    the gui. Therefore complex calculations can be done without slowing down the
#    HUD. Long-running calculations will delay the appearance or updating of the HUD.
#    This function should NOT interact with the gui--that will cause unpredictable 
#    results on some systems.

#    This long running calculation is incrementing the number of hands played.
        self.hands_played = self.hands_played + 1

    def update_gui(self, new_hand_id):
        """Update the aux_window gui."""
#    This function runs inside the gui thread and should only be used for
#    interacting with the gui. Long-running calculations should not be done
#    in this function--they will prevent HUD interaction until they are 
#    complete.

#    Here, we just update the label in our aux_window from the number of
#    hands played that was updated in the "update_data()" function.
        self.label.set_text(("Hello %s\nYou have played %d hands\n on %s.") % (self.hero, self.hands_played, self.site))

class Hello_Seats(Aux_Seats):
    """A 'Hello World' Seat_Window demo."""

    def create_contents(self, container, i):
        container.label = gtk.Label("empty")
        container.add(container.label)
        container.show_all()

    def update_contents(self, container, i):
        if i == "common": return
        id = self.get_id_from_seat(i)
        if id == None:
            container.label.set_text("empty")
        else:
            container.label.set_text("player = %s" % self.hud.stat_dict[id]['screen_name'])
