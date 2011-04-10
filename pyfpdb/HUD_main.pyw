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
import thread
import time
import string

#    pyGTK modules
import gtk
import gobject

#    FreePokerTools modules
import Configuration
import Database
import Hud
import Options

(options, argv) = Options.fpdb_options()

#    get the correct module for the current os
if sys.platform == 'linux2':
    import XTables as Tables
elif sys.platform == 'darwin':
    import OSXTables as Tables
else: # This is bad--figure out the values for the various windows flavors
    is_windows = True
    import WinTables as Tables

# get config and set up logger
c = Configuration.Config(file=options.config, dbname=options.dbname)
log = Configuration.get_logger("logging.conf", "hud", log_dir=c.dir_log, log_file='HUD-log.txt')

class HUD_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name='fpdb'):
        self.db_name = db_name
        self.config = c
        log.info(_("HUD_main starting: using db name = %s") % (db_name))

        try:
            if not options.errorsToConsole:
                fileName = os.path.join(self.config.dir_log, 'HUD-errors.txt')
                log.info(_("Note: error output is being diverted to:") + fileName)
                log.info(_("Any major error will be reported there _only_."))
                errorFile = open(fileName, 'w', 0)
                sys.stderr = errorFile
                log.info(_("HUD_main: starting ...\n"))

            self.hud_dict = {}
            self.hud_params = self.config.get_hud_ui_parameters()

            # a thread to read stdin
            gobject.threads_init()                        # this is required
            thread.start_new_thread(self.read_stdin, ())  # starts the thread

            # a main window
            self.main_window = gtk.Window()
            
            if os.name == 'nt': # Check for admin rights, don't start auto import if we don't have them
                if (os.sys.getwindowsversion()[0] >= 6):
                    import ctypes
                    if not ctypes.windll.shell32.IsUserAnAdmin():
                        dia = gtk.MessageDialog(parent=self.main_window, flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_ERROR, buttons=(gtk.BUTTONS_OK), message_format=_("No admin rights for HUD"))
                        dia.format_secondary_text(_("Please right click fpdb.exe and HUD_main.exe, select properties, and set them both to run as admin.")+" "+_("You will need to restart fpdb afterwards."))
                        response = dia.run()
                        dia.destroy()
                        return
            
            if options.minimized:
                self.main_window.iconify()
            if options.hidden:
                self.main_window.hide()        
            
            if options.xloc is not None or options.yloc is not None:
                if options.xloc is None:
                    options.xloc = 0
                if options.yloc is None:
                    options.yloc = 0
                self.main_window.move(options.xloc,options.yloc)
            self.main_window.connect("client_moved", self.client_moved)
            self.main_window.connect("client_resized", self.client_resized)
            self.main_window.connect("client_destroyed", self.client_destroyed)
            self.main_window.connect("game_changed", self.game_changed)
            self.main_window.connect("table_changed", self.table_changed)
            self.main_window.connect("destroy", self.destroy)
            self.vb = gtk.VBox()
            self.label = gtk.Label(_('Closing this window will exit from the HUD.'))
            self.vb.add(self.label)
            self.main_window.add(self.vb)
            self.main_window.set_title("HUD Main Window")
            cards = os.path.join(os.getcwd(), '..','gfx','fpdb-cards.png')
            if os.path.exists(cards):
                self.main_window.set_icon_from_file(cards)
            elif os.path.exists('/usr/share/pixmaps/fpdb-cards.png'):
                self.main_window.set_icon_from_file('/usr/share/pixmaps/fpdb-cards.png')
            else:
                self.main_window.set_icon_stock(gtk.STOCK_HOME)
            if not options.hidden:
                self.main_window.show_all()
            gobject.timeout_add(800, self.check_tables)

        except:
            log.exception(_("Error initializing main_window"))
            gtk.main_quit()   # we're hosed, just terminate

    def client_moved(self, widget, hud):
        hud.up_update_table_position()

    def client_resized(self, widget, hud):
#TODO   Don't forget to get rid of this.
        if not is_windows:
            gigobject.idle_add(idle_resize, hud)

    def client_destroyed(self, widget, hud): # call back for terminating the main eventloop
        self.kill_hud(None, hud.table.key)

    def game_changed(self, widget, hud):
        print _("hud_main: Game changed.")

    def table_changed(self, widget, hud):
        self.kill_hud(None, hud.table.key)

    def destroy(self, *args):             # call back for terminating the main eventloop
        log.info(_("Quitting normally"))
        gtk.main_quit()

    def kill_hud(self, event, table):
        gobject.idle_add(idle_kill, self, table)
    
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
        gobject.idle_add(idle_create, self, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards)

    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
        gobject.idle_add(idle_update, self, new_hand_id, table_name, config)

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
            log.info(_("HUD_main.read_stdin: hand processing starting ..."))
            try:
                (table_name, max, poker_game, type, site_id, site_name, num_seats, tour_number, tab_number) = \
                                self.db_connection.get_table_info(new_hand_id)
            except Exception:
                log.exception(_("db error: skipping %s") % new_hand_id)
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
                    log.error(_('hud_dict[%s] was not found\n') % temp_key)
                    log.error(_('will not send hand\n'))
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
                        log.error(_('Table "%s" no longer exists\n') % table_name)
                        return

            self.db_connection.connection.rollback()
            if type == "tour":
                try:
                    self.hud_dict[temp_key].table.check_table_no(self.hud_dict[temp_key])
                except KeyError:
                    pass

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
    gtk.gdk.threads_enter()
    try:
        [aw.update_card_positions() for aw in hud.aux_windows]
        hud.resize_windows()
    except:
        log.exception(_("Error resizing HUD for table: %s.") % hud.table.title)
    finally:
        gtk.gdk.threads_leave()

def idle_kill(hud_main, table):
    gtk.gdk.threads_enter()
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
        gtk.gdk.threads_leave()

def idle_create(hud_main, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards):

    gtk.gdk.threads_enter()
    try:
        if table.gdkhandle is not None:  # on windows this should already be set
            table.gdkhandle = gtk.gdk.window_foreign_new(table.number)
        newlabel = gtk.Label("%s - %s" % (table.site, temp_key))
        hud_main.vb.add(newlabel)
        newlabel.show()
        hud_main.main_window.resize_children()

        hud_main.hud_dict[temp_key].tablehudlabel = newlabel
        hud_main.hud_dict[temp_key].create(new_hand_id, hud_main.config, stat_dict, cards)
        for m in hud_main.hud_dict[temp_key].aux_windows:
            m.create()
            m.update_gui(new_hand_id)
        hud_main.hud_dict[temp_key].update(new_hand_id, hud_main.config)
        hud_main.hud_dict[temp_key].reposition_windows()
    except:
        log.exception(_("Error creating HUD for hand %s.") % new_hand_id)
    finally:
        gtk.gdk.threads_leave()
    return False

def idle_update(hud_main, new_hand_id, table_name, config):
    gtk.gdk.threads_enter()
    try:
        hud_main.hud_dict[table_name].update(new_hand_id, config)
        [aw.update_gui(new_hand_id) for aw in hud_main.hud_dict[table_name].aux_windows]
    except:
        log.exception(_("Error updating HUD for hand %s.") % new_hand_id)
    finally:
        gtk.gdk.threads_leave()
        return False

if __name__== "__main__":

#    start the HUD_main object
    hm = HUD_main(db_name = options.dbname)

#    start the event loop
    gtk.main()
