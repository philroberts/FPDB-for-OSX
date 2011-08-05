#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""Hud_main.py

Main for FreePokerTools HUD.
"""
import L10n
_ = L10n.get_translation()

#    Standard Library modules
import sys
import os
import traceback
import threading
import time
import string

import objc
from Foundation import *
from AppKit import *

#    FreePokerTools modules
import Configuration
import Database
import Hud
import Options

from HandHistoryConverter import getTableTitleRe

(options, argv) = Options.fpdb_options()

#    get the correct module for the current os
if sys.platform[0:5] == 'linux':
    import XTables as Tables
elif sys.platform == 'darwin':
    import OSXTables as Tables
else: # This is bad--figure out the values for the various windows flavors
    is_windows = True
    import WinTables as Tables

# get config and set up logger
c = Configuration.Config(file=options.config, dbname=options.dbname)
log = Configuration.get_logger("logging.conf", "hud", log_dir=c.dir_log, log_file='HUD-log.txt')

class AppDelegate(NSObject):
  def windowWillClose_(self, notification):
    app.terminate_(self)

class UpdateOnGUIThread(NSObject):
    def updateHUD(self):
        idle_update(self.owner, self.new_hand_id, self.table_name, self.config)
    def createHUD(self):
        idle_create(self.owner, self.new_hand_id, self.table, self.temp_key, self.max, self.poker_game, self.type, self.stat_dict, self.cards)

class HUD_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name='fpdb'):
        self.db_name = db_name
        self.config = c
        log.info(_("HUD_main starting") + ": " + _("Using db name = %s") % (db_name))

        try:
            if not options.errorsToConsole:
                fileName = os.path.join(self.config.dir_log, 'HUD-errors.txt')
                log.info(_("Note: error output is being diverted to %s.") % fileName)
                log.info(_("Any major error will be reported there _only_."))
                errorFile = open(fileName, 'w', 0)
                sys.stderr = errorFile
                log.info(_("HUD_main starting"))

            self.hud_dict = {}
            self.hud_params = self.config.get_hud_ui_parameters()

            # a thread to read stdin
            threading.Thread(target=self.read_stdin).start()

            # a main window
            
            if options.xloc is None:
                options.xloc = 0
            if options.yloc is None:
                options.yloc = 0


            
            rect = NSMakeRect(options.xloc + 100, options.yloc + 400, 300, 20)
            self.main_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | NSMiniaturizableWindowMask, NSBackingStoreBuffered, False)
            self.main_window.setTitle_("HUD Main Window")
            self.vb = NSMatrix.alloc().initWithFrame_mode_cellClass_numberOfRows_numberOfColumns_(rect, NSListModeMatrix, NSTextFieldCell.class__(), 1, 1)
            self.vb.setAutosizesCells_(True)
            cell = self.vb.cellAtRow_column_(0, 0)
            cell.setAlignment_(NSCenterTextAlignment)
            cell.setStringValue_("Closing this window will exit from the HUD.")
            self.main_window.setContentView_(self.vb)
            self.delegate = AppDelegate.alloc().init()
            self.main_window.setDelegate_(self.delegate)
            self.main_window.setLevel_(NSFloatingWindowLevel)
            self.main_window.orderWindow_relativeTo_(NSWindowAbove, 0)
            self.main_window.display()

            objc.loadBundle("axlib", globals(), "axlib/build/Release/axlib.framework")
            self.tm = tablemonitor.alloc().init()
            class mycallback(tmcallback):
                def callback_event_(self, tablename, eventtype):
                    if eventtype == "app_activated":
                        for hud in self.owner.hud_dict.values():
                            hud.topify_all()
                        return
                    for k in self.owner.hud_dict.keys():
                        if tablename.startswith(k):
                            hud = self.owner.hud_dict[k]
                            
                            if eventtype == "window_moved":
                                hud.table.check_loc()
                                hud.up_update_table_position()
                            elif eventtype == "window_resized":
                                hud.resize_windows()
                            elif eventtype == "focus_changed":
                                hud.topify_all()
                            elif eventtype == "clicked":
                                hud.topify_all()
                            elif eventtype == "window_destroyed":
                                (_, row, col) = self.owner.vb.getRow_column_ofCell_(None, None, hud.tablehudlabel)
                                self.owner.vb.removeRow_(row)
                                frame = self.owner.main_window.frame()
                                frame.size.height -= 20
                                self.owner.main_window.setFrame_display_(frame, True)
                                hud.main_window.close()
                                hud.kill()
                                del(self.owner.hud_dict[hud.table_name])
                            break
            self.cb = mycallback.alloc().init()
            self.cb.owner = self
            self.tm.registerCallback_(self.cb)
            #self.tm.detectFakePS()
            self.tm.detectPS()
            self.tm.doObserver()
        except:
            log.exception(_("Error initializing main_window"))
            app.terminate_(None)

    def client_moved(self, widget, hud):
        hud.up_update_table_position()

    def client_resized(self, widget, hud):
#TODO   Don't forget to get rid of this.
        if not is_windows:
            gigobject.idle_add(idle_resize, hud)

    def client_destroyed(self, widget, hud): # call back for terminating the main eventloop
        self.kill_hud(None, hud.table.key)

    def game_changed(self, widget, hud):
        print "hud_main: " + _("Game changed.")

    def table_changed(self, widget, hud):
        self.kill_hud(None, hud.table.key)

    def destroy(self, *args):             # call back for terminating the main eventloop
        log.info(_("Quitting normally"))
        app.terminate_(None)

    def kill_hud(self, event, table):
        pass
        #gobject.idle_add(idle_kill, self, table)
    
    def check_tables(self):
        for hud in self.hud_dict.keys():
            self.hud_dict[hud].table.check_table(self.hud_dict[hud])
        return True

    def create_HUD(self, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards):
        """type is "ring" or "tour" used to set hud_params"""

        self.hud_dict[temp_key] = Hud.Hud(self, table, max, poker_game, self.config, self.db_connection)
        self.hud_dict[temp_key].table_name = temp_key
        self.hud_dict[temp_key].stat_dict = stat_dict
        self.hud_dict[temp_key].cards = cards
        table.hud = self.hud_dict[temp_key]
        
        # set agg_bb_mult so that aggregate_tour and aggregate_ring can be ignored,
        # agg_bb_mult == 1 means no aggregation after these if statements:
        if type == "tour" and self.hud_params['aggregate_tour'] == False:
            self.hud_dict[temp_key].hud_params['agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['aggregate_ring'] == False:
            self.hud_dict[temp_key].hud_params['agg_bb_mult'] = 1
        if type == "tour" and self.hud_params['h_aggregate_tour'] == False:
            self.hud_dict[temp_key].hud_params['h_agg_bb_mult'] = 1
        elif type == "ring" and self.hud_params['h_aggregate_ring'] == False:
            self.hud_dict[temp_key].hud_params['h_agg_bb_mult'] = 1
        # sqlcoder: I forget why these are set to true (aren't they ignored from now on?)
        # but I think it's needed:
        self.hud_params['aggregate_ring'] = True
        self.hud_params['h_aggregate_ring'] = True
        # so maybe the tour ones should be set as well? does this fix the bug I see mentioned?
        self.hud_params['aggregate_tour'] = True
        self.hud_params['h_aggregate_tour'] = True

        [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]

        updateObject = UpdateOnGUIThread.alloc().init()
        updateObject.new_hand_id = new_hand_id
        updateObject.table = table
        updateObject.temp_key = temp_key
        updateObject.max = max
        updateObject.poker_game = poker_game
        updateObject.type = type
        updateObject.stat_dict = stat_dict
        updateObject.cards = cards
        updateObject.owner = self
        sel = objc.selector(updateObject.createHUD, signature = "v@:")
        updateObject.performSelectorOnMainThread_withObject_waitUntilDone_(sel, None, False)

    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
        updateObject = UpdateOnGUIThread.alloc().init()
        updateObject.new_hand_id = new_hand_id
        updateObject.table_name = table_name
        updateObject.config = config
        updateObject.owner = self
        sel = objc.selector(updateObject.updateHUD, signature = "v@:")
        updateObject.performSelectorOnMainThread_withObject_waitUntilDone_(sel, None, False)

    def read_stdin(self):            # This is the thread function
        """Do all the non-gui heavy lifting for the HUD program."""

#    This db connection is for the read_stdin thread only. It should not
#    be passed to HUDs for use in the gui thread. HUD objects should not
#    need their own access to the database, but should open their own
#    if it is required.
        self.db_connection = Database.Database(self.config)

#       get hero's screen names and player ids
        self.hero, self.hero_ids = {}, {}
        found = False

        while 1:    # wait for a new hand number on stdin
            pool = NSAutoreleasePool.alloc().init()
            new_hand_id = sys.stdin.readline()
            new_hand_id = string.rstrip(new_hand_id)
            log.debug(_("Received hand no %s") % new_hand_id)
            if new_hand_id == "":           # blank line means quit
                self.destroy()
                break # this thread is not always killed immediately with gtk.main_quit()

#    This block cannot be hoisted outside the while loop, because it would
#    cause a problem when auto importing into an empty db.

#    FIXME: This doesn't work in the case of the player playing on 2
#    sites at once (???)  Eratosthenes
            if not found:
                for site in self.config.get_supported_sites():
                    result = self.db_connection.get_site_id(site)
                    if result:
                        site_id = result[0][0]
                        self.hero[site_id] = self.config.supported_sites[site].screen_name
                        self.hero_ids[site_id] = self.db_connection.get_player_id(self.config, site, self.hero[site_id])
                        if self.hero_ids[site_id] is not None:
                            found = True
                        else:
                            self.hero_ids[site_id] = -1

#        get basic info about the new hand from the db
#        if there is a db error, complain, skip hand, and proceed
            log.info("HUD_main.read_stdin: " + _("Hand processing starting."))
            try:
                (table_name, max, poker_game, type, site_id, site_name, num_seats, tour_number, tab_number) = \
                                self.db_connection.get_table_info(new_hand_id)
            except Exception:
                log.exception(_("database error: skipping %s") % new_hand_id)
                continue

            if type == "tour":   # hand is from a tournament
                temp_key = "%s Table %s" % (tour_number, tab_number)
            else:
                temp_key = table_name

#        Update an existing HUD
            if temp_key in self.hud_dict:
                # get stats using hud's specific params and get cards
                self.db_connection.init_hud_stat_vars( self.hud_dict[temp_key].hud_params['hud_days']
                                                     , self.hud_dict[temp_key].hud_params['h_hud_days'])
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_dict[temp_key].hud_params,
                                                                   self.hero_ids[site_id], num_seats)

                try:
                    self.hud_dict[temp_key].stat_dict = stat_dict
                except KeyError:    # HUD instance has been killed off, key is stale
                    log.error(_('%s was not found') % ("hud_dict[%s]" % temp_key))
                    log.error(_('will not send hand'))
                    # Unlocks table, copied from end of function
                    self.db_connection.connection.rollback()
                    return

                self.hud_dict[temp_key].cards = self.get_cards(new_hand_id)
                [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
                self.update_HUD(new_hand_id, temp_key, self.config)

#        Or create a new HUD
            else:
                # get stats using default params--also get cards
                self.db_connection.init_hud_stat_vars( self.hud_params['hud_days'], self.hud_params['h_hud_days'] )
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_params,
                                                                   self.hero_ids[site_id], num_seats)
                cards = self.get_cards(new_hand_id)
                table_kwargs = dict(table_name=table_name, tournament=tour_number, table_number=tab_number)
                tablewindow = Tables.Table(self.config, site_name, **table_kwargs)
                if tablewindow.number is None:
#        If no client window is found on the screen, complain and continue
                    if type == "tour":
                        table_name = "%s %s" % (tour_number, tab_number)
                    log.error(_("HUD create: table name %s not found, skipping.") % table_name)
                else:
                    tablewindow.key = temp_key
                    tablewindow.max = max
                    tablewindow.site = site_name
                    # Test that the table window still exists
                    if hasattr(tablewindow, 'number'):
                        self.create_HUD(new_hand_id, tablewindow, temp_key, max, poker_game, type, stat_dict, cards)
                    else:
                        log.error(_('Table "%s" no longer exists') % table_name)
                        return

            self.db_connection.connection.rollback()
            if type == "tour":
                try:
                    self.hud_dict[temp_key].table.check_table_no(self.hud_dict[temp_key])
                except KeyError:
                    pass
            del pool

    def get_cards(self, new_hand_id):
        cards = self.db_connection.get_cards(new_hand_id)
        comm_cards = self.db_connection.get_common_cards(new_hand_id)
        if comm_cards != {}: # stud!
            cards['common'] = comm_cards['common']
        return cards
######################################################################
#   idle FUNCTIONS
#
#    These are passed to the event loop by the non-gui thread to do
#    gui things in a thread-safe way. They are passed to the event
#    loop using the gobject.idle_add() function.
#
#    A general rule for gtk is that only 1 thread should be messing
#    with the gui.

def idle_resize(hud):
    #gtk.gdk.threads_enter()
    try:
        [aw.update_card_positions() for aw in hud.aux_windows]
        hud.resize_windows()
    except:
        log.exception(_("Error resizing HUD for table: %s.") % hud.table.title)
    finally:
        pass
        #gtk.gdk.threads_leave()

def idle_kill(hud_main, table):
    #gtk.gdk.threads_enter()
    try:
        if table in hud_main.hud_dict:
            hud_main.vb.remove(hud_main.hud_dict[table].tablehudlabel)
            hud_main.hud_dict[table].main_window.destroy()
            hud_main.hud_dict[table].kill()
            del(hud_main.hud_dict[table])
        hud_main.main_window.resize(1, 1)
    except:
        log.exception(_("Error killing HUD for table: %s.") % table.title)
    finally:
        pass
        #gtk.gdk.threads_leave()

def idle_create(hud_main, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards):
    try:
        hud_main.vb.addRow()
        cell = hud_main.vb.cellAtRow_column_(hud_main.vb.numberOfRows() - 1, 0)
        cell.setStringValue_("%s - %s" % (table.site, temp_key))
        cell.setAlignment_(NSCenterTextAlignment)
        frame = hud_main.main_window.frame()
        frame.size.height += 20
        hud_main.main_window.setFrame_display_(frame, True)
        hud_main.vb.setNeedsDisplay_(True)
        
        hud_main.hud_dict[temp_key].tablehudlabel = hud_main.vb.cellAtRow_column_(hud_main.vb.numberOfRows() - 1, 0)
        hud_main.hud_dict[temp_key].create(new_hand_id, hud_main.config, stat_dict, cards)
        for m in hud_main.hud_dict[temp_key].aux_windows:
            m.create()
            m.update_gui(new_hand_id)
        hud_main.hud_dict[temp_key].update(new_hand_id, hud_main.config)
        hud_main.hud_dict[temp_key].reposition_windows()
    except:
        log.exception(_("Error creating HUD for hand %s.") % new_hand_id)
    return False

def idle_update(hud_main, new_hand_id, table_name, config):
    #gtk.gdk.threads_enter()
    try:
        hud_main.hud_dict[table_name].update(new_hand_id, config)
        [aw.update_gui(new_hand_id) for aw in hud_main.hud_dict[table_name].aux_windows]
    except:
        log.exception(_("Error updating HUD for hand %s.") % new_hand_id)
    finally:
        pass
        #gtk.gdk.threads_leave()
    return False

if __name__== "__main__":
    global app
    app = NSApplication.sharedApplication()
#    start the HUD_main object
    hm = HUD_main(db_name = options.dbname)
#    start the event loop
    app.run()
