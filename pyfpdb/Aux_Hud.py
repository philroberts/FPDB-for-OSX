#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aux_Hud.py

Simple HUD display for FreePokerTools/fpdb HUD.
"""
import L10n
_ = L10n.get_translation()
#    Copyright 2011-2012,  Ray E. Barker
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
from functools import partial

from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout,
                             QLabel, QPushButton, QSpinBox,
                             QVBoxLayout, QWidget)

#    FreePokerTools modules
import Aux_Base
import Stats
import Popup


class Simple_HUD(Aux_Base.Aux_Seats):
    """A simple HUD class based on the Aux_Window interface."""

    def __init__(self, hud, config, aux_params):
        super(Simple_HUD, self).__init__(hud, config, aux_params)
        
        #    Save everything you need to know about the hud as attrs.
        #    That way a subclass doesn't have to grab them.
        #    Also, the subclass can override any of these attributes

        self.poker_game  = self.hud.poker_game
        self.site_params = self.hud.site_parameters
        self.aux_params  = aux_params
        self.game_params = self.hud.supported_games_parameters["game_stat_set"]
        self.max         = self.hud.max
        self.nrows       = self.game_params.rows
        self.ncols       = self.game_params.cols
        self.xpad        = self.game_params.xpad
        self.ypad        = self.game_params.ypad
        self.xshift      = self.site_params['hud_menu_xshift']
        self.yshift      = self.site_params['hud_menu_yshift']
        self.fgcolor     = self.aux_params["fgcolor"]
        self.bgcolor     = self.aux_params["bgcolor"]
        self.opacity     = self.aux_params["opacity"]
        self.font        = QFont(self.aux_params["font"], int(self.aux_params["font_size"]))
        
        #store these class definitions for use elsewhere
        # this is needed to guarantee that the classes in _this_ module
        # are called, and that some other overriding class is not used.

        self.aw_class_window = Simple_Stat_Window
        self.aw_class_stat = Simple_stat
        self.aw_class_table_mw = Simple_table_mw
        self.aw_class_label = Simple_label

        #    layout is handled by superclass!
        #    retrieve the contents of the stats. popup and tips elements
        #    for future use do this here so that subclasses don't have to bother
        
        self.stats  = [ [None]*self.ncols for i in range(self.nrows) ]
        self.popups = [ [None]*self.ncols for i in range(self.nrows) ]
        self.tips   = [ [None]*self.ncols for i in range(self.nrows) ]

        for stat in self.game_params.stats:
            self.stats[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].stat_name
            self.popups[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].popup
            self.tips[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].tip
                                        
    def create_contents(self, container, i):
        # this is a call to whatever is in self.aw_class_window but it isn't obvious
        container.create_contents(i)

    def update_contents(self, container, i):
        # this is a call to whatever is in self.aw_class_window but it isn't obvious
        container.update_contents(i)

    def create_common(self, x, y):
        # invokes the simple_table_mw class (or similar)
        self.table_mw = self.aw_class_table_mw(self.hud, aw = self)
        return self.table_mw
        
    def move_windows(self):
        super(Simple_HUD, self).move_windows()
        #
        #tell our mw that an update is needed (normally on table move)
        # custom code here, because we don't use the ['common'] element
        # to control menu position
        self.table_mw.move_windows()

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""

        new_locs = {}
        for (i, pos) in self.positions.iteritems():
            if i != 'common':
                new_locs[self.adj[int(i)]] = ((pos[0]), (pos[1]))
            else:
                #common position belongs to mucked display so, don't alter its location
                pass

        self.config.save_layout_set(self.hud.layout_set, self.hud.max,
                    new_locs ,self.hud.table.width, self.hud.table.height)

        
class Simple_Stat_Window(Aux_Base.Seat_Window):
    """Simple window class for stat windows."""
    
    def __init__(self, aw = None, seat = None):
        super(Simple_Stat_Window, self).__init__(aw, seat)
        self.popup_count = 0
        
    def button_release_right(self, event):  #show pop up
        widget = self.childAt(event.pos())

        if widget.stat_dict and self.popup_count == 0 and widget.aw_popup: # do not popup on empty blocks or if one is already active
            pu = Popup.popup_factory(
                seat = widget.aw_seat,
                stat_dict = widget.stat_dict,
                win = self,
                pop = self.aw.config.popup_windows[widget.aw_popup],
                hand_instance = self.aw.hud.hand_instance,
                config = self.aw.config)
            pu.setStyleSheet("QWidget{background:%s;color:%s;}QToolTip{}" % (self.aw.bgcolor, self.aw.fgcolor))
                    
    def create_contents(self, i):
        self.setStyleSheet("QWidget{background:%s;color:%s;}QToolTip{}" % (self.aw.bgcolor, self.aw.fgcolor))
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(4)
        self.grid.setVerticalSpacing(1)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.grid)
        self.stat_box = [ [None]*self.aw.ncols for i in range(self.aw.nrows) ]

        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c] = self.aw.aw_class_stat(self.aw.stats[r][c],
                    seat = self.seat,
                    popup = self.aw.popups[r][c],
                    game_stat_config = self.aw.hud.supported_games_parameters["game_stat_set"].stats[(r,c)],
                    aw = self.aw)
                self.grid.addWidget(self.stat_box[r][c].widget, r, c)
                self.stat_box[r][c].widget.setFont(self.aw.font)

    def update_contents(self, i):
        if i == "common": return
        player_id = self.aw.get_id_from_seat(i)
        if player_id is None: return
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c].update(player_id, self.aw.hud.stat_dict)


class Simple_stat(object):
    """A simple class for displaying a single stat."""
    def __init__(self, stat, seat, popup, game_stat_config=None, aw=None):
        self.stat = stat
        self.lab = aw.aw_class_label("xxx") # xxx is used as initial value because longer labels don't shrink
        self.lab.setAlignment(Qt.AlignCenter)
        self.lab.aw_seat = aw.hud.layout.hh_seats[seat]
        self.lab.aw_popup = popup
        self.lab.stat_dict = None
        self.widget = self.lab
        self.stat_dict = None
        self.hud = aw.hud

    def update(self, player_id, stat_dict):
        self.stat_dict = stat_dict     # So the Simple_stat obj always has a fresh stat_dict
        self.lab.stat_dict = stat_dict
        self.number = Stats.do_stat(stat_dict, player_id, self.stat, self.hud.hand_instance)
        if self.number:
            self.lab.setText(unicode(self.number[1]))

    def set_color(self, fg=None, bg=None):
        ss = "QLabel{"
        if fg:
            ss += "color: %s;" % fg
        if bg:
            ss += "background: %s;" % bg
        self.lab.setStyleSheet(ss + "}")

class Simple_label(QLabel): pass

class Simple_table_mw(Aux_Base.Seat_Window):
    """Create a default table hud menu label"""
#    This is a recreation of the table main window from the default HUD
#    in the old Hud.py. This has the menu options from that hud. 

#    BTW: It might be better to do this with a different AW.

    def __init__(self, hud, aw = None):
        super(Simple_table_mw, self).__init__(aw)
        self.hud = hud
        self.aw = aw
        self.menu_is_popped = False

        #self.connect("configure_event", self.configure_event_cb, "auxmenu") base class will deal with this

        try:
            self.menu_label = hud.hud_params['label']
        except:
            self.menu_label = ("fpdb menu")

        lab = QLabel(self.menu_label)
        lab.setStyleSheet("background: %s; color: %s;" % (self.aw.bgcolor, self.aw.fgcolor))

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(lab)

        self.move(self.hud.table.x + self.aw.xshift, self.hud.table.y + self.aw.yshift)

    def button_press_right(self, event):
        """Handle button clicks in the FPDB main menu event box."""

        if not self.menu_is_popped:
            self.menu_is_popped = True
            Simple_table_popup_menu(self)
    
    def move_windows(self, *args):
        # force menu to the offset position from table origin (do not use common setting)
        self.move(self.hud.table.x + self.aw.xshift, self.hud.table.y + self.aw.yshift)


class Simple_table_popup_menu(QWidget):

    def __init__(self, parentwin):
        
        super(Simple_table_popup_menu, self).__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.parentwin = parentwin
        self.move(self.parentwin.hud.table.x + self.parentwin.aw.xshift,
                  self.parentwin.hud.table.y + self.parentwin.aw.yshift)
        self.setWindowTitle(self.parentwin.menu_label)

#combobox statrange
        stat_range_combo_dict = {} #[position][screentext, field value]
        stat_range_combo_dict[0] = ((_('Since:')+" "+_('All Time')), "A")
        stat_range_combo_dict[1] = ((_('Since:')+" "+_('Session')), "S")
        stat_range_combo_dict[2] = ((_('Since:')+" "+_('n Days')+" - - >"), "T")
#combobox seatsstyle
        seats_style_combo_dict = {} #[position][screentext, field value]
        seats_style_combo_dict[0] = ((_('Number of Seats:')+" "+_('Any Number')), "A")
        seats_style_combo_dict[1] = ((_('Number of Seats:')+" "+_('Custom')), "C")
        seats_style_combo_dict[2] = ((_('Number of Seats:')+" "+_('Exact')), "E")
#combobox multiplier
        multiplier_combo_dict = {}
        multiplier_combo_dict[0] = (_('For This Blind Level Only'), 1)
        multiplier_combo_dict[1] = ((_('%s to %s * Current Blinds') % ("  0.5", "2")), 2)
        multiplier_combo_dict[2] = ((_('%s to %s * Current Blinds') % ("  0.33", "3")), 3)
        multiplier_combo_dict[3] = ((_('%s to %s * Current Blinds') % ("  0.1", "10")), 10)
        multiplier_combo_dict[4] = (_('All Levels'), 10000)
#ComboBox - set max seats
        cb_max_dict = {} #[position][screentext, field value]
        cb_max_dict[0] = (_('Force layout')+'...',None)
        pos = 1
        for i in (sorted(self.parentwin.hud.layout_set.layout)):
            cb_max_dict[pos]= (('%d-max' % i), i)
            pos+=1

        grid = QGridLayout()
        self.setLayout(grid)
        vbox1=QVBoxLayout()
        vbox2=QVBoxLayout()
        vbox3=QVBoxLayout()
        
        vbox1.addWidget(self.build_button(_('Restart This HUD'), "kill"))
        vbox1.addWidget(self.build_button(_('Save HUD Layout'), "save"))
        vbox1.addWidget(self.build_button(_('Stop this HUD'), "blacklist"))
        vbox1.addWidget(self.build_button(_('Close'), "close"))
        vbox1.addWidget(QLabel(''))
        vbox1.addWidget(self.build_combo_and_set_active('new_max_seats', cb_max_dict))
        
        vbox2.addWidget(QLabel(_('Show Player Stats for')))
        vbox2.addWidget(self.build_combo_and_set_active('h_agg_bb_mult', multiplier_combo_dict))
        vbox2.addWidget(self.build_combo_and_set_active('h_seats_style', seats_style_combo_dict))
        hbox=QHBoxLayout()
        hbox.addWidget(QLabel(_('Custom')))
        self.h_nums_low_spinner = self.build_spinner('h_seats_cust_nums_low',1,9)
        hbox.addWidget(self.h_nums_low_spinner)
        hbox.addWidget(QLabel(_('To')))
        self.h_nums_high_spinner = self.build_spinner('h_seats_cust_nums_high',2,10)
        hbox.addWidget(self.h_nums_high_spinner)
        vbox2.addLayout(hbox)
        hbox=QHBoxLayout()
        hbox.addWidget(self.build_combo_and_set_active('h_stat_range', stat_range_combo_dict))
        self.h_hud_days_spinner = self.build_spinner('h_hud_days',1,9999)
        hbox.addWidget(self.h_hud_days_spinner)
        vbox2.addLayout(hbox)

        vbox3.addWidget(QLabel(_('Show Opponent Stats for')))
        vbox3.addWidget(self.build_combo_and_set_active('agg_bb_mult', multiplier_combo_dict))
        vbox3.addWidget(self.build_combo_and_set_active('seats_style', seats_style_combo_dict))
        hbox=QHBoxLayout()
        hbox.addWidget(QLabel(_('Custom')))
        self.nums_low_spinner = self.build_spinner('seats_cust_nums_low',1,9)
        hbox.addWidget(self.nums_low_spinner)
        hbox.addWidget(QLabel(_('To')))
        self.nums_high_spinner = self.build_spinner('seats_cust_nums_high',2,10)
        hbox.addWidget(self.nums_high_spinner)
        vbox3.addLayout(hbox)
        hbox=QHBoxLayout()
        hbox.addWidget(self.build_combo_and_set_active('stat_range', stat_range_combo_dict))
        self.hud_days_spinner = self.build_spinner('hud_days',1,9999)
        hbox.addWidget(self.hud_days_spinner)
        vbox3.addLayout(hbox)

        self.set_spinners_active()

        grid.addLayout(vbox1, 0, 0)
        grid.addLayout(vbox2, 0, 1)
        grid.addLayout(vbox3, 0, 2)

        self.show()
        self.raise_()

    def delete_event(self):
        self.parentwin.menu_is_popped = False
        self.destroy()
        
    def callback(self, checkState, data=None):
        if data == "kill":
            self.parentwin.hud.parent.kill_hud("kill", self.parentwin.hud.table.key)
        if data == "blacklist":
            self.parentwin.hud.parent.blacklist_hud("kill", self.parentwin.hud.table.key)
        if data == "save":
            # This calls the save_layout method of the Hud object. The Hud object 
            # then calls the save_layout method in each installed AW.
            self.parentwin.hud.save_layout()
        self.delete_event()

    def build_button(self, labeltext, cbkeyword):
        button = QPushButton(labeltext)
        button.clicked.connect(partial(self.callback, data=cbkeyword))
        return button

    def build_spinner(self, field, low, high):
        spinBox = QSpinBox()
        spinBox.setRange(low, high)
        spinBox.setValue(self.parentwin.hud.hud_params[field])
        spinBox.valueChanged.connect(partial(self.change_spin_field_value, field=field))
        return spinBox

    def build_combo_and_set_active(self, field, combo_dict):
        widget = QComboBox()
        for pos in combo_dict:
            widget.addItem(combo_dict[pos][0])
            if combo_dict[pos][1] == self.parentwin.hud.hud_params[field]:
                widget.setCurrentIndex(pos)
        widget.currentIndexChanged[int].connect(partial(self.change_combo_field_value, field=field, combo_dict=combo_dict))
        return widget
                
    def change_combo_field_value(self, sel, field, combo_dict):
        self.parentwin.hud.hud_params[field] = combo_dict[sel][1]
        self.set_spinners_active()
                
    def change_spin_field_value(self, value, field):
        self.parentwin.hud.hud_params[field] = value

    def set_spinners_active(self):
        if self.parentwin.hud.hud_params['h_stat_range'] == "T":
            self.h_hud_days_spinner.setEnabled(True)
        else:
            self.h_hud_days_spinner.setEnabled(False)
        if self.parentwin.hud.hud_params['stat_range'] == "T":
            self.hud_days_spinner.setEnabled(True)
        else:
            self.hud_days_spinner.setEnabled(False)
        if self.parentwin.hud.hud_params['h_seats_style'] == "C":
            self.h_nums_low_spinner.setEnabled(True)
            self.h_nums_high_spinner.setEnabled(True)
        else:
            self.h_nums_low_spinner.setEnabled(False)
            self.h_nums_high_spinner.setEnabled(False)
        if self.parentwin.hud.hud_params['seats_style'] == "C":
            self.nums_low_spinner.setEnabled(True)
            self.nums_high_spinner.setEnabled(True)
        else:
            self.nums_low_spinner.setEnabled(False)
            self.nums_high_spinner.setEnabled(False)
