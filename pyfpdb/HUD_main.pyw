#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2008-2012,  Ray E. Barker
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

#TODO


"""Hud_main.py

Main for FreePokerTools HUD.
"""
import L10n
_ = L10n.init_translation()

#    Standard Library modules
import codecs
import sys
import os
import thread
import time
import string
import logging

from PyQt5.QtCore import (QCoreApplication, QMetaObject, QObject, Qt,
                          QThread, pyqtSignal)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow,
                             QVBoxLayout, QWidget)

#    FreePokerTools modules
import Configuration
import Database
import Hud
import Options
import Deck

(options, argv) = Options.fpdb_options()

# get config and set up logger
Configuration.set_logfile(u"HUD-log.txt")
c = Configuration.Config(file=options.config, dbname=options.dbname)
log = logging.getLogger("hud")

# get the correct module for the current os
if c.os_family == 'Linux':
    import XTables as Tables
elif c.os_family == 'Mac':
    import OSXTables as Tables
elif c.os_family in ('XP', 'Win7'):
    import WinTables as Tables

class Reader(QObject):
    handRead = pyqtSignal(str)

    def readStdin(self):
        while 1:    # wait for a new hand number on stdin
            time.sleep(0.45) # pause an arbitrary amount of time
                            # This throttles thru-put to about 2 or 3
                            # hands per second.  Otherwise, the downstream
                            # code can become flooded and errors start to
                            # occur due to stat_dict being overwritten before
                            # the previous hand completed processing.
                            # Flooding normally occurs when the hud "fast forwards"
                            # at tables where a bunch of hands have already been played
                            # with the HUD switched off.
            new_hand_id = string.rstrip(sys.stdin.readline())
            log.debug(_("Received hand no %s") % new_hand_id)
            self.handRead.emit(new_hand_id)

class HUD_main(QObject):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name='fpdb'):
        QObject.__init__(self)
        self.db_name = db_name
        self.config = c
        log.info(_("HUD_main starting") + ": " + _("Using db name = %s") % (db_name))

        if not options.errorsToConsole:
            fileName = os.path.join(self.config.dir_log, u'HUD-errors.txt')
            log.info(_("Note: error output is being diverted to %s.") % fileName)
            log.info(_("Any major error will be reported there _only_."))
            errorFile = codecs.open(fileName, 'w', 'utf-8')
            sys.stderr = errorFile
            log.info(_("HUD_main starting"))
        self.db_connection = Database.Database(self.config)
        #update and save config
        self.hud_dict = {}
        self.blacklist = [] #a list of blacklisted table numbers (handles)
        self.hud_params = self.config.get_hud_ui_parameters()
        self.deck = Deck.Deck(self.config,
            deck_type=self.hud_params["deck_type"], card_back=self.hud_params["card_back"],
            width=self.hud_params['card_wd'], height=self.hud_params['card_ht'])

        # a thread to read stdin
        self.stdinThread = QThread()
        self.stdinReader = Reader()
        self.stdinReader.moveToThread(self.stdinThread)
        self.stdinReader.handRead.connect(self.read_stdin)
        self.stdinThread.started.connect(self.stdinReader.readStdin)
        self.stdinThread.start()

        # a main window
        self.main_window = QWidget(None, Qt.Dialog)

        if options.xloc is not None or options.yloc is not None:
            if options.xloc is None:
                options.xloc = 0
            if options.yloc is None:
                options.yloc = 0
            self.main_window.move(options.xloc,options.yloc)
        self.main_window.destroyed.connect(self.destroy)
        self.vb = QVBoxLayout()
        self.vb.setContentsMargins(2, 0, 2, 0)
        self.main_window.setLayout(self.vb)
        self.label = QLabel(_('Closing this window will exit from the HUD.'))
        self.main_window.closeEvent = lambda event: sys.exit()
        self.vb.addWidget(self.label)
        self.main_window.setWindowTitle("HUD Main Window")
        cards = os.path.join(self.config.graphics_path,'fpdb-cards.png')
        if os.path.exists(cards):
            self.main_window.setWindowIcon(QIcon(cards))

        self.startTimer(800)
        self.main_window.show()

    def timerEvent(self, event):
        self.check_tables()
        if self.config.os_family == "Mac":
            for hud in self.hud_dict.values():
                for aw in hud.aux_windows:
                    if not hasattr(aw, 'm_windows'):
                        continue
                    for w in aw.m_windows.values():
                        if w.isVisible():
                            hud.table.topify(w)


    def client_moved(self, widget, hud):
        log.debug(_("client_moved event"))
        idle_move(hud)

    def client_resized(self, widget, hud):
        log.debug(_("client_resized event"))
        idle_resize(hud)

    def client_destroyed(self, widget, hud): # call back for terminating the main eventloop
        log.debug(_("client_destroyed event"))
        self.kill_hud(None, hud.table.key)

#    def game_changed(self, widget, hud):
#        print "hud_main: " + _("Game changed.")

    def table_title_changed(self, widget, hud):
        print "hud_main: " + _("Table title changed, killing current hud")
        self.kill_hud(None, hud.table.key)

    def table_is_stale(self, hud):
        print "hud_main: " + _("Moved to a new table, killing current hud")
        self.kill_hud(None, hud.table.key)
        
    def destroy(self, *args):             # call back for terminating the main eventloop
        log.info(_("Quitting normally"))
        QCoreApplication.quit()

    def kill_hud(self, event, table):
        log.debug(_("kill_hud event"))
        idle_kill(self, table)

    def blacklist_hud(self, event, table):
        log.debug(_("blacklist_hud event"))
        self.blacklist.append(self.hud_dict[table].tablenumber)
        idle_kill(self, table)

    def check_tables(self):
        idle_check_tables(self)

    def create_HUD(self, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards):
        """type is "ring" or "tour" used to set hud_params"""

        self.hud_dict[temp_key] = Hud.Hud(self, table, max, poker_game, type, self.config)
        self.hud_dict[temp_key].table_name = temp_key
        self.hud_dict[temp_key].stat_dict = stat_dict
        self.hud_dict[temp_key].cards = cards
        self.hud_dict[temp_key].max = max
        
        table.hud = self.hud_dict[temp_key]
    
        self.hud_dict[temp_key].hud_params['new_max_seats'] = None #trigger for seat layout change
        #fixme - passing self.db_connection into another thread
        # is probably pointless.
        [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
        idle_create(self, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards)

    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
        idle_update(self, new_hand_id, table_name, config)

    def read_stdin(self, new_hand_id):
#       get hero's screen names and player ids
        self.hero, self.hero_ids = {}, {}
        found = False
        
        enabled_sites = self.config.get_supported_sites()
        if not enabled_sites:
            log.exception(_("No enabled sites found"))
            self.db_connection.connection.rollback()
            self.destroy()
            return
        
        aux_disabled_sites = []
        for i in enabled_sites:
            if not c.get_site_parameters(i)['aux_enabled']:
                log.info(_("Aux disabled for site %s") % i)
                aux_disabled_sites.append(i)

        self.db_connection.connection.rollback() # release lock from previous iteration
        if new_hand_id == "":           # blank line means quit
            self.db_connection.connection.rollback()
            sys.exit()

#    The following block cannot be hoisted outside the while loop, because it would
#    cause a problem when auto importing into an empty db.
#    FIXME (corner-case): Because this block only executes once when the hud starts,
#    if our hero plays at another site for the __first_time__ during that session,
#     the hud won't display correctly, because the heroname isn't known yet.

        if not found:
            for site in enabled_sites:
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
        #log.info("HUD_main.read_stdin: " + _("Hand processing starting."))
        try:
            (table_name, max, poker_game, type, fast, site_id, site_name, num_seats, tour_number, tab_number) = \
                            self.db_connection.get_table_info(new_hand_id)
        except Exception:
            log.error(_("database error: skipping %s") % new_hand_id)
            return

        if fast:
            #we are rush/zoom
            return

        # Do nothing if this site is on the ignore list
        if site_name in aux_disabled_sites:
            return
        # Do nothing if this site is not enabled
        if site_name not in enabled_sites:
            return

        # regenerate temp_key for this hand- this is the tablename (+ tablenumber (if mtt))
        if type == "tour":   # hand is from a tournament
            temp_key = "%s Table %s" % (tour_number, tab_number)
        else:
            temp_key = table_name

        if type == "tour":
            #
            # Has there been a table-change?  if yes, clean-up the current hud
            # Two checks are needed,
            #  if a hand is received for an existing table-number, but the table-title has changed,  kill the old hud
            #  if a hand is received for a "new" table number, clean-up the old one and create a new hud
            #
            if temp_key in self.hud_dict:
                # check if our attached window's titlebar has changed, if it has
                # this method will emit a "table_changed" signal which will trigger
                # a kill
                if self.hud_dict[temp_key].table.has_table_title_changed(self.hud_dict[temp_key]):
                    #table has been renamed; the idle_kill method will housekeep hud_dict
                    # We will skip this hand, to give time for the idle function
                    # to complete its' work.  Normal service will be resumed on the next hand
                    self.table_is_stale(self.hud_dict[temp_key])
                    return # abort processing this hand
            else:
                #check if the tournament number is in the hud_dict under a different table
                #if it is, trigger a hud_kill - we can safely drop through the rest of the code
                # because this is a brand-new hud being created
                for k in self.hud_dict:
                    if k.startswith(tour_number):
                        self.table_is_stale(self.hud_dict[k])
                        continue # this cancels the "for k in...." loop, NOT the outer while: loop


#       detect maxseats changed in hud
#       if so, kill and create new hud with specified "max"
        if temp_key in self.hud_dict:
            try:
                newmax = self.hud_dict[temp_key].hud_params['new_max_seats']  # trigger
                if newmax and self.hud_dict[temp_key].max != newmax:  # max has changed
                    self.kill_hud("activate", temp_key)   # kill everything
                    while temp_key in self.hud_dict: time.sleep(0.5)   # wait for idle_kill to complete
                    max = newmax   # "max" localvar used in create_HUD call below
                self.hud_dict[temp_key].hud_params['new_max_seats'] = None   # reset trigger
            except:
                pass
                    
#       detect poker_game changed in latest hand (i.e. mixed game)
#       if so, kill and create new hud with specified poker_game
#       Note that this will reset the aggretation params for that table
        if temp_key in self.hud_dict:
            if self.hud_dict[temp_key].poker_game != poker_game:
                print "game changed!:", poker_game
                try:
                    self.kill_hud("activate", temp_key)   # kill everything
                    while temp_key in self.hud_dict: time.sleep(0.5)   # wait for idle_kill to complete
                except:
                    pass

#        Update an existing HUD
        if temp_key in self.hud_dict:
            # get stats using hud's specific params and get cards
            self.db_connection.init_hud_stat_vars( self.hud_dict[temp_key].hud_params['hud_days']
                                                 , self.hud_dict[temp_key].hud_params['h_hud_days'])
            #print "update an existing hud ", temp_key, self.hud_dict[temp_key].hud_params
            stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_dict[temp_key].hud_params,
                                                               self.hero_ids[site_id], num_seats)

            try:
                self.hud_dict[temp_key].stat_dict = stat_dict
            except KeyError:    # HUD instance has been killed off, key is stale
                log.error(_('%s was not found') % ("hud_dict[%s]" % temp_key))
                log.error(_('will not send hand'))
                return

            self.hud_dict[temp_key].cards = self.get_cards(new_hand_id, poker_game)
            #fixme - passing self.db_connection into another thread
            # is probably pointless
            [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
            self.update_HUD(new_hand_id, temp_key, self.config)

#        Or create a new HUD
        else:
            # get stats using default params--also get cards

            self.db_connection.init_hud_stat_vars( self.hud_params['hud_days'], self.hud_params['h_hud_days'] )
            stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, type, self.hud_params,
                                                               self.hero_ids[site_id], num_seats)

            #Confirm our hero is seated for this hand, otherwise we must __not__ create a hud
            # because it is impossible to work out who is sitting where, and that working-out
            # of seat positions __only__ happens during creation.  (see Aux_Base.Aux_Seats.adj_seats())
            #Fixes issue with 888/pacific which includes cash hands before the hero is dealt-in
            hero_found = False
            for key in stat_dict:
                if stat_dict[key]['screen_name'] == self.hero[site_id]:
                    hero_found = True
                    break
            if not hero_found:
                log.info(_('hud not created yet, because hero is not seated for this hand'))
                return
                
            cards = self.get_cards(new_hand_id, poker_game)
            table_kwargs = dict(table_name=table_name, tournament=tour_number, table_number=tab_number)
            tablewindow = Tables.Table(self.config, site_name, **table_kwargs)
            if tablewindow.number is None:
#        If no client window is found on the screen, complain and continue
                if type == "tour":
                    table_name = "%s %s" % (tour_number, tab_number)
                log.error(_("HUD create: table name %s not found, skipping.") % table_name)
                return
            elif tablewindow.number in self.blacklist:
                return    #no hud please, we are blacklisted
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

    def get_cards(self, new_hand_id, poker_game):
        cards = self.db_connection.get_cards(new_hand_id)
        if poker_game in ['holdem','omahahi','omahahilo']:
            comm_cards = self.db_connection.get_common_cards(new_hand_id)
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
    try:
        hud.resize_windows()
        [aw.resize_windows() for aw in hud.aux_windows]
    except:
        log.exception(_("Error resizing HUD for table: %s.") % hud.table.title)
        
def idle_move(hud):
    try:
        hud.move_table_position()
        [aw.move_windows() for aw in hud.aux_windows]
    except:
        log.exception(_("Error moving HUD for table: %s.") % hud.table.title)
        
def idle_kill(hud_main, table):
    try:
        if table in hud_main.hud_dict:
            hud_main.vb.removeWidget(hud_main.hud_dict[table].tablehudlabel)
            hud_main.hud_dict[table].tablehudlabel.setParent(None)
#            hud_main.hud_dict[table].main_window.destroy()
            hud_main.hud_dict[table].kill()
            del(hud_main.hud_dict[table])
        hud_main.main_window.resize(1, 1)
    except:
        log.exception(_("Error killing HUD for table: %s.") % table.title)

def idle_create(hud_main, new_hand_id, table, temp_key, max, poker_game, type, stat_dict, cards):

    try:
        newlabel = QLabel("%s - %s" % (table.site, temp_key))
        hud_main.vb.addWidget(newlabel)

        hud_main.hud_dict[temp_key].tablehudlabel = newlabel
        hud_main.hud_dict[temp_key].tablenumber = table.number
        # call the hud.create method, apparently
        hud_main.hud_dict[temp_key].create(new_hand_id, hud_main.config, stat_dict)
        for m in hud_main.hud_dict[temp_key].aux_windows:
            m.create() # create method of aux_window class (generally Mucked.aux_seats.create)
            m.update_gui(new_hand_id)


    except:
        log.exception(_("Error creating HUD for hand %s.") % new_hand_id)

def idle_update(hud_main, new_hand_id, table_name, config):
    try:
        hud_main.hud_dict[table_name].update(new_hand_id, config)
        [aw.update_gui(new_hand_id) for aw in hud_main.hud_dict[table_name].aux_windows]
    except:
        log.exception(_("Error updating HUD for hand %s.") % new_hand_id)

def idle_check_tables(hud_main):
    try:
        for tablename, hud in hud_main.hud_dict.items():
            status = hud.table.check_table()
            if status == "client_destroyed":
                hud_main.client_destroyed(None, hud)
            elif status == "client_moved":
                hud_main.client_moved(None, hud)
            elif status == "client_resized":
                hud_main.client_resized(None, hud)
    except:
        log.exception("Error checking tables.")

if __name__== "__main__":
    app = QApplication([])

#    start the HUD_main object
    hm = HUD_main(db_name = options.dbname)

#    start the event loop
    app.exec_()
