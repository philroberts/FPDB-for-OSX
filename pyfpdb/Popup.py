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
        self.destroy_pop()

    def create(self):
        
        #popup_count is used by Aux_hud to prevent multiple active popups per player
        #do not increment count if this popup is a child of another popup
        if self.parent_popup:
            self.parent_popup.submenu_count += 1
        else:
            self.win.popup_count += 1
        

        
    def destroy_pop(self):
        
        if self.parent_popup:
            self.parent_popup.submenu_count -= 1
        else:
            self.win.popup_count -= 1
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
            if number:
                text += number[3] + "\n"
                tip_text += number[5] + " " + number[4] + "\n"
            else:
                text += "xxx" + "\n"
                tip_text += "xxx" + " " + "xxx" + "\n"
                       
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
#fixme refactor this class, too much repeat code
    def create(self):
        super(Submenu, self).create()

        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()

        number_of_items = len(self.pop.pu_stats)
        if number_of_items < 1:
            self.destroy_pop()

        #Put an eventbox into an eventbox - this allows an all-round
        #border to be created
        self.inner_box = gtk.EventBox()
        self.inner_box.set_border_width(1)
        self.inner_box.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
        self.inner_box.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
        #set outerbox colour to grey, and attach innerbox
        self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#303030"))
        self.eb.add(self.inner_box)
        
        self.grid = gtk.Table(number_of_items,3,False)
        self.inner_box.add(self.grid)
        
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
            grid_line[row]['lab'].set_alignment(xalign=0, yalign=1)
            grid_line[row]['lab'].set_padding(2,0)
                        
            number = Stats.do_stat(
                    self.stat_dict, player = int(player_id),stat = stat, hand_instance = self.hand_instance)
            if number:
                grid_line[row]['text'] = number[3]
                grid_line[row]['lab'].set_text(number[3])
                Stats.do_tip(grid_line[row]['lab'], number[5] + " " + number[4])
            else:
                grid_line[row]['text'] = stat
                grid_line[row]['lab'].set_text(stat)            

            if row == 1:
                #put an "x" close label onto the popup, invert bg/fg
                # the window can also be closed by clicking on any non-menu label
                # but this "x" is added incase the menu is entirely non-menu labels
                
                grid_line[row]['x'] = gtk.EventBox()
                xlab = gtk.Label()
                xlab.set_text("x")
                xlab.modify_bg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                xlab.modify_fg(gtk.STATE_NORMAL, self.win.aw.bgcolor) 
                grid_line[row]['x'].add(xlab)
                grid_line[row]['x'].modify_bg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                grid_line[row]['x'].modify_fg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
                #grid_line[row]['x'].set_border_width(2)
                self.grid.attach(grid_line[row]['x'], 2, 3, row-1, row)
                grid_line[row]['x'].connect("button_press_event", self.submenu_press_cb, "_destroy")
                
            if submenu_to_run:
                grid_line[row]['arrow_object'] = gtk.EventBox()
                lab = gtk.Label()
                lab.set_text(">")
                lab.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
                lab.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                lab.set_alignment(xalign=0.75, yalign=0.5)
                grid_line[row]['arrow_object'].add(lab)
                grid_line[row]['arrow_object'].modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
                grid_line[row]['arrow_object'].modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
                grid_line[row]['arrow_object'].connect("button_press_event", self.submenu_press_cb, submenu_to_run)
                if row == 1:
                    self.grid.attach(grid_line[row]['arrow_object'], 1, 2, row-1, row)
                else:
                    self.grid.attach(grid_line[row]['arrow_object'], 1, 3, row-1, row)
                grid_line[row]['eb'].connect("button_press_event", self.submenu_press_cb, submenu_to_run)
            else:
                grid_line[row]['eb'].connect("button_press_event", self.button_press_cb)

            self.grid.attach(grid_line[row]['eb'], 0, 1, row-1, row)
                
            row += 1

        self.show_all()


    def submenu_press_cb(self, widget, event, *args):
        """Handle button clicks in the FPDB main menu event box."""

        popup_to_run = args[0]
        if popup_to_run == "_destroy":
            self.destroy_pop()
            return
        if self.submenu_count < 1: # only 1 popup allowed to be open at this level
            popup_factory(self.seat,self.stat_dict, self.win, self.config.popup_windows[popup_to_run], self.hand_instance, self.config, self)
            
class Multicol(Popup):
#like a default, but will flow into columns of 16 items
#use "blank" items if the default flowing affects readability

    def create(self):
        super(Multicol, self).create()

        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()

        number_of_items = len(self.pop.pu_stats)
        if number_of_items < 1:
            self.destroy_pop()

        number_of_cols = number_of_items / 16.
        if number_of_cols != round((number_of_items / 16.),0):
            number_of_cols += 1
        number_of_cols = int(number_of_cols)

        number_per_col = number_of_items / float(number_of_cols)

        #if number_per_col != round((number_of_items / float(number_of_cols)),0):
        #    number_per_col += 1
        #number_per_col = int(number_per_col)
        number_per_col = 16

        self.grid = gtk.Table(1,int(number_of_cols),False)
        self.grid.set_col_spacings(5)
        self.eb.add(self.grid)

        col_index,row_index  = 0,0
        text, tip_text = {},{}
        for i in range(number_of_cols):
            text[i], tip_text[i] = "", ""

        for stat in self.pop.pu_stats:

            number = Stats.do_stat(
                self.stat_dict, player = int(player_id),stat = stat, hand_instance = self.hand_instance)
            if number:
                text[col_index] += number[3] + "\n"
                tip_text[col_index] += number[5] + " " + number[4] + "\n"
            else:
                text[col_index] += stat + "\n"
                tip_text[col_index] += stat + "\n"

            row_index += 1
            if row_index >= number_per_col:
                col_index += 1
                row_index = 0
                
        if row_index > 0:
            for i in range(number_per_col - row_index):
                # pad final column with blank lines
                text[col_index] += "\n"

        for i in text:
            contentbox = gtk.EventBox()
            contentbox.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
            contentbox.connect("button_press_event", self.button_press_cb)
            contentlab = gtk.Label()
            contentbox.add(contentlab)
            contentlab.set_text(text[i][:-1])
            contentlab.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
            Stats.do_tip(contentlab, tip_text[i][:-1])
            self.grid.attach(contentbox, int(i), int(i)+1, 0, 1)

        self.show_all()

            
def popup_factory(seat = None, stat_dict = None, win = None, pop = None, hand_instance = None, config = None, parent_popup = None):
    # a factory function to discover the base type of the popup
    # and to return a class instance of the correct popup
    # getattr looksup the class reference in this module

    class_to_return = getattr(__import__(__name__), pop.pu_class)
    popup_instance = class_to_return(seat, stat_dict, win, pop, hand_instance, config, parent_popup)
    
    return popup_instance
