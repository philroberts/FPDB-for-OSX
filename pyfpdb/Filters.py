#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

import threading
import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
from optparse import OptionParser
from time import *
import gobject
#import pokereval

import Configuration
import fpdb_db
import FpdbSQLQueries
import Charset

class Filters(threading.Thread):
    def __init__(self, db, config, qdict, display = {}, debug=True):
        # config and qdict are now redundant
        self.debug = debug
        #print "start of GraphViewer constructor"
        self.db = db
        self.cursor = db.cursor
        self.sql = db.sql
        self.conf = db.config
        self.display = display

        self.sites  = {}
        self.games  = {}
        self.limits = {}
        self.seats  = {}
        self.groups = {}
        self.siteid = {}
        self.heroes = {}
        self.boxes  = {}

        for site in self.conf.get_supported_sites():
            #Get db site id for filtering later
            self.cursor.execute(self.sql.query['getSiteId'], (site,))
            result = self.db.cursor.fetchall()
            if len(result) == 1:
                self.siteid[site] = result[0][0]
            else:
                print "Either 0 or more than one site matched - EEK"


        # text used on screen stored here so that it can be configured
        self.filterText = {'limitsall':'All', 'limitsnone':'None', 'limitsshow':'Show _Limits'
                          ,'seatsbetween':'Between:', 'seatsand':'And:', 'seatsshow':'Show Number of _Players'
                          ,'limitstitle':'Limits:', 'seatstitle':'Number of Players:'
                          ,'groupstitle':'Grouping:', 'posnshow':'Show Position Stats:'
                          ,'groupsall':'All Players'
                          ,'limitsFL':'FL', 'limitsNL':'NL', 'limitsPL':'PL', 'ring':'Ring', 'tour':'Tourney'
                          }

        # For use in date ranges.
        self.start_date = gtk.Entry(max=12)
        self.end_date = gtk.Entry(max=12)
        self.start_date.set_property('editable', False)
        self.end_date.set_property('editable', False)

        # For use in groups etc
        self.sbGroups = {}
        self.numHands = 0

        # Outer Packing box
        self.mainVBox = gtk.VBox(False, 0)

        playerFrame = gtk.Frame("Hero:")
        playerFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillPlayerFrame(vbox, self.display)
        playerFrame.add(vbox)
        self.boxes['player'] = vbox

        sitesFrame = gtk.Frame("Sites:")
        sitesFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillSitesFrame(vbox)
        sitesFrame.add(vbox)
        self.boxes['sites'] = vbox

        # Game types
        gamesFrame = gtk.Frame("Games:")
        gamesFrame.set_label_align(0.0, 0.0)
        gamesFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillGamesFrame(vbox)
        gamesFrame.add(vbox)
        self.boxes['games'] = vbox

        # Limits
        limitsFrame = gtk.Frame()
        limitsFrame.show()
        vbox = gtk.VBox(False, 0)
        self.cbLimits = {}
        self.cbNoLimits = None
        self.cbAllLimits = None
        self.cbFL = None
        self.cbNL = None
        self.cbPL = None
        self.rb = {}     # radio buttons for ring/tour
        self.type = None # ring/tour
        self.types = {}  # list of all ring/tour values

        self.fillLimitsFrame(vbox, self.display)
        limitsFrame.add(vbox)

        # Seats
        seatsFrame = gtk.Frame()
        seatsFrame.show()
        vbox = gtk.VBox(False, 0)
        self.sbSeats = {}

        self.fillSeatsFrame(vbox, self.display)
        seatsFrame.add(vbox)

        # Groups
        groupsFrame = gtk.Frame()
        groupsFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillGroupsFrame(vbox, self.display)
        groupsFrame.add(vbox)

        # Date
        dateFrame = gtk.Frame("Date:")
        dateFrame.set_label_align(0.0, 0.0)
        dateFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillDateFrame(vbox)
        dateFrame.add(vbox)
        self.boxes['date'] = vbox

        # Buttons
        self.Button1=gtk.Button("Unnamed 1")
        self.Button1.set_sensitive(False)

        self.Button2=gtk.Button("Unnamed 2")
        self.Button2.set_sensitive(False)

        self.mainVBox.add(playerFrame)
        self.mainVBox.add(sitesFrame)
        self.mainVBox.add(gamesFrame)
        self.mainVBox.add(limitsFrame)
        self.mainVBox.add(seatsFrame)
        self.mainVBox.add(groupsFrame)
        self.mainVBox.add(dateFrame)
        self.mainVBox.add(self.Button1)
        self.mainVBox.add(self.Button2)

        self.mainVBox.show_all()

        # Should do this cleaner
        if "Heroes" not in self.display or self.display["Heroes"] == False:
            playerFrame.hide()
        if "Sites" not in self.display or self.display["Sites"] == False:
            sitesFrame.hide()
        if "Games" not in self.display or self.display["Games"] == False:
            gamesFrame.hide()
        if "Limits" not in self.display or self.display["Limits"] == False:
            limitsFrame.hide()
        if "Seats" not in self.display or self.display["Seats"] == False:
            seatsFrame.hide()
        if "Groups" not in self.display or self.display["Groups"] == False:
            groupsFrame.hide()
        if "Dates" not in self.display or self.display["Dates"] == False:
            dateFrame.hide()
        if "Button1" not in self.display or self.display["Button1"] == False:
            self.Button1.hide()
        if "Button2" not in self.display or self.display["Button2"] == False:
            self.Button2.hide()

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    def getNumHands(self):
        return self.numHands

    def getSites(self):
        return self.sites

    def getGames(self):
        return self.games

    def getSiteIds(self):
        return self.siteid

    def getHeroes(self):
        return self.heroes

    def getLimits(self):
        ltuple = []
        for l in self.limits:
            if self.limits[l] == True:
                ltuple.append(l)
        return ltuple

    def getType(self):
        return(self.type)

    def getSeats(self):
        if 'from' in self.sbSeats:
            self.seats['from'] = self.sbSeats['from'].get_value_as_int()
        if 'to' in self.sbSeats:
            self.seats['to'] = self.sbSeats['to'].get_value_as_int()
        return self.seats

    def getGroups(self):
        return self.groups

    def getDates(self):
        return self.__get_dates()

    def registerButton1Name(self, title):
        self.Button1.set_label(title)

    def registerButton1Callback(self, callback):
        self.Button1.connect("clicked", callback, "clicked")
        self.Button1.set_sensitive(True)

    def registerButton2Name(self, title):
        self.Button2.set_label(title)

    def registerButton2Callback(self, callback):
        self.Button2.connect("clicked", callback, "clicked")
        self.Button2.set_sensitive(True)

    def cardCallback(self, widget, data=None):
        print "DEBUG: %s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])

    def createPlayerLine(self, hbox, site, player):
        print 'DEBUG :: add:"%s"' % player
        label = gtk.Label(site +" id:")
        hbox.pack_start(label, False, False, 0)

        pname = gtk.Entry()
        pname.set_text(player)
        pname.set_width_chars(20)
        hbox.pack_start(pname, False, True, 0)
        pname.connect("changed", self.__set_hero_name, site)

        # Added EntryCompletion but maybe comboBoxEntry is more flexible? (e.g. multiple choices)
        completion = gtk.EntryCompletion()
        pname.set_completion(completion)
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        completion.set_model(liststore)
        completion.set_text_column(0)
        names = self.db.get_player_names(self.conf, self.siteid[site])  # (config=self.conf, site_id=None, like_player_name="%")
        for n in names: # list of single-element "tuples"
            _n = Charset.to_gui(n[0])
            _nt = (_n, )
            liststore.append(_nt)

        self.__set_hero_name(pname, site)

    def __set_hero_name(self, w, site):
        _name = w.get_text()
        _guiname = Charset.to_gui(_name)
        self.heroes[site] = _guiname
#        print "DEBUG: setting heroes[%s]: %s"%(site, self.heroes[site])

    def __set_num_hands(self, w, val):
        try:
            self.numHands = int(w.get_text())
        except:
            self.numHands = 0
#        print "DEBUG: setting numHands:", self.numHands

    def createSiteLine(self, hbox, site):
        cb = gtk.CheckButton(site)
        cb.connect('clicked', self.__set_site_select, site)
        cb.set_active(True)
        hbox.pack_start(cb, False, False, 0)

    def createGameLine(self, hbox, game):
        cb = gtk.CheckButton(game)
        cb.connect('clicked', self.__set_game_select, game)
        hbox.pack_start(cb, False, False, 0)
        cb.set_active(True)

    def createLimitLine(self, hbox, limit, ltext):
        cb = gtk.CheckButton(str(ltext))
        cb.connect('clicked', self.__set_limit_select, limit)
        hbox.pack_start(cb, False, False, 0)
        if limit != "none":
            cb.set_active(True)
        return(cb)

    def __set_site_select(self, w, site):
        #print w.get_active()
        self.sites[site] = w.get_active()
        print "self.sites[%s] set to %s" %(site, self.sites[site])

    def __set_game_select(self, w, game):
        #print w.get_active()
        self.games[game] = w.get_active()
        print "self.games[%s] set to %s" %(game, self.games[game])

    def __set_limit_select(self, w, limit):
        #print w.get_active()
        self.limits[limit] = w.get_active()
        print "self.limit[%s] set to %s" %(limit, self.limits[limit])
        if limit.isdigit() or (len(limit) > 2 and (limit[-2:] == 'nl' or limit[-2:] == 'fl' or limit[-2:] == 'pl')):
            if self.limits[limit]:
                if self.cbNoLimits is not None:
                    self.cbNoLimits.set_active(False)
            else:
                if self.cbAllLimits is not None:
                    self.cbAllLimits.set_active(False)
            if not self.limits[limit]:
                if limit.isdigit():
                    if self.cbFL is not None:
                        self.cbFL.set_active(False)
                elif (len(limit) > 2 and (limit[-2:] == 'nl')):
                    if self.cbNL is not None:
                        self.cbNL.set_active(False)
                else:
                    if self.cbPL is not None:
                        self.cbPL.set_active(False)
        elif limit == "all":
            if self.limits[limit]:
                #for cb in self.cbLimits.values():
                #    cb.set_active(True)
                if self.cbFL is not None:
                    self.cbFL.set_active(True)
                if self.cbNL is not None:
                    self.cbNL.set_active(True)
                if self.cbPL is not None:
                    self.cbPL.set_active(True)
        elif limit == "none":
            if self.limits[limit]:
                for cb in self.cbLimits.values():
                    cb.set_active(False)
                if self.cbNL is not None:
                    self.cbNL.set_active(False)
                if self.cbFL is not None:
                    self.cbFL.set_active(False)
                if self.cbPL is not None:
                    self.cbPL.set_active(False)
        elif limit == "fl":
            if not self.limits[limit]:
                # only toggle all fl limits off if they are all currently on
                # this stops turning one off from cascading into 'fl' box off
                # and then all fl limits being turned off
                all_fl_on = True
                for cb in self.cbLimits.values():
                    t = cb.get_children()[0].get_text()
                    if t.isdigit():
                        if not cb.get_active():
                            all_fl_on = False
            found = {'ring':False, 'tour':False}
            for cb in self.cbLimits.values():
                #print "cb label: ", cb.children()[0].get_text()
                t = cb.get_children()[0].get_text()
                if t.isdigit():
                    if self.limits[limit] or all_fl_on:
                        cb.set_active(self.limits[limit])
                    found[self.types[t]] = True
            if self.limits[limit]:
                if not found[self.type]:
                    if self.type == 'ring':
                        if 'tour' in self.rb:
                            self.rb['tour'].set_active(True)
                    elif self.type == 'tour':
                        if 'ring' in self.rb:
                            self.rb['ring'].set_active(True)
        elif limit == "nl":
            if not self.limits[limit]:
                # only toggle all nl limits off if they are all currently on
                # this stops turning one off from cascading into 'nl' box off
                # and then all nl limits being turned off
                all_nl_on = True
                for cb in self.cbLimits.values():
                    t = cb.get_children()[0].get_text()
                    if "nl" in t and len(t) > 2:
                        if not cb.get_active():
                            all_nl_on = False
            found = {'ring':False, 'tour':False}
            for cb in self.cbLimits.values():
                t = cb.get_children()[0].get_text()
                if "nl" in t and len(t) > 2:
                    if self.limits[limit] or all_nl_on:
                        cb.set_active(self.limits[limit])
                    found[self.types[t]] = True
            if self.limits[limit]:
                if not found[self.type]:
                    if self.type == 'ring':
                        self.rb['tour'].set_active(True)
                    elif self.type == 'tour':
                        self.rb['ring'].set_active(True)
        elif limit == "pl":
            if not self.limits[limit]:
                # only toggle all nl limits off if they are all currently on
                # this stops turning one off from cascading into 'nl' box off
                # and then all nl limits being turned off
                all_nl_on = True
                for cb in self.cbLimits.values():
                    t = cb.get_children()[0].get_text()
                    if "pl" in t and len(t) > 2:
                        if not cb.get_active():
                            all_nl_on = False
            found = {'ring':False, 'tour':False}
            for cb in self.cbLimits.values():
                t = cb.get_children()[0].get_text()
                if "pl" in t and len(t) > 2:
                    if self.limits[limit] or all_nl_on:
                        cb.set_active(self.limits[limit])
                    found[self.types[t]] = True
            if self.limits[limit]:
                if not found[self.type]:
                    if self.type == 'ring':
                        self.rb['tour'].set_active(True)
                    elif self.type == 'tour':
                        self.rb['ring'].set_active(True)
        elif limit == "ring":
            print "set", limit, "to", self.limits[limit]
            if self.limits[limit]:
                self.type = "ring"
                for cb in self.cbLimits.values():
                    #print "cb label: ", cb.children()[0].get_text()
                    if self.types[cb.get_children()[0].get_text()] == 'tour':
                        cb.set_active(False)
        elif limit == "tour":
            print "set", limit, "to", self.limits[limit]
            if self.limits[limit]:
                self.type = "tour"
                for cb in self.cbLimits.values():
                    #print "cb label: ", cb.children()[0].get_text()
                    if self.types[cb.get_children()[0].get_text()] == 'ring':
                        cb.set_active(False)

    def __set_seat_select(self, w, seat):
        #print "__set_seat_select: seat =", seat, "active =", w.get_active()
        self.seats[seat] = w.get_active()
        print "self.seats[%s] set to %s" %(seat, self.seats[seat])

    def __set_group_select(self, w, group):
        #print "__set_seat_select: seat =", seat, "active =", w.get_active()
        self.groups[group] = w.get_active()
        print "self.groups[%s] set to %s" %(group, self.groups[group])

    def fillPlayerFrame(self, vbox, display):
        for site in self.conf.get_supported_sites():
            hBox = gtk.HBox(False, 0)
            vbox.pack_start(hBox, False, True, 0)

            player = self.conf.supported_sites[site].screen_name
            _pname = Charset.to_gui(player)
            self.createPlayerLine(hBox, site, _pname)

        if "GroupsAll" in display and display["GroupsAll"] == True:
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, False, 0)
            cb = gtk.CheckButton(self.filterText['groupsall'])
            cb.connect('clicked', self.__set_group_select, 'allplayers')
            hbox.pack_start(cb, False, False, 0)
            self.sbGroups['allplayers'] = cb
            self.groups['allplayers'] = False

            lbl = gtk.Label('Min # Hands:')
            lbl.set_alignment(xalign=1.0, yalign=0.5)
            hbox.pack_start(lbl, expand=True, padding=3)

            phands = gtk.Entry()
            phands.set_text('0')
            phands.set_width_chars(8)
            hbox.pack_start(phands, False, False, 0)
            phands.connect("changed", self.__set_num_hands, site)

    def fillSitesFrame(self, vbox):
        for site in self.conf.get_supported_sites():
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, True, 0)
            self.createSiteLine(hbox, site)
            #Get db site id for filtering later
            #self.cursor.execute(self.sql.query['getSiteId'], (site,))
            #result = self.db.cursor.fetchall()
            #if len(result) == 1:
            #    self.siteid[site] = result[0][0]
            #else:
            #    print "Either 0 or more than one site matched - EEK"

    def fillGamesFrame(self, vbox):
        self.cursor.execute(self.sql.query['getGames'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in result:
                hbox = gtk.HBox(False, 0)
                vbox.pack_start(hbox, False, True, 0)
                self.createGameLine(hbox, line[0])
        else:
            print "INFO: No games returned from database"

    def fillLimitsFrame(self, vbox, display):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['limitstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label="hide", stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'limits')

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['limits'] = vbox1

        self.cursor.execute(self.sql.query['getLimits2'])
        # selects  limitType, bigBlind
        result = self.db.cursor.fetchall()
        found = {'nl':False, 'fl':False, 'pl':False, 'ring':False, 'tour':False}

        if len(result) >= 1:
            hbox = gtk.HBox(True, 0)
            vbox1.pack_start(hbox, False, False, 0)
            vbox2 = gtk.VBox(False, 0)
            hbox.pack_start(vbox2, False, False, 0)
            vbox3 = gtk.VBox(False, 0)
            hbox.pack_start(vbox3, False, False, 0)
            for i, line in enumerate(result):
                if "UseType" in self.display:
                    if line[0] != self.display["UseType"]:
                        continue
                hbox = gtk.HBox(False, 0)
                if i <= len(result)/2:
                    vbox2.pack_start(hbox, False, False, 0)
                else:
                    vbox3.pack_start(hbox, False, False, 0)
                if line[0] == 'ring':
                    if line[1] == 'fl':
                        name = str(line[2])
                        found['fl'] = True
                    elif line[1] == 'pl':
                        name = str(line[2])+line[1]
                        found['pl'] = True
                    else:
                        name = str(line[2])+line[1]
                        found['nl'] = True
                    self.cbLimits[name] = self.createLimitLine(hbox, name, name)
                    self.types[name] = line[0]
                found[line[0]] = True      # type is ring/tour
                self.type = line[0]        # if only one type, set it now
            if "LimitSep" in display and display["LimitSep"] == True and len(result) >= 2:
                hbox = gtk.HBox(True, 0)
                vbox1.pack_start(hbox, False, False, 0)
                vbox2 = gtk.VBox(False, 0)
                hbox.pack_start(vbox2, False, False, 0)
                vbox3 = gtk.VBox(False, 0)
                hbox.pack_start(vbox3, False, False, 0)

                hbox = gtk.HBox(False, 0)
                vbox2.pack_start(hbox, False, False, 0)
                self.cbAllLimits = self.createLimitLine(hbox, 'all', self.filterText['limitsall'])
                hbox = gtk.HBox(False, 0)
                vbox2.pack_start(hbox, False, False, 0)
                self.cbNoLimits = self.createLimitLine(hbox, 'none', self.filterText['limitsnone'])

                dest = vbox3  # for ring/tour buttons
                if "LimitType" in display and display["LimitType"] == True and found['nl'] and found['fl']:
                    #if found['fl']:
                    hbox = gtk.HBox(False, 0)
                    vbox3.pack_start(hbox, False, False, 0)
                    self.cbFL = self.createLimitLine(hbox, 'fl', self.filterText['limitsFL'])
                    #if found['nl']:
                    hbox = gtk.HBox(False, 0)
                    vbox3.pack_start(hbox, False, False, 0)
                    self.cbNL = self.createLimitLine(hbox, 'nl', self.filterText['limitsNL'])
                    hbox = gtk.HBox(False, 0)
                    vbox3.pack_start(hbox, False, False, 0)
                    self.cbPL = self.createLimitLine(hbox, 'pl', self.filterText['limitsPL'])
                    dest = vbox2  # for ring/tour buttons
        else:
            print "INFO: No games returned from database"

        if "Type" in display and display["Type"] == True and found['ring'] and found['tour']:
            rb1 = gtk.RadioButton(None, self.filterText['ring'])
            rb1.connect('clicked', self.__set_limit_select, 'ring')
            rb2 = gtk.RadioButton(rb1, self.filterText['tour'])
            rb2.connect('clicked', self.__set_limit_select, 'tour')
            top_hbox.pack_start(rb1, False, False, 0)  # (child, expand, fill, padding)
            top_hbox.pack_start(rb2, True, True, 0)   # child uses expand space if fill is true

            self.rb['ring'] = rb1
            self.rb['tour'] = rb2
            #print "about to set ring to true"
            rb1.set_active(True)
            # set_active doesn't seem to call this for some reason so call manually:
            self.__set_limit_select(rb1, 'ring')
            self.type = 'ring'
        top_hbox.pack_start(showb, expand=False, padding=1)

    def fillSeatsFrame(self, vbox, display):
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['seatstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label="hide", stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'seats')
        hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['seats'] = vbox1

        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, True, 0)

        lbl_from = gtk.Label(self.filterText['seatsbetween'])
        lbl_to   = gtk.Label(self.filterText['seatsand'])
        adj1 = gtk.Adjustment(value=2, lower=2, upper=10, step_incr=1, page_incr=1, page_size=0)
        sb1 = gtk.SpinButton(adjustment=adj1, climb_rate=0.0, digits=0)
        adj2 = gtk.Adjustment(value=10, lower=2, upper=10, step_incr=1, page_incr=1, page_size=0)
        sb2 = gtk.SpinButton(adjustment=adj2, climb_rate=0.0, digits=0)

        hbox.pack_start(lbl_from, expand=False, padding=3)
        hbox.pack_start(sb1, False, False, 0)
        hbox.pack_start(lbl_to, expand=False, padding=3)
        hbox.pack_start(sb2, False, False, 0)

        self.sbSeats['from'] = sb1
        self.sbSeats['to']   = sb2

    def fillGroupsFrame(self, vbox, display):
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['groupstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label="hide", stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'groups')
        hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['groups'] = vbox1

        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, False, 0)
        cb = self.createLimitLine(hbox, 'show', self.filterText['limitsshow'])

        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, True, 0)
        cb = gtk.CheckButton(self.filterText['posnshow'])
        cb.connect('clicked', self.__set_group_select, 'posn')
        hbox.pack_start(cb, False, False, 0)
        self.sbGroups['posn'] = cb
        self.groups['posn'] = False

        if "SeatSep" in display and display["SeatSep"] == True:
            hbox = gtk.HBox(False, 0)
            vbox1.pack_start(hbox, False, True, 0)
            cb = gtk.CheckButton(self.filterText['seatsshow'])
            cb.connect('clicked', self.__set_seat_select, 'show')
            hbox.pack_start(cb, False, False, 0)
            self.sbSeats['show'] = cb
            self.seats['show'] = False

    def fillCardsFrame(self, vbox):
        hbox1 = gtk.HBox(True,0)
        hbox1.show()
        vbox.pack_start(hbox1, True, True, 0)

        cards = [ "A", "K","Q","J","T","9","8","7","6","5","4","3","2" ]

        for j in range(0, len(cards)):
            hbox1 = gtk.HBox(True,0)
            hbox1.show()
            vbox.pack_start(hbox1, True, True, 0)
            for i in range(0, len(cards)):
                if i < (j + 1):
                    suit = "o"
                else:
                    suit = "s"
                button = gtk.ToggleButton("%s%s%s" %(cards[i], cards[j], suit))
                button.connect("toggled", self.cardCallback, "%s%s%s" %(cards[i], cards[j], suit))
                hbox1.pack_start(button, True, True, 0)
                button.show()

    def fillDateFrame(self, vbox):
        # Hat tip to Mika Bostrom - calendar code comes from PokerStats
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)

        lbl_start = gtk.Label('From:')

        btn_start = gtk.Button()
        btn_start.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_start.connect('clicked', self.__calendar_dialog, self.start_date)

        hbox.pack_start(lbl_start, expand=False, padding=3)
        hbox.pack_start(btn_start, expand=False, padding=3)
        hbox.pack_start(self.start_date, expand=False, padding=2)

        #New row for end date
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)

        lbl_end = gtk.Label('  To:')
        btn_end = gtk.Button()
        btn_end.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_end.connect('clicked', self.__calendar_dialog, self.end_date)

        btn_clear = gtk.Button(label=' Clear Dates ')
        btn_clear.connect('clicked', self.__clear_dates)

        hbox.pack_start(lbl_end, expand=False, padding=3)
        hbox.pack_start(btn_end, expand=False, padding=3)
        hbox.pack_start(self.end_date, expand=False, padding=2)

        hbox.pack_start(btn_clear, expand=False, padding=15)

    def __toggle_box(self, widget, entry):
        if "Limits" not in self.display or self.display["Limits"] == False:
            self.boxes[entry].hide()
        elif self.boxes[entry].props.visible:
            self.boxes[entry].hide()
            widget.set_label("show")
        else:
            self.boxes[entry].show()
            widget.set_label("hide")

    def __calendar_dialog(self, widget, entry):
        d = gtk.Window(gtk.WINDOW_TOPLEVEL)
        d.set_title('Pick a date')

        vb = gtk.VBox()
        cal = gtk.Calendar()
        vb.pack_start(cal, expand=False, padding=0)

        btn = gtk.Button('Done')
        btn.connect('clicked', self.__get_date, cal, entry, d)

        vb.pack_start(btn, expand=False, padding=4)

        d.add(vb)
        d.set_position(gtk.WIN_POS_MOUSE)
        d.show_all()

    def __clear_dates(self, w):
        self.start_date.set_text('')
        self.end_date.set_text('')

    def __get_dates(self):
        t1 = self.start_date.get_text()
        t2 = self.end_date.get_text()

        if t1 == '':
            t1 = '1970-01-01'
        if t2 == '':
            t2 = '2020-12-12'

        return (t1, t2)

    def __get_date(self, widget, calendar, entry, win):
# year and day are correct, month is 0..11
        (year, month, day) = calendar.get_date()
        month += 1
        ds = '%04d-%02d-%02d' % (year, month, day)
        entry.set_text(ds)
        win.destroy()

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    if argv is None:
        argv = sys.argv[1:]

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    parser = OptionParser()
    (options, argv) = parser.parse_args(args = argv)

    config = Configuration.Config()
    db = None

    db = fpdb_db.fpdb_db()
    db.do_connect(config)

    qdict = FpdbSQLQueries.FpdbSQLQueries(db.get_backend_name())

    i = Filters(db, config, qdict)
    main_window = gtk.Window()
    main_window.connect('destroy', destroy)
    main_window.add(i.get_vbox())
    main_window.show()
    gtk.main()

if __name__ == '__main__':
   sys.exit(main())
