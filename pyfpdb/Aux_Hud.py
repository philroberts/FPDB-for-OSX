#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008-2010,  Ray E. Barker
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
import pango

#    FreePokerTools modules
import Mucked
import Stats
class Stat_Window(Mucked.Seat_Window):
    """Simple window class for stat windows."""

    def create_contents(self, i):
        self.grid = gtk.Table(rows = self.aw.nrows, columns = self.aw.ncols, homogeneous = False)
        self.add(self.grid)

        self.grid.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        self.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        self.stat_box = [ [None]*self.aw.ncols for i in range(self.aw.nrows) ]
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c] = Simple_stat(self.aw.stats[r][c])
                self.grid.attach(self.stat_box[r][c].widget, c, c+1, r, r+1, xpadding = self.aw.xpad, ypadding = self.aw.ypad)
                self.stat_box[r][c].set_color(self.aw.fgcolor, self.aw.bgcolor)
                self.stat_box[r][c].set_font(self.aw.font)

    def update_contents(self, i):
        if i == "common": return
        player_id = self.aw.get_id_from_seat(i)
        if player_id is None: return
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c].update(player_id, self.aw.hud.stat_dict)
                self.stat_box[r][c].widget.connect("button_press_event", self.button_press_cb)

class Simple_HUD(Mucked.Aux_Seats):
    """A simple HUD class based on the Aux_Window interface."""

    def __init__(self, hud, config, params):
        super(Simple_HUD, self).__init__(hud, config, params)
#    Save everything you need to know about the hud as attrs.
#    That way a subclass doesn't have to grab them.
        self.poker_game  = self.hud.poker_game
        self.game_params = self.hud.config.get_game_parameters(self.hud.poker_game)
        self.game        = self.hud.config.supported_games[self.hud.poker_game]
        self.max         = self.hud.max
        self.nrows       = self.game_params['rows']
        self.ncols       = self.game_params['cols']
        self.xpad        = self.game_params['xpad']
        self.ypad        = self.game_params['ypad']
        self.xshift      = self.game_params['xshift']
        self.yshift      = self.game_params['yshift']

        self.fgcolor   = gtk.gdk.color_parse(params["fgcolor"])
        self.bgcolor   = gtk.gdk.color_parse(params["bgcolor"])
        self.opacity   = params["opacity"]
        self.font      = pango.FontDescription("%s %s" % (params["font"], params["font_size"]))
        self.aw_window_type = Stat_Window
        self.aw_mw_type = Simple_table_mw

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

    def create_common(self, x, y):
        return self.aw_mw_type(self.hud, aw = self)
#        return Simple_table_mw(self.hud, aw = self)

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

    def set_color(self, fg, bg):
        self.eb.modify_fg(gtk.STATE_NORMAL, fg)
        self.eb.modify_bg(gtk.STATE_NORMAL, bg)

        self.lab.modify_fg(gtk.STATE_NORMAL, fg)
        self.lab.modify_bg(gtk.STATE_NORMAL, bg)

    def set_font(self, font):
        self.lab.modify_font(font)

#    Override thise methods to customize your eb or label
class Simple_eb(gtk.EventBox): pass
class Simple_label(gtk.Label): pass

class Simple_table_mw(Mucked.Seat_Window):
    """Create a default table hud main window with a menu."""
#    This is a recreation of the table main windeow from the default HUD
#    in the old Hud.py. This has the menu options from that hud. 

#    BTW: It might be better to do this with a different AW.

    def __init__(self, hud, aw = None):
        super(Simple_table_mw, self).__init__(aw)
        self.hud = hud

        self.set_skip_taskbar_hint(True)  # invisible to taskbar
        self.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.set_decorated(False)    # kill titlebars
#        self.set_opacity(self.colors["hudopacity"])  # set it to configured hud opacity
        self.set_focus(None)
        self.set_focus_on_map(False)
        self.set_accept_focus(False)
        self.connect("configure_event", self.aw.configure_event_cb, "common")

        eb = gtk.EventBox()
        lab = gtk.Label("Menu")

        eb.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        eb.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)
        lab.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        lab.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)

        self.add(eb)
        eb.add(lab)

        self.menu = gtk.Menu()
        menus = {}
        menu_items = (  ('Kill This HUD', self.kill),  #self.hud.parent.kill_hud),
                        ('Save HUD Layout', self.save_current_layouts), 
#                        ('Reposition Windows', self.aw.reposition_windows), 
                        ('Show Player Stats', None)
                     )
        for item, cb in menu_items:
            menus[item] = gtk.MenuItem(item)
            self.menu.append(menus[item])
            if cb is not None:
                menus[item].connect("activate", cb)
        eb.connect_object("button-press-event", self.button_press_cb, self.menu)

        (x, y) = self.aw.params['layout'][self.hud.max].common
        self.move(x + self.hud.table.x, y + self.hud.table.y)
        self.menu.show_all()
        self.show_all()
        self.hud.table.topify(self)

    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the event boxes."""

        if event.button == 3:   # right button event does nothing for now
            widget.popup(None, None, None, event.button, event.time)
 
#    button 2 is not handled here because it is the pupup window

        elif event.button == 1:   # left button event -- drag the window
            try:
                self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            except AttributeError:  # in case get_ancestor returns None
                pass
            return True
        return False

    def create_contents(self, *args):
        pass
    def update_contents(self, *args):
        pass

    def save_current_layouts(self, event):
#    This calls the save_layout method of the Hud object. The Hud object 
#    then calls the save_layout method in each installed AW.
        self.hud.save_layout()

    def kill(self, event):
        self.hud.parent.kill_hud(event, self.hud.table.key)