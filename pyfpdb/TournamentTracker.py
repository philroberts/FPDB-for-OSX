#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TourneyTracker.py
    Based on HUD_main .. who knows if we want to actually use this or not
"""
# Copyright (c) 2009-2011 Eric Blade, and the FPDB team.

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.


import L10n
_ = L10n.get_translation()

#    to do allow window resizing
#    to do hud to echo, but ignore non numbers
#    to do no stat window for hero
#    to do things to add to config.xml

#    Standard Library modules
import sys
import os
import Options
import traceback

(options, argv) = Options.fpdb_options()

if not options.errorsToConsole:
    print (_("Note: error output is being diverted to %s.") % "tourneyerror.txt"),
             _("Any major error will be reported there _only_.")
    errorFile = open('tourneyerror.txt', 'w', 0)
    sys.stderr = errorFile

import thread
import time
import string
import re

#    pyGTK modules
import pygtk
import gtk
import gobject

#    FreePokerTools modules
import Configuration
import Database
import SummaryEverleaf

class Tournament:
    """Tournament will hold the information about a tournament, I guess ? Remember I'm new to this language, so I don't know the best ways to do things"""

    def __init__(self, parent, site, tid): # site should probably be something in the config object, but i don't know how the config object works right now, so we're going to make it a str ..
        print "Tournament init"
        self.parent = parent
        self.window = None
        self.site = site
        self.id = tid
        self.starttime = time.time()
        self.endtime = None
        self.game = None
        self.structure = None
        self.buyin = 0
        self.fee = 0
        self.rebuys = False
        self.numrebuys = 0 # this should probably be attached to the players list...
        self.numplayers = 0
        self.prizepool = 0
        self.players = {} # eventually i'd guess we'd probably want to fill this with playername:playerid's
        self.results = {} # i'd guess we'd want to load this up with playerid's instead of playernames, too, as well, also

        # if site == "Everleaf": # this should be attached to a button that says "retrieve tournament info" or something for sites that we know how to do it for
        summary = SummaryEverleaf.EverleafSummary()
        self.site = summary.parser.SiteName
        self.id = summary.parser.TourneyId
        self.starttime = summary.parser.TourneyStartTime
        self.endtime = summary.parser.TourneyEndTime
        self.game = summary.parser.TourneyGameType
        self.structure = summary.parser.TourneyStructure
        self.buyin = summary.parser.TourneyBuyIn # need to remember to parse the Fee out of this and move it to self.fee
        self.rebuys = (summary.parser.TourneyRebuys == "yes")
        self.prizepool = summary.parser.TourneyPool
        self.numplayers = summary.parser.TourneysPlayers

        self.openwindow() # let's start by getting any info we need.. meh

    def openwindow(self, widget=None):
        if self.window is not None:
            self.window.show() # isn't there a better way to bring something to the front? not that GTK focus works right anyway, ever
        else:
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            #print("tournament edit window:", self.window)
            self.window.connect("delete_event", self.delete_event)
            self.window.connect("destroy", self.destroy)
            self.window.set_title(_("FPDB Tournament Entry"))
            self.window.set_border_width(1)
            self.window.set_default_size(480,640)
            self.window.set_resizable(True)

            self.main_vbox = gtk.VBox(False, 1)
            self.main_vbox.set_border_width(1)
            self.window.add(self.main_vbox)
            self.window.show()

    def addrebuy(self, widget=None):
        t = self
        t.numrebuys += 1
        t.mylabel.set_label("%s - %s - %s - %s - %s %s - %s - %s - %s - %s - %s" % (t.site, t.id, t.starttime, t.endtime, t.structure, t.game, t.buyin, t.fee, t.numrebuys, t.numplayers, t.prizepool))

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        return False
    #end def destroy


class ttracker_main(object):
    """A main() object to own both the read_stdin thread and the gui."""
#    This class mainly provides state for controlling the multiple HUDs.

    def __init__(self, db_name = 'fpdb'):
        self.db_name = db_name
        self.config = Configuration.Config(file=options.config, dbname=options.dbname)
        self.tourney_list = []

#    a thread to read stdin
        gobject.threads_init()                       # this is required
        thread.start_new_thread(self.read_stdin, ()) # starts the thread

#    a main window
        self.main_window = gtk.Window()
        self.main_window.connect("destroy", self.destroy)
        self.vb = gtk.VBox()
        self.label = gtk.Label(_('Closing this window will stop the Tournament Tracker'))
        self.vb.add(self.label)
        self.addbutton = gtk.Button(label=_("Add Tournament"))
        self.addbutton.connect("clicked", self.addClicked, "add tournament")
        self.vb.add(self.addbutton)

        self.main_window.add(self.vb)
        self.main_window.set_title(_("FPDB Tournament Tracker"))
        self.main_window.show_all()

    def addClicked(self, widget, data): # what is "data"? i'm guessing anything i pass in after the function name in connect() but unsure because the documentation sucks
        print "addClicked", widget, data
        t = Tournament(self, None, None)
        if t is not None:
            print "new tournament=", t
            self.tourney_list.append(t)
            mylabel = gtk.Label("%s - %s - %s - %s - %s %s - %s - %s - %s - %s - %s" % (t.site, t.id, t.starttime, t.endtime, t.structure, t.game, t.buyin, t.fee, t.numrebuys, t.numplayers, t.prizepool))
            print "new label=", mylabel
            editbutton = gtk.Button(label=_("Edit"))
            print "new button=", editbutton
            editbutton.connect("clicked", t.openwindow)
            rebuybutton = gtk.Button(label=_("Rebuy"))
            rebuybutton.connect("clicked", t.addrebuy)
            self.vb.add(rebuybutton)
            self.vb.add(editbutton) # These should probably be put in.. a.. h-box? i don't know..
            self.vb.add(mylabel)
            self.main_window.resize_children()
            self.main_window.show()
            mylabel.show()
            editbutton.show()
            rebuybutton.show()
            t.mylabel = mylabel
            t.editbutton = editbutton
            t.rebuybutton = rebuybutton
            self.vb.show()
            print self.tourney_list

            return True
        else:
            return False
        # when we move the start command over to the main program, we can have the main program ask for the tourney id, and pipe it into the stdin here
        # at least that was my initial thought on it

    def destroy(*args):             # call back for terminating the main eventloop
        gtk.main_quit()

    def create_HUD(self, new_hand_id, table, table_name, max, poker_game, stat_dict, cards):

        def idle_func():

            gtk.gdk.threads_enter()
            try:
                newlabel = gtk.Label("%s - %s" % (table.site, table_name))
                self.vb.add(newlabel)
                newlabel.show()
                self.main_window.resize_children()

                self.hud_dict[table_name].tablehudlabel = newlabel
                self.hud_dict[table_name].create(new_hand_id, self.config, stat_dict, cards)
                for m in self.hud_dict[table_name].aux_windows:
                    m.create()
                    m.update_gui(new_hand_id)
                self.hud_dict[table_name].update(new_hand_id, self.config)
                self.hud_dict[table_name].reposition_windows()
                return False
            finally:
                gtk.gdk.threads_leave()

        self.hud_dict[table_name] = Hud.Hud(self, table, max, poker_game, self.config, self.db_connection)
        self.hud_dict[table_name].table_name = table_name
        self.hud_dict[table_name].stat_dict = stat_dict
        self.hud_dict[table_name].cards = cards
        [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[table_name].aux_windows]
        gobject.idle_add(idle_func)

    def update_HUD(self, new_hand_id, table_name, config):
        """Update a HUD gui from inside the non-gui read_stdin thread."""
#    This is written so that only 1 thread can touch the gui--mainly
#    for compatibility with Windows. This method dispatches the
#    function idle_func() to be run by the gui thread, at its leisure.
        def idle_func():
            gtk.gdk.threads_enter()
            try:
                self.hud_dict[table_name].update(new_hand_id, config)
                [aw.update_gui(new_hand_id) for aw in self.hud_dict[table_name].aux_windows]
                return False
            finally:
                gtk.gdk.threads_leave()
        gobject.idle_add(idle_func)

    def read_stdin(self):            # This is the thread function
        """Do all the non-gui heavy lifting for the HUD program."""

#    This db connection is for the read_stdin thread only. It should not
#    be passed to HUDs for use in the gui thread. HUD objects should not
#    need their own access to the database, but should open their own
#    if it is required.
        self.db_connection = Database.Database(self.config, self.db_name, 'temp')
#        self.db_connection.init_hud_stat_vars(hud_days)
        tourny_finder = re.compile('(\d+) (\d+)')

        while 1: # wait for a new hand number on stdin
            new_hand_id = sys.stdin.readline()
            new_hand_id = string.rstrip(new_hand_id)
            if new_hand_id == "":           # blank line means quit
                self.destroy()
                break # this thread is not always killed immediately with gtk.main_quit()
#    get basic info about the new hand from the db
#    if there is a db error, complain, skip hand, and proceed
            try:
                (table_name, max, poker_game, type, fast, site_id, numseats) = self.db_connection.get_table_name(new_hand_id)
                stat_dict = self.db_connection.get_stats_from_hand(new_hand_id, aggregate_stats[type]
                                                                  ,hud_style, agg_bb_mult)

                cards      = self.db_connection.get_cards(new_hand_id)
                comm_cards = self.db_connection.get_common_cards(new_hand_id)
                if comm_cards != {}: # stud!
                    cards['common'] = comm_cards['common']
            except Exception, err:
                err = traceback.extract_tb(sys.exc_info()[2])[-1]
                #print _("db error: skipping ")+str(new_hand_id)+" "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
                if new_hand_id: # new_hand_id is none if we had an error prior to the store
                    sys.stderr.write(_("Database error %s in hand %d. Skipping.") % (err, int(new_hand_id)) + "\n")
                continue

            if type == "tour":   # hand is from a tournament
                mat_obj = tourny_finder.search(table_name)
                if mat_obj:
                    (tour_number, tab_number) = mat_obj.group(1, 2)
                    temp_key = tour_number
                else:   # tourney, but can't get number and table
                    #print _("could not find tournament: skipping")
                    sys.stderr.write(_("Could not find tournament %d in hand %d. Skipping.") % (int(tour_number), int(new_hand_id)) + "\n")
                    continue

            else:
                temp_key = table_name

#    Update an existing HUD
            if temp_key in self.hud_dict:
                self.hud_dict[temp_key].stat_dict = stat_dict
                self.hud_dict[temp_key].cards = cards
                [aw.update_data(new_hand_id, self.db_connection) for aw in self.hud_dict[temp_key].aux_windows]
                self.update_HUD(new_hand_id, temp_key, self.config)

#    Or create a new HUD
            else:
                if type == "tour":
                    tablewindow = Tables.discover_tournament_table(self.config, tour_number, tab_number)
                else:
                    tablewindow = Tables.discover_table_by_name(self.config, table_name)
                if tablewindow is None:
#    If no client window is found on the screen, complain and continue
                    if type == "tour":
                        table_name = "%s %s" % (tour_number, tab_number)
                    sys.stderr.write(_("Table name %s not found, skipping.")% table_name)
                else:
                    self.create_HUD(new_hand_id, tablewindow, temp_key, max, poker_game, stat_dict, cards)
            self.db_connection.connection.rollback()

if __name__== "__main__":

    sys.stderr.write(_("Tournament tracker starting"))
    sys.stderr.write(_("Using db name = %s") % (options.dbname))

    Configuration.set_logfile("fpdb-log.txt")
#    start the HUD_main object
    hm = ttracker_main(db_name = options.dbname)

#    start the event loop
    gtk.main()
