#!/usr/bin/env python
"""Hud.py

Create and manage the hud overlays.
"""
#    Copyright 2008, Ray E. Barker

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
#    Standard Library modules

#    pyGTK modules
import pygtk
import gtk
import pango
import gobject

#    FreePokerTools modules
import Tables # needed for testing only
import Configuration
import Stats
import Mucked
import Database

class Hud:
    
    def __init__(self, table, max, poker_game, config, db_connection):
        self.table         = table
        self.config        = config
        self.poker_game    = poker_game
        self.max           = max
        self.db_connection = db_connection

        self.stat_windows = {}
        self.font = pango.FontDescription("Sans 8")

        
    def create(self, hand, config):
#    update this hud, to the stats and players as of "hand"
#    hand is the hand id of the most recent hand played at this table
#
#    this method also manages the creating and destruction of stat
#    windows via calls to the Stat_Window class
        for i in range(1, self.max + 1):
            (x, y) = config.supported_sites[self.table.site].layout[self.max].location[i]
            self.stat_windows[i] = Stat_Window(game = config.supported_games[self.poker_game],
                                               table = self.table, 
                                               x = x,
                                               y = y,
                                               seat = i,
                                               player_id = 'fake',
                                               font = self.font)

        self.stats = []
        for i in range(0, config.supported_games[self.poker_game].rows + 1):
            row_list = [''] * config.supported_games[self.poker_game].cols
            self.stats.append(row_list)
        for stat in config.supported_games[self.poker_game].stats.keys():
            self.stats[config.supported_games[self.poker_game].stats[stat].row] \
                      [config.supported_games[self.poker_game].stats[stat].col] = \
                      config.supported_games[self.poker_game].stats[stat].stat_name

#        self.mucked_window = gtk.Window()
#        self.m = Mucked.Mucked(self.mucked_window, self.db_connection)
#        self.mucked_window.show_all() 
            
    def update(self, hand, db, config):
        stat_dict = db.get_stats_from_hand(hand, 3)
        for s in stat_dict.keys():
#            for r in range(0, 2):
#                for c in range(0, 3):
            for r in range(0, config.supported_games[self.poker_game].rows):
                for c in range(0, config.supported_games[self.poker_game].cols):
                    number = Stats.do_stat(stat_dict, player = stat_dict[s]['player_id'], stat = self.stats[r][c])
                    self.stat_windows[stat_dict[s]['seat']].label[r][c].set_text(number[1])
                    tip = stat_dict[s]['screen_name'] + "\n" + number[5] + "\n" + \
                          number[3] + ", " + number[4]
                    Stats.do_tip(self.stat_windows[stat_dict[s]['seat']].e_box[r][c], tip)
#        self.m.update(hand)
        
class Stat_Window:

    def button_press_cb(self, widget, event, *args):
#    This handles all callbacks from button presses on the event boxes in 
#    the stat windows.  There is a bit of an ugly kludge to separate single-
#    and double-clicks.
        if event.button == 1:   # left button event
            if event.type == gtk.gdk.BUTTON_PRESS: # left button single click
                if self.sb_click > 0: return
                self.sb_click = gobject.timeout_add(250, self.single_click)
            elif event.type == gtk.gdk._2BUTTON_PRESS: # left button double click
                if self.sb_click > 0:
                    gobject.source_remove(self.sb_click)
                    self.sb_click = 0
                    self.double_click(widget, event, *args)

        if event.button == 2:   # middle button event
            print "middle button clicked"

        if event.button == 3:   # right button event
            print "right button clicked"

    def single_click(self):
#    Callback from the timeout in the single-click finding part of the
#    button press call back.  This needs to be modified to get all the 
#    arguments from the call.
        print "left button clicked"
        self.sb_click = 0
        return False

    def double_click(self, widget, event, *args):
        self.toggle_decorated(widget)

    def toggle_decorated(self, widget):
        top = widget.get_toplevel()
        (x, y) = top.get_position()
                    
        if top.get_decorated():
            top.set_decorated(0)
            top.move(x, y)
        else:
            top.set_decorated(1)
            top.move(x, y)

    def __init__(self, game, table, seat, x, y, player_id, font):
        self.game = game
        self.table = table
        self.x = x + table.x
        self.y = y + table.y
        self.player_id = player_id
        self.sb_click = 0

        self.window = gtk.Window()
        self.window.set_decorated(0)
        self.window.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.window.set_title("%s" % seat)

        self.grid = gtk.Table(rows = self.game.rows, columns = self.game.cols, homogeneous = False)
        self.window.add(self.grid)
        
        self.e_box = []
        self.frame = []
        self.label = []
        for r in range(self.game.rows):
            self.e_box.append([])
            self.label.append([])
            for c in range(self.game.cols):
                self.e_box[r].append( gtk.EventBox() )
                Stats.do_tip(self.e_box[r][c], 'farts')
                self.grid.attach(self.e_box[r][c], c, c+1, r, r+1, xpadding = 1, ypadding = 1)
                self.label[r].append( gtk.Label('xxx') )
                self.e_box[r][c].add(self.label[r][c])
                self.e_box[r][c].connect("button_press_event", self.button_press_cb)
#                font = pango.FontDescription("Sans 8")
                self.label[r][c].modify_font(font)
        self.window.realize
        self.window.move(self.x, self.y)
        self.window.set_keep_above(1)
        self.window.show_all()
        
def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()
        
if __name__== "__main__":
    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    label = gtk.Label('Fake main window, blah blah, blah\nblah, blah')
    main_window.add(label)
    main_window.show_all()
    
    c = Configuration.Config()
    tables = Tables.discover(c)
    db = Database.Database(c, 'PTrackSv2', 'razz')
    
    for t in tables:
        win = Hud(t, 8, c, db)
#        t.get_details()
        win.update(8300, db, c)

    gtk.main()
