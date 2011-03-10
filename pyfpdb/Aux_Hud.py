#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008-2011,  Ray E. Barker
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

#    pyGTK modules
import gtk
import gobject

#    FreePokerTools modules
import Mucked
import Stats
class Stat_Window(Mucked.Seat_Window):
    """Simple window class for stat windows."""

    def create_contents(self, i):
        self.grid = gtk.Table(rows = self.aw.nrows, columns = self.aw.ncols, homogeneous = False)
        self.add(self.grid)

        self.stat_box = [ [None]*self.aw.ncols for i in range(self.aw.nrows) ]
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c] = Simple_stat(self.aw.stats[r][c])
                self.grid.attach(self.stat_box[r][c].widget, c, c+1, r, r+1, xpadding = self.aw.xpad, ypadding = self.aw.ypad)

    def update_contents(self, i):
        if i == "common": return
        player_id = self.aw.get_id_from_seat(i)
        if player_id is None: return
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c].update(player_id, self.aw.hud.stat_dict)

class Simple_HUD(Mucked.Aux_Seats):
    """A simple HUD class based on the Aux_Window interface."""

    def __init__(self, hud, config, params):
        super(Simple_HUD, self).__init__(hud, config, params)
#    Save everything you need to know about the hud as attrs.
#    That way a subclass doesn't have to grab them.
        self.poker_game = self.hud.poker_game
        self.game_params = self.hud.config.get_game_parameters(self.hud.poker_game)
        self.game = self.hud.config.supported_games[self.hud.poker_game]
        self.max = self.hud.max
        self.nrows = self.game_params['rows']
        self.ncols = self.game_params['cols']
        self.xpad = self.game_params['xpad']
        self.ypad = self.game_params['ypad']
        self.xshift = self.game_params['xshift']
        self.yshift = self.game_params['yshift']
        
        self.aw_window_type = Stat_Window

#    layout is handled by superclass!
        self.stats = [ [None]*self.ncols for i in range(self.nrows) ]
        for stat in self.game.stats:
            self.stats[self.config.supported_games[self.poker_game].stats[stat].row] \
                      [self.config.supported_games[self.poker_game].stats[stat].col] = \
                      self.config.supported_games[self.poker_game].stats[stat].stat_name

    def create_contents(self, container, i):
        container.create_contents(i)

    def update_contents(self, container, i):
        container.update_contents(i)

class Simple_stat(object):
    """A simple class for displaying a single stat."""
    def __init__(self, stat):
        self.stat = stat
        self.eb = Simple_eb();
        self.lab = Simple_label(self.stat)
        self.eb.add(self.lab)
        self.widget = self.eb

    def update(self, player_id, stat_dict):
        self.lab.set_text( str(Stats.do_stat(stat_dict, player_id, self.stat)[1]) )

#    Override thise methods to customize your eb or label
class Simple_eb(gtk.EventBox): pass
class Simple_label(gtk.Label): pass
