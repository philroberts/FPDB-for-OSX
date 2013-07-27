#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
from optparse import OptionParser
from time import gmtime, mktime, strftime, strptime, localtime
import gobject
import pango
#import pokereval

import logging

import Configuration
import Database
import SQL
import Charset
import Filters
import Card

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("filter")

class Filters:
    MIN_DATE = '1970-01-02 00:00:00'
    MAX_DATE = '2100-12-12 23:59:59'
    def __init__(self, db, config, qdict, display = {}, debug=True):
        # config and qdict are now redundant
        self.debug = debug
        self.db = db
        self.cursor = db.cursor
        self.sql = db.sql
        self.conf = db.config
        self.display = display
            
        self.gameName = {"27_1draw"  : _("Single Draw 2-7 Lowball")
                        ,"27_3draw"  : _("Triple Draw 2-7 Lowball")
                        ,"a5_3draw"  : _("Triple Draw A-5 Lowball")
                        ,"5_studhi"   : _("5 Card Stud")
                        ,"badugi"    : _("Badugi")
                        ,"fivedraw"  : _("5 Card Draw")
                        ,"holdem"    : _("Hold'em")
                        ,"omahahi"   : _("Omaha")
                        ,"omahahilo" : _("Omaha Hi/Lo")
                        ,"razz"      : _("Razz")
                        ,"studhi"    : _("7 Card Stud")
                        ,"studhilo"  : _("7 Card Stud Hi/Lo")
                        ,"5_omahahi" : _("5 Card Omaha")
                        ,"5_omaha8"  : _("5 Card Omaha Hi/Lo")
                        ,"cour_hi"   : _("Courchevel")
                        ,"cour_hilo" : _("Courchevel Hi/Lo")
                        ,"2_holdem"  : _("Double hold'em")
                        ,"irish"     : _("Irish")
                        ,"6_omahahi" : _("6 Card Omaha")
                        }

        self.currencyName = {"USD" : _("US Dollar")
                            ,"EUR" : _("Euro")
                            ,"T$"  : _("Tournament Dollar")
                            ,"play": _("Play Money")
                            }

        # text used on screen stored here so that it can be configured
        self.filterText = {'limitsall':_('All'), 'limitsnone':_('None'), 'limitsshow':_('Show _Limits')
                          ,'gamesall':_('All'), 'gamesnone':_('None')
                          ,'positionsall':_('All'), 'positionsnone':_('None')
                          ,'currenciesall':_('All'), 'currenciesnone':_('None')
                          ,'seatsbetween':_('Between:'), 'seatsand':_('And:'), 'seatsshow':_('Show Number of _Players')
                          ,'playerstitle':_('Hero:'), 'sitestitle':(_('Sites')+':'), 'gamestitle':(_('Games')+':')
                          ,'limitstitle':_('Limits:'), 'positionstitle':_('Positions:'), 'seatstitle':_('Number of Players:')
                          ,'groupstitle':_('Grouping:'), 'posnshow':_('Show Position Stats')
                          ,'datestitle':_('Date:'), 'currenciestitle':(_('Currencies')+':')
                          ,'groupsall':_('All Players'), 'cardstitle':(_('Hole Cards')+':')
                          ,'limitsFL':'FL', 'limitsNL':'NL', 'limitsPL':'PL', 'limitsCN':'CAP', 'ring':_('Ring'), 'tour':_('Tourney'), 'limitsHP':'HP'
                          }

        gen = self.conf.get_general_params()
        self.day_start = 0

        if 'day_start' in gen:
            self.day_start = float(gen['day_start'])


        self.sw = gtk.ScrolledWindow()
        self.sw.set_border_width(0)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_size_request(235, 300)


        # Outer Packing box
        self.mainVBox = gtk.VBox(False, 0)
        self.sw.add_with_viewport(self.mainVBox)
        self.sw.show()
        #print(_("DEBUG:") + _("New packing box created!"))

        self.found = {'nl':False, 'fl':False, 'pl':False, 'cn':False, 'hp':False, 'ring':False, 'tour':False}
        self.label = {}
        self.callback = {}

        self.make_filter()
        
    def make_filter(self):
        self.sites  = {}
        self.games  = {}
        self.limits = {}
        self.positions = {}
        self.seats  = {}
        self.groups = {}
        self.siteid = {}
        self.heroes = {}
        self.boxes  = {}
        self.toggles  = {}
        self.graphops = {}
        self.currencies  = {}
        self.cards  = {}

        for site in self.conf.get_supported_sites():
            #Get db site id for filtering later
            self.cursor.execute(self.sql.query['getSiteId'], (site,))
            result = self.db.cursor.fetchall()
            if len(result) == 1:
                self.siteid[site] = result[0][0]
            else:
                log.debug(_("Either 0 or more than one site matched for %s") % site)

        # For use in date ranges.
        self.start_date = gtk.Entry(max=12)
        self.start_date.set_width_chars(12)
        self.end_date = gtk.Entry(max=12)
        self.end_date.set_width_chars(12)
        self.start_date.set_property('editable', False)
        self.end_date.set_property('editable', False)

        # For use in groups etc
        self.sbGroups = {}
        self.numHands = 0

        # for use in graphops
        # dspin = display in '$' or 'B'
        self.graphops['dspin'] = "$"
        self.graphops['showdown'] = 'OFF'
        self.graphops['nonshowdown'] = 'OFF'
        self.graphops['ev'] = 'OFF'

        playerFrame = gtk.Frame()
        playerFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillPlayerFrame(vbox, self.display)
        playerFrame.add(vbox)

        # Sites
        sitesFrame = gtk.Frame()
        sitesFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillSitesFrame(vbox)
        sitesFrame.add(vbox)

        # Game types
        gamesFrame = gtk.Frame()
        gamesFrame.set_label_align(0.0, 0.0)
        gamesFrame.show()
        vbox = gtk.VBox(False, 0)
        self.cbGames = {}
        self.cbNoGames = None
        self.cbAllGames = None

        self.fillGamesFrame(vbox)
        gamesFrame.add(vbox)

        # Currencies
        currenciesFrame = gtk.Frame()
        currenciesFrame.set_label_align(0.0, 0.0)
        currenciesFrame.show()
        vbox = gtk.VBox(False, 0)
        self.cbCurrencies = {}
        self.cbNoCurrencies = None
        self.cbAllCurrencies = None

        self.fillCurrenciesFrame(vbox)
        currenciesFrame.add(vbox)

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
        self.cbCN = None
        self.cbHP = None
        self.rb = {}     # radio buttons for ring/tour
        self.type = None # ring/tour
        self.types = {}  # list of all ring/tour values
        self.num_limit_types = 0

        self.fillLimitsFrame(vbox, self.display)
        limitsFrame.add(vbox)
        
        #Positions  
        positionsFrame = gtk.Frame()
        positionsFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)
        
        self.cbPositions = {}
        self.cbNoPositions = None
        self.cbAllPositions = None

        self.fillPositionsFrame(vbox, self.display)
        positionsFrame.add(vbox)

        # GraphOps
        graphopsFrame = gtk.Frame()
        #graphops.set_label_align(0,0, 0.0)
        graphopsFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillGraphOpsFrame(vbox)
        graphopsFrame.add(vbox)


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
        dateFrame = gtk.Frame()
        dateFrame.set_label_align(0.0, 0.0)
        dateFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillDateFrame(vbox)
        dateFrame.add(vbox)

        # Hole cards
        cardsFrame = gtk.Frame()
        cardsFrame.set_label_align(0.0, 0.0)
        cardsFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillHoleCardsFrame(vbox)
        cardsFrame.add(vbox)

        # Buttons
        self.Button1=gtk.Button("Unnamed 1")
        self.Button1.set_sensitive(False)

        self.Button2=gtk.Button("Unnamed 2")
        self.Button2.set_sensitive(False)

        expand = False
        self.mainVBox.pack_start(playerFrame, expand)
        self.mainVBox.pack_start(sitesFrame, expand)
        self.mainVBox.pack_start(gamesFrame, expand)
        self.mainVBox.pack_start(currenciesFrame, expand)
        self.mainVBox.pack_start(limitsFrame, expand)
        self.mainVBox.pack_start(positionsFrame, expand)
        self.mainVBox.pack_start(seatsFrame, expand)
        self.mainVBox.pack_start(groupsFrame, expand)
        self.mainVBox.pack_start(dateFrame, expand)
        self.mainVBox.pack_start(graphopsFrame, expand)
        self.mainVBox.pack_start(cardsFrame, expand)
        self.mainVBox.pack_start(gtk.VBox(False, 0))
        self.mainVBox.pack_start(self.Button1, expand)
        self.mainVBox.pack_start(self.Button2, expand)

        self.mainVBox.show_all()

        # Should do this cleaner
        if "Heroes" not in self.display or self.display["Heroes"] == False:
            playerFrame.hide()
        if "Sites" not in self.display or self.display["Sites"] == False:
            sitesFrame.hide()
        if "Games" not in self.display or self.display["Games"] == False:
            gamesFrame.hide()
        if "Currencies" not in self.display or self.display["Currencies"] == False:
            currenciesFrame.hide()
        if "Limits" not in self.display or self.display["Limits"] == False:
            limitsFrame.hide()
        if "Positions" not in self.display or self.display["Positions"] == False:
            positionsFrame.hide()
        if "Seats" not in self.display or self.display["Seats"] == False:
            seatsFrame.hide()
        if "Groups" not in self.display or self.display["Groups"] == False:
            groupsFrame.hide()
        if "Dates" not in self.display or self.display["Dates"] == False:
            dateFrame.hide()
        if "GraphOps" not in self.display or self.display["GraphOps"] == False:
            graphopsFrame.hide()
        if "Cards" not in self.display or self.display["Cards"] == False:
            cardsFrame.hide()
        if "Button1" not in self.display or self.display["Button1"] == False:
            self.Button1.hide()
        if "Button2" not in self.display or self.display["Button2"] == False:
            self.Button2.hide()

        if 'button1' in self.label and self.label['button1']:
            self.Button1.set_label( self.label['button1'] )
        if 'button2' in self.label and self.label['button2']:
            self.Button2.set_label( self.label['button2'] )
        if 'button1' in self.callback and self.callback['button1']:
            self.Button1.connect("clicked", self.callback['button1'], "clicked")
            self.Button1.set_sensitive(True)
        if 'button2' in self.callback and self.callback['button2']:
            self.Button2.connect("clicked", self.callback['button2'], "clicked")
            self.Button2.set_sensitive(True)

        # make sure any locks on db are released:
        self.db.rollback()

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.sw
    #end def get_vbox

    def getNumHands(self):
        return self.numHands
    #end def getNumHands

    def getNumTourneys(self):
        return self.numTourneys
    #end def getNumTourneys

    def getSites(self):
        return self.sites
    #end def getSites
    
    def getPositions(self):
        return self.positions
    #end def getPositions

    def getTourneyTypes(self):
        return self.tourneyTypes
    #end def getTourneyTypes

    def getGames(self):
        return self.games
    #end def getGames

    def getCards(self):
        return self.cards

    def getCurrencies(self):
        return self.currencies
    #end def getCurrencies

    def getSiteIds(self):
        return self.siteid
    #end def getSiteIds

    def getHeroes(self):
        return self.heroes
    #end def getHeroes

    def getGraphOps(self):
        return self.graphops

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
    #end def getSeats

    def getGroups(self):
        return self.groups

    def getDates(self):
        return self.__get_dates()
    #end def getDates

    def registerButton1Name(self, title):
        self.Button1.set_label(title)
        self.label['button1'] = title

    def registerButton1Callback(self, callback):
        self.Button1.connect("clicked", callback, "clicked")
        self.Button1.set_sensitive(True)
        self.callback['button1'] = callback

    def registerButton2Name(self, title):
        self.Button2.set_label(title)
        self.label['button2'] = title
    #end def registerButton2Name

    def registerButton2Callback(self, callback):
        self.Button2.connect("clicked", callback, "clicked")
        self.Button2.set_sensitive(True)
        self.callback['button2'] = callback
    #end def registerButton2Callback

    def registerCardsCallback(self, callback):
        self.callback['cards'] = callback

    def createPlayerLine(self, vbox, site, player):
        log.debug('add:"%s"' % player)
        label = gtk.Label(site +" id:")
        label.set_alignment(xalign=0.0, yalign=1.0)
        vbox.pack_start(label, False, False, 3)

        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, True, 0)

        pname = gtk.Entry()
        pname.set_text(player)
        pname.set_width_chars(20)
        hbox.pack_start(pname, True, True, 20)
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
    #end def createPlayerLine

    def __set_hero_name(self, w, site):
        _name = w.get_text()
        # get_text() returns a str but we want internal variables to be unicode:
        _guiname = unicode(_name)
        self.heroes[site] = _guiname
        #log.debug("setting heroes[%s]: %s"%(site, self.heroes[site]))
    #end def __set_hero_name

    def __set_num_hands(self, w, val):
        try:
            self.numHands = int(w.get_text())
        except:
            self.numHands = 0
        #log.debug("setting numHands:", self.numHands)
    #end def __set_num_hands

    def createSiteLine(self, hbox, site):
        cb = gtk.CheckButton(site)
        cb.connect('clicked', self.__set_site_select, site)
        cb.set_active(True)
        hbox.pack_start(cb, False, False, 0)
    #end def createSiteLine

    def __set_tourney_type_select(self, w, tourneyType):
        #print w.get_active()
        self.tourneyTypes[tourneyType] = w.get_active()
        log.debug("self.tourney_types[%s] set to %s" %(tourneyType, self.tourneyTypes[tourneyType]))
    #end def __set_tourney_type_select

    def createTourneyTypeLine(self, hbox, tourneyType):
        cb = gtk.CheckButton(str(tourneyType))
        cb.connect('clicked', self.__set_tourney_type_select, tourneyType)
        hbox.pack_start(cb, False, False, 0)
        cb.set_active(True)
    #end def createTourneyTypeLine

    def createGameLine(self, hbox, game, gtext):
        cb = gtk.CheckButton(gtext.replace("_", "__"))
        cb.connect('clicked', self.__set_game_select, game)
        hbox.pack_start(cb, False, False, 0)
        if game != "none":
            cb.set_active(True)
        return(cb)
    
    def createPositionLine(self, hbox, pos, pos_text):
        cb = gtk.CheckButton(pos_text.replace("_", "__"))
        cb.connect('clicked', self.__set_position_select, pos)
        hbox.pack_start(cb, False, False, 0)
        if pos != "none":
            cb.set_active(True)
        return cb
    #end def createPositionLine

    def createCardsWidget(self, hbox):
        for i in range(0,13):
            vbox = gtk.VBox(False, 0)
            for j in range(0,13):
                abbr = Card.card_map_abbr[j][i]
                b = gtk.Button("")
                b.connect('clicked', self.__toggle_card_select, abbr)
                self.cards[abbr] = False # NOTE: This is flippped in __toggle_card_select below
                self.__toggle_card_select(b, abbr)
                vbox.pack_start(b, False, False, 0)
            hbox.pack_start(vbox, False, False, 0)

    def createCardsControls(self, hbox):
        selections = ["All", "Suited", "Off Suit"]
        for s in selections:
            cb = gtk.CheckButton(s)
            cb.connect('clicked', self.__set_cards, s)
            hbox.pack_start(cb, False, False, 0)

    def createCurrencyLine(self, hbox, currency, ctext):
        cb = gtk.CheckButton(ctext.replace("_", "__"))
        cb.connect('clicked', self.__set_currency_select, currency)
        hbox.pack_start(cb, False, False, 0)
        if currency != "none" and currency != "all" and currency != "play":
            cb.set_active(True)
        return(cb)

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
        log.debug(_("self.sites[%s] set to %s") %(site, self.sites[site]))
    #end def __set_site_select

    def __set_game_select(self, w, game):
        if (game == 'all'):
            if (w.get_active()):
                for cb in self.cbGames.values():
                    cb.set_active(True)
        elif (game == 'none'):
            if (w.get_active()):
                for cb in self.cbGames.values():
                    cb.set_active(False)
        else:
            self.games[game] = w.get_active()
            if (w.get_active()): # when we turn a pos on, turn 'none' off if it's on
                if (self.cbNoGames and self.cbNoGames.get_active()):
                    self.cbNoGames.set_active(False)
            else:                # when we turn a pos off, turn 'all' off if it's on
                if (self.cbAllGames and self.cbAllGames.get_active()):
                    self.cbAllGames.set_active(False)
    #end def __set_game_select

    def __set_position_select(self, w, pos):      
        if (pos == 'all'):
            if (w.get_active()):
                for cb in self.cbPositions.values():
                    cb.set_active(True)
        elif (pos == 'none'):
            if (w.get_active()):
                for cb in self.cbPositions.values():
                    cb.set_active(False)
        else:
            self.positions[pos] = w.get_active()
            if (w.get_active()): # when we turn a pos on, turn 'none' off if it's on
                if (self.cbNoPositions and self.cbNoPositions.get_active()):
                    self.cbNoPositions.set_active(False)
            else:                # when we turn a pos off, turn 'all' off if it's on
                if (self.cbAllPositions and self.cbAllPositions.get_active()):
                    self.cbAllPositions.set_active(False)
    #end def __set_position_select

    def __card_select_bgcolor(self, card, selected):
        s_on  = "red"
        s_off = "orange"
        o_on  = "white"
        o_off = "lightgrey"
        p_on  = "blue"
        p_off = "lightblue"
        if len(card) == 2: return p_on if selected else p_off
        if card[2] == 's': return s_on if selected else s_off
        if card[2] == 'o': return o_on if selected else o_off

    def __toggle_card_select(self, w, card):
        font_size = "xx-small"
        markup = "<span size='%s'>%s</span>" % (font_size, card)
        w.child.set_use_markup(True)
        w.child.set_label(markup)

        self.cards[card] = (self.cards[card] == False)

        bg_color = self.__card_select_bgcolor(card, self.cards[card])

        style = w.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = w.get_colormap().alloc(bg_color)
        w.set_style(style)
        if 'cards' in self.callback:
            self.callback['cards'](card)

    def __set_cards(self, w, val):
        print "DEBUG: val: %s = %s" %(val, w.get_active())

    def __set_currency_select(self, w, currency):
        if (currency == 'all'):
            if (w.get_active()):
                for cb in self.cbCurrencies.values():
                    cb.set_active(True)
        elif (currency == 'none'):
            if (w.get_active()):
                for cb in self.cbCurrencies.values():
                    cb.set_active(False)
        else:
            self.currencies[currency] = w.get_active()
            if (w.get_active()): # when we turn a currency on, turn 'none' off if it's on
                if (self.cbNoCurrencies and self.cbNoCurrencies.get_active()):
                    self.cbNoCurrencies.set_active(False)
            else:                # when we turn a currency off, turn 'all' off if it's on
                if (self.cbAllCurrencies and self.cbAllCurrencies.get_active()):
                    self.cbAllCurrencies.set_active(False)
    #end def __set_currency_select

    def __set_limit_select(self, w, limit):
        #print "__set_limit_select:  limit =", limit, w.get_active()
        self.limits[limit] = w.get_active()
        log.debug(_("self.limit[%s] set to %s") %(limit, self.limits[limit]))
        if limit.isdigit() or (len(limit) > 2 and (limit[-2:] == 'nl' or limit[-2:] == 'fl' or limit[-2:] == 'pl' or limit[-2:] == 'cn')):
            # turning a leaf limit on with 'None' checked turns 'None' off
            if self.limits[limit]:
                if self.cbNoLimits is not None:
                    self.cbNoLimits.set_active(False)
            # turning a leaf limit off with 'All' checked turns 'All' off
            else:
                if self.cbAllLimits is not None:
                    self.cbAllLimits.set_active(False)
            # turning off a leaf limit turns off the corresponding fl. nl, cn or pl
            if not self.limits[limit]:
                if (limit.isdigit() or (len(limit) > 2 and (limit[-2:] == 'fl'))):
                    if self.cbFL is not None:
                        self.cbFL.set_active(False)
                elif (len(limit) > 2 and (limit[-2:] == 'nl')):
                    if self.cbNL is not None:
                        self.cbNL.set_active(False)
                elif (len(limit) > 2 and (limit[-2:] == 'cn')):
                    if self.cbCN is not None:
                        self.cbCN.set_active(False)
                else:
                    if self.cbPL is not None:
                        self.cbPL.set_active(False)
        elif limit == "all":
            if self.limits[limit]:
                if self.num_limit_types == 1:
                    for cb in self.cbLimits.values():
                        cb.set_active(True)
                else:
                    if self.cbFL is not None:
                        self.cbFL.set_active(True)
                    if self.cbNL is not None:
                        self.cbNL.set_active(True)
                    if self.cbPL is not None:
                        self.cbPL.set_active(True)
                    if self.cbCN is not None:
                        self.cbCN.set_active(True)
        elif limit == "none":
            if self.limits[limit]:
                if self.num_limit_types > 1:
                    if self.cbNL is not None:
                        self.cbNL.set_active(False)
                    if self.cbFL is not None:
                        self.cbFL.set_active(False)
                    if self.cbPL is not None:
                        self.cbPL.set_active(False)
                    if self.cbCN is not None:
                        self.cbCN.set_active(False)
            #
            #   Finally, clean-up all individual limit checkboxes
            #       needed because the overall limit checkbox may 
            #       not be set, or num_limit_types == 1
            #
                for cb in self.cbLimits.values():
                        cb.set_active(False)
        elif limit == "fl":
            if not self.limits[limit]:
                # only toggle all fl limits off if they are all currently on
                # this stops turning one off from cascading into 'fl' box off
                # and then all fl limits being turned off
                all_fl_on = True
                for cb in self.cbLimits.values():
                    t = cb.get_children()[0].get_text()
                    if (t.isdigit() or ("fl" in t and len(t) > 2)):
                        if not cb.get_active():
                            all_fl_on = False
            found = {'ring':False, 'tour':False}
            for cb in self.cbLimits.values():
                #print "cb label: ", cb.children()[0].get_text()
                t = cb.get_children()[0].get_text()
                if (t.isdigit() or ("fl" in t and len(t) > 2)):
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
                        if 'tour' in self.rb:
                            self.rb['tour'].set_active(True)
                    elif self.type == 'tour':
                        if 'ring' in self.rb:
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
                        if 'tour' in self.rb:
                            self.rb['tour'].set_active(True)
                    elif self.type == 'tour':
                        if 'ring' in self.rb:
                            self.rb['ring'].set_active(True)
        elif limit == "cn":
            if not self.limits[limit]:
                all_cn_on = True
                for cb in self.cbLimits.values():
                    t = cb.get_children()[0].get_text()
                    if "cn" in t and len(t) > 2:
                        if not cb.get_active():
                            all_cn_on = False
            found = {'ring':False, 'tour':False}
            for cb in self.cbLimits.values():
                t = cb.get_children()[0].get_text()
                if "cn" in t and len(t) > 2:
                    if self.limits[limit] or all_cn_on:
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
        elif limit == "ring":
            log.debug("set", limit, "to", self.limits[limit])
            if self.limits[limit]:
                self.type = "ring"
                for cb in self.cbLimits.values():
                    #print "cb label: ", cb.children()[0].get_text()
                    if self.types[cb.get_children()[0].get_text()] == 'tour':
                        cb.set_active(False)
        elif limit == "tour":
            log.debug( "set", limit, "to", self.limits[limit] )
            if self.limits[limit]:
                self.type = "tour"
                for cb in self.cbLimits.values():
                    #print "cb label: ", cb.children()[0].get_text()
                    if self.types[cb.get_children()[0].get_text()] == 'ring':
                        cb.set_active(False)

    def __set_seat_select(self, w, seat):
        #print "__set_seat_select: seat =", seat, "active =", w.get_active()
        self.seats[seat] = w.get_active()
        log.debug( _("self.seats[%s] set to %s") %(seat, self.seats[seat]) )
    #end def __set_seat_select

    def __set_group_select(self, w, group):
        #print "__set_seat_select: seat =", seat, "active =", w.get_active()
        self.groups[group] = w.get_active()
        log.debug( _("self.groups[%s] set to %s") %(group, self.groups[group]) )


    def __set_displayin_select(self, w, ops):
        self.graphops['dspin'] = ops

    def __set_graphopscheck_select(self, w, data):
        #print "%s was toggled %s" % (data, ("OFF", "ON")[w.get_active()])
        self.graphops[data] = ("OFF", "ON")[w.get_active()]

    def fillPlayerFrame(self, vbox, display):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['playerstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)

        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Heroes')
        self.toggles['Heroes'] = showb
        showb.show()
        top_hbox.pack_end(showb, expand=False, padding=1)

        showb = gtk.Button(label=_("hide all"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'all')
        self.toggles['all'] = showb
        showb.show()
        top_hbox.pack_end(showb, expand=False, padding=1)

        showb = gtk.Button(label=_("Refresh"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__refresh, 'Heroes')

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Heroes'] = vbox1

        for site in self.conf.get_supported_sites():
            player = self.conf.supported_sites[site].screen_name
            _pname = Charset.to_gui(player)
            self.createPlayerLine(vbox1, site, _pname)

        if "GroupsAll" in display and display["GroupsAll"] == True:
            hbox = gtk.HBox(False, 0)
            vbox1.pack_start(hbox, False, False, 0)
            cb = gtk.CheckButton(self.filterText['groupsall'])
            cb.connect('clicked', self.__set_group_select, 'allplayers')
            hbox.pack_start(cb, False, False, 0)
            self.sbGroups['allplayers'] = cb
            self.groups['allplayers'] = False

            lbl = gtk.Label(_('Min # Hands:'))
            lbl.set_alignment(xalign=1.0, yalign=0.5)
            hbox.pack_start(lbl, expand=True, padding=3)

            phands = gtk.Entry()
            phands.set_text('0')
            phands.set_width_chars(8)
            hbox.pack_start(phands, False, False, 0)
            phands.connect("changed", self.__set_num_hands, site)
        top_hbox.pack_start(showb, expand=False, padding=1)
    #end def fillPlayerFrame

    def fillSitesFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        top_hbox.show()
        vbox.pack_start(top_hbox, False, False, 0)

        lbl_title = gtk.Label(self.filterText['sitestitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)

        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Sites')
        self.toggles['Sites'] = showb
        showb.show()
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        self.boxes['Sites'] = vbox1
        vbox.pack_start(vbox1, False, False, 0)

        for site in self.conf.get_supported_sites():
            hbox = gtk.HBox(False, 0)
            vbox1.pack_start(hbox, False, True, 0)
            self.createSiteLine(hbox, site)
            #Get db site id for filtering later
            #self.cursor.execute(self.sql.query['getSiteId'], (site,))
            #result = self.db.cursor.fetchall()
            #if len(result) == 1:
            #    self.siteid[site] = result[0][0]
            #else:
            #    print "Either 0 or more than one site matched - EEK"
    #end def fillSitesFrame

    def fillTourneyTypesFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['tourneyTypesTitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'tourneyTypes')
        self.toggles['tourneyTypes'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['tourneyTypes'] = vbox1

        result = self.db.getTourneyTypesIds()
        if len(result) >= 1:
            for line in result:
                hbox = gtk.HBox(False, 0)
                vbox1.pack_start(hbox, False, True, 0)
                self.createTourneyTypeLine(hbox, line[0])
        else:
            print _("INFO: No tourney types returned from database")
            log.info(_("No tourney types returned from database"))
    #end def fillTourneyTypesFrame

    def fillGamesFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['gamestitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Games')
        self.toggles['Games'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Games'] = vbox1

        self.cursor.execute(self.sql.query['getGames'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in sorted(result, key = lambda game: self.gameName[game[0]]):
                hbox = gtk.HBox(False, 0)
                vbox1.pack_start(hbox, False, True, 0)
                self.cbGames[line[0]] = self.createGameLine(hbox, line[0], self.gameName[line[0]])

            if len(result) >= 2:
                hbox = gtk.HBox(True, 0)
                vbox1.pack_start(hbox, False, False, 0)
                vbox2 = gtk.VBox(False, 0)
                hbox.pack_start(vbox2, False, False, 0)
                vbox3 = gtk.VBox(False, 0)
                hbox.pack_start(vbox3, False, False, 0)

                hbox = gtk.HBox(False, 0)
                vbox2.pack_start(hbox, False, False, 0)
                self.cbAllGames = self.createGameLine(hbox, 'all', self.filterText['gamesall'])
                hbox = gtk.HBox(False, 0)
                vbox3.pack_start(hbox, False, False, 0)
                self.cbNoGames = self.createGameLine(hbox, 'none', self.filterText['gamesnone'])
        else:
            print _("INFO: No games returned from database")
            log.info(_("No games returned from database"))
    #end def fillGamesFrame
    
    def fillPositionsFrame(self, vbox, display):
        top_hbox = gtk.HBox(False, 0)
        top_hbox.show()
        vbox.pack_start(top_hbox, False, False, 0)

        lbl_title = gtk.Label(self.filterText['positionstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)

        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Positions')
        self.toggles['Positions'] = showb
        showb.show()
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        self.boxes['Positions'] = vbox1
        vbox.pack_start(vbox1, False, False, 0)
        
        #the following is not the fastest query (as it querys a table with potentialy a lot of data), so dont execute it if not necessary
        if "Positions" not in display or display["Positions"] == False:
            return
        
        #This takes too long if there are a couple of 100k hands in the DB
        #self.cursor.execute(self.sql.query['getPositions'])
        #result = self.db.cursor.fetchall()
        result = [[0], [1], [2], [3], [4], [5], [6], [7], ['S'], ['B']]
        res_count = len(result)
        
        if res_count > 0:     
            v_count = 0
            COL_COUNT = 4           #Number of columns
            hbox = None
            for line in result:
                if v_count == 0:    #start a new line when the vertical count is 0
                    hbox = gtk.HBox(True, 0)
                    vbox1.pack_start(hbox, False, True, 0)
                    
                line_str = str(line[0])
                self.cbPositions[line_str] = self.createPositionLine(hbox, line_str, line_str)
                
                v_count += 1
                if v_count == COL_COUNT:    #set the counter to 0 if the line is full
                    v_count = 0
            
            dif = res_count % COL_COUNT    
            while dif > 0:          #fill the rest of the line with empy boxes, so that every line contains COL_COUNT elements
                fillbox = gtk.VBox(False, 0)
                hbox.pack_start(fillbox, False, False, 0)
                dif -= 1

            if res_count > 1:
                hbox = gtk.HBox(True, 0)
                vbox1.pack_start(hbox, False, False, 0)
                self.cbAllPositions = self.createPositionLine(hbox, 'all', self.filterText['positionsall'])
                self.cbNoPositions = self.createPositionLine(hbox, 'none', self.filterText['positionsnone'])
        else:
            print(_("INFO") + ": " + _("No positions returned from database"))
            log.info(_("No positions returned from database"))
        
    #end def fillSitesFrame(self, vbox, display):


    def fillHoleCardsFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['cardstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Cards')
        self.toggles['Cards'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Cards'] = vbox1

        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, True, 0)
        self.createCardsWidget(hbox)

        # Additional controls for bulk changing card selection
        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, True, 0)
        self.createCardsControls(hbox)

    def fillCurrenciesFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['currenciestitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Currencies')
        self.toggles['Currencies'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Currencies'] = vbox1

        self.cursor.execute(self.sql.query['getCurrencies'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in result:
                hbox = gtk.HBox(False, 0)
                vbox1.pack_start(hbox, False, True, 0)
                if (self.currencyName.has_key(line[0])):
                    cname = self.currencyName[line[0]]
                else:
                    cname = line[0]
                self.cbCurrencies[line[0]] = self.createCurrencyLine(hbox, line[0], cname)

            if len(result) >= 2:
                hbox = gtk.HBox(True, 0)
                vbox1.pack_start(hbox, False, False, 0)
                vbox2 = gtk.VBox(False, 0)
                hbox.pack_start(vbox2, False, False, 0)
                vbox3 = gtk.VBox(False, 0)
                hbox.pack_start(vbox3, False, False, 0)

                hbox = gtk.HBox(False, 0)
                vbox2.pack_start(hbox, False, False, 0)
                self.cbAllCurrencies = self.createCurrencyLine(hbox, 'all', self.filterText['currenciesall'])
                hbox = gtk.HBox(False, 0)
                vbox3.pack_start(hbox, False, False, 0)
                self.cbNoCurrencies = self.createCurrencyLine(hbox, 'none', self.filterText['currenciesnone'])
            else:
                # There is only one currency. Select it, even if it's Play Money.
                self.cbCurrencies[line[0]].set_active(True)
        else:
            #print "INFO: No currencies returned from database"
            log.info(_("No currencies returned from database"))
    #end def fillCurrenciesFrame

    def fillLimitsFrame(self, vbox, display):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['limitstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Limits')
        self.toggles['Limits'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 15)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Limits'] = vbox1

        self.cursor.execute(self.sql.query['getCashLimits'])
        # selects  limitType, bigBlind
        result = self.db.cursor.fetchall()
        self.found = {'nl':False, 'fl':False, 'pl':False, 'cn':False, 'hp':False, 'ring':False, 'tour':False}

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
                if i < (len(result)+1)/2:
                    vbox2.pack_start(hbox, False, False, 0)
                else:
                    vbox3.pack_start(hbox, False, False, 0)
                if True:  #line[0] == 'ring':
                    name = str(line[2])+line[1]
                    self.found[line[1]] = True
                    self.cbLimits[name] = self.createLimitLine(hbox, name, name)
                    self.types[name] = line[0]
                self.found[line[0]] = True      # type is ring/tour
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
                if "LimitType" in display and display["LimitType"] == True:
                    self.num_limit_types = 0
                    if self.found['fl']:  self.num_limit_types = self.num_limit_types + 1
                    if self.found['pl']:  self.num_limit_types = self.num_limit_types + 1
                    if self.found['nl']:  self.num_limit_types = self.num_limit_types + 1
                    if self.found['cn']:  self.num_limit_types = self.num_limit_types + 1
                    if self.found['hp']:  self.num_limit_types = self.num_limit_types + 1
                    if self.num_limit_types > 1:
                       if self.found['fl']:
                           hbox = gtk.HBox(False, 0)
                           vbox3.pack_start(hbox, False, False, 0)
                           self.cbFL = self.createLimitLine(hbox, 'fl', self.filterText['limitsFL'])
                       if self.found['nl']:
                           hbox = gtk.HBox(False, 0)
                           vbox3.pack_start(hbox, False, False, 0)
                           self.cbNL = self.createLimitLine(hbox, 'nl', self.filterText['limitsNL'])
                       if self.found['pl']:
                           hbox = gtk.HBox(False, 0)
                           vbox3.pack_start(hbox, False, False, 0)
                           self.cbPL = self.createLimitLine(hbox, 'pl', self.filterText['limitsPL'])
                       if self.found['cn']:
                           hbox = gtk.HBox(False, 0)
                           vbox3.pack_start(hbox, False, False, 0)
                           self.cbCN = self.createLimitLine(hbox, 'cn', self.filterText['limitsCN'])
                       if self.found['hp']:
                           hbox = gtk.HBox(False, 0)
                           vbox3.pack_start(hbox, False, False, 0)
                           self.cbHP = self.createLimitLine(hbox, 'hp', self.filterText['limitsHP'])
                       dest = vbox2  # for ring/tour buttons
        else:
            print _("INFO: No games returned from database")
            log.info(_("No games returned from database"))

        if "Type" in display and display["Type"] == True and self.found['ring'] and self.found['tour']:
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

    def fillGraphOpsFrame(self, vbox):
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        title = gtk.Label(_("Graphing Options:"))
        title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'GraphOps')
        self.toggles['GraphOps'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        vbox1.show()
        self.boxes['GraphOps'] = vbox1

        hbox1 = gtk.HBox(False, 0)
        vbox1.pack_start(hbox1, False, False, 0)
        hbox1.show()

        label = gtk.Label(_("Show Graph In:"))
        label.set_alignment(xalign=0.0, yalign=0.5)
        hbox1.pack_start(label, True, True, 0)
        label.show()

        button = gtk.RadioButton(None, "$$")
        hbox1.pack_start(button, True, True, 0)
        button.connect("toggled", self.__set_displayin_select, "$")
        button.set_active(True)
        button.show()

        button = gtk.RadioButton(button, "BB")
        hbox1.pack_start(button, True, True, 0)
        button.connect("toggled", self.__set_displayin_select, "BB")
        button.show()

        button = gtk.CheckButton(_("Showdown Winnings"), False)
        vbox1.pack_start(button, True, True, 0)
        # wouldn't it be awesome if there was a way to remember the state of things like
        # this and be able to set it to what it was last time?
        #button.set_active(True)
        button.connect("toggled", self.__set_graphopscheck_select, "showdown")
        button.show()

        button = gtk.CheckButton(_("Non-Showdown Winnings"), False)
        vbox1.pack_start(button, True, True, 0)
        # ditto as 8 lines up :)
        #button.set_active(True)
        button.connect("toggled", self.__set_graphopscheck_select, "nonshowdown");
        button.show()

        button = gtk.CheckButton(_("EV"), False)
        vbox1.pack_start(button, True, True, 0)
        button.connect("toggled", self.__set_graphopscheck_select, "ev");
        button.show()

    def fillSeatsFrame(self, vbox, display):
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['seatstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Seats')
        self.toggles['Seats'] = showb
        hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Seats'] = vbox1

        hbox = gtk.HBox(False, 0)
        vbox1.pack_start(hbox, False, True, 0)

        lbl_from = gtk.Label(self.filterText['seatsbetween'])
        lbl_to   = gtk.Label(self.filterText['seatsand'])

        adj1 = gtk.Adjustment(value=2, lower=2, upper=10, step_incr=1, page_incr=1, page_size=0)
        sb1 = gtk.SpinButton(adjustment=adj1, climb_rate=0.0, digits=0)
        adj1.connect('value-changed', self.__seats_changed, 'from')

        adj2 = gtk.Adjustment(value=10, lower=2, upper=10, step_incr=1, page_incr=1, page_size=0)
        sb2 = gtk.SpinButton(adjustment=adj2, climb_rate=0.0, digits=0)
        adj2.connect('value-changed', self.__seats_changed, 'to')

        hbox.pack_start(lbl_from, expand=False, padding=3)
        hbox.pack_start(sb1, False, False, 0)
        hbox.pack_start(lbl_to, expand=False, padding=3)
        hbox.pack_start(sb2, False, False, 0)

        self.sbSeats['from'] = sb1
        self.sbSeats['to']   = sb2
    #end def fillSeatsFrame

    def fillGroupsFrame(self, vbox, display):
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['groupstitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Groups')
        self.toggles['Groups'] = showb
        hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = gtk.VBox(False, 0)
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['Groups'] = vbox1

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
        top_hbox = gtk.HBox(False, 0)
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = gtk.Label(self.filterText['datestitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = gtk.Button(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'Dates')
        self.toggles['Dates'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        hbox1 = gtk.HBox(False, 0)
        vbox.pack_start(hbox1, False, False, 0)
        self.boxes['Dates'] = hbox1

        table = gtk.Table(2,4,False)
        hbox1.pack_start(table, False, True, 0)

        lbl_start = gtk.Label(_('From:'))
        lbl_start.set_alignment(xalign=1.0, yalign=0.5)
        btn_start = gtk.Button()
        btn_start.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_start.connect('clicked', self.__calendar_dialog, self.start_date)
        clr_start = gtk.Button()
        clr_start.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
        clr_start.connect('clicked', self.__clear_start_date)

        lbl_end = gtk.Label(_('To:'))
        lbl_end.set_alignment(xalign=1.0, yalign=0.5)
        btn_end = gtk.Button()
        btn_end.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_end.connect('clicked', self.__calendar_dialog, self.end_date)
        clr_end = gtk.Button()
        clr_end.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
        clr_end.connect('clicked', self.__clear_end_date)

        table.attach(lbl_start,       0,1, 0,1)
        table.attach(btn_start,       1,2, 0,1)
        table.attach(self.start_date, 2,3, 0,1)
        table.attach(clr_start,       3,4, 0,1)

        table.attach(lbl_end,         0,1, 1,2)
        table.attach(btn_end,         1,2, 1,2)
        table.attach(self.end_date,   2,3, 1,2)
        table.attach(clr_end,         3,4, 1,2)

    #end def fillDateFrame

    def get_limits_where_clause(self, limits):
        """Accepts a list of limits and returns a formatted SQL where clause starting with AND.
            Sql statement MUST link to gameType table and use the alias gt for that table."""
        where = ""
        lims = [int(x[0:-2]) for x in limits if len(x) > 2 and x[-2:] == 'fl']
        potlims = [int(x[0:-2]) for x in limits if len(x) > 2 and x[-2:] == 'pl']
        nolims = [int(x[0:-2]) for x in limits if len(x) > 2 and x[-2:] == 'nl']
        capnolims = [int(x[0:-2]) for x in limits if len(x) > 2 and x[-2:] == 'cn']
        hpnolims = [int(x[0:-2]) for x in limits if len(x) > 2 and x[-2:] == 'hp']

        where          = "AND ( "

        if lims: 
            clause = "(gt.limitType = 'fl' and gt.bigBlind in (%s))" % (','.join(map(str, lims)))
        else:
            clause = "(gt.limitType = 'fl' and gt.bigBlind in (-1))"
        where = where + clause
        if potlims:
            clause = "or (gt.limitType = 'pl' and gt.bigBlind in (%s))" % (','.join(map(str, potlims)))
        else:
            clause = "or (gt.limitType = 'pl' and gt.bigBlind in (-1))"
        where = where + clause
        if nolims:
            clause = "or (gt.limitType = 'nl' and gt.bigBlind in (%s))" % (','.join(map(str, nolims)))
        else:
            clause = "or (gt.limitType = 'nl' and gt.bigBlind in (-1))"
        where = where + clause
        if hpnolims:
            clause = "or (gt.limitType = 'hp' and gt.bigBlind in (%s))" % (','.join(map(str, hpnolims)))
        else:
            clause = "or (gt.limitType = 'hp' and gt.bigBlind in (-1))"
        where = where + clause
        if capnolims:
            clause = "or (gt.limitType = 'cp' and gt.bigBlind in (%s))" % (','.join(map(str, capnolims)))
        else:
            clause = "or (gt.limitType = 'cp' and gt.bigBlind in (-1))"
        where = where + clause + ' )'

        return where
    
    def replace_placeholders_with_filter_values(self, query):
        """ Returnes given query with replaced placeholders by the filter values from self.
        
            List of Placeholders that are replaced and some infos how the statement has to look like:
            (whole clause means it starts with AND and contains the whole clause)
        
            Placeholders      table & alias or field     SQL usage          coresponding filter Name
            <player_test>     Players.Id                in <player_test>   Heroes
            <game_test>       GameType gt               whole clause       Game
            <limit_test>      GameType gt               whole clause       Limits, LimitSep, LimitType
            <position_test>   HandsPlayers hp           whole clause       Positions
        """
        
        #copyed from GuiRingPlayerStats withouth thinking if this could be done any better
        if '<game_test>' in query:
            games = self.getGames()    
            q = []

            for n in games:
                if games[n]:
                    q.append(n)
            if len(q) > 0:
                gametest = str(tuple(q))
                gametest = gametest.replace("L", "")
                gametest = gametest.replace(",)",")")
                gametest = gametest.replace("u'","'")
                gametest = "and gt.category in %s" % gametest
            else:
                gametest = "and gt.category IS NULL"
            query = query.replace('<game_test>', gametest)
            
        if '<limit_test>' in query:  #copyed from GuiGraphView
            limits = self.getLimits()
            for i in ('show', 'none'):
                if i in limits:
                    limits.remove(i)
            limittest = self.get_limits_where_clause(limits)
            query = query.replace('<limit_test>', limittest)
            
        if '<player_test>' in query: #copyed from GuiGraphView
            sites = self.getSites()
            heroes = self.getHeroes()
            siteids = self.getSiteIds()
            sitenos = []
            playerids = []

            for site in sites:
                if sites[site] == True:
                    sitenos.append(siteids[site])
                    _hname = Charset.to_utf8(heroes[site])
                    result = self.db.get_player_id(self.conf, site, _hname)
                    if result is not None:
                        playerids.append(str(result))
            
            query = query.replace('<player_test>', '(' + ','.join(playerids) + ')')
            
        if '<position_test>' in query:
            positions = self.getPositions()
            pos_list = []
            
            for pos in positions:
                if positions[pos]:
                    pos_list.append(pos)
            
            positiontest = "AND hp.position in ('" + "','".join(pos_list) + "')"   #values must be set in '' because they can be strings as well as numbers
            query = query.replace('<position_test>', positiontest)

        return query

    def __refresh(self, widget, entry):
        for w in self.mainVBox.get_children():
            w.destroy()
        self.make_filter()
    #end def __refresh

    def __toggle_box(self, widget, entry):
        if (entry == "all"):
            if (widget.get_label() == _("hide all")):
                for entry in self.boxes.keys():
                    if (self.boxes[entry].props.visible):
                        self.__toggle_box(widget, entry)
                        widget.set_label(_("show all"))
            else:
                for entry in self.boxes.keys():
                    if (not self.boxes[entry].props.visible):
                        self.__toggle_box(widget, entry)
                    widget.set_label(_("hide all"))
        elif self.boxes[entry].props.visible:
            self.boxes[entry].hide()
            self.toggles[entry].set_label(_("show"))
            for entry in self.boxes.keys():
                if (self.display.has_key(entry) and
                    self.display[entry] and
                    self.boxes[entry].props.visible):
                    break
            else:
                self.toggles["all"].set_label(_("show all"))
        else:
            self.boxes[entry].show()
            self.toggles[entry].set_label(_("hide"))
            for entry in self.boxes.keys():
                if (self.display.has_key(entry) and
                    self.display[entry] and
                    not self.boxes[entry].props.visible):
                    break
            else:
                self.toggles["all"].set_label(_("hide all"))
    #end def __toggle_box

    def __calendar_dialog(self, widget, entry):
        d = gtk.Window(gtk.WINDOW_TOPLEVEL)
        d.set_title(_('Pick a date'))

        vb = gtk.VBox()
        cal = gtk.Calendar()
        vb.pack_start(cal, expand=False, padding=0)

        # if the date field is already set, default to the currently selected date, else default to 'today'
        text = entry.get_text()
        if (text):
            date = strptime(text, "%Y-%m-%d")
        else:
            # if the day is configured to not start at midnight, check whether it's still yesterday,
            # and if so, select yesterday in the calendar instead of today
            date = localtime()
            if (date.tm_hour < self.day_start):
                date = localtime(mktime(date) - 24*3600)
        cal.select_month(date.tm_mon - 1, date.tm_year) # months are 0 through 11
        cal.select_day(date.tm_mday)
            
        btn = gtk.Button(_('Done'))
        btn.connect('clicked', self.__get_date, cal, entry, d)

        vb.pack_start(btn, expand=False, padding=4)

        d.add(vb)
        d.set_position(gtk.WIN_POS_MOUSE)
        d.show_all()
    #end def __calendar_dialog

    def __clear_start_date(self, w):
        self.start_date.set_text('')
    #end def __clear_start_date

    def __clear_end_date(self, w):
        self.end_date.set_text('')
    #end def __clear_end_date

    def __get_dates(self):
        # self.day_start gives user's start of day in hours
        offset = int(self.day_start * 3600)   # calc day_start in seconds

        t1 = self.start_date.get_text()
        t2 = self.end_date.get_text()

        adj_t1 = self.MIN_DATE
        adj_t2 = self.MAX_DATE
        
        if t1 != '':
            s1 = strptime(t1, "%Y-%m-%d") # make time_struct
            e1 = mktime(s1) + offset  # s1 is localtime, but returned time since epoch is UTC, then add the 
            adj_t1 = strftime("%Y-%m-%d %H:%M:%S", gmtime(e1)) # make adjusted string including time
         
        if t2 != '':   
            s2 = strptime(t2, "%Y-%m-%d")
            e2 = mktime(s2) + offset  # s2 is localtime, but returned time since epoch is UTC
            e2 = e2 + 24 * 3600 - 1   # date test is inclusive, so add 23h 59m 59s to e2
            adj_t2 = strftime("%Y-%m-%d %H:%M:%S", gmtime(e2))
            
        log.info("t1="+t1+" adj_t1="+adj_t1+'.')

        return (adj_t1, adj_t2)
    #end def __get_dates

    def __get_date(self, widget, calendar, entry, win):
        # year and day are correct, month is 0..11
        (year, month, day) = calendar.get_date()
        month += 1
        ds = '%04d-%02d-%02d' % (year, month, day)
        entry.set_text(ds)
        win.destroy()

        # if the opposite date is set, and now the start date is later
        # than the end date, modify the one we didn't just set to be
        # the same as the one we did just set
        if (entry == self.start_date):
            end = self.end_date.get_text()
            if (end and ds > end):
                self.end_date.set_text(ds)
        else:
            start = self.start_date.get_text()
            if (start and ds < start):
                self.start_date.set_text(ds)

    def __seats_changed(self, widget, which):
        seats_from = self.sbSeats['from'].get_value_as_int()
        seats_to = self.sbSeats['to'].get_value_as_int()
        if (seats_from > seats_to):
            if (which == 'from'):
                self.sbSeats['to'].set_value(seats_from)
            else:
                self.sbSeats['from'].set_value(seats_to)

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    if argv is None:
        argv = sys.argv[1:]

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    parser = OptionParser()
    (options, argv) = parser.parse_args(args = argv)

    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)

    qdict = SQL.Sql(db_server = 'sqlite')

    filters_display = { "Heroes"    : False,
                        "Sites"     : False,
                        "Games"     : False,
                        "Cards"     : True,
                        "Currencies": False,
                        "Limits"    : False,
                        "LimitSep"  : False,
                        "LimitType" : False,
                        "Type"      : False,
                        "UseType"   : 'ring',
                        "Seats"     : False,
                        "SeatSep"   : False,
                        "Dates"     : False,
                        "GraphOps"  : False,
                        "Groups"    : False,
                        "Button1"   : False,
                        "Button2"   : False
                          }

    i = Filters(db, config, qdict, display = filters_display)
    main_window = gtk.Window()
    main_window.set_default_size(600,600)
    main_window.connect('destroy', destroy)
    main_window.add(i.get_vbox())
    main_window.show()
    gtk.main()

if __name__ == '__main__':
   sys.exit(main())

