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

import ctypes

try:
    from AppKit import NSView, NSWindowAbove
except ImportError:
    NSView = None

from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

#    FreePokerTools modules
import Stats

class Popup(QWidget):

    def __init__(self, seat = None, stat_dict = None, win = None, pop = None, hand_instance = None, config = None, parent_popup = None):
        super(Popup, self).__init__(parent_popup or win, Qt.Window | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.seat = seat
        self.stat_dict = stat_dict
        self.win = win
        self.pop = pop
        self.hand_instance = hand_instance
        self.config = config
        self.parent_popup = parent_popup #parent's instance only used if this popup is a child of another popup
        self.submenu_count = 0 #used to keep track of active submenus - only one at once allowed

        self.create()
        self.show()
        #child popups are positioned at the mouse pointer and must be killed if
        # the parent is killed
        parent = parent_popup or win
        if config.os_family == 'Mac' and NSView is not None:
            selfwinid = self.effectiveWinId()
            selfcvp = ctypes.c_void_p(int(selfwinid))
            selfview = NSView(c_void_p=selfcvp)
            parentwinid = parent.effectiveWinId()
            parentcvp = ctypes.c_void_p(int(parentwinid))
            parentview = NSView(c_void_p=parentcvp)
            parentview.window().addChildWindow_ordered_(selfview.window(), NSWindowAbove)
        else:
            self.windowHandle().setTransientParent(self.parent().windowHandle())
        parent.destroyed.connect(self.destroy)
        self.move(QCursor.pos())

#    Every popup window needs one of these
    def mousePressEvent(self, event):
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
            
        self.lab = QLabel()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.lab)
               
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
        
        self.lab.setText(text)
        Stats.do_tip(self.lab, tip_text)

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

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)
        
        grid_line = {}
        row = 1
        
        for stat,submenu_to_run in self.pop.pu_stats_submenu:

            grid_line[row]={}
            grid_line[row]['lab'] = QLabel()
                        
            number = Stats.do_stat(
                    self.stat_dict, player = int(player_id),stat = stat, hand_instance = self.hand_instance)
            if number:
                grid_line[row]['text'] = number[3]
                grid_line[row]['lab'].setText(number[3])
                Stats.do_tip(grid_line[row]['lab'], number[5] + " " + number[4])
            else:
                grid_line[row]['text'] = stat
                grid_line[row]['lab'].setText(stat)

            if row == 1:
                #put an "x" close label onto the popup, invert bg/fg
                # the window can also be closed by clicking on any non-menu label
                # but this "x" is added incase the menu is entirely non-menu labels
                
                xlab = QLabel("x")
                xlab.setStyleSheet("background:%s;color:%s;" % (self.win.aw.fgcolor, self.win.aw.bgcolor))
                grid_line[row]['x'] = xlab
                self.grid.addWidget(grid_line[row]['x'], row-1, 2)
                
            if submenu_to_run:
                lab = QLabel(">")
                grid_line[row]['arrow_object'] = lab
                lab.submenu = submenu_to_run
                grid_line[row]['lab'].submenu = submenu_to_run
                if row == 1:
                    self.grid.addWidget(grid_line[row]['arrow_object'], row-1, 1)
                else:
                    self.grid.addWidget(grid_line[row]['arrow_object'], row-1, 1, 1, 2)

            self.grid.addWidget(grid_line[row]['lab'], row-1, 0)
                
            row += 1

    def mousePressEvent(self, event):
        widget = self.childAt(event.pos())
        submenu = "_destroy"
        if hasattr(widget, 'submenu'):
            submenu = widget.submenu
        if submenu == "_destroy":
            self.destroy_pop()
            return
        if self.submenu_count < 1: # only 1 popup allowed to be open at this level
            popup_factory(self.seat,self.stat_dict, self.win, self.config.popup_windows[submenu], self.hand_instance, self.config, self)
            
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

        number_of_cols = number_of_items / 16
        if number_of_cols % 16:
            number_of_cols += 1

        number_per_col = number_of_items / float(number_of_cols)

        #if number_per_col != round((number_of_items / float(number_of_cols)),0):
        #    number_per_col += 1
        #number_per_col = int(number_per_col)
        number_per_col = 16

        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setHorizontalSpacing(5)

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
            contentlab = QLabel(text[i][:-1])
            Stats.do_tip(contentlab, tip_text[i][:-1])
            self.grid.addWidget(contentlab, 0, int(i))

            
def popup_factory(seat = None, stat_dict = None, win = None, pop = None, hand_instance = None, config = None, parent_popup = None):
    # a factory function to discover the base type of the popup
    # and to return a class instance of the correct popup
    # getattr looksup the class reference in this module

    class_to_return = getattr(__import__(__name__), pop.pu_class)
    popup_instance = class_to_return(seat, stat_dict, win, pop, hand_instance, config, parent_popup)
    
    return popup_instance
