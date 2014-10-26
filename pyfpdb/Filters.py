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

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (QCalendarWidget, QCheckBox, QCompleter, QDateEdit,
                             QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QRadioButton,
                             QScrollArea, QSizePolicy, QSpinBox, QToolButton,
                             QVBoxLayout, QWidget)
import os
import sys
from optparse import OptionParser
from time import gmtime, mktime, strftime, strptime, localtime
from functools import partial
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

class Filters(QWidget):
    MIN_DATE = '1970-01-02 00:00:00'
    MAX_DATE = '2100-12-12 23:59:59'
    def __init__(self, db, config, qdict, display = {}, debug=True):
        QWidget.__init__(self, None)
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


        # Outer Packing box
        self.setLayout(QVBoxLayout())

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
        self.start_date = QDateEdit(QDate(1970,1,1))
        self.end_date = QDateEdit(QDate(2100,1,1))

        # For use in groups etc
        self.sbGroups = {}
        self.numHands = 0

        # for use in graphops
        # dspin = display in '$' or 'B'
        self.graphops['dspin'] = "$"
        self.graphops['showdown'] = 'OFF'
        self.graphops['nonshowdown'] = 'OFF'
        self.graphops['ev'] = 'OFF'

        playerFrame = QGroupBox(self.filterText['playerstitle'])
        self.fillPlayerFrame(playerFrame, self.display)
        self.layout().addWidget(playerFrame)

        # Sites
        sitesFrame = QGroupBox(self.filterText['sitestitle'])

        self.fillSitesFrame(sitesFrame)
        self.layout().addWidget(sitesFrame)

        # Game types
        gamesFrame = QGroupBox(self.filterText['gamestitle'])
        self.layout().addWidget(gamesFrame)
        self.cbGames = {}
        self.cbNoGames = None
        self.cbAllGames = None

        self.fillGamesFrame(gamesFrame)

        # Currencies
        currenciesFrame = QGroupBox(self.filterText['currenciestitle'])
        self.layout().addWidget(currenciesFrame)
        self.cbCurrencies = {}
        self.cbNoCurrencies = None
        self.cbAllCurrencies = None

        self.fillCurrenciesFrame(currenciesFrame)

        # Limits
        limitsFrame = QGroupBox(self.filterText['limitstitle'])
        self.layout().addWidget(limitsFrame)
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

        self.fillLimitsFrame(limitsFrame, self.display)
        
        #Positions  
        positionsFrame = QGroupBox(self.filterText['positionstitle'])
        self.layout().addWidget(positionsFrame)
        
        self.cbPositions = {}
        self.cbNoPositions = None
        self.cbAllPositions = None

        self.fillPositionsFrame(positionsFrame, self.display)

        # GraphOps
        graphopsFrame = QGroupBox(_("Graphing Options:"))
        self.layout().addWidget(graphopsFrame)

        self.fillGraphOpsFrame(graphopsFrame)


        # Seats
        seatsFrame = QGroupBox(self.filterText['seatstitle'])
        self.layout().addWidget(seatsFrame)
        self.sbSeats = {}

        self.fillSeatsFrame(seatsFrame, self.display)

        # Groups
        groupsFrame = QGroupBox(self.filterText['groupstitle'])
        self.layout().addWidget(groupsFrame)

        self.fillGroupsFrame(groupsFrame, self.display)

        # Date
        dateFrame = QGroupBox(self.filterText['datestitle'])
        self.layout().addWidget(dateFrame)

        self.fillDateFrame(dateFrame)

        # Hole cards
        cardsFrame = QGroupBox(self.filterText['cardstitle'])
        self.layout().addWidget(cardsFrame)

        self.fillHoleCardsFrame(cardsFrame)

        # Buttons
        self.Button1 = QPushButton("Unnamed 1")
        self.Button1.setEnabled(False)

        self.Button2 = QPushButton("Unnamed 2")
        self.Button2.setEnabled(False)

        self.layout().addWidget(self.Button1)
        self.layout().addWidget(self.Button2)

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

    def getCards(self):
        return self.cards

    def getCurrencies(self):
        return self.currencies

    def getSiteIds(self):
        return self.siteid
    #end def getSiteIds

    def getHeroes(self):
        return self.heroes

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
            self.seats['from'] = self.sbSeats['from'].value()
        if 'to' in self.sbSeats:
            self.seats['to'] = self.sbSeats['to'].value()
        return self.seats

    def getGroups(self):
        return self.groups

    def getDates(self):
        return self.__get_dates()

    def registerButton1Name(self, title):
        self.Button1.setText(title)
        self.label['button1'] = title

    def registerButton1Callback(self, callback):
        self.Button1.clicked.connect(callback)
        self.Button1.setEnabled(True)
        self.callback['button1'] = callback

    def registerButton2Name(self, title):
        self.Button2.setText(title)
        self.label['button2'] = title

    def registerButton2Callback(self, callback):
        self.Button2.clicked.connect(callback)
        self.Button2.setEnabled(True)
        self.callback['button2'] = callback

    def registerCardsCallback(self, callback):
        self.callback['cards'] = callback

    def createPlayerLine(self, vbox, site, player):
        log.debug('add:"%s"' % player)
        label = QLabel(site +" id:")
        vbox.addWidget(label)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        pname = QLineEdit(player)
        hbox.addWidget(pname)
        pname.textChanged.connect(partial(self.__set_hero_name, site=site))

        # Added EntryCompletion but maybe comboBoxEntry is more flexible? (e.g. multiple choices)
        names = self.db.get_player_names(self.conf, self.siteid[site])  # (config=self.conf, site_id=None, like_player_name="%")
        completer = QCompleter([Charset.to_gui(n[0]) for n in names])
        pname.setCompleter(completer)

        self.__set_hero_name(player, site)
    #end def createPlayerLine

    def __set_hero_name(self, name, site):
        self.heroes[site] = unicode(name)

    def __set_num_hands(self, val):
        self.numHands = val

    def createSiteLine(self, hbox, site):
        cb = QCheckBox(site)
        cb.stateChanged.connect(partial(self.__set_site_select, site=site))
        cb.setChecked(True)
        hbox.addWidget(cb)

    def __set_tourney_type_select(self, w, tourneyType):
        #print w.get_active()
        self.tourneyTypes[tourneyType] = w.get_active()
        log.debug("self.tourney_types[%s] set to %s" %(tourneyType, self.tourneyTypes[tourneyType]))
    #end def __set_tourney_type_select

    def createTourneyTypeLine(self, hbox, tourneyType):
        cb = QCheckBox(str(tourneyType))
        cb.connect('clicked', self.__set_tourney_type_select, tourneyType)
        hbox.pack_start(cb, False, False, 0)
        cb.set_active(True)
    #end def createTourneyTypeLine

    def createGameLine(self, hbox, game, gtext):
        cb = QCheckBox(gtext.replace("_", "__"))
        cb.stateChanged.connect(partial(self.__set_game_select, game=game))
        hbox.addWidget(cb)
        if game != "none":
            cb.setChecked(True)
        return(cb)
    
    def createPositionLine(self, hbox, pos, pos_text):
        cb = QCheckBox(pos_text.replace("_", "__"))
        cb.stateChanged.connect(partial(self.__set_position_select, pos=pos))
        hbox.addWidget(cb)
        if pos != "none":
            cb.setChecked(True)
        return cb

    def createCardsWidget(self, grid):
        grid.setSpacing(0)
        for i in range(0,13):
            for j in range(0,13):
                abbr = Card.card_map_abbr[j][i]
                b = QPushButton("")
                b.setStyleSheet("QPushButton {border-width:0;margin:6;padding:0;}")
                b.clicked.connect(partial(self.__toggle_card_select, widget=b, card=abbr))
                self.cards[abbr] = False # NOTE: This is flippped in __toggle_card_select below
                self.__toggle_card_select(False, widget=b, card=abbr)
                grid.addWidget(b, j, i)

    def createCardsControls(self, hbox):
        selections = ["All", "Suited", "Off Suit"]
        for s in selections:
            cb = QCheckBox(s)
            cb.clicked.connect(self.__set_cards)
            hbox.addWidget(cb)

    def createCurrencyLine(self, hbox, currency, ctext):
        cb = QCheckBox(ctext.replace("_", "__"))
        cb.stateChanged.connect(partial(self.__set_currency_select, currency=currency))
        hbox.addWidget(cb)
        if currency != "none" and currency != "all" and currency != "play":
            cb.setChecked(True)
        return(cb)

    def createLimitLine(self, hbox, limit, ltext):
        cb = QCheckBox(str(ltext))
        cb.stateChanged.connect(partial(self.__set_limit_select, limit=limit))
        hbox.addWidget(cb)
        if limit != "none":
            cb.setChecked(True)
        return(cb)

    def __set_site_select(self, checkState, site):
        self.sites[site] = bool(checkState)
        log.debug(_("self.sites[%s] set to %s") %(site, self.sites[site]))

    def __set_game_select(self, checkState, game):
        if game == 'all':
            if checkState:
                for cb in self.cbGames.values():
                    cb.setChecked(True)
        elif game == 'none':
            if checkState:
                for cb in self.cbGames.values():
                    cb.setChecked(False)
        else:
            self.games[game] = bool(checkState)
            if checkState: # when we turn a pos on, turn 'none' off if it's on
                if self.cbNoGames and self.cbNoGames.isChecked():
                    self.cbNoGames.setChecked(False)
            else:                # when we turn a pos off, turn 'all' off if it's on
                if self.cbAllGames and self.cbAllGames.isChecked():
                    self.cbAllGames.setChecked(False)

    def __set_position_select(self, checkState, pos):      
        if (pos == 'all'):
            if checkState:
                for cb in self.cbPositions.values():
                    cb.setChecked(True)
        elif (pos == 'none'):
            if checkState:
                for cb in self.cbPositions.values():
                    cb.setChecked(False)
        else:
            self.positions[pos] = checkState
            if checkState: # when we turn a pos on, turn 'none' off if it's on
                if (self.cbNoPositions and self.cbNoPositions.isChecked()):
                    self.cbNoPositions.setChecked(False)
            else:                # when we turn a pos off, turn 'all' off if it's on
                if (self.cbAllPositions and self.cbAllPositions.isChecked()):
                    self.cbAllPositions.setChecked(False)

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

    def __toggle_card_select(self, checkstate, widget, card):
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setText(card)

        self.cards[card] = (self.cards[card] == False)

        bg_color = self.__card_select_bgcolor(card, self.cards[card])

#        style = w.get_style().copy()
#        style.bg[gtk.STATE_NORMAL] = w.get_colormap().alloc(bg_color)
#        w.set_style(style)
        if 'cards' in self.callback:
            self.callback['cards'](card)

    def __set_cards(self, w, val):
        print "DEBUG: val: %s = %s" %(val, w.get_active())

    def __set_currency_select(self, checkState, currency):
        if currency == 'all':
            if checkState:
                for cb in self.cbCurrencies.values():
                    cb.setChecked(True)
        elif currency == 'none':
            if checkState:
                for cb in self.cbCurrencies.values():
                    cb.setChecked(False)
        else:
            self.currencies[currency] = bool(checkState)
            if checkState: # when we turn a currency on, turn 'none' off if it's on
                if self.cbNoCurrencies and self.cbNoCurrencies.isChecked():
                    self.cbNoCurrencies.setChecked(False)
            else:          # when we turn a currency off, turn 'all' off if it's on
                if self.cbAllCurrencies and self.cbAllCurrencies.isChecked():
                    self.cbAllCurrencies.setChecked(False)

    def __set_limit_select(self, checkState, limit):
        self.limits[limit] = bool(checkState)
        return
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

    def __set_seat_select(self, checkState, seat):
        self.seats[seat] = checkState
        log.debug( _("self.seats[%s] set to %s") %(seat, self.seats[seat]) )

    def __set_group_select(self, checkState, group):
        self.groups[group] = checkState
        log.debug( _("self.groups[%s] set to %s") %(group, self.groups[group]) )

    def __set_displayin_select(self, w, ops):
        self.graphops['dspin'] = ops

    def __set_graphopscheck_select(self, checkState, data):
        self.graphops[data] = "ON" if checkState else "OFF"

    def fillPlayerFrame(self, frame, display):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        for site in self.conf.get_supported_sites():
            player = self.conf.supported_sites[site].screen_name
            _pname = Charset.to_gui(player)
            self.createPlayerLine(vbox1, site, _pname)

        if "GroupsAll" in display and display["GroupsAll"] == True:
            hbox = QHBoxLayout()
            vbox1.addLayout(hbox)
            cb = QCheckBox(self.filterText['groupsall'])
            cb.clicked.connect(partial(self.__set_group_select, group='allplayers'))
            hbox.addWidget(cb)
            self.sbGroups['allplayers'] = cb
            self.groups['allplayers'] = False

            lbl = QLabel(_('Min # Hands:'))
            hbox.addWidget(lbl)

            phands = QSpinBox()
            phands.setMaximum(1e9)
            hbox.addWidget(phands)
            phands.valueChanged.connect(self.__set_num_hands)

    def fillSitesFrame(self, frame):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        for site in self.conf.get_supported_sites():
            hbox = QHBoxLayout()
            vbox1.addLayout(hbox)
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
        top_hbox = QHBoxLayout()
        vbox.pack_start(top_hbox, False, False, 0)
        lbl_title = QLabel(self.filterText['tourneyTypesTitle'])
        lbl_title.set_alignment(xalign=0.0, yalign=0.5)
        top_hbox.pack_start(lbl_title, expand=True, padding=3)
        showb = QPushButton(label=_("hide"), stock=None, use_underline=True)
        showb.set_alignment(xalign=1.0, yalign=0.5)
        showb.connect('clicked', self.__toggle_box, 'tourneyTypes')
        self.toggles['tourneyTypes'] = showb
        top_hbox.pack_start(showb, expand=False, padding=1)

        vbox1 = QVBoxLayout()
        vbox.pack_start(vbox1, False, False, 0)
        self.boxes['tourneyTypes'] = vbox1

        result = self.db.getTourneyTypesIds()
        if len(result) >= 1:
            for line in result:
                hbox = QHBoxLayout()
                vbox1.pack_start(hbox, False, True, 0)
                self.createTourneyTypeLine(hbox, line[0])
        else:
            print _("INFO: No tourney types returned from database")
            log.info(_("No tourney types returned from database"))
    #end def fillTourneyTypesFrame

    def fillGamesFrame(self, frame):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        self.cursor.execute(self.sql.query['getGames'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in sorted(result, key = lambda game: self.gameName[game[0]]):
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                self.cbGames[line[0]] = self.createGameLine(hbox, line[0], self.gameName[line[0]])

            if len(result) >= 2:
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                vbox2 = QVBoxLayout()
                hbox.addLayout(vbox2)
                vbox3 = QVBoxLayout()
                hbox.addLayout(vbox3)

                hbox = QHBoxLayout()
                vbox2.addLayout(hbox)
                self.cbAllGames = self.createGameLine(hbox, 'all', self.filterText['gamesall'])
                hbox = QHBoxLayout()
                vbox3.addLayout(hbox)
                self.cbNoGames = self.createGameLine(hbox, 'none', self.filterText['gamesnone'])
        else:
            print _("INFO: No games returned from database")
            log.info(_("No games returned from database"))
    #end def fillGamesFrame
    
    def fillPositionsFrame(self, frame, display):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

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
                    hbox = QHBoxLayout()
                    vbox1.addLayout(hbox)
                    
                line_str = str(line[0])
                self.cbPositions[line_str] = self.createPositionLine(hbox, line_str, line_str)
                
                v_count += 1
                if v_count == COL_COUNT:    #set the counter to 0 if the line is full
                    v_count = 0
            
            dif = res_count % COL_COUNT    
            while dif > 0:          #fill the rest of the line with empy boxes, so that every line contains COL_COUNT elements
                fillbox = QVBoxLayout()
                hbox.addLayout(fillbox)
                dif -= 1

            if res_count > 1:
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                self.cbAllPositions = self.createPositionLine(hbox, 'all', self.filterText['positionsall'])
                self.cbNoPositions = self.createPositionLine(hbox, 'none', self.filterText['positionsnone'])
        else:
            print(_("INFO") + ": " + _("No positions returned from database"))
            log.info(_("No positions returned from database"))
        
    #end def fillSitesFrame(self, vbox, display):


    def fillHoleCardsFrame(self, frame):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        grid = QGridLayout()
        vbox1.addLayout(grid)
        self.createCardsWidget(grid)

        # Additional controls for bulk changing card selection
        hbox = QHBoxLayout()
        vbox1.addLayout(hbox)
        self.createCardsControls(hbox)

    def fillCurrenciesFrame(self, frame):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        self.cursor.execute(self.sql.query['getCurrencies'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in result:
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                if (self.currencyName.has_key(line[0])):
                    cname = self.currencyName[line[0]]
                else:
                    cname = line[0]
                self.cbCurrencies[line[0]] = self.createCurrencyLine(hbox, line[0], cname)

            if len(result) >= 2:
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                vbox2 = QVBoxLayout()
                hbox.addLayout(vbox2)
                vbox3 = QVBoxLayout()
                hbox.addLayout(vbox3)

                hbox = QHBoxLayout()
                vbox2.addLayout(hbox)
                self.cbAllCurrencies = self.createCurrencyLine(hbox, 'all', self.filterText['currenciesall'])
                hbox = QHBoxLayout()
                vbox3.addLayout(hbox)
                self.cbNoCurrencies = self.createCurrencyLine(hbox, 'none', self.filterText['currenciesnone'])
            else:
                # There is only one currency. Select it, even if it's Play Money.
                self.cbCurrencies[line[0]].set_active(True)
        else:
            #print "INFO: No currencies returned from database"
            log.info(_("No currencies returned from database"))
    #end def fillCurrenciesFrame

    def fillLimitsFrame(self, frame, display):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        self.cursor.execute(self.sql.query['getCashLimits'])
        # selects  limitType, bigBlind
        result = self.db.cursor.fetchall()
        self.found = {'nl':False, 'fl':False, 'pl':False, 'cn':False, 'hp':False, 'ring':False, 'tour':False}

        if len(result) >= 1:
            hbox = QHBoxLayout()
            vbox1.addLayout(hbox)
            vbox2 = QVBoxLayout()
            hbox.addLayout(vbox2)
            vbox3 = QVBoxLayout()
            hbox.addLayout(vbox3)
            for i, line in enumerate(result):
                if "UseType" in self.display:
                    if line[0] != self.display["UseType"]:
                        continue
                hbox = QHBoxLayout()
                if i < (len(result)+1)/2:
                    vbox2.addLayout(hbox)
                else:
                    vbox3.addLayout(hbox)
                if True:  #line[0] == 'ring':
                    name = str(line[2])+line[1]
                    self.found[line[1]] = True
                    self.cbLimits[name] = self.createLimitLine(hbox, name, name)
                    self.types[name] = line[0]
                self.found[line[0]] = True      # type is ring/tour
                self.type = line[0]        # if only one type, set it now
            if "LimitSep" in display and display["LimitSep"] == True and len(result) >= 2:
                hbox = QHBoxLayout()
                vbox1.addLayout(hbox)
                vbox2 = QVBoxLayout()
                hbox.addLayout(vbox2)
                vbox3 = QVBoxLayout()
                hbox.addLayout(vbox3)

                hbox = QHBoxLayout()
                vbox2.addLayout(hbox)
                self.cbAllLimits = self.createLimitLine(hbox, 'all', self.filterText['limitsall'])
                hbox = QHBoxLayout()
                vbox2.addLayout(hbox)
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
                            hbox = QHBoxLayout()
                            vbox3.addLayout(hbox)
                            self.cbFL = self.createLimitLine(hbox, 'fl', self.filterText['limitsFL'])
                        if self.found['nl']:
                            hbox = QHBoxLayout()
                            vbox3.addLayout(hbox)
                            self.cbNL = self.createLimitLine(hbox, 'nl', self.filterText['limitsNL'])
                        if self.found['pl']:
                            hbox = QHBoxLayout()
                            vbox3.addLayout(hbox)
                            self.cbPL = self.createLimitLine(hbox, 'pl', self.filterText['limitsPL'])
                        if self.found['cn']:
                            hbox = QHBoxLayout()
                            vbox3.addLayout(hbox)
                            self.cbCN = self.createLimitLine(hbox, 'cn', self.filterText['limitsCN'])
                        if self.found['hp']:
                            hbox = QHBoxLayout()
                            vbox3.addLayout(hbox)
                            self.cbHP = self.createLimitLine(hbox, 'hp', self.filterText['limitsHP'])
                        dest = vbox2  # for ring/tour buttons
        else:
            print _("INFO: No games returned from database")
            log.info(_("No games returned from database"))

        if "Type" in display and display["Type"] == True and self.found['ring'] and self.found['tour']:
            rb1 = QRadioButton(frame, self.filterText['ring'])
            rb1.clicked.connect(self.__set_limit_select)
            rb2 = QRadioButton(frame, self.filterText['tour'])
            rb2.clicked.connect(self.__set_limit_select)
            top_hbox.addWidget(rb1)
            top_hbox.addWidget(rb2)

            self.rb['ring'] = rb1
            self.rb['tour'] = rb2
            #print "about to set ring to true"
            rb1.setChecked(True)
            # set_active doesn't seem to call this for some reason so call manually:
            self.__set_limit_select(rb1)
            self.type = 'ring'

    def fillGraphOpsFrame(self, frame):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        hbox1 = QHBoxLayout()
        vbox1.addLayout(hbox1)

        label = QLabel(_("Show Graph In:"))
        hbox1.addWidget(label)

        button = QRadioButton("$$", frame)
        hbox1.addWidget(button)
        button.setChecked(True)
        button.clicked.connect(partial(self.__set_displayin_select, ops='$'))

        button = QRadioButton("BB", frame)
        hbox1.addWidget(button)
        button.clicked.connect(partial(self.__set_displayin_select, ops='BB'))

        button = QCheckBox(_("Showdown Winnings"))
        vbox1.addWidget(button)
        # wouldn't it be awesome if there was a way to remember the state of things like
        # this and be able to set it to what it was last time?
        button.clicked.connect(partial(self.__set_graphopscheck_select, data='showdown'))

        button = QCheckBox(_("Non-Showdown Winnings"))
        vbox1.addWidget(button)
        # ditto as 8 lines up :)
        #button.set_active(True)
        button.clicked.connect(partial(self.__set_graphopscheck_select, data='nonshowdown'))

        button = QCheckBox(_("EV"))
        vbox1.addWidget(button)
        button.clicked.connect(partial(self.__set_graphopscheck_select, data='ev'))

    def fillSeatsFrame(self, frame, display):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        hbox = QHBoxLayout()
        vbox1.addLayout(hbox)

        lbl_from = QLabel(self.filterText['seatsbetween'])
        lbl_to   = QLabel(self.filterText['seatsand'])

        adj1 = QSpinBox()
        adj1.setRange(2, 10)
        adj1.setValue(2)
        adj1.valueChanged.connect(partial(self.__seats_changed, 'from'))

        adj2 = QSpinBox()
        adj2.setRange(2, 10)
        adj2.setValue(10)
        adj2.valueChanged.connect(partial(self.__seats_changed, 'to'))

        hbox.addWidget(lbl_from)
        hbox.addWidget(adj1)
        hbox.addWidget(lbl_to)
        hbox.addWidget(adj2)

        self.sbSeats['from'] = adj1
        self.sbSeats['to']   = adj2

    def fillGroupsFrame(self, frame, display):
        vbox1 = QVBoxLayout()
        frame.setLayout(vbox1)

        hbox = QHBoxLayout()
        vbox1.addLayout(hbox)
        cb = self.createLimitLine(hbox, 'show', self.filterText['limitsshow'])

        hbox = QHBoxLayout()
        vbox1.addLayout(hbox)
        cb = QCheckBox(self.filterText['posnshow'])
        cb.clicked.connect(partial(self.__set_group_select, group='posn'))
        hbox.addWidget(cb)
        self.sbGroups['posn'] = cb
        self.groups['posn'] = False

        if "SeatSep" in display and display["SeatSep"] == True:
            hbox = QHBoxLayout()
            vbox1.addLayout(hbox)
            cb = QCheckBox(self.filterText['seatsshow'])
            cb.clicked.connect(partial(self.__set_seat_select, seat='show'))
            hbox.addWidget(cb)
            self.sbSeats['show'] = cb
            self.seats['show'] = False

    def fillCardsFrame(self, frame):
        frame.setLayout(QVBoxLayout)
        hbox1 = QHBoxLayout()
        frame.layout().addLayout(hbox1)

        cards = [ "A", "K","Q","J","T","9","8","7","6","5","4","3","2" ]

        for j in range(0, len(cards)):
            hbox1 = QHBoxLayout()
            vbox.addLayout(hbox1)
            for i in range(0, len(cards)):
                if i < (j + 1):
                    suit = "o"
                else:
                    suit = "s"
                button = QToolButton("%s%s%s" %(cards[i], cards[j], suit))
                button.clicked.connect(self.cardCallback)
                hbox1.addWidget(button)

    def fillDateFrame(self, frame):
        table = QGridLayout()
        frame.setLayout(table)

        lbl_start = QLabel(_('From:'))
        btn_start = QPushButton("Cal")
        btn_start.clicked.connect(partial(self.__calendar_dialog, entry=self.start_date))
        clr_start = QPushButton("Reset")
        clr_start.clicked.connect(self.__clear_start_date)

        lbl_end = QLabel(_('To:'))
        btn_end = QPushButton("Cal")
        btn_end.clicked.connect(partial(self.__calendar_dialog, entry=self.end_date))
        clr_end = QPushButton("Reset")
        clr_end.clicked.connect(self.__clear_end_date)

        table.addWidget(lbl_start, 0, 0)
        table.addWidget(btn_start, 0, 1)
        table.addWidget(self.start_date, 0, 2)
        table.addWidget(clr_start, 0, 3)

        table.addWidget(lbl_end, 1, 0)
        table.addWidget(btn_end, 1, 1)
        table.addWidget(self.end_date, 1, 2)
        table.addWidget(clr_end, 1, 3)

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

    def __calendar_dialog(self, widget, entry):
        d = QDialog()
        d.setWindowTitle(_('Pick a date'))

        vb = QVBoxLayout()
        d.setLayout(vb)
        cal = QCalendarWidget()
        vb.addWidget(cal)

        btn = QPushButton(_('Done'))
        btn.clicked.connect(partial(self.__get_date, dlg=d, calendar=cal, entry=entry))

        vb.addWidget(btn)

        d.exec_()

    def __clear_start_date(self, w):
        self.start_date.setDate(QDate(1970,1,1))

    def __clear_end_date(self, w):
        self.end_date.setDate(QDate(2100,1,1))

    def __get_dates(self):
        # self.day_start gives user's start of day in hours
        offset = int(self.day_start * 3600)   # calc day_start in seconds

        t1 = self.start_date.date()
        t2 = self.end_date.date()

        adj_t1 = self.MIN_DATE
        adj_t2 = self.MAX_DATE
        
        if t1 != '':
            s1 = strptime(t1.toString("yyyy-MM-dd"), "%Y-%m-%d") # make time_struct
            e1 = mktime(s1) + offset  # s1 is localtime, but returned time since epoch is UTC, then add the 
            adj_t1 = strftime("%Y-%m-%d %H:%M:%S", gmtime(e1)) # make adjusted string including time
         
        if t2 != '':   
            s2 = strptime(t2.toString("yyyy-MM-dd"), "%Y-%m-%d")
            e2 = mktime(s2) + offset  # s2 is localtime, but returned time since epoch is UTC
            e2 = e2 + 24 * 3600 - 1   # date test is inclusive, so add 23h 59m 59s to e2
            adj_t2 = strftime("%Y-%m-%d %H:%M:%S", gmtime(e2))
            
#        log.info("t1="+t1+" adj_t1="+adj_t1+'.')

        return (adj_t1, adj_t2)

    def __get_date(self, widget, dlg, calendar, entry):
        newDate = calendar.selectedDate()
        entry.setDate(newDate)

        # if the opposite date is set, and now the start date is later
        # than the end date, modify the one we didn't just set to be
        # the same as the one we did just set
        if (entry == self.start_date):
            end = self.end_date.date()
            if newDate > end:
                self.end_date.setDate(newDate)
        else:
            start = self.start_date.date()
            if newDate < start:
                self.start_date.setDate(newDate)
        dlg.accept()

    def __seats_changed(self, value, which):
        seats_from = self.sbSeats['from'].value()
        seats_to = self.sbSeats['to'].value()
        if (seats_from > seats_to):
            if (which == 'from'):
                self.sbSeats['to'].setValue(seats_from)
            else:
                self.sbSeats['from'].setValue(seats_to)

if __name__ == '__main__':
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

    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication([])
    i = Filters(db, config, qdict, display = filters_display)
    main_window = QMainWindow()
    main_window.setCentralWidget(i)
    main_window.show()
    app.exec_()
