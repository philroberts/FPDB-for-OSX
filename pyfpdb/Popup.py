#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Popup.py

Popup windows for the HUD.
"""
#    Copyright 2011-2012,  Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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

#    FreePokerTools modules
import Stats

class Popup(gtk.Window):

    def __init__(self, seat = None, stat_dict = None, win = None, pop = None, hand_instance = None):
        self.seat = seat
        self.stat_dict = stat_dict
        self.win = win
        self.pop = pop
        self.hand_instance = hand_instance
        super(Popup, self).__init__()
        

        self.set_destroy_with_parent(True)

#    Most (all?) popups want a label and eb, so let's create them here
        self.eb = gtk.EventBox()
        self.lab = gtk.Label()
        self.add(self.eb)
        self.eb.add(self.lab)
        self.eb.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
        self.eb.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)

#    They will also usually want to be undecorated, default colors, etc.
        self.set_decorated(False)
        self.set_property("skip-taskbar-hint", True)
        self.set_focus_on_map(False)
        self.set_focus(None)
        self.set_transient_for(win)
        self.connect("button_press_event", self.button_press_cb)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.create()

#    Every popup window needs one of these
    def button_press_cb(self, widget, event, *args):
        """Handle button clicks on the popup window."""
#    Any button click gets rid of popup.
        self.destroy_pop()

#    Override these methods to make a popup
    def create(self):   pass
    def destroy_pop(self):
        self.destroy()

class default(Popup):

    def create(self):
        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()
            
        text,tip_text = "",""
        for stat in self.pop.pu_stats:
            number = Stats.do_stat(
                self.stat_dict, player = int(player_id),stat = stat, hand_instance = self.hand_instance)
            text += number[3] + "\n"
            tip_text += number[5] + " " + number[4] + "\n"
        
        #trim final \n
        tip_text = tip_text[:-1]
        text = text[:-1]
        
        self.lab.set_text(text)
        Stats.do_tip(self.lab, tip_text)
        self.lab.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
        self.lab.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
        self.show_all()
