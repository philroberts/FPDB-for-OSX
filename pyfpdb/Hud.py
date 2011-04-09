#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hud.py

Create and manage the hud overlays.
"""
#    Copyright 2008-2011  Ray E. Barker

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

#    Standard Library modules
import os
import sys

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import pygtk
import gtk
import pango
import gobject

#    win32 modules -- only imported on windows systems
if os.name == 'nt':
    import win32gui
    import win32con
    import win32api

#    FreePokerTools modules
import Configuration
import Stats
import Mucked
import Database
#import HUD_main


def importName(module_name, name):
    """Import a named object 'name' from module 'module_name'."""
#    Recipe 16.3 in the Python Cookbook, 2nd ed.  Thanks!!!!

    try:
        module = __import__(module_name, globals(), locals(), [name])
    except:
        return None
    return(getattr(module, name))


class Hud:
    def __init__(self, parent, table, max, poker_game, config, db_connection):
#    __init__ is (now) intended to be called from the stdin thread, so it
#    cannot touch the gui
        if parent is None:  # running from cli ..
            self.parent = self
        else:
            self.parent    = parent
        self.table         = table
        self.config        = config
        self.poker_game    = poker_game
        self.max           = max
        self.db_connection = db_connection
        self.deleted       = False
        self.stacked       = True
        self.site          = table.site
        self.mw_created    = False
        self.hud_params    = parent.hud_params

        self.stat_windows  = {}
        self.popup_windows = {}
        self.aux_windows   = []

        # configure default font and colors from the configuration
        (font, font_size) = config.get_default_font(self.table.site)
        self.colors        = config.get_default_colors(self.table.site)
        self.hud_ui     = config.get_hud_ui_parameters()
        self.site_params = config.get_site_parameters(self.table.site)

        self.backgroundcolor = gtk.gdk.color_parse(self.colors['hudbgcolor'])
        self.foregroundcolor = gtk.gdk.color_parse(self.colors['hudfgcolor'])

        self.font = pango.FontDescription("%s %s" % (font, font_size))
        # do we need to add some sort of condition here for dealing with a request for a font that doesn't exist?

        game_params = config.get_game_parameters(self.poker_game)
        # if there are AUX windows configured, set them up (Ray knows how this works, if anyone needs info)
        if not game_params['aux'] == [""]:
            for aux in game_params['aux']:
                aux_params = config.get_aux_parameters(aux)
                my_import = importName(aux_params['module'], aux_params['class'])
                if my_import == None:
                    continue
                self.aux_windows.append(my_import(self, config, aux_params))

        self.creation_attrs = None

    def create_mw(self):
#	Set up a main window for this this instance of the HUD
        win = gtk.Window()
        win.set_skip_taskbar_hint(True)  # invisible to taskbar
        win.set_gravity(gtk.gdk.GRAVITY_STATIC)
        win.set_title("%s FPDBHUD" % (self.table.name)) # give it a title that we can easily filter out in the window list when Table search code is looking
        win.set_decorated(False)    # kill titlebars
        win.set_opacity(self.colors["hudopacity"])  # set it to configured hud opacity
        win.set_focus(None)
        win.set_focus_on_map(False)
        win.set_accept_focus(False)

        eventbox = gtk.EventBox()
        label = gtk.Label(self.hud_ui['label'])

        win.add(eventbox)
        eventbox.add(label)

        # set it to the desired color of the HUD for this site
        label.modify_bg(gtk.STATE_NORMAL, self.backgroundcolor)
        label.modify_fg(gtk.STATE_NORMAL, self.foregroundcolor)

        eventbox.modify_bg(gtk.STATE_NORMAL, self.backgroundcolor)
        eventbox.modify_fg(gtk.STATE_NORMAL, self.foregroundcolor)

        self.main_window = win
        # move it to the table window's X/Y position (0,0 on the table window usually)
        self.main_window.move(self.table.x, self.table.y)

#    A popup menu for the main window
#    This menu code has become extremely long - is there a better way to do this?
        menu = gtk.Menu()

        killitem = gtk.MenuItem(_('Kill This HUD'))
        menu.append(killitem)
        if self.parent is not None:
            killitem.connect("activate", self.parent.kill_hud, self.table_name)

        saveitem = gtk.MenuItem(_('Save HUD Layout'))
        menu.append(saveitem)
        saveitem.connect("activate", self.save_layout)

        repositem = gtk.MenuItem(_('Reposition StatWindows'))
        menu.append(repositem)
        repositem.connect("activate", self.reposition_windows)

        aggitem = gtk.MenuItem(_('Show Player Stats'))
        menu.append(aggitem)
        self.aggMenu = gtk.Menu()
        aggitem.set_submenu(self.aggMenu)
        # set agg_bb_mult to 1 to stop aggregation
        item = gtk.CheckMenuItem(_('For This Blind Level Only'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('P', 1))
        setattr(self, 'h_aggBBmultItem1', item)

        item = gtk.MenuItem(_('For Multiple Blind Levels:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  0.5 to 2.0 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('P',2))
        setattr(self, 'h_aggBBmultItem2', item)
        
        item = gtk.CheckMenuItem(_('  0.33 to 3.0 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('P',3))
        setattr(self, 'h_aggBBmultItem3', item)
        
        item = gtk.CheckMenuItem(_('  0.1 to 10 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('P',10))
        setattr(self, 'h_aggBBmultItem10', item)
        
        item = gtk.CheckMenuItem(_('  All Levels'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('P',10000))
        setattr(self, 'h_aggBBmultItem10000', item)
        
        item = gtk.MenuItem(_('For #Seats:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  Any Number'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('P','A'))
        setattr(self, 'h_seatsStyleOptionA', item)
        
        item = gtk.CheckMenuItem(_('  Custom'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('P','C'))
        setattr(self, 'h_seatsStyleOptionC', item)
        
        item = gtk.CheckMenuItem(_('  Exact'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('P','E'))
        setattr(self, 'h_seatsStyleOptionE', item)
        
        item = gtk.MenuItem(_('Since:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  All Time'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('P','A'))
        setattr(self, 'h_hudStyleOptionA', item)
        
        item = gtk.CheckMenuItem(_('  Session'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('P','S'))
        setattr(self, 'h_hudStyleOptionS', item)
        
        item = gtk.CheckMenuItem(_('  %s Days') % (self.hud_params['h_hud_days']))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('P','T'))
        setattr(self, 'h_hudStyleOptionT', item)

        aggitem = gtk.MenuItem(_('Show Opponent Stats'))
        menu.append(aggitem)
        self.aggMenu = gtk.Menu()
        aggitem.set_submenu(self.aggMenu)
        # set agg_bb_mult to 1 to stop aggregation
        item = gtk.CheckMenuItem(_('For This Blind Level Only'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('O',1))
        setattr(self, 'aggBBmultItem1', item)
        
        item = gtk.MenuItem(_('For Multiple Blind Levels:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  0.5 to 2.0 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('O',2))
        setattr(self, 'aggBBmultItem2', item)
        
        item = gtk.CheckMenuItem(_('  0.33 to 3.0 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('O',3))
        setattr(self, 'aggBBmultItem3', item)
        
        item = gtk.CheckMenuItem(_('  0.1 to 10 x Current Blinds'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('O',10))
        setattr(self, 'aggBBmultItem10', item)
        
        item = gtk.CheckMenuItem(_('  All Levels'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_aggregation, ('O',10000))
        setattr(self, 'aggBBmultItem10000', item)
        
        item = gtk.MenuItem(_('For #Seats:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  Any Number'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('O','A'))
        setattr(self, 'seatsStyleOptionA', item)
        
        item = gtk.CheckMenuItem(_('  Custom'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('O','C'))
        setattr(self, 'seatsStyleOptionC', item)
        
        item = gtk.CheckMenuItem(_('  Exact'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_seats_style, ('O','E'))
        setattr(self, 'seatsStyleOptionE', item)
        
        item = gtk.MenuItem(_('Since:'))
        self.aggMenu.append(item)
        
        item = gtk.CheckMenuItem(_('  All Time'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('O','A'))
        setattr(self, 'hudStyleOptionA', item)
        
        item = gtk.CheckMenuItem(_('  Session'))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('O','S'))
        setattr(self, 'hudStyleOptionS', item)
        
        item = gtk.CheckMenuItem(_('  %s Days') % (self.hud_params['h_hud_days']))
        self.aggMenu.append(item)
        item.connect("activate", self.set_hud_style, ('O','T'))
        setattr(self, 'hudStyleOptionT', item)

        # set active on current options:
        if self.hud_params['h_agg_bb_mult'] == 1:
            getattr(self, 'h_aggBBmultItem1').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 2:
            getattr(self, 'h_aggBBmultItem2').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 3:
            getattr(self, 'h_aggBBmultItem3').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 10:
            getattr(self, 'h_aggBBmultItem10').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] > 9000:
            getattr(self, 'h_aggBBmultItem10000').set_active(True)
        
        if self.hud_params['agg_bb_mult'] == 1:
            getattr(self, 'aggBBmultItem1').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 2:
            getattr(self, 'aggBBmultItem2').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 3:
            getattr(self, 'aggBBmultItem3').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 10:
            getattr(self, 'aggBBmultItem10').set_active(True)
        elif self.hud_params['agg_bb_mult'] > 9000:
            getattr(self, 'aggBBmultItem10000').set_active(True)
        
        if self.hud_params['h_seats_style'] == 'A':
            getattr(self, 'h_seatsStyleOptionA').set_active(True)
        elif self.hud_params['h_seats_style'] == 'C':
            getattr(self, 'h_seatsStyleOptionC').set_active(True)
        elif self.hud_params['h_seats_style'] == 'E':
            getattr(self, 'h_seatsStyleOptionE').set_active(True)
        
        if self.hud_params['seats_style'] == 'A':
            getattr(self, 'seatsStyleOptionA').set_active(True)
        elif self.hud_params['seats_style'] == 'C':
            getattr(self, 'seatsStyleOptionC').set_active(True)
        elif self.hud_params['seats_style'] == 'E':
            getattr(self, 'seatsStyleOptionE').set_active(True)
        
        if self.hud_params['h_hud_style'] == 'A':
            getattr(self, 'h_hudStyleOptionA').set_active(True)
        elif self.hud_params['h_hud_style'] == 'S':
            getattr(self, 'h_hudStyleOptionS').set_active(True)
        elif self.hud_params['h_hud_style'] == 'T':
            getattr(self, 'h_hudStyleOptionT').set_active(True)
        
        if self.hud_params['hud_style'] == 'A':
            getattr(self, 'hudStyleOptionA').set_active(True)
        elif self.hud_params['hud_style'] == 'S':
            getattr(self, 'hudStyleOptionS').set_active(True)
        elif self.hud_params['hud_style'] == 'T':
            getattr(self, 'hudStyleOptionT').set_active(True)

        eventbox.connect_object("button-press-event", self.on_button_press, menu)

        debugitem = gtk.MenuItem(_('Debug StatWindows'))
        menu.append(debugitem)
        debugitem.connect("activate", self.debug_stat_windows)

        item5 = gtk.MenuItem(_('Set max seats'))
        menu.append(item5)
        maxSeatsMenu = gtk.Menu()
        item5.set_submenu(maxSeatsMenu)
        for i in range(2, 11, 1):
            item = gtk.MenuItem('%d-max' % i)
            item.ms = i
            maxSeatsMenu.append(item)
            item.connect("activate", self.change_max_seats)
            setattr(self, 'maxSeatsMenuItem%d' % (i - 1), item)

        eventbox.connect_object("button-press-event", self.on_button_press, menu)

        self.mw_created = True
        self.label = label
        menu.show_all()
        self.main_window.show_all()
#        self.topify_window(self.main_window)

    def change_max_seats(self, widget):
        if self.max != widget.ms:
            #print 'change_max_seats', widget.ms
            self.max = widget.ms
            try:
                self.kill()
                self.create(*self.creation_attrs)
                self.update(self.hand, self.config)
            except Exception, e:
                log.error("Exception:",str(e))
                pass

    def set_aggregation(self, widget, val):
        (player_opp, num) = val
        if player_opp == 'P':
            # set these true all the time, set the multiplier to 1 to turn agg off:
            self.hud_params['h_aggregate_ring'] = True
            self.hud_params['h_aggregate_tour'] = True

            if     self.hud_params['h_agg_bb_mult'] != num \
               and getattr(self, 'h_aggBBmultItem'+str(num)).get_active():
                log.debug('set_player_aggregation %d', num)
                self.hud_params['h_agg_bb_mult'] = num
                for mult in ('1', '2', '3', '10', '10000'):
                    if mult != str(num):
                        getattr(self, 'h_aggBBmultItem'+mult).set_active(False)
        else:
            self.hud_params['aggregate_ring'] = True
            self.hud_params['aggregate_tour'] = True

            if     self.hud_params['agg_bb_mult'] != num \
               and getattr(self, 'aggBBmultItem'+str(num)).get_active():
                log.debug('set_opponent_aggregation %d', num)
                self.hud_params['agg_bb_mult'] = num
                for mult in ('1', '2', '3', '10', '10000'):
                    if mult != str(num):
                        getattr(self, 'aggBBmultItem'+mult).set_active(False)

    def set_seats_style(self, widget, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_seats_style'
            prefix = 'h_'
        else:
            param = 'seats_style'
            prefix = ''

        if style == 'A' and getattr(self, prefix+'seatsStyleOptionA').get_active():
            self.hud_params[param] = 'A'
            getattr(self, prefix+'seatsStyleOptionC').set_active(False)
            getattr(self, prefix+'seatsStyleOptionE').set_active(False)
        elif style == 'C' and getattr(self, prefix+'seatsStyleOptionC').get_active():
            self.hud_params[param] = 'C'
            getattr(self, prefix+'seatsStyleOptionA').set_active(False)
            getattr(self, prefix+'seatsStyleOptionE').set_active(False)
        elif style == 'E' and getattr(self, prefix+'seatsStyleOptionE').get_active():
            self.hud_params[param] = 'E'
            getattr(self, prefix+'seatsStyleOptionA').set_active(False)
            getattr(self, prefix+'seatsStyleOptionC').set_active(False)
        log.debug("setting self.hud_params[%s] = %s" % (param, style))

    def set_hud_style(self, widget, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_hud_style'
            prefix = 'h_'
        else:
            param = 'hud_style'
            prefix = ''

        if style == 'A' and getattr(self, prefix+'hudStyleOptionA').get_active():
            self.hud_params[param] = 'A'
            getattr(self, prefix+'hudStyleOptionS').set_active(False)
            getattr(self, prefix+'hudStyleOptionT').set_active(False)
        elif style == 'S' and getattr(self, prefix+'hudStyleOptionS').get_active():
            self.hud_params[param] = 'S'
            getattr(self, prefix+'hudStyleOptionA').set_active(False)
            getattr(self, prefix+'hudStyleOptionT').set_active(False)
        elif style == 'T' and getattr(self, prefix+'hudStyleOptionT').get_active():
            self.hud_params[param] = 'T'
            getattr(self, prefix+'hudStyleOptionA').set_active(False)
            getattr(self, prefix+'hudStyleOptionS').set_active(False)
        log.debug("setting self.hud_params[%s] = %s" % (param, style))

    def update_table_position(self):
        # get table's X/Y position on the desktop, and relocate all of our child windows to accomodate
        # In Windows, we can verify the existence of a Window, with win32gui.IsWindow().  In Linux, there doesn't seem to be a
        # way to verify the existence of a Window, without trying to access it, which if it doesn't exist anymore, results in a
        # big giant X trap and crash.
        # People tell me this is a bad idea, because theoretically, IsWindow() could return true now, but not be true when we actually
        # use it, but accessing a dead window doesn't result in a complete windowing system shutdown in Windows, whereas it does
        # in X. - Eric
        if os.name == 'nt':
            if not win32gui.IsWindow(self.table.number):
                self.parent.kill_hud(self, self.table.name)
                self.parent.kill_hud(self, self.table.name.split(" ")[0])
                #table.name is only a valid handle for ring games ! we are not killing tourney tables here.
                return False
        # anyone know how to do this in unix, or better yet, trap the X11 error that is triggered when executing the get_origin() for a closed window?
        if self.table.gdkhandle is not None:
            (oldx, oldy) = self.table.gdkhandle.get_origin() # In Windows, this call returns (0,0) if it's an invalid window.  In X, the X server is immediately killed.
            #(x, y, width, height) = self.table.get_geometry()
            #print "self.table.get_geometry=",x,y,width,height
            if self.table.oldx != oldx or self.table.oldy != oldy: # If the current position does not equal the stored position, save the new position, and then move all the sub windows.
                self.table.oldx = oldx
                self.table.oldy = oldy
                self.main_window.move(oldx + self.site_params['xshift'], oldy + self.site_params['yshift'])
                adj = self.adj_seats(self.hand, self.config)
                loc = self.config.get_locations(self.table.site, self.max)
                # TODO: is stat_windows getting converted somewhere from a list to a dict, for no good reason?
                for i, w in enumerate(self.stat_windows.itervalues()):
                    (oldx, oldy) = loc[adj[i+1]]
                    w.relocate(oldx, oldy)

                # While we're at it, fix the positions of mucked cards too
                for aux in self.aux_windows:
                    aux.update_card_positions()
                
                self.reposition_windows()
                # call reposition_windows, which apparently moves even hidden windows, where this function does not, even though they do the same thing, afaict

        return True

    def up_update_table_position(self):
#    callback for table moved

#    move the stat windows
        adj = self.adj_seats(self.hand, self.config)
        loc = self.config.get_locations(self.table.site, self.max)
        for i, w in enumerate(self.stat_windows.itervalues()):
            (x, y) = loc[adj[i+1]]
            w.relocate(x, y)
#    move the main window
        self.main_window.move(self.table.x + self.site_params['xshift'], self.table.y + self.site_params['yshift'])
#    and move any auxs
        for aux in self.aux_windows:
            aux.update_card_positions()
        return True

    def on_button_press(self, widget, event):
        if event.button == 1: # if primary button, start movement
            self.main_window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        if event.button == 3: # if secondary button, popup our main popup window
            widget.popup(None, None, None, event.button, event.time)
            return True
        return False

    def kill(self, *args):
#    kill all stat_windows, popups and aux_windows in this HUD
#    heap dead, burnt bodies, blood 'n guts, veins between my teeth
        for s in self.stat_windows.itervalues():
            s.kill_popups()
            try:
                # throws "invalid window handle" in WinXP (sometimes?)
                s.window.destroy()
            except: # TODO: what exception?
                pass
        self.stat_windows = {}
#    also kill any aux windows
        for aux in self.aux_windows:
            aux.destroy()
        self.aux_windows = []

    def resize_windows(self, *args):
        for w in self.stat_windows.itervalues():
            if type(w) == int:
                continue
            rel_x = (w.x - self.table.x) * self.table.width  / self.table.oldwidth
            rel_y = (w.y - self.table.y) * self.table.height / self.table.oldheight
            w.x = self.table.x + rel_x
            w.y = self.table.y + rel_y
            w.window.move(w.x, w.y) 

    def reposition_windows(self, *args):
        self.update_table_position()
        for w in self.stat_windows.itervalues():
            if type(w) == int:
#                print "in reposition, w =", w
                continue
#            print "in reposition, w =", w, w.x, w.y
            w.window.move(w.x, w.y)
        return True

    def debug_stat_windows(self, *args):
#        print self.table, "\n", self.main_window.window.get_transient_for()
        for w in self.stat_windows:
            try:
                print self.stat_windows[w].window.window.get_transient_for()
            except AttributeError:
                print "this window doesnt have get_transient_for"

    def save_layout(self, *args):
        new_layout = [(0, 0)] * self.max
        for sw in self.stat_windows:
            loc = self.stat_windows[sw].window.get_position()
            new_loc = (loc[0] - self.table.x, loc[1] - self.table.y)
            new_layout[self.stat_windows[sw].adj - 1] = new_loc
        self.config.edit_layout(self.table.site, self.max, locations=new_layout)
#    ask each aux to save its layout back to the config object
        [aux.save_layout() for aux in self.aux_windows]
#    save the config object back to the file
        print _("Updating config file")
        self.config.save()

    def adj_seats(self, hand, config):
    # determine how to adjust seating arrangements, if a "preferred seat" is set in the hud layout configuration
#        Need range here, not xrange -> need the actual list
        adj = range(0, self.max + 1) # default seat adjustments = no adjustment
#    does the user have a fav_seat?
        if self.max not in config.supported_sites[self.table.site].layout:
            sys.stderr.write(_("No layout found for %d-max games for site %s\n") % (self.max, self.table.site))
            return adj
        if self.table.site != None and int(config.supported_sites[self.table.site].layout[self.max].fav_seat) > 0:
            try:
                fav_seat = config.supported_sites[self.table.site].layout[self.max].fav_seat
                actual_seat = self.get_actual_seat(config.supported_sites[self.table.site].screen_name)
                for i in xrange(0, self.max + 1):
                    j = actual_seat + i
                    if j > self.max:
                        j = j - self.max
                    adj[j] = fav_seat + i
                    if adj[j] > self.max:
                        adj[j] = adj[j] - self.max
            except Exception, inst:
                sys.stderr.write(_("Exception in Hud.adj_seats\n\n"))
                sys.stderr.write(_("Error is %s") % inst)           # __str__ allows args to printed directly
        return adj

    def get_actual_seat(self, name):
        for key in self.stat_dict:
            if self.stat_dict[key]['screen_name'] == name:
                return self.stat_dict[key]['seat']
        sys.stderr.write(_("Error finding actual seat.\n"))

    def create(self, hand, config, stat_dict, cards):
#    update this hud, to the stats and players as of "hand"
#    hand is the hand id of the most recent hand played at this table
#
#    this method also manages the creating and destruction of stat
#    windows via calls to the Stat_Window class
        self.creation_attrs = hand, config, stat_dict, cards

        self.hand = hand
        if not self.mw_created:
            self.create_mw()

        self.stat_dict = stat_dict
        self.cards = cards
        log.info(_('Creating hud from hand ')+str(hand))
        adj = self.adj_seats(hand, config)
        loc = self.config.get_locations(self.table.site, self.max)
        if loc is None and self.max != 10:
            loc = self.config.get_locations(self.table.site, 10)
        if loc is None and self.max != 9:
            loc = self.config.get_locations(self.table.site, 9)

#    create the stat windows
        for i in xrange(1, self.max + 1):
            (x, y) = loc[adj[i]]
            if i in self.stat_windows:
                self.stat_windows[i].relocate(x, y)
            else:
                self.stat_windows[i] = Stat_Window(game = config.supported_games[self.poker_game],
                                               parent = self,
                                               table = self.table,
                                               x = x,
                                               y = y,
                                               seat = i,
                                               adj = adj[i],
                                               player_id = 'fake',
                                               font = self.font)

        self.topify_window(self.main_window)
        for i in xrange(1, self.max + 1):
            self.topify_window(self.stat_windows[i].window, self.main_window)
        self.stats = []
        game = config.supported_games[self.poker_game]

        for i in xrange(0, game.rows + 1):
            row_list = [''] * game.cols
            self.stats.append(row_list)
        for stat in game.stats:
            self.stats[config.supported_games[self.poker_game].stats[stat].row] \
                      [config.supported_games[self.poker_game].stats[stat].col] = \
                      config.supported_games[self.poker_game].stats[stat].stat_name

#        if os.name == "nt": # we call update_table_position() regularly in Windows to see if we're moving around.  See comments on that function for why this isn't done in X.
#            gobject.timeout_add(500, self.update_table_position)

    def update(self, hand, config):
        self.hand = hand   # this is the last hand, so it is available later
        if os.name == 'nt':
            if self.update_table_position() == False: # we got killed by finding our table was gone
                return

        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.colors['hudfgcolor']))
        for s in self.stat_dict:
            try:
                statd = self.stat_dict[s]
            except KeyError:
                log.error(_("KeyError at the start of the for loop in update in hud_main. How this can possibly happen is totally beyond my comprehension. Your HUD may be about to get really weird. -Eric"))
                log.error(_("(btw, the key was %s and statd is %s") % (s, statd))
                continue
            try:
                self.stat_windows[statd['seat']].player_id = statd['player_id']
                #self.stat_windows[self.stat_dict[s]['seat']].player_id = self.stat_dict[s]['player_id']
            except KeyError: # omg, we have more seats than stat windows .. damn poker sites with incorrect max seating info .. let's force 10 here
                self.max = 10
                self.create(hand, config, self.stat_dict, self.cards)
                self.stat_windows[statd['seat']].player_id = statd['player_id']

            for r in xrange(0, config.supported_games[self.poker_game].rows):
                for c in xrange(0, config.supported_games[self.poker_game].cols):
                    this_stat = config.supported_games[self.poker_game].stats[self.stats[r][c]]
                    number = Stats.do_stat(self.stat_dict, player = statd['player_id'], stat = self.stats[r][c])
                    statstring = "%s%s%s" % (this_stat.hudprefix, str(number[1]), this_stat.hudsuffix)
                    window = self.stat_windows[statd['seat']]

                    if this_stat.hudcolor != "":
                        window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.hudcolor))
                    else:
                        window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.colors['hudfgcolor']))	
                    
                    if this_stat.stat_loth != "":
                        if number[0] < (float(this_stat.stat_loth)/100):
                            window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.stat_locolor))

                    if this_stat.stat_hith != "":
                        if number[0] > (float(this_stat.stat_hith)/100):
                            window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.stat_hicolor))

                    window.label[r][c].set_text(statstring)
                    if statstring != "xxx": # is there a way to tell if this particular stat window is visible already, or no?
                        unhidewindow = True
                    tip = "%s\n%s\n%s, %s" % (statd['screen_name'], number[5], number[3], number[4])
                    Stats.do_tip(window.e_box[r][c], tip)
            if unhidewindow: #and not window.window.visible: # there is no "visible" attribute in gtk.Window, although the docs seem to indicate there should be
                window.window.show_all()
            unhidewindow = False

    def topify_window(self, window, parentwindow=None):
        window.set_focus_on_map(False)
        window.set_accept_focus(False)
#        print "topify_window", window, parentwindow

        if not self.table.gdkhandle:
            self.table.gdkhandle = gtk.gdk.window_foreign_new(int(self.table.number)) # gtk handle to poker window
        if parentwindow is not None:
            window.window.set_transient_for(parentwindow.window)
        else:
            window.window.set_transient_for(self.table.gdkhandle)
        window.set_destroy_with_parent(True)

class Stat_Window:

    def button_press_cb(self, widget, event, *args):
#    This handles all callbacks from button presses on the event boxes in
#    the stat windows.  There is a bit of an ugly kludge to separate single-
#    and double-clicks.
        self.window.show() #_all()

        if event.button == 3:   # right button event
            newpopup = Popup_window(self.window, self)
            #print "added popup", newpopup
            # TODO: how should we go about making sure it doesn't open a dozen popups if you click?
            self.popups.append(newpopup)
            return True

        if event.button == 2:   # middle button event
            self.window.hide()
            return True

        if event.button == 1:   # left button event
            # close on double click for a stat window
            # for those that don't have a mouse with middle button
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.window.hide()
                return True
            # TODO: make position saving save sizes as well?
            if event.state & gtk.gdk.SHIFT_MASK:
                self.window.begin_resize_drag(gtk.gdk.WINDOW_EDGE_SOUTH_EAST, event.button, int(event.x_root), int(event.y_root), event.time)
            else:
                self.window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        return False

    def noop(self, arga=None, argb=None): # i'm going to try to connect the focus-in and focus-out events here, to see if that fixes any of the focus problems.
        return True

    def kill_popup(self, popup):
        #print "remove popup", popup
        self.popups.remove(popup)
        popup.window.destroy()

    def kill_popups(self):
        map(lambda x: x.window.destroy(), self.popups)
        self.popups = { }

    def relocate(self, x, y):
        self.x = x + self.table.x
        self.y = y + self.table.y
        self.window.move(self.x, self.y)

    def __init__(self, parent, game, table, seat, adj, x, y, player_id, font):
        self.parent = parent        # Hud object that this stat window belongs to
        self.game = game            # Configuration object for the curren
        self.table = table          # Table object where this is going
        self.seat = seat            # seat number of his player
        self.adj = adj              # the adjusted seat number for this player
        self.x = x + table.x        # table.x and y are the location of the table
        self.y = y + table.y        # x and y are the location relative to table.x & y
        self.player_id = player_id  # looks like this isn't used ;)
        self.sb_click = 0           # used to figure out button clicks
        self.popups = []            # list of open popups for this stat window
        self.useframes = parent.config.get_frames(parent.site)

        self.window = gtk.Window()
        self.window.set_decorated(0)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_gravity(gtk.gdk.GRAVITY_STATIC)

        self.window.set_title("%s" % seat)
        self.window.set_focus(None) # set gtk default focus widget for this window to None
        self.window.set_focus_on_map(False)
        self.window.set_accept_focus(False)

        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)

        grid = gtk.Table(rows = game.rows, columns = game.cols, homogeneous = False)
        self.grid = grid
        self.window.add(grid)
        self.window.modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)

        self.e_box = []
        self.frame = []
        self.label = []
        usegtkframes = self.useframes
        e_box = self.e_box
        label = self.label
        for r in xrange(game.rows):
            if usegtkframes:
                self.frame.append([])
            e_box.append([])
            label.append([])
            for c in xrange(game.cols):
                if usegtkframes:
                    self.frame[r].append( gtk.Frame() )
                e_box[r].append( gtk.EventBox() )

                e_box[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                e_box[r][c].modify_fg(gtk.STATE_NORMAL, parent.foregroundcolor)

                Stats.do_tip(e_box[r][c], 'stuff')
                if usegtkframes:
                    grid.attach(self.frame[r][c], c, c+1, r, r+1, xpadding = game.xpad, ypadding = game.ypad)
                    self.frame[r][c].add(e_box[r][c])
                else:
                    grid.attach(e_box[r][c], c, c+1, r, r+1, xpadding = game.xpad, ypadding = game.ypad)
                label[r].append( gtk.Label('xxx') )

                if usegtkframes:
                    self.frame[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                label[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                label[r][c].modify_fg(gtk.STATE_NORMAL, parent.foregroundcolor)

                e_box[r][c].add(self.label[r][c])
                e_box[r][c].connect("button_press_event", self.button_press_cb)
                e_box[r][c].connect("focus-in-event", self.noop)
                e_box[r][c].connect("focus", self.noop)
                e_box[r][c].connect("focus-out-event", self.noop)
                label[r][c].modify_font(font)

        self.window.set_opacity(parent.colors['hudopacity'])
        self.window.connect("focus", self.noop)
        self.window.connect("focus-in-event", self.noop)
        self.window.connect("focus-out-event", self.noop)
        self.window.connect("button_press_event", self.button_press_cb)
        self.window.set_focus_on_map(False)
        self.window.set_accept_focus(False)


        self.window.move(self.x, self.y)
        self.window.hide()
        self.window.realize() # window must be realized before it has a gdkwindow so we can attach it to the table window..
#        self.topify_window(self.window)


def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()

class Popup_window:
    def __init__(self, parent, stat_window):
        self.sb_click = 0
        self.stat_window = stat_window
        self.parent = parent

#    create the popup window
        self.window = gtk.Window()
        self.window.set_decorated(0)
        self.window.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.window.set_title("popup")
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_focus_on_map(False)
        self.window.set_accept_focus(False)
        self.window.set_transient_for(parent.get_toplevel())

        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

        self.ebox = gtk.EventBox()
        self.ebox.connect("button_press_event", self.button_press_cb)
        self.lab  = gtk.Label("stuff\nstuff\nstuff")

#    need an event box so we can respond to clicks
        self.window.add(self.ebox)
        self.ebox.add(self.lab)

        self.ebox.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.ebox.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)
        self.window.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.window.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)
        self.lab.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.lab.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)

#    figure out the row, col address of the click that activated the popup
        row = 0
        col = 0
        for r in xrange(0, stat_window.game.rows):
            for c in xrange(0, stat_window.game.cols):
                if stat_window.e_box[r][c] == parent:
                    row = r
                    col = c
                    break

#    figure out what popup format we're using
        popup_format = "default"
        for stat in stat_window.game.stats:
            if stat_window.game.stats[stat].row == row and stat_window.game.stats[stat].col == col:
                popup_format = stat_window.game.stats[stat].popup
                break

#    get the list of stats to be presented from the config
        stat_list = []
        for w in stat_window.parent.config.popup_windows:
            if w == popup_format:
                stat_list = stat_window.parent.config.popup_windows[w].pu_stats
                break

#    get a database connection
#        db_connection = Database.Database(stat_window.parent.config, stat_window.parent.db_name, 'temp')

#    calculate the stat_dict and then create the text for the pu
#        stat_dict = db_connection.get_stats_from_hand(stat_window.parent.hand, stat_window.player_id)
#        stat_dict = self.db_connection.get_stats_from_hand(stat_window.parent.hand)
#        db_connection.close_connection()
        stat_dict = stat_window.parent.stat_dict
        pu_text = ""
        mo_text = ""
        for s in stat_list:
            number = Stats.do_stat(stat_dict, player = int(stat_window.player_id), stat = s)
            mo_text += number[5] + " " + number[4] + "\n"
            pu_text += number[3] + "\n"


        self.lab.set_text(pu_text)
        Stats.do_tip(self.lab, mo_text)
        self.window.show_all()

        self.window.set_transient_for(stat_window.window)

    def button_press_cb(self, widget, event, *args):
#    This handles all callbacks from button presses on the event boxes in
#    the popup windows.  There is a bit of an ugly kludge to separate single-
#    and double-clicks.  This is the same code as in the Stat_window class
        if event.button == 1:   # left button event
            pass

        if event.button == 2:   # middle button event
            pass

        if event.button == 3:   # right button event
            self.stat_window.kill_popup(self)
            return True
#            self.window.destroy()
        return False

    def toggle_decorated(self, widget):
        top = widget.get_toplevel()
        (x, y) = top.get_position()

        if top.get_decorated():
            top.set_decorated(0)
            top.move(x, y)
        else:
            top.set_decorated(1)
            top.move(x, y)

    def topify_window(self, window):
        window.set_focus_on_map(False)
        window.set_accept_focus(False)

        if not self.table.gdkhandle:
            self.table.gdkhandle = gtk.gdk.window_foreign_new(int(self.table.number)) # gtk handle to poker window
#        window.window.reparent(self.table.gdkhandle, 0, 0)
        window.window.set_transient_for(self.table.gdkhandle)
#        window.present()


