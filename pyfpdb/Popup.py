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

    def __init__(self, seat = None, stat_dict = None, win = None, pop = None, hand_instance = None, config = None, parent_popup = None):
        self.seat = seat
        self.stat_dict = stat_dict
        self.win = win
        self.pop = pop
        self.hand_instance = hand_instance
        self.config = config
        self.parent_popup = parent_popup #parent's instance only used if this popup is a child of another popup
        self.submenu_count = 0 #used to keep track of active submenus - only one at once allowed
        super(Popup, self).__init__()
        
        self.set_destroy_with_parent(True)

#    Most (all?) popups want a label and eb, so let's create them here
        self.eb = gtk.EventBox()
        self.add(self.eb)

        self.eb.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
        self.eb.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)

#    They will also usually want to be undecorated, default colors, etc.
        self.set_decorated(False)
        self.set_property("skip-taskbar-hint", True)
        self.set_focus_on_map(False)
        self.set_focus(None)

        #child popups are positioned at the mouse pointer and must be killed if
        # the parent is killed
        if self.parent_popup:
            self.set_position(gtk.WIN_POS_MOUSE)
            self.set_transient_for(self.parent_popup)
        else:
            self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            self.set_transient_for(win)
            
        self.set_destroy_with_parent(True)
        self.create()

#    Every popup window needs one of these
    def button_press_cb(self, widget, event, *args):
        """Handle button clicks on the popup window."""
#    Any button click gets rid of popup.
        print "buttonpress cb"
        self.destroy_pop()

    def create(self):
        
        #popup_count is used by Aux_hud to prevent multiple active popups per player
        #do not increment count if this popup is a child of another popup
        if self.parent_popup:
            self.parent_popup.submenu_count += 1
        else:
            self.win.popup_count += 1
        print "create", self.win.popup_count, self.submenu_count
        

        
    def destroy_pop(self):
        
        if self.parent_popup:
            self.parent_popup.submenu_count -= 1
        else:
            self.win.popup_count -= 1
        print "destroy", self.win.popup_count, self.submenu_count
        self.destroy()

class default(Popup):

    def create(self):
        super(default, self).create()

        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()
            
        self.lab = gtk.Label()
        self.eb.add(self.lab)
               
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
        self.eb.connect("button_press_event", self.button_press_cb)
        self.show_all()


class Submenu(Popup):

    def create(self):
        super(Submenu, self).create()

        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()

        count_toplevel = len(self.pop.pu_stats)

        if count_toplevel < 1:
            self.destroy_pop()

        self.grid = gtk.Table(count_toplevel,2,False)
        self.eb.add(self.grid)
        
        grid_line = {}
        row = 1
        
        for stat,submenu_to_run in self.pop.pu_stats_submenu:

            grid_line[row]={}
            grid_line[row]['eb'] = gtk.EventBox()
            grid_line[row]['lab'] = gtk.Label()
            grid_line[row]['eb'].add(grid_line[row]['lab'])
            grid_line[row]['eb'].modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
            grid_line[row]['eb'].modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
            grid_line[row]['lab'].modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
            grid_line[row]['lab'].modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
            grid_line[row]['lab'].set_alignment(xalign=0, yalign=0.5) 
            grid_line[row]['eb'].connect("button_press_event", self.button_press_cb)            
            try:
                number = Stats.do_stat(
                    self.stat_dict, player = int(player_id),stat = stat, hand_instance = self.hand_instance)
                grid_line[row]['text'] = number[3]
                grid_line[row]['lab'].set_text(number[3])
                Stats.do_tip(grid_line[row]['lab'], number[5] + " " + number[4])
            except:
                grid_line[row]['text'] = stat
                grid_line[row]['lab'].set_text(stat)

            self.grid.attach(grid_line[row]['eb'], 0, 1, row-1, row, xpadding=2)

            if submenu_to_run:
                grid_line[row]['arrow_object'] = gtk.EventBox()
                lab = gtk.Label()
                lab.set_text(">  ")
                lab.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
                lab.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                lab.set_alignment(xalign=0.75, yalign=0.5)
                grid_line[row]['arrow_object'].add(lab)
                grid_line[row]['arrow_object'].modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
                grid_line[row]['arrow_object'].modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                grid_line[row]['arrow_object'].connect("button_press_event", self.arrow_press_cb, submenu_to_run)
                self.grid.attach(grid_line[row]['arrow_object'], 1, 2, row-1, row)
                
                
            row += 1

        self.show_all()


    def arrow_press_cb(self, widget, event, *args):
        """Handle button clicks in the FPDB main menu event box."""
        print "custom", args
        popup_to_run = args[0]
        print self.config.popup_windows[popup_to_run].pu_class
        print dir(self.config.popup_windows)

        if self.submenu_count < 1: # only 1 popup allowed to be open at this level
            popup_factory(self.seat,self.stat_dict, self.win, self.config.popup_windows[popup_to_run], self.hand_instance, self.config, self)
            

def popup_factory(seat = None, stat_dict = None, win = None, pop = None, hand_instance = None, config = None, parent_popup = None):
    # a factory function to discover the base type of the popup
    # and to return a class instance of the correct popup
    # getattr looksup the class reference in this module

    class_to_return = getattr(__import__(__name__), pop.pu_class)
    popup_instance = class_to_return(seat, stat_dict, win, pop, hand_instance, config, parent_popup)
    
    return popup_instance
