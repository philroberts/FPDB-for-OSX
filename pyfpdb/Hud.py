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

from Cocoa import *

titlebarheight = 22

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


def importName(module_name, name):
    """Import a named object 'name' from module 'module_name'."""
#    Recipe 16.3 in the Python Cookbook, 2nd ed.  Thanks!!!!

    try:
        module = __import__(module_name, globals(), locals(), [name])
    except:
        return None
    return(getattr(module, name))

NSToolTipManager.sharedToolTipManager().setInitialToolTipDelay_(0.1)

class MainWindowTextField(NSTextField):
    def initWithFrame_HUD_(self, frame, hud):
        self = super(MainWindowTextField, self).initWithFrame_(frame)
        if self is None: return None

        self.hud = hud
        # Local override of translation routine because pyobjc's autoconversion to NSString doesn't fare well otherwise.
        _ = lambda x: unicode(globals()['_'](x))
        
        menu = NSMenu.alloc().initWithTitle_("HUD menu")
        menu.addItemWithTitle_action_keyEquivalent_(_('Kill This HUD'), objc.selector(self.killHud_, signature = "v@:@"), "")
        menu.addItemWithTitle_action_keyEquivalent_(_('Save HUD Layout'), objc.selector(self.saveLayout_, signature = "v@:@"), "")

        # Player stats
        aggItem = NSMenuItem.alloc().init()
        aggItem.setTitle_(_('Show Player Stats for'))
        aggMenu = NSMenu.alloc().initWithTitle_(_('Show Player Stats for'))
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('For This Blind Level Only'), objc.selector(self.aggregation_, signature = "v@:@"), "").setTag_(1)
        blindItem = NSMenuItem.alloc().init()
        blindItem.setTitle_(_('For Multiple Blind Levels:'))
        aggMenu.addItem_(blindItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.5", "2.0"), objc.selector(self.aggregation_, signature = "v@:@"), "").setTag_(2)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.33", "3.0"), objc.selector(self.aggregation_, signature = "v@:@"), "").setTag_(3)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.1", "10.0"), objc.selector(self.aggregation_, signature = "v@:@"), "").setTag_(10)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('All Levels'), objc.selector(self.aggregation_, signature = "v@:@"), "").setTag_(10000)
        self.playerAgg = aggMenu.itemWithTag_(self.hud.hud_params['h_agg_bb_mult'])
        if self.playerAgg == None:
            self.playerAgg = aggMenu.itemWithTitle_("  " + _('All Levels'))
        self.playerAgg.setState_(NSOnState)

        seatsItem = NSMenuItem.alloc().init()
        seatsItem.setTitle_(_('Number of Seats:'))
        aggMenu.addItem_(seatsItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Any Number'), objc.selector(self.seats_, signature = "v@:@"), "").setRepresentedObject_("A")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Custom'), objc.selector(self.seats_, signature = "v@:@"), "").setRepresentedObject_("C")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Exact'), objc.selector(self.seats_, signature = "v@:@"), "").setRepresentedObject_("T")
        currentStyle = self.hud.hud_params['h_seats_style']
        if currentStyle == 'A':
            self.playerSeats = aggMenu.itemWithTitle_("  " + _('Any Number'))
        elif currentStyle == 'C':
            self.playerSeats = aggMenu.itemWithTitle_("  " + _('Custom'))
        else:
            self.playerSeats = aggMenu.itemWithTitle_("  " + _('Exact'))
        self.playerSeats.setState_(NSOnState)

        sinceItem = NSMenuItem.alloc().init()
        sinceItem.setTitle_(_('Since:'))
        aggMenu.addItem_(sinceItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('All Time'), objc.selector(self.since_, signature = "v@:@"), "").setRepresentedObject_("A")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Session'), objc.selector(self.since_, signature = "v@:@"), "").setRepresentedObject_("S")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('%s Days') % (self.hud.hud_params['hud_days']), objc.selector(self.since_, signature = "v@:@"), "").setRepresentedObject_("T")
        currentSince = self.hud.hud_params['h_hud_style']
        if currentSince == 'A':
            self.playerSince = aggMenu.itemWithTitle_("  " + _('All Time'))
        elif currentSince == 'S':
            self.playerSince = aggMenu.itemWithTitle_("  " + _('Session'))
        else:
            self.playerSince = aggMenu.itemWithTitle_("  " + _('%s Days') % (self.hud.hud_params['hud_days']))
        self.playerSince.setState_(NSOnState)

        menu.addItem_(aggItem)
        menu.setSubmenu_forItem_(aggMenu, aggItem)
        
        # Opponent stats
        aggItem = NSMenuItem.alloc().init()
        aggItem.setTitle_(_('Show Opponent Stats for'))
        aggMenu = NSMenu.alloc().initWithTitle_(_('Show Opponent Stats for'))
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('For This Blind Level Only'), objc.selector(self.aggregationOpp_, signature = "v@:@"), "").setTag_(1)
        blindItem = NSMenuItem.alloc().init()
        blindItem.setTitle_(_('For Multiple Blind Levels:'))
        aggMenu.addItem_(blindItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.5", "2.0"), objc.selector(self.aggregationOpp_, signature = "v@:@"), "").setTag_(2)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.33", "3.0"), objc.selector(self.aggregationOpp_, signature = "v@:@"), "").setTag_(3)
        aggMenu.addItemWithTitle_action_keyEquivalent_(_('%s to %s * Current Blinds') % ("  0.1", "10.0"), objc.selector(self.aggregationOpp_, signature = "v@:@"), "").setTag_(10)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('All Levels'), objc.selector(self.aggregationOpp_, signature = "v@:@"), "").setTag_(10000)
        self.opponentAgg = aggMenu.itemWithTag_(self.hud.hud_params['h_agg_bb_mult'])
        if self.opponentAgg == None:
            self.opponentAgg = aggMenu.itemWithTitle_("  " + _('All Levels'))
        self.opponentAgg.setState_(NSOnState)

        seatsItem = NSMenuItem.alloc().init()
        seatsItem.setTitle_(_('Number of Seats:'))
        aggMenu.addItem_(seatsItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Any Number'), objc.selector(self.seatsOpp_, signature = "v@:@"), "").setRepresentedObject_("A")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Custom'), objc.selector(self.seatsOpp_, signature = "v@:@"), "").setRepresentedObject_("C")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Exact'), objc.selector(self.seatsOpp_, signature = "v@:@"), "").setRepresentedObject_("T")
        currentStyle = self.hud.hud_params['h_seats_style']
        if currentStyle == 'A':
            self.opponentSeats = aggMenu.itemWithTitle_("  " + _('Any Number'))
        elif currentStyle == 'C':
            self.opponentSeats = aggMenu.itemWithTitle_("  " + _('Custom'))
        else:
            self.opponentSeats = aggMenu.itemWithTitle_("  " + _('Exact'))
        self.opponentSeats.setState_(NSOnState)

        sinceItem = NSMenuItem.alloc().init()
        sinceItem.setTitle_(_('Since:'))
        aggMenu.addItem_(sinceItem)
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('All Time'), objc.selector(self.sinceOpp_, signature = "v@:@"), "").setRepresentedObject_("A")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('Session'), objc.selector(self.sinceOpp_, signature = "v@:@"), "").setRepresentedObject_("S")
        aggMenu.addItemWithTitle_action_keyEquivalent_("  " + _('%s Days') % (self.hud.hud_params['hud_days']), objc.selector(self.sinceOpp_, signature = "v@:@"), "").setRepresentedObject_("T")
        currentSince = self.hud.hud_params['h_hud_style']
        if currentSince == 'A':
            self.opponentSince = aggMenu.itemWithTitle_("  " + _('All Time'))
        elif currentSince == 'S':
            self.opponentSince = aggMenu.itemWithTitle_("  " + _('Session'))
        else:
            self.opponentSince = aggMenu.itemWithTitle_("  " + _('%s Days') % (self.hud.hud_params['hud_days']))
        self.opponentSince.setState_(NSOnState)

        menu.addItem_(aggItem)
        menu.setSubmenu_forItem_(aggMenu, aggItem)

        # Set max seats
        maxSeatsItem = NSMenuItem.alloc().init()
        maxSeatsItem.setTitle_(_('Set max seats'))
        maxSeatsMenu = NSMenu.alloc().initWithTitle_(_('Set max seats'))
        for i in range(2, 11, 1):
            maxSeatsMenu.addItemWithTitle_action_keyEquivalent_('%d-max' % i, objc.selector(self.changeMaxSeats_, signature = "v@:@"), "").setTag_(i)
        self.maxSeats = maxSeatsMenu.itemWithTag_(self.hud.max)
        self.maxSeats.setState_(NSOnState)
        menu.addItem_(maxSeatsItem)
        menu.setSubmenu_forItem_(maxSeatsMenu, maxSeatsItem)

        self.setMenu_(menu)
        
        return self

    def mouseDragged_(self, event):
        frame = self.owner.frame()
        frame.origin.x += event.deltaX()
        frame.origin.y -= event.deltaY()
        self.owner.setFrame_display_(frame, True)

    def killHud_(self, sender):
        self.hud.parent.kill_hud(self.hud.table_name)
    def saveLayout_(self, sender):
        self.hud.save_layout()

    # Player stats menu actions
    def aggregation_(self, sender):
        self.playerAgg.setState_(NSOffState)
        self.playerAgg = sender
        sender.setState_(NSOnState)
        self.hud.set_aggregation(('P', sender.tag()))
    def seats_(self, sender):
        self.playerSeats.setState_(NSOffState)
        self.playerSeats = sender
        sender.setState_(NSOnState)
        self.hud.set_seats_style(('P', sender.representedObject()))
    def since_(self, sender):
        self.playerSince.setState_(NSOffState)
        self.playerSince = sender
        sender.setState_(NSOnState)
        self.hud.set_hud_style(('P', sender.representedObject()))

    # Opponent stats menu actions
    def aggregationOpp_(self, sender):
        self.opponentAgg.setState_(NSOffState)
        self.opponentAgg = sender
        sender.setState_(NSOnState)
        self.hud.set_aggregation(('O', sender.tag()))
    def seatsOpp_(self, sender):
        self.opponentSeats.setState_(NSOffState)
        self.opponentSeats = sender
        sender.setState_(NSOnState)
        self.hud.set_seats_style(('O', sender.representedObject()))
    def sinceOpp_(self, sender):
        self.opponentSince.setState_(NSOffState)
        self.opponentSince = sender
        sender.setState_(NSOnState)
        self.hud.set_hud_style(('O', sender.representedObject()))

    # Set max seats menu actions
    def changeMaxSeats_(self, sender):
        self.maxSeats.setState_(NSOffState)
        self.maxSeats = sender
        sender.setState_(NSOnState)
        self.hud.change_max_seats(sender.tag())

def parseColor(colorstring):
    r = int(colorstring[1:3], 16) / 255.0
    g = int(colorstring[3:5], 16) / 255.0
    b = int(colorstring[5:7], 16) / 255.0
    return NSColor.colorWithDeviceRed_green_blue_alpha_(r, g, b, 1)

class Hud:
    def __init__(self, parent, table, max, poker_game, config, db_connection):
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

        self.backgroundcolor = parseColor(self.colors['hudbgcolor'])
        self.foregroundcolor = parseColor(self.colors['hudfgcolor'])

        self.font = NSFont.fontWithName_size_(font, font_size)
        self.fontpixels = NSString.stringWithString_(self.hud_ui['label']).sizeWithAttributes_(NSDictionary.dictionaryWithObject_forKey_(self.font, NSFontAttributeName))
        self.fontpixels.width += 6 # Account for the padding needed for NSTextField

        game_params = config.get_game_parameters(self.poker_game)
        # if there are AUX windows configured, set them up (Ray knows how this works, if anyone needs info)
        if False and not game_params['aux'] == [""]:
            for aux in game_params['aux']:
                aux_params = config.get_aux_parameters(aux)
                my_import = importName(aux_params['module'], aux_params['class'])
                if my_import == None:
                    continue
                self.aux_windows.append(my_import(self, config, aux_params))

        self.creation_attrs = None

    # Set up a main window for this this instance of the HUD
    def create_mw(self):
        adjustedy = NSScreen.mainScreen().frame().size.height - self.table.y - self.fontpixels.height - titlebarheight
        rect = NSMakeRect(self.table.x, adjustedy, self.fontpixels.width, self.fontpixels.height)
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, NSBorderlessWindowMask, NSBackingStoreBuffered, False)
        win.setTitle_("%s FPDBHUD" % (self.table.name))
            
        label = MainWindowTextField.alloc().initWithFrame_HUD_(rect, self)
        label.owner = win
        label.setStringValue_(self.hud_ui['label'])
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBezeled_(False)
        label.setFont_(self.font)
        label.setTextColor_(self.foregroundcolor)
        label.setBackgroundColor_(self.backgroundcolor)
        win.setContentView_(label)
        win.setAlphaValue_(self.colors["hudopacity"])
        self.main_window = win

        self.mw_created = True
        self.label = label
        self.topify_window(self.main_window)

    def change_max_seats(self, seats):
        if self.max != seats:
            self.max = seats
            try:
                self.kill()
                self.create(*self.creation_attrs)
                self.update(self.hand, self.config)
            except Exception, e:
                log.error("Exception:",str(e))
                pass

    def set_aggregation(self, val):
        (player_opp, num) = val
        if player_opp == 'P':
            # set these true all the time, set the multiplier to 1 to turn agg off:
            self.hud_params['h_aggregate_ring'] = True
            self.hud_params['h_aggregate_tour'] = True

            if     self.hud_params['h_agg_bb_mult'] != num:
                log.debug('set_player_aggregation %d', num)
                self.hud_params['h_agg_bb_mult'] = num
        else:
            self.hud_params['aggregate_ring'] = True
            self.hud_params['aggregate_tour'] = True

            if     self.hud_params['agg_bb_mult'] != num:
                log.debug('set_opponent_aggregation %d', num)
                self.hud_params['agg_bb_mult'] = num

    def set_seats_style(self, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_seats_style'
        else:
            param = 'seats_style'

        log.debug("setting self.hud_params[%s] = %s" % (param, style))
        self.hud_params[param] = style

    def set_hud_style(self, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_hud_style'
        else:
            param = 'hud_style'

        log.debug("setting self.hud_params[%s] = %s" % (param, style))
        self.hud_params[param] = style

    def update_table_position(self):
#    callback for table moved
#    OSX uses different coordinate systems in different APIs.  Convert CGWindow coords into NSWindow coords.
        adjustedy = NSScreen.mainScreen().frame().size.height - self.table.y - self.fontpixels.height - titlebarheight
#    move the main window - use the "old" position as it's already updated by the time we get here.
        frame = self.main_window.frame()
        frame.origin.x = self.table.x
        frame.origin.y = adjustedy
        self.main_window.setFrame_display_(frame, True)
        self.topify_window(self.main_window)
#    move the stat windows
        adj = self.adj_seats(self.hand, self.config)
        loc = self.config.get_locations(self.table.site, self.max)
        for i, w in enumerate(self.stat_windows.itervalues()):
            (x, y) = loc[adj[i+1]]
            w.relocate(x, y)
            self.topify_window(w.window)
#    and move any auxs
        for aux in self.aux_windows:
            aux.update_card_positions()
        return True
    
    def topify_all(self):
        self.topify_window(self.main_window)
        for w in self.stat_windows.values():
            self.topify_window(w.window)
    
    def kill(self, *args):
#    kill all stat_windows, popups and aux_windows in this HUD
#    heap dead, burnt bodies, blood 'n guts, veins between my teeth
        for s in self.stat_windows.itervalues():
            s.kill_popups()
            try:
                # Defer release til after this loop when we empty the dict.
                s.window.setReleasedWhenClosed_(False)
                s.window.close()
            except: # TODO: what exception?
                pass
        self.stat_windows = {}
#    also kill any aux windows
        for aux in self.aux_windows:
            aux.destroy()
        self.aux_windows = []

    def resize_windows(self, *args):
        adjustedy = NSScreen.mainScreen().frame().size.height - self.table.y - titlebarheight
        for w in self.stat_windows.itervalues():
            if type(w) == int:
                continue
            frame = w.window.frame()
            rel_x = (frame.origin.x - self.table.x) * self.table.width  / float(self.table.oldwidth)
            rel_y = (frame.origin.y - adjustedy) * self.table.height / float(self.table.oldheight)
            frame.origin.x = int(rel_x + self.table.x)
            frame.origin.y = int(rel_y + adjustedy)
            w.window.setFrame_display_(frame, False)
        [aw.update_card_positions() for aw in self.aux_windows]

    def save_layout(self, *args):
        new_layout = [(0, 0)] * self.max
        for sw in self.stat_windows:
            frame = self.stat_windows[sw].window.frame()
            adjustedy = NSScreen.mainScreen().frame().size.height - frame.origin.y - frame.size.height - titlebarheight

            new_loc = (int(frame.origin.x - self.table.x), int(adjustedy - self.table.y))
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
            sys.stderr.write(_("No layout found for %d-max games for site %s.") % (self.max, self.table.site))
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
                sys.stderr.write(_("Exception in %s\n") % "Hud.adj_seats")
                sys.stderr.write("Error:" + (" %s\n") % inst)           # __str__ allows args to printed directly
        return adj

    def get_actual_seat(self, name):
        for key in self.stat_dict:
            if self.stat_dict[key]['screen_name'] == name:
                return self.stat_dict[key]['seat']
        sys.stderr.write(_("Error finding actual seat."))

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
        log.info(_('Creating hud from hand %s') % str(hand))
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
            self.topify_window(self.stat_windows[i].window)

        game = config.supported_games[self.poker_game]
        self.stats = [None for i in range (game.rows*game.cols)] # initialize to None for not present stats at [row][col]
        for i in range (game.rows*game.cols):
            if config.supported_games[self.poker_game].stats[i] is not None:
                self.stats[i] = config.supported_games[self.poker_game].stats[i].stat_name

    def update(self, hand, config):
        self.hand = hand   # this is the last hand, so it is available later

        for s in self.stat_dict:
            try:
                statd = self.stat_dict[s]
            except KeyError:
                log.error(_("HUD process overloaded, skipping this hand."))
                continue
            try:
                self.stat_windows[statd['seat']].player_id = statd['player_id']
            except KeyError: # omg, we have more seats than stat windows .. damn poker sites with incorrect max seating info .. let's force 10 here
                self.max = 10
                self.create(hand, config, self.stat_dict, self.cards)
                self.stat_windows[statd['seat']].player_id = statd['player_id']

            unhidewindow = False
            for r in xrange(0, config.supported_games[self.poker_game].rows):
                for c in xrange(0, config.supported_games[self.poker_game].cols):
                    # stats may be None if the user hasn't configured a stat for this row,col
                    if self.stats[r*config.supported_games[self.poker_game].cols+c] is not None:
                        this_stat = config.supported_games[self.poker_game].stats[r*config.supported_games[self.poker_game].cols+c]
                        number = Stats.do_stat(self.stat_dict, player = statd['player_id'], stat = self.stats[r*config.supported_games[self.poker_game].cols+c])
                        statstring = "%s%s%s" % (this_stat.hudprefix, str(number[1]), this_stat.hudsuffix)
                        window = self.stat_windows[statd['seat']]
    
                        if this_stat.hudcolor != "":
                            window.labels[r][c].setTextColor_(parseColor(this_stat.hudcolor))
                        else:
                            window.labels[r][c].setTextColor_(parseColor(self.colors['hudfgcolor']))
                        
                        if this_stat.stat_loth != "":
                            if number[0] < (float(this_stat.stat_loth)/100):
                                window.labels[r][c].setTextColor_(parseColor(this_stat.stat_locolor))
     
                        if this_stat.stat_hith != "":
                            if number[0] > (float(this_stat.stat_hith)/100):
                                window.labels[r][c].setTextColor_(parseColor(this_stat.stat_hicolor))
    
                        window.labels[r][c].setStringValue_(unicode(statstring))
                        if statstring != "xxx": # is there a way to tell if this particular stat window is visible already, or no?
                            unhidewindow = True
                        tip = "%s\n%s\n%s, %s" % (statd['screen_name'], number[5], number[3], number[4])
                        Stats.do_tip(window.labels[r][c], tip)
            if unhidewindow:
                window.window.display()
            unhidewindow = False

    def topify_window(self, window):
        window.orderWindow_relativeTo_(NSWindowAbove, self.table.number)

class StatWindowTextField(NSTextField):
    def mouseDragged_(self, event):
        frame = self.owner.window.frame()
        frame.origin.x += event.deltaX()
        frame.origin.y -= event.deltaY()
        self.owner.window.setFrame_display_(frame, True)
    def rightMouseDown_(self, event):
        newpopup = Popup_window(self, self.owner)
        self.owner.popups.append(newpopup)

class Stat_Window:
    def kill_popup(self, popup):
        self.popups.remove(popup)
        del popup.window

    def kill_popups(self):
        for x in self.popups:
            del x.window
        self.popups = []

    def relocate(self, x, y):
        frame = self.window.frame()
        frame.origin.x = x + self.table.x
        frame.origin.y = NSScreen.mainScreen().frame().size.height - self.table.y - y - titlebarheight - frame.size.height
        self.window.setFrame_display_(frame, True)

    def __init__(self, parent, game, table, seat, adj, x, y, player_id, font):
        self.parent = parent        # Hud object that this stat window belongs to
        self.game = game            # Configuration object for the curren
        self.table = table          # Table object where this is going
        self.seat = seat            # seat number of his player
        self.adj = adj              # the adjusted seat number for this player
        self.x = x + table.x        # table.x and y are the location of the table
        self.fontpixels = NSString.stringWithString_("player").sizeWithAttributes_(NSDictionary.dictionaryWithObject_forKey_(self.parent.font, NSFontAttributeName))
        self.y = NSScreen.mainScreen().frame().size.height - table.y - y - titlebarheight - self.fontpixels.height * game.rows
        self.player_id = player_id  # looks like this isn't used ;)
        self.sb_click = 0           # used to figure out button clicks
        self.popups = []            # list of open popups for this stat window
        self.useframes = parent.config.get_frames(parent.site)

        colWidth = self.fontpixels.width
        rowHeight = self.fontpixels.height
        rect = NSMakeRect(self.x, self.y, colWidth * game.cols, rowHeight * game.rows)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, NSBorderlessWindowMask, NSBackingStoreBuffered, False)
        self.window.setAllowsToolTipsWhenApplicationIsInactive_(True)
        self.window.setTitle_("%s" % seat)
        self.window.setAlphaValue_(parent.colors['hudopacity'])
        self.labels = []
        
        for r in xrange(game.rows):
            self.labels.append([])
            for c in xrange(game.cols):
                rect = NSMakeRect(c * colWidth, (game.rows - r - 1) * rowHeight, colWidth, rowHeight)
                label = StatWindowTextField.alloc().initWithFrame_(rect)
                label.owner = self
                label.setStringValue_('xxx')
                label.setTextColor_(parent.foregroundcolor)
                label.setBackgroundColor_(parent.backgroundcolor)
                label.setFont_(parent.font)
                label.setBezeled_(False)
                label.setEditable_(False)
                label.setSelectable_(False)
                label.setAlignment_(NSCenterTextAlignment)
                for stat in game.stats:
                    if stat.row == r and stat.col == c:
                        label.popup_format = stat.popup
                        break
                self.window.contentView().addSubview_(label)
                self.labels[r].append(label)

class PopupTextField(NSTextField):
    def mouseDragged_(self, event):
        frame = self.owner.window.frame()
        frame.origin.x += event.deltaX()
        frame.origin.y -= event.deltaY()
        self.owner.window.setFrame_display_(frame, True)
    def rightMouseDown_(self, event):
        self.owner.stat_window.kill_popup(self.owner)

class Popup_window:
    def __init__(self, parent, stat_window):
        self.stat_window = stat_window

        #    get the list of stats to be presented from the config
        stat_list = []
        for w in stat_window.parent.config.popup_windows:
            if w == parent.popup_format:
                stat_list = stat_window.parent.config.popup_windows[w].pu_stats
                break

        self.fontpixels = NSString.stringWithString_("totalprofit=$-10.00").sizeWithAttributes_(NSDictionary.dictionaryWithObject_forKey_(self.stat_window.parent.font, NSFontAttributeName))

        colWidth = self.fontpixels.width
        rowHeight = self.fontpixels.height
        frame = stat_window.window.frame()
        rect = NSMakeRect(frame.origin.x, frame.origin.y - rowHeight * len(stat_list) / 2, colWidth, rowHeight * len(stat_list))
        screenheight = NSScreen.mainScreen().frame().size.height - titlebarheight
        if rect.origin.y < 0:
            rect.origin.y = 0
        elif rect.origin.y + rect.size.height > screenheight:
            rect.origin.y = screenheight - rect.size.height
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, NSBorderlessWindowMask, NSBackingStoreBuffered, False)
        self.window.setAllowsToolTipsWhenApplicationIsInactive_(True)
        self.window.setTitle_("popup")
        self.window.setAlphaValue_(stat_window.parent.colors['hudopacity'])
        rect = NSMakeRect(0, 0, colWidth, len(stat_list) * rowHeight)
        r = 0
        for s in stat_list:
            rect = NSMakeRect(0, (len(stat_list) - r - 1) * rowHeight, colWidth, rowHeight)
            label = PopupTextField.alloc().initWithFrame_(rect)
            label.setTextColor_(stat_window.parent.foregroundcolor)
            label.setBackgroundColor_(stat_window.parent.backgroundcolor)
            label.setFont_(stat_window.parent.font)
            label.setBezeled_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setAlignment_(NSCenterTextAlignment)
            label.owner = self

            number = Stats.do_stat(stat_window.parent.stat_dict, player = int(stat_window.player_id), stat = s, handid = int(stat_window.parent.hand))
            label.setStringValue_(number[3])

            Stats.do_tip(label, number[5] + " " + number[4])
            self.window.contentView().addSubview_(label)
            r += 1
        self.window.orderFrontRegardless()
