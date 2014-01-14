#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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

# TODO: get writehand() encoding correct

import re
import sys
import traceback
import os
import os.path
from decimal_wrapper import Decimal
import operator
import time,datetime
from copy import deepcopy
from string import upper
import pprint

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")

import Configuration
from Exceptions import *
import DerivedStats
import Card
Configuration.set_logfile("fpdb-log.txt")

class Hand(object):

###############################################################3
#    Class Variables
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}
    SYMBOL = {'USD': '$', 'CAD': 'C$', 'EUR': u'€', 'GBP': u'£', 'SEK': 'kr.', 'RSD': u'РСД', 'mBTC': u'mɃ', 'T$': '', 'play': ''}
    MS = {'horse' : 'HORSE', '8game' : '8-Game', 'hose'  : 'HOSE', 'ha': 'HA'}
    ACTION = {'ante': 1, 'small blind': 2, 'secondsb': 3, 'big blind': 4, 'both': 5, 'calls': 6, 'raises': 7,
              'bets': 8, 'stands pat': 9, 'folds': 10, 'checks': 11, 'discards': 12, 'bringin': 13, 'completes': 14}


    def __init__(self, config, sitename, gametype, handText, builtFrom = "HHC"):
        #log.debug( _("Hand.init(): handText is ") + str(handText) )
        self.config = config
        self.saveActions = self.config.get_import_parameters().get('saveActions')
        self.callHud    = self.config.get_import_parameters().get("callFpdbHud")
        self.cacheSessions = self.config.get_import_parameters().get("cacheSessions")
        self.publicDB = self.config.get_import_parameters().get("publicDB")
        self.sitename = sitename
        self.siteId = self.config.get_site_id(sitename)
        self.stats = DerivedStats.DerivedStats()
        self.gametype = gametype
        self.startTime = 0
        self.handText = handText
        self.handid = 0
        self.in_path = None
        self.cancelled = False
        self.dbid_hands = 0
        self.dbid_pids = None
        self.dbid_hpid = None
        self.dbid_gt = 0
        self.tablename = ""
        self.hero = ""
        self.maxseats = None
        self.counted_seats = 0
        self.buttonpos = 0
        self.runItTimes = 0
        self.uncalledbets = False
        self.checkForUncalled = False
        self.adjustCollected = False

        #tourney stuff
        self.tourNo = None
        self.tourneyId = None
        self.tourneyTypeId = None
        self.buyin = None
        self.buyinCurrency = None
        self.buyInChips = None
        self.fee = None  # the Database code is looking for this one .. ?
        self.level = None
        self.mixed = None
        self.speed = "Normal"
        self.isSng = False
        self.isRebuy = False
        self.rebuyCost = 0
        self.isAddOn = False
        self.addOnCost = 0
        self.isKO = False
        self.koBounty = 0
        self.isMatrix = False
        self.isShootout = False
        self.isFast = False
        self.stack = "Regular"
        self.isStep = False
        self.stepNo = 0
        self.isChance = False
        self.chanceCount = 0
        self.isMultiEntry = False
        self.isReEntry = False
        self.isHomeGame = False
        self.isNewToGame = False
        self.isFifty50 = False
        self.isTime = False
        self.timeAmt = 0
        self.isSatellite = False
        self.isDoubleOrNothing = False
        self.isCashOut = False
        self.isOnDemand = False
        self.isFlighted = False
        self.isGuarantee = False
        self.guaranteeAmt = 0
        self.added = None
        self.addedCurrency = None
        self.entryId = 1

        self.seating = []
        self.players = []
        # Cache used for checkPlayerExists.
        self.player_exists_cache = set()
        self.posted = []
        self.tourneysPlayersIds = {}

        # Collections indexed by street names
        self.bets = {}
        self.lastBet = {}
        self.streets = {}
        self.actions = {} # [['mct','bets','$10'],['mika','folds'],['carlg','raises','$20']]
        self.board = {} # dict from street names to community cards
        self.holecards = {}
        self.discards = {}
        self.showdownStrings = {}
        for street in self.allStreets:
            self.streets[street] = "" # portions of the handText, filled by markStreets()
            self.actions[street] = []
        for street in self.actionStreets:
            self.bets[street] = {}
            self.lastBet[street] = 0
            self.board[street] = []
        for street in self.holeStreets:
            self.holecards[street] = {} # dict from player names to holecards
        for street in self.discardStreets:
            self.discards[street] = {} # dict from player names to dicts by street ... of tuples ... of discarded holecards
        # Collections indexed by player names
        self.rakes = {}
        self.stacks = {}
        self.collected = [] #list of ?
        self.collectees = {} # dict from player names to amounts collected (?)

        # Sets of players
        self.folded = set()
        self.dealt = set()  # 'dealt to' line to be printed
        self.shown = set()  # cards were shown
        self.mucked = set() # cards were mucked at showdown
        self.sitout = set() # players sitting out or not dealt in (usually tournament)

        # Things to do with money
        self.pot = Pot()
        self.totalpot = None
        self.totalcollected = None
        self.rake = None
        self.roundPenny = False
        self.fastFold = False
        # currency symbol for this hand
        self.sym = self.SYMBOL[self.gametype['currency']] # save typing! delete this attr when done
        self.pot.setSym(self.sym)
        self.is_duplicate = False  # i.e. don't update hudcache if true

    def __str__(self):
        vars = ( (_("BB"), self.bb),
                 (_("SB"), self.sb),
                 (_("BUTTON POS"), self.buttonpos),
                 (_("HAND NO."), self.handid),
                 (_("SITE"), self.sitename),
                 (_("TABLE NAME"), self.tablename),
                 (_("HERO"), self.hero),
                 (_("MAX SEATS"), self.maxseats),
                 (_("LEVEL"), self.level),
                 (_("MIXED"), self.mixed),
                 (_("LAST BET"), self.lastBet),
                 (_("ACTION STREETS"), self.actionStreets),
                 (_("STREETS"), self.streets),
                 (_("ALL STREETS"), self.allStreets),
                 (_("COMMUNITY STREETS"), self.communityStreets),
                 (_("HOLE STREETS"), self.holeStreets),
                 (_("COUNTED SEATS"), self.counted_seats),
                 (_("DEALT"), self.dealt),
                 (_("SHOWN"), self.shown),
                 (_("MUCKED"), self.mucked),
                 (_("TOTAL POT"), self.totalpot),
                 (_("TOTAL COLLECTED"), self.totalcollected),
                 (_("RAKE"), self.rake),
                 (_("START TIME"), self.startTime),
                 (_("TOURNAMENT NO"), self.tourNo),
                 (_("TOURNEY ID"), self.tourneyId),
                 (_("TOURNEY TYPE ID"), self.tourneyTypeId),
                 (_("BUYIN"), self.buyin),
                 (_("BUYIN CURRENCY"), self.buyinCurrency),
                 (_("BUYIN CHIPS"), self.buyInChips),
                 (_("FEE"), self.fee),
                 (_("IS REBUY"), self.isRebuy),
                 (_("IS ADDON"), self.isAddOn),
                 (_("IS KO"), self.isKO),
                 (_("KO BOUNTY"), self.koBounty),
                 (_("IS MATRIX"), self.isMatrix),
                 (_("IS SHOOTOUT"), self.isShootout),
        )

        structs = ( (_("PLAYERS"), self.players),
                    (_("STACKS"), self.stacks),
                    (_("POSTED"), self.posted),
                    (_("POT"), self.pot),
                    (_("SEATING"), self.seating),
                    (_("GAMETYPE"), self.gametype),
                    (_("ACTION"), self.actions),
                    (_("COLLECTEES"), self.collectees),
                    (_("BETS"), self.bets),
                    (_("BOARD"), self.board),
                    (_("DISCARDS"), self.discards),
                    (_("HOLECARDS"), self.holecards),
                    (_("TOURNEYS PLAYER IDS"), self.tourneysPlayersIds),
        )
        str = ''
        for (name, var) in vars:
            str = str + "\n%s = " % name + pprint.pformat(var)

        for (name, struct) in structs:
            str = str + "\n%s =\n" % name + pprint.pformat(struct, 4)
        return str

    def addHoleCards(self, street, player, open=[], closed=[], shown=False, mucked=False, dealt=False):
        """ Assigns observed holecards to a player.
            cards   list of card bigrams e.g. ['2h','Jc']
            player  (string) name of player
            shown   whether they were revealed at showdown
            mucked  whether they were mucked at showdown
            dealt   whether they were seen in a 'dealt to' line """
        log.debug("Hand.addHoleCards open+closed: %s, player: %s, shown: %s, mucked: %s, dealt: %s"
            % (open + closed, player, shown, mucked, dealt))
        self.checkPlayerExists(player, 'addHoleCards')

        if dealt:  self.dealt.add(player)
        if shown:  self.shown.add(player)
        if mucked: self.mucked.add(player)

        for i in range(len(closed)):
            if closed[i] in ('', 'Xx', 'Null', 'null'):
                closed[i] = '0x'

        try:
            self.holecards[street][player] = [open, closed]
        except KeyError, e:
            log.error(_("Hand.addHoleCards: '%s': Major failure while adding holecards: '%s'") % (self.handid, e))
            raise FpdbParseError

    def prepInsert(self, db, printtest = False):
        #####
        # Players, Gametypes, TourneyTypes are all shared functions that are needed for additional tables
        # These functions are intended for prep insert eventually
        #####
        self.gametype['maxSeats'] = self.maxseats #TODO: move up to individual parsers
        self.dbid_pids = db.getSqlPlayerIDs([p[1] for p in self.players], self.siteId, self.hero)
        self.dbid_gt = db.getSqlGameTypeId(self.siteId, self.gametype, printdata = printtest)
        
        #Gametypes
        hilo = Card.games[self.gametype['category']][2]
                
        self.gametyperow = (self.siteId, self.gametype['currency'], self.gametype['type'], self.gametype['base'],
                            self.gametype['category'], self.gametype['limitType'], hilo, self.gametype['mix'],
                            int(Decimal(self.gametype['sb'])*100), int(Decimal(self.gametype['bb'])*100),
                            int(Decimal(self.gametype['bb'])*100), int(Decimal(self.gametype['bb'])*200),
                            int(self.gametype['maxSeats']), int(self.gametype['ante']*100),
                            self.gametype['buyinType'], self.gametype['fast'], 
                            self.gametype['newToGame'], self.gametype['homeGame'])
        # Note: the above data is calculated in db.getGameTypeId
        #       Only being calculated above so we can grab the testdata
        if self.tourNo!=None:
            self.tourneyTypeId = db.getSqlTourneyTypeIDs(self)
            self.tourneyId = db.getSqlTourneyIDs(self)
            self.tourneysPlayersIds = db.getSqlTourneysPlayersIDs(self)
        
    def assembleHand(self):
        self.stats.getStats(self)
        self.hands = self.stats.getHands()
        self.handsplayers = self.stats.getHandsPlayers()
        self.handsactions = self.stats.getHandsActions()
        self.handsstove = self.stats.getHandsStove()
        self.handspots = self.stats.getHandsPots()
        
    def getHandId(self, db, id):
        if db.isDuplicate(self.siteId, self.hands['siteHandNo'], self.hands['heroSeat'], self.publicDB):
            #log.debug(_("Hand.insert(): hid #: %s is a duplicate") % hh['siteHandNo'])
            self.is_duplicate = True  # i.e. don't update hudcache
            next = id
            raise FpdbHandDuplicate(self.hands['siteHandNo'])
        else:
            self.dbid_hands = id
            self.hands['id'] = self.dbid_hands
            next = id + db.hand_inc
        return next

    def insertHands(self, db, fileId, doinsert = False, printtest = False):
        """ Function to insert Hand into database
            Should not commit, and do minimal selects. Callers may want to cache commits
            db: a connected Database object"""
        self.hands['gametypeId'] = self.dbid_gt
        self.hands['seats']      = len(self.dbid_pids)
        self.hands['fileId']     = fileId
        db.storeHand(self.hands, doinsert, printtest)
        db.storeBoards(self.dbid_hands, self.hands['boards'], doinsert)

    def insertHandsPlayers(self, db, doinsert = False, printtest = False):
        """ Function to inserts HandsPlayers into database"""
        db.storeHandsPlayers(self.dbid_hands, self.dbid_pids, self.handsplayers, doinsert, printtest)
        if self.handspots:
            self.handspots.sort(key=lambda x: x[1])
            for ht in self.handspots: 
                ht[0] = self.dbid_hands
        db.storeHandsPots(self.handspots, doinsert)
    
    def insertHandsActions(self, db, doinsert = False, printtest = False):
        """ Function to inserts HandsActions into database"""
        if self.saveActions:
            db.storeHandsActions(self.dbid_hands, self.dbid_pids, self.handsactions, doinsert, printtest)
    
    def insertHandsStove(self, db, doinsert = False):
        """ Function to inserts HandsStove into database"""
        if self.handsstove:
            for hs in self.handsstove: hs[0] = self.dbid_hands
        db.storeHandsStove(self.handsstove, doinsert)

    def updateHudCache(self, db, doinsert = False):
        """ Function to update the HudCache"""
        if self.callHud:
            db.storeHudCache(self.dbid_gt, self.gametype, self.dbid_pids, self.startTime, self.handsplayers, doinsert)
        
    def updateSessionsCache(self, db, tz, doinsert = False):
        """ Function to update the SessionsCache"""
        if self.cacheSessions:
            heroes = []
            if self.hero in self.dbid_pids:
                heroes = [self.dbid_pids[self.hero]]
            else:
                heroes = [self.dbid_pids[self.players[0][1]]]
                
            db.storeSessionsCache(self.dbid_hands, self.dbid_pids, self.startTime, self.tourneyId, heroes, tz, doinsert) 
            db.storeCashCache(self.dbid_hands, self.dbid_pids, self.startTime, self.dbid_gt, self.gametype, self.handsplayers, heroes, self.hero, doinsert)
            db.storeTourCache(self.dbid_hands, self.dbid_pids, self.startTime, self.tourneyId, self.gametype, self.handsplayers, heroes, self.hero, doinsert)
            
    def updateCardsCache(self, db, tz, doinsert = False):
        """ Function to update the CardsCache"""
        if self.cacheSessions:
            heroes = []
            if self.hero in self.dbid_pids: 
                heroes = [self.dbid_pids[self.hero]]
            db.storeCardsCache(self.dbid_hands, self.dbid_pids, self.startTime, self.dbid_gt, self.tourneyTypeId, self.gametype, self.siteId, self.handsplayers, self.handsstove, heroes, tz, doinsert)
                
    def updatePositionsCache(self, db, tz, doinsert = False):
        """ Function to update the PositionsCache"""
        if self.cacheSessions:
            heroes = []
            if self.hero in self.dbid_pids: 
                heroes = [self.dbid_pids[self.hero]]
            db.storePositionsCache(self.dbid_hands, self.dbid_pids, self.startTime, self.dbid_gt, self.tourneyTypeId, self.gametype, self.siteId, self.handsplayers, heroes, tz, doinsert)

    def select(self, db, handId):
        """ Function to create Hand object from database """
        c = db.get_cursor()
        q = db.sql.query['playerHand']
        q = q.replace('%s', db.sql.query['placeholder'])

        # PlayerStacks
        c.execute(q, (handId,))
        # See NOTE: below on what this does.

        # Discripter must be set to lowercase as postgres returns all descriptors lower case and SQLight returns them as they are
        res = [dict(line) for line in [zip([ column[0].lower() for column in c.description], row) for row in c.fetchall()]]
        for row in res:
            #print "DEBUG: addPlayer(%s, %s, %s, %s)" %(row['seatno'],row['name'],row['chips'],row['position'])
            self.addPlayer(row['seatno'],row['name'],str(row['chips']), str(row['position']))
            cardlist = []
            cardlist.append(Card.valueSuitFromCard(row['card1']))
            cardlist.append(Card.valueSuitFromCard(row['card2']))
            cardlist.append(Card.valueSuitFromCard(row['card3']))
            cardlist.append(Card.valueSuitFromCard(row['card4']))
            cardlist.append(Card.valueSuitFromCard(row['card5']))
            cardlist.append(Card.valueSuitFromCard(row['card6']))
            cardlist.append(Card.valueSuitFromCard(row['card7']))
            cardlist.append(Card.valueSuitFromCard(row['card8']))
            cardlist.append(Card.valueSuitFromCard(row['card9']))
            cardlist.append(Card.valueSuitFromCard(row['card10']))
            cardlist.append(Card.valueSuitFromCard(row['card11']))
            cardlist.append(Card.valueSuitFromCard(row['card12']))
            cardlist.append(Card.valueSuitFromCard(row['card13']))
            cardlist.append(Card.valueSuitFromCard(row['card14']))
            cardlist.append(Card.valueSuitFromCard(row['card15']))
            cardlist.append(Card.valueSuitFromCard(row['card16']))
            cardlist.append(Card.valueSuitFromCard(row['card17']))
            cardlist.append(Card.valueSuitFromCard(row['card18']))
            cardlist.append(Card.valueSuitFromCard(row['card19']))
            cardlist.append(Card.valueSuitFromCard(row['card20']))
            # mucked/shown/dealt is not in the database, use mucked for villain and dealt for hero
            if row['name'] == self.hero:
                dealt=True
                mucked=False
            else:
                dealt=False
                mucked=True
            if cardlist[0] == '':
                pass
            elif self.gametype['category'] == 'holdem':
                self.addHoleCards('PREFLOP', row['name'], closed=cardlist[0:2], shown=False, mucked=mucked, dealt=dealt)
            elif self.gametype['category'] in ('omahahi', 'omahahilo'):
                self.addHoleCards('PREFLOP', row['name'], closed=cardlist[0:4], shown=False, mucked=mucked, dealt=dealt)
            elif self.gametype['category'] in ('27_3draw', '27_1draw', 'fivedraw'):
                self.addHoleCards('DEAL', row['name'], closed=cardlist[0:5], shown=False, mucked=mucked, dealt=dealt)
            elif self.gametype['category'] in ('razz', 'studhi', 'studhilo'):
                #print "DEBUG: cardlist: %s" % cardlist
                # FIXME?: shown/dealt/mucked correct for the next method calls?
                self.addHoleCards('THIRD',   row['name'], open=[cardlist[2]], closed=cardlist[0:2], shown=False, dealt=True)
                self.addHoleCards('FOURTH',  row['name'], open=[cardlist[3]], closed=cardlist[0:3], shown=False, mucked=False)
                self.addHoleCards('FIFTH',   row['name'], open=[cardlist[4]], closed=cardlist[0:4], shown=False, mucked=False)
                self.addHoleCards('SIXTH',   row['name'], open=[cardlist[5]], closed=cardlist[0:5], shown=False, mucked=False)
                self.addHoleCards('SEVENTH', row['name'], open=[cardlist[6]], closed=cardlist[0:6], shown=False, mucked=False)
            if row['winnings'] > 0:
                self.addCollectPot(row['name'], str(row['winnings']))
            if row['position'] == '0':
                # position 0 is the button, heads-up there is no position 0
                self.buttonpos = row['seatno']
            elif row['position'] == 'B':
                # Headsup the BB is the button, only set the button position if it's not set before
                if self.buttonpos == None or self.buttonpos == 0:
                    self.buttonpos = row['seatno']


        # HandInfo
        q = db.sql.query['singleHand']
        q = q.replace('%s', db.sql.query['placeholder'])
        c.execute(q, (handId,))

        # NOTE: This relies on row_factory = sqlite3.Row (set in connect() params)
        #       Need to find MySQL and Postgres equivalents
        #       MySQL maybe: cursorclass=MySQLdb.cursors.DictCursor
        #res = c.fetchone()

        # Using row_factory is global, and affects the rest of fpdb. The following 2 line achieves
        # a similar result

        # Discripter must be set to lowercase as supported dbs differ on what is returned.
        res = [dict(line) for line in [zip([ column[0].lower() for column in c.description], row) for row in c.fetchall()]]
        res = res[0]

        #res['tourneyId'] #res['seats'] #res['rush']
        self.tablename = res['tablename']
        self.handid    = res['sitehandno']
        # FIXME: Need to figure out why some times come out of the DB as %Y-%m-%d %H:%M:%S+00:00,
        #        and others as %Y-%m-%d %H:%M:%S
        #print "DEBUG: res['*']: %s" % res
        
        #self.startTime currently unused in the replayer and commented out. 
        #    Can't be done like this because not all dbs return the same type for starttime
        #try:
        #    self.startTime = datetime.datetime.strptime(res['starttime'], "%Y-%m-%d %H:%M:%S+00:00")
        #except ValueError:
        #    self.startTime = datetime.datetime.strptime(res['starttime'], "%Y-%m-%d %H:%M:%S")
        # However a startTime is needed for a valid output by writeHand:
        self.startTime = datetime.datetime.strptime("1970-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")

        cards = map(Card.valueSuitFromCard, [res['boardcard1'], res['boardcard2'], res['boardcard3'], res['boardcard4'], res['boardcard5']])
        #print "DEBUG: res['boardcard1']: %s" % res['boardcard1']
        #print "DEBUG: cards: %s" % cards
        if cards[0]:
            self.setCommunityCards('FLOP', cards[0:3])
        if cards[3]:
            self.setCommunityCards('TURN', [cards[3]])
        if cards[4]:
            self.setCommunityCards('RIVER', [cards[4]])
        # playersVpi | playersAtStreet1 | playersAtStreet2 | playersAtStreet3 |
        # playersAtStreet4 | playersAtShowdown | street0Raises | street1Raises |
        # street2Raises | street3Raises | street4Raises | street1Pot | street2Pot |
        # street3Pot | street4Pot | showdownPot | comment | commentTs | texture

        # Actions
        q = db.sql.query['handActions']
        q = q.replace('%s', db.sql.query['placeholder'])
        c.execute(q, (handId,))
        
        # Discripter must be set to lowercase as supported dbs differ on what is returned.
        res = [dict(line) for line in [zip([ column[0].lower() for column in c.description], row) for row in c.fetchall()]]
        for row in res:
            name = row['name']
            street = row['street']
            act = row['actionid']
            # allin True/False if row['allIn'] == 0
            bet = str(row['bet'])
            street = self.allStreets[int(street)+1]
            discards = row['cardsdiscarded']
            log.debug("Hand.select():: name: '%s' street: '%s' act: '%s' bet: '%s'" %(name, street, act, bet))
            if   act == 1: # Ante
                self.addAnte(name, bet)
            elif act == 2: # Small Blind
                self.addBlind(name, 'small blind', bet)
            elif act == 3: # Second small blind
                self.addBlind(name, 'secondsb', bet)
            elif act == 4: # Big Blind
                self.addBlind(name, 'big blind', bet)
            elif act == 5: # Post both blinds
                self.addBlind(name, 'both', bet)
            elif act == 6: # Call
                self.addCall(street, name, bet)
            elif act == 7: # Raise
                self.addRaiseBy(street, name, bet)
            elif act == 8: # Bet
                self.addBet(street, name, bet)
            elif act == 9: # Stands pat
                self.addStandsPat(street, name, discards)
            elif act == 10: # Fold
                self.addFold(street, name)
            elif act == 11: # Check
                self.addCheck(street, name)
            elif act == 12: # Discard
                self.addDiscard(street, name, row['numdiscarded'], discards)
            elif act == 13: # Bringin
                self.addBringIn(name, bet)
            elif act == 14: # Complete
                self.addComplete(street, name, bet)
            else:
                print "DEBUG: unknown action: '%s'" % act

        self.totalPot()
        self.rake = self.totalpot - self.totalcollected
        #self.writeHand()

        #hhc.readShowdownActions(self)
        #hc.readShownCards(self)


    def addPlayer(self, seat, name, chips, position=None, sitout=False):
        """ Adds a player to the hand, and initialises data structures indexed by player.
            seat    (int) indicating the seat
            name    (string) player name
            chips   (string) the chips the player has at the start of the hand (can be None)
            position     (string) indicating the position of the player (S,B, 0-7) (optional, not needed on Hand import from Handhistory).
            If a player has None chips he won't be added."""
        log.debug("addPlayer: %s %s (%s)" % (seat, name, chips))
        if chips is not None:
            chips = chips.replace(u',', u'') #some sites have commas
            self.players.append([seat, name, chips, position]) #removed most likely unused 0s from list and added position... former list: [seat, name, chips, 0, 0]
            self.stacks[name] = Decimal(chips)
            self.pot.addPlayer(name)
            for street in self.actionStreets:
                self.bets[street][name] = []
                #self.holecards[name] = {} # dict from street names.
                #self.discards[name] = {} # dict from street names.
            if sitout:
                self.sitout.add(name)
                
    def removePlayer(self, name):
        if self.stacks.get(name):
            self.players = [p for p in self.players if p[1]!=name]
            del self.stacks[name]
            self.pot.removePlayer(name)
            for street in self.actionStreets:
                del self.bets[street][name]
            self.sitout.discard(name)

    def addStreets(self, match):
        # go through m and initialise actions to empty list for each street.
        if match:
            self.streets.update(match.groupdict())
            log.debug("markStreets:\n"+ str(self.streets))
        else:
            tmp = self.handText[0:100]
            self.cancelled = True
            raise FpdbHandPartial(_("Streets didn't match - Assuming hand '%s' was cancelled.") % (self.handid) + " " + _("First 100 characters: %s") % tmp)

    def checkPlayerExists(self,player,source = None):
        # Fast path, because this function is called ALL THE TIME.
        if player in self.player_exists_cache:
            return

        if player not in (p[1] for p in self.players):
            if source is not None:
                log.error(_("Hand.%s: '%s' unknown player: '%s'") % (source, self.handid, player))
            raise FpdbParseError
        else:
            self.player_exists_cache.add(player)

    def setCommunityCards(self, street, cards):
        log.debug("setCommunityCards %s %s" %(street,  cards))
        self.board[street] = [self.card(c) for c in cards]
#        print "DEBUG: self.board: %s" % self.board

    def card(self,c):
        """upper case the ranks but not suits, 'atjqk' => 'ATJQK'"""
        for k,v in self.UPS.items():
            c = c.replace(k,v)
        return c

    def addAllIn(self, street, player, amount):
        """ For sites (currently only Merge & Microgaming) which record "all in" as a special action, 
            which can mean either "calls and is all in" or "raises all in"."""
        self.checkPlayerExists(player, 'addAllIn')
        amount = amount.replace(u',', u'') #some sites have commas
        Ai = Decimal(amount)
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        C = Bp - Bc
        if Ai <= C:
            self.addCall(street, player, amount)
        elif Bp == 0:
            self.addBet(street, player, amount)
        else:
            Rb = Ai - C
            Rt = Bp + Rb
            self._addRaise(street, player, C, Rb, Rt)

    def addAnte(self, player, ante):
        log.debug("%s %s antes %s" % ('BLINDSANTES', player, ante))
        if player is not None:
            ante = ante.replace(u',', u'') #some sites have commas
            self.checkPlayerExists(player, 'addAnte')
            ante = Decimal(ante)
            self.bets['BLINDSANTES'][player].append(ante)
            self.stacks[player] -= ante
            act = (player, 'ante', ante, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)
            self.pot.addCommonMoney(player, ante)
            self.pot.addAntes(player, ante)
            if not 'ante' in self.gametype.keys() or self.gametype['ante'] == 0:
                self.gametype['ante'] = ante
#I think the antes should be common money, don't have enough hand history to check

    def addBlind(self, player, blindtype, amount):
        # if player is None, it's a missing small blind.
        # The situation we need to cover are:
        # Player in small blind posts
        #   - this is a bet of 1 sb, as yet uncalled.
        # Player in the big blind posts
        #   - this is a call of 1 sb and a raise to 1 bb
        #
        log.debug("addBlind: %s posts %s, %s" % (player, blindtype, amount))
        if player is not None:
            self.checkPlayerExists(player, 'addBlind')
            amount = amount.replace(u',', u'') #some sites have commas
            amount = Decimal(amount)
            self.stacks[player] -= amount
            act = (player, blindtype, amount, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)

            if blindtype == 'both':
                # work with the real amount. limit games are listed as $1, $2, where
                # the SB 0.50 and the BB is $1, after the turn the minimum bet amount is $2....
                amount = Decimal(str(self.bb))
                sb = Decimal(str(self.sb))
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)

            if blindtype == 'secondsb':
                amount = Decimal(0)
                sb = Decimal(str(self.sb))
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)
                
            street = 'BLAH'

            if self.gametype['base'] == 'hold':
                street = 'PREFLOP'
            elif self.gametype['base'] == 'draw':
                street = 'DEAL'
            
            self.bets[street][player].append(amount)
            self.pot.addMoney(player, amount)
            if amount>self.lastBet.get(street):
                self.lastBet[street] = amount
            self.posted = self.posted + [[player,blindtype]]


    def addCall(self, street, player=None, amount=None):
        if amount is not None:
            amount = amount.replace(u',', u'') #some sites have commas
        log.debug(_("%s %s calls %s") %(street, player, amount))
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            self.checkPlayerExists(player, 'addCall')
            amount = Decimal(amount)
            self.bets[street][player].append(amount)
            if street in ('PREFLOP', 'DEAL', 'THIRD') and self.lastBet.get(street)<amount:
                self.lastBet[street] = amount
            self.stacks[player] -= amount
            #print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            act = (player, 'calls', amount, self.stacks[player] == 0)
            self.actions[street].append(act)
            self.pot.addMoney(player, amount)
            
    def addCallTo(self, street, player=None, amountTo=None):
        if amountTo:
            amountTo = amountTo.replace(u',', u'') #some sites have commas
        #log.debug(_("%s %s calls %s") %(street, player, amount))
        # Potentially calculate the amount of the callTo if not supplied
        # corner cases include if player would be all in
        if amountTo is not None:
            self.checkPlayerExists(player, 'addCallTo')
            Bc = sum(self.bets[street][player])
            Ct = Decimal(amountTo)
            C = Ct - Bc
            amount = C
            self.bets[street][player].append(amount)
            #self.lastBet[street] = amount
            self.stacks[player] -= amount
            #print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            act = (player, 'calls', amount, self.stacks[player] == 0)
            self.actions[street].append(act)
            self.pot.addMoney(player, amount)

    def addRaiseBy(self, street, player, amountBy):
        """ Add a raise by amountBy on [street] by [player] """
        #Given only the amount raised by, the amount of the raise can be calculated by
        # working out how much this player has already in the pot
        #   (which is the sum of self.bets[street][player])
        # and how much he needs to call to match the previous player
        #   (which is tracked by self.lastBet)
        # let Bp = previous bet
        #     Bc = amount player has committed so far
        #     Rb = raise by
        # then: C = Bp - Bc (amount to call)
        #      Rt = Bp + Rb (raise to)
        #
        amountBy = amountBy.replace(u',', u'') #some sites have commas
        self.checkPlayerExists(player, 'addRaiseBy')
        Rb = Decimal(amountBy)
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        C = Bp - Bc
        Rt = Bp + Rb

        self._addRaise(street, player, C, Rb, Rt)
        #~ self.bets[street][player].append(C + Rb)
        #~ self.stacks[player] -= (C + Rb)
        #~ self.actions[street] += [(player, 'raises', Rb, Rt, C, self.stacks[player]==0)]
        #~ self.lastBet[street] = Rt

    def addCallandRaise(self, street, player, amount):
        """ For sites which by "raises x" mean "calls and raises putting a total of x in the por". """
        self.checkPlayerExists(player, 'addCallandRaise')
        amount = amount.replace(u',', u'') #some sites have commas
        CRb = Decimal(amount)
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        C = Bp - Bc
        Rb = CRb - C
        Rt = Bp + Rb

        self._addRaise(street, player, C, Rb, Rt)

    def addRaiseTo(self, street, player, amountTo):
        """ Add a raise on [street] by [player] to [amountTo] """
        self.checkPlayerExists(player, 'addRaiseTo')
        amountTo = amountTo.replace(u',', u'') #some sites have commas
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        Rt = Decimal(amountTo)
        C = Bp - Bc
        Rb = Rt - C - Bc
        self._addRaise(street, player, C, Rb, Rt)

    def _addRaise(self, street, player, C, Rb, Rt, action = 'raises'):
        log.debug(_("%s %s raise %s") %(street, player, Rt))
        self.bets[street][player].append(C + Rb)
        self.stacks[player] -= (C + Rb)
        act = (player, action, Rb, Rt, C, self.stacks[player]==0)
        self.actions[street].append(act)
        self.lastBet[street] = Rt # TODO check this is correct
        self.pot.addMoney(player, C+Rb)



    def addBet(self, street, player, amount):
        log.debug(_("%s %s bets %s") %(street, player, amount))
        amount = amount.replace(u',', u'') #some sites have commas
        amount = Decimal(amount)
        self.checkPlayerExists(player, 'addBet')
        self.bets[street][player].append(amount)
        self.stacks[player] -= amount
        #print "DEBUG %s bets %s, stack %s" % (player, amount, self.stacks[player])
        act = (player, 'bets', amount, self.stacks[player]==0)
        self.actions[street].append(act)
        self.lastBet[street] = amount
        self.pot.addMoney(player, amount)


    def addStandsPat(self, street, player, cards=None):
        self.checkPlayerExists(player, 'addStandsPat')
        act = (player, 'stands pat')
        self.actions[street].append(act)
        if cards:
            cards = cards.split(' ')
            self.addHoleCards(street, player, open=[], closed=cards)


    def addFold(self, street, player):
        log.debug(_("%s %s folds") % (street, player))
        self.checkPlayerExists(player, 'addFold')
        self.folded.add(player)
        self.pot.addFold(player)
        self.actions[street].append((player, 'folds'))


    def addCheck(self, street, player):
        #print "DEBUG: %s %s checked" % (street, player)
        logging.debug(_("%s %s checks") % (street, player))
        self.checkPlayerExists(player, 'addCheck')
        self.actions[street].append((player, 'checks'))


    def discardDrawHoleCards(self, cards, player, street):
        log.debug("discardDrawHoleCards '%s' '%s' '%s'" % (cards, player, street))
        self.discards[street][player] = set([cards])


    def addDiscard(self, street, player, num, cards=None):
        self.checkPlayerExists(player, 'addDiscard')
        if cards:
            act = (player, 'discards', Decimal(num), cards)
            self.discardDrawHoleCards(cards, player, street)
        else:
            act = (player, 'discards', Decimal(num))
        self.actions[street].append(act)


    def addCollectPot(self,player, pot):
        log.debug("%s collected %s" % (player, pot))
        self.checkPlayerExists(player, 'addCollectPot')
        self.collected = self.collected + [[player, pot]]
        if player not in self.collectees:
            self.collectees[player] = Decimal(pot)
        else:
            self.collectees[player] += Decimal(pot)


    def addShownCards(self, cards, player, holeandboard=None, shown=True, mucked=False, string=None):
        """ For when a player shows cards for any reason (for showdown or out of choice).
            Card ranks will be uppercased """
        log.debug("addShownCards %s hole=%s all=%s" % (player, cards,  holeandboard))
        if cards is not None:
            self.addHoleCards(cards,player,shown, mucked)
            if string is not None:
                self.showdownStrings[player] = string
        elif holeandboard is not None:
            holeandboard = set([self.card(c) for c in holeandboard])
            board = set([c for s in self.board.values() for c in s])
            self.addHoleCards(holeandboard.difference(board),player,shown, mucked)
            
    def sittingOut(self):
        dealtIn = set()
        for i, street in enumerate(self.actionStreets):
            for j, act in enumerate(self.actions[street]):
                dealtIn.add(act[0])
        for player in self.collectees.keys():
            dealtIn.add(player)
        for player in self.dealt:
            dealtIn.add(player)
        for p in list(self.players):
            if p[1] not in dealtIn:
                if self.gametype['type']=='tour':
                    self.sitout.add(p[1])
                else:
                    self.removePlayer(p[1])
            
    def setUncalledBets(self, value):
        self.uncalledbets = value                
                
    def totalPot(self):
        """ If all bets and blinds have been added, totals up the total pot size"""

        # This gives us the total amount put in the pot
        if self.totalpot is None:
            self.pot.end()
            self.totalpot = self.pot.total
        
        if self.adjustCollected:
            self.stats.awardPots(self)
        
        def gettempcontainers(collected, collectees):
            (collectedCopy, collecteesCopy, totalcollected) = ([], {}, 0)
            for i,v in enumerate(sorted(collected, key=lambda collectee: collectee[1], reverse=True)):
                if Decimal(v[1])!=0:
                    totalcollected += Decimal(v[1])
                    collectedCopy.append([v[0], Decimal(v[1])])
            for k, j in collectees.iteritems():
                if j!=0: collecteesCopy[k] = j
            return collectedCopy, collecteesCopy, totalcollected
        
        collected, collectees, totalcollected = gettempcontainers(self.collected, self.collectees)
        if (self.uncalledbets or ((self.totalpot - totalcollected < 0) and self.checkForUncalled)):
            for i,v in enumerate(sorted(self.collected, key=lambda collectee: collectee[1], reverse=True)):
                if v[0] in self.pot.returned: 
                    collected[i][1] = Decimal(v[1]) - self.pot.returned[v[0]]
                    collectees[v[0]] -= self.pot.returned[v[0]]
                    self.pot.returned[v[0]] = 0
            (self.collected, self.collectees, self.totalcollected) = gettempcontainers(collected, collectees)

        # This gives us the amount collected, i.e. after rake
        if self.totalcollected is None:
            self.totalcollected = 0;
            #self.collected looks like [[p1,amount][px,amount]]
            for entry in self.collected:
                self.totalcollected += Decimal(entry[1])

    def getGameTypeAsString(self):
        """ Map the tuple self.gametype onto the pokerstars string describing it """
        # currently it appears to be something like ["ring", "hold", "nl", sb, bb]:
        gs = {"holdem"     : "Hold'em",
              "omahahi"    : "Omaha",
              "omahahilo"  : "Omaha Hi/Lo",
              "razz"       : "Razz",
              "studhi"     : "7 Card Stud",
              "studhilo"   : "7 Card Stud Hi/Lo",
              "fivedraw"   : "5 Card Draw",
              "27_1draw"   : "Single Draw 2-7 Lowball",
              "27_3draw"   : "Triple Draw 2-7 Lowball",
              "5_studhi"   : "5 Card Stud",
              "badugi"     : "Badugi"
             }
        ls = {"nl"  : "No Limit",
              "pl"  : "Pot Limit",
              "fl"  : "Limit",
              "cn"  : "Cap No Limit",
              "cp"  : "Cap Pot Limit"
             }

        log.debug("gametype: %s" %(self.gametype))
        retstring = "%s %s" %(gs[self.gametype['category']], ls[self.gametype['limitType']])
        return retstring


    def writeHand(self, fh=sys.__stdout__):
        print >>fh, "Override me"

    def printHand(self):
        self.writeHand(sys.stdout)

    def actionString(self, act, street=None):
        log.debug("Hand.actionString(act=%s, street=%s)" % (act, street))
        
        if act[1] == 'folds':
            return ("%s: folds " %(act[0]))
        elif act[1] == 'checks':
            return ("%s: checks " %(act[0]))
        elif act[1] == 'calls':
            return ("%s: calls %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'bets':
            return ("%s: bets %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'raises':
            return ("%s: raises %s%s to %s%s%s" %(act[0], self.sym, act[2], self.sym, act[3], ' and is all-in' if act[5] else ''))
        elif act[1] == 'completes':
            return ("%s: completes to %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif(act[1] == "small blind"):
            return ("%s: posts small blind %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif(act[1] == "big blind"):
            return ("%s: posts big blind %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif(act[1] == "both"):
            return ("%s: posts small & big blinds %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif(act[1] == "ante"):
            return ("%s: posts the ante %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'bringin':
            return ("%s: brings in for %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'discards':
            return ("%s: discards %s %s%s" %(act[0], act[2], 'card' if act[2] == 1 else 'cards' , " [" + " ".join(self.discards[street][act[0]]) + "]" if self.hero == act[0] else ''))
        elif act[1] == 'stands pat':
            return ("%s: stands pat" %(act[0]))
        
    def get_actions_short(self, player, street):
        """ Returns a string with shortcuts for the actions of the given player and the given street
            F ... fold, X ... Check, B ...Bet, C ... Call, R ... Raise
        """
        actions = self.actions[street]
        list = []
        for action in actions:
            if player in action:
                if action[1] == 'folds':
                    list.append('F')
                elif action[1] == 'checks':
                    list.append('X')
                elif action[1] == 'bets':
                    list.append('B')
                elif action[1] == 'calls':
                    list.append('C')
                elif action[1] == 'raises':
                    list.append('R')
                
        return ''.join(list) 

    def get_actions_short_streets(self, player, *streets):
        """ Returns a string with shortcuts for the actions of the given player on all given streets seperated by ',' """
        list = []
        for street in streets:
            str = self.get_actions_short(player, street)
            if len(str) > 0:                            #if there is no action on later streets, nothing is added.
                list.append(str)
        return ','.join(list)
    
    def get_player_position(self, player):
        """ Returns the given players postion (S, B, 0-7) """
        #position has been added to the players list. It could be calculated from buttonpos and player seatnums, 
        #but whats the point in calculating a value that has been there anyway?
        for p in self.players:
            if p[1] == player:
                return p[3]

    def getStakesAsString(self):
        """Return a string of the stakes of the current hand."""
        return "%s%s/%s%s" % (self.sym, self.sb, self.sym, self.bb)

    def getStreetTotals(self):
        pass

    def writeGameLine(self):
        """Return the first HH line for the current hand."""
        gs = "PokerStars Game #%s: " % self.handid

        if self.tourNo is not None and self.mixed is not None: # mixed tournament
            gs = gs + "Tournament #%s, %s %s (%s) - Level %s (%s) - " % (self.tourNo, self.buyin, self.MS[self.mixed], self.getGameTypeAsString(), self.level, self.getStakesAsString())
        elif self.tourNo is not None: # all other tournaments
            gs = gs + "Tournament #%s, %s %s - Level %s (%s) - " % (self.tourNo,
                            self.buyin, self.getGameTypeAsString(), self.level, self.getStakesAsString())
        elif self.mixed is not None: # all other mixed games
            gs = gs + " %s (%s, %s) - " % (self.MS[self.mixed],
                            self.getGameTypeAsString(), self.getStakesAsString())
        else: # non-mixed cash games
            gs = gs + " %s (%s) - " % (self.getGameTypeAsString(), self.getStakesAsString())

        try:
            timestr = datetime.datetime.strftime(self.startTime, '%Y/%m/%d %H:%M:%S ET')
        except TypeError:
            print _("*** ERROR - HAND: calling writeGameLine with unexpected STARTTIME value, expecting datetime.date object, received:"), self.startTime
            print _("*** Make sure your HandHistoryConverter is setting hand.startTime properly!")
            print _("*** Game String:"), gs
            return gs
        else:
            return gs + timestr

    def writeTableLine(self):
        table_string = "Table "
        if self.gametype['type'] == 'tour':
            table_string = table_string + "\'%s %s\' %s-max" % (self.tourNo, self.tablename, self.maxseats)
        else:
            table_string = table_string + "\'%s\' %s-max" % (self.tablename, self.maxseats)
        if self.gametype['currency'] == 'play':
            table_string = table_string + " (Play Money)"
        if self.buttonpos != None and self.buttonpos != 0:
            table_string = table_string + " Seat #%s is the button" % self.buttonpos
        return table_string


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        print >>fh, self.writeGameLine()
        print >>fh, self.writeTableLine()


class HoldemOmahaHand(Hand):
    def __init__(self, config, hhc, sitename, gametype, handText, builtFrom = "HHC", handid=None):
        self.config = config
        if gametype['base'] != 'hold':
            pass # or indeed don't pass and complain instead
        log.debug("HoldemOmahaHand")
        self.allStreets = ['BLINDSANTES', 'PREFLOP','FLOP','TURN','RIVER']
        self.holeStreets = ['PREFLOP']
        if gametype['category']=='irish':
            self.discardStreets = ['TURN']
        else:
            self.discardStreets = ['PREFLOP']
        self.communityStreets = ['FLOP', 'TURN', 'RIVER']
        self.actionStreets = ['BLINDSANTES','PREFLOP','FLOP','TURN','RIVER']
        Hand.__init__(self, self.config, sitename, gametype, handText, builtFrom = "HHC")
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        if hasattr(hhc, "in_path"):
            self.in_path = hhc.in_path
        else:
            self.in_path = "database"

        #Populate a HoldemOmahaHand
        #Generally, we call 'read' methods here, which get the info according to the particular filter (hhc)
        # which then invokes a 'addXXX' callback
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            if self.gametype['type'] == 'tour':
                self.tablename = "%s %s" % (self.tourNo, self.tablename)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)

            if self.cancelled:
                return

            hhc.readBlinds(self)

            hhc.readAntes(self)
            hhc.readButton(self)
            hhc.readHeroCards(self)
            hhc.readShowdownActions(self)
            # Read actions in street order
            #print "debugging there"
            for street, text in self.streets.iteritems():
                if text and (street is not "PREFLOP"): #TODO: the except PREFLOP shouldn't be necessary, but regression-test-files/cash/Everleaf/Flop/NLHE-10max-USD-0.01-0.02-201008.2Way.All-in.pre.txt fails without it
                    #print(street)
                    hhc.readCommunityCards(self, street)
            for street in self.actionStreets:
                if self.streets[street]:
                    hhc.readAction(self, street)
                    self.pot.markTotal(street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self)
            self.pot.handid = self.handid # This is only required so Pot can throw it in totalPot
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            self.sittingOut()
            hhc.readOther(self)
            #print "\nHand:\n"+str(self)
        elif builtFrom == "DB":
            # Creator expected to call hhc.select(hid) to fill out object
            log.debug("HoldemOmahaHand.__init__: " + _("DEBUG:") + " " +_("HoldemOmaha hand initialised for %s") % "select()")
            self.maxseats = 10
        else:
            log.warning("HoldemOmahaHand.__init__: " + _("Neither HHC nor DB+handID provided"))
            pass


    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False, string=None):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
            if len(cards) in (2, 3, 4, 6) or self.gametype['category'] in ('5_omahahi', '5_omaha8', 'cour_hi', 'cour_hilo'):  # avoid adding board by mistake (Everleaf problem)
                self.addHoleCards('PREFLOP', player, open=[], closed=cards, shown=shown, mucked=mucked, dealt=dealt)
            elif len(cards) == 5:     # cards holds a winning hand, not hole cards
                # filter( lambda x: x not in b, a )             # calcs a - b where a and b are lists
                # so diff is set to the winning hand minus the board cards, if we're lucky that leaves the hole cards
                diff = filter( lambda x: x not in self.board['FLOP']+self.board['TURN']+self.board['RIVER'], cards )
                if len(diff) == 2 and self.gametype['category'] in ('holdem'):
                    self.addHoleCards('PREFLOP', player, open=[], closed=diff, shown=shown, mucked=mucked, dealt=dealt)
        if string is not None:
            self.showdownStrings[player] = string

    def getStreetTotals(self):
        # street1Pot INT,                  /* pot size at flop/street4 */
        # street2Pot INT,                  /* pot size at turn/street5 */
        # street3Pot INT,                  /* pot size at river/street6 */
        # street4Pot INT,                  /* pot size at sd/street7 */
        # showdownPot INT,                 /* pot size at sd/street7 */
        tmp1 = self.pot.getTotalAtStreet('FLOP')
        tmp2 = self.pot.getTotalAtStreet('TURN')
        tmp3 = self.pot.getTotalAtStreet('RIVER')
        tmp4 = 0
        tmp5 = 0
        return (tmp1,tmp2,tmp3,tmp4,tmp5)

    def join_holecards(self, player, asList=False):
        """With asList = True it returns the set cards for a player including down cards if they aren't know"""
        hcs = [u'0x', u'0x', u'0x', u'0x', u'0x', u'0x']
        holeNo = Card.games[self.gametype['category']][5][0][1]
        for street in self.holeStreets:
            if player in self.holecards[street].keys():
                if len(self.holecards[street][player][1])==1: continue
                for i in 0,1:
                    hcs[i] = self.holecards[street][player][1][i]
                    hcs[i] = upper(hcs[i][0:1])+hcs[i][1:2]
                try:
                    for i in (2,3,4,5):
                        hcs[i] = self.holecards[street][player][1][i]
                        hcs[i] = upper(hcs[i][0:1])+hcs[i][1:2]
                except IndexError:
                    hcs = hcs[0:holeNo]
                    pass

        if asList == False:
            return " ".join(hcs)
        else:
            return hcs


    def writeHTMLHand(self):
        from nevow import tags as T
        from nevow import flat
        players_who_act_preflop = (([x[0] for x in self.actions['PREFLOP']]+[x[0] for x in self.actions['BLINDSANTES']]))
        players_stacks = [x for x in self.players if x[1] in players_who_act_preflop]
        action_streets = [x for x in self.actionStreets if len(self.actions[x]) > 0]
        def render_stack(context,data):
            pat = context.tag.patternGenerator('list_item')
            for player in data:
                x = "Seat %s: %s (%s%s in chips) " %(player[0], player[1],
                self.sym, player[2])
                context.tag[ pat().fillSlots('playerStack', x)]
            return context.tag

        def render_street(context,data):
            pat = context.tag.patternGenerator('list_item')
            for street in data:
                lines = []
                if street in self.holeStreets and self.holecards[street]:
                     lines.append(
                        T.ol(class_='dealclosed', data=street,
                        render=render_deal) [
                            T.li(pattern='list_item')[ T.slot(name='deal') ]
                        ]
                    )
                if street in self.communityStreets and self.board[street]:
                    lines.append(
                        T.ol(class_='community', data=street,
                        render=render_deal_community)[
                            T.li(pattern='list_item')[ T.slot(name='deal') ]
                        ]
                    )
                if street in self.actionStreets and self.actions[street]:
                    lines.append(
                        T.ol(class_='actions', data=self.actions[street], render=render_action) [
                            T.li(pattern='list_item')[ T.slot(name='action') ]
                        ]
                    )
                if lines:
                    context.tag[ pat().fillSlots('street', [ T.h3[ street ] ]+lines)]
            return context.tag

        def render_deal(context,data):
            # data is streetname
# we can have open+closed, or just open, or just closed.

            if self.holecards[data]:
                for player in self.holecards[data]:
                    somestuff = 'dealt to %s %s' % (player, self.holecards[data][player])
                    pat = context.tag.patternGenerator('list_item')
                    context.tag[ pat().fillSlots('deal', somestuff)]
            return context.tag

        def render_deal_community(context,data):
            # data is streetname
            if self.board[data]:
                somestuff = '[' + ' '.join(self.board[data]) + ']'
                pat = context.tag.patternGenerator('list_item')
                context.tag[ pat().fillSlots('deal', somestuff)]
            return context.tag
        def render_action(context,data):
            pat = context.tag.patternGenerator('list_item')
            for act in data:
                x = self.actionString(act)
                context.tag[ pat().fillSlots('action', x)]
            return context.tag

        s = T.p[
            T.h1[
                T.span(class_='site')["%s Game #%s]" % ('PokerStars', self.handid)],
                T.span(class_='type_limit')[ "%s ($%s/$%s)" %(self.getGameTypeAsString(), self.sb, self.bb) ],
                T.span(class_='date')[ datetime.datetime.strftime(self.startTime,'%Y/%m/%d - %H:%M:%S ET') ]
            ],
            T.h2[ "Table '%s' %d-max Seat #%s is the button" %(self.tablename,
            self.maxseats, self.buttonpos)],
            T.ol(class_='stacks', data = players_stacks, render=render_stack)[
                T.li(pattern='list_item')[ T.slot(name='playerStack') ]
            ],
            T.ol(class_='streets', data = self.allStreets,
            render=render_street)[
                T.li(pattern='list_item')[ T.slot(name='street')]
            ]
        ]
        import tidy

        options = dict(input_xml=True,
                   output_xhtml=True,
                   add_xml_decl=False,
                   doctype='omit',
                   indent='auto',
                   tidy_mark=False)

        return str(tidy.parseString(flat.flatten(s), **options))


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        super(HoldemOmahaHand, self).writeHand(fh)

        players_who_act_preflop = set(([x[0] for x in self.actions['PREFLOP']]+[x[0] for x in self.actions['BLINDSANTES']]))
        log.debug(self.actions['PREFLOP'])
        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            #Only print stacks of players who do something preflop
            print >>fh, ("Seat %s: %s ($%.2f in chips) " %(player[0], player[1], float(player[2])))

        if self.actions['BLINDSANTES']:
            log.debug(self.actions['BLINDSANTES'])
            for act in self.actions['BLINDSANTES']:
                print >>fh, self.actionString(act)

        print >>fh, ("*** HOLE CARDS ***")
        for player in self.dealt:
            print >>fh, ("Dealt to %s [%s]" %(player, " ".join(self.holecards['PREFLOP'][player][1])))
        if self.hero == "":
            for player in self.shown.difference(self.dealt):
                print >>fh, ("Dealt to %s [%s]" %(player, " ".join(self.holecards['PREFLOP'][player][1])))

        if self.actions['PREFLOP']:
            for act in self.actions['PREFLOP']:
                print >>fh, self.actionString(act)

        if self.board['FLOP']:
            print >>fh, ("*** FLOP *** [%s]" %( " ".join(self.board['FLOP'])))
        if self.actions['FLOP']:
            for act in self.actions['FLOP']:
                print >>fh, self.actionString(act)

        if self.board['TURN']:
            print >>fh, ("*** TURN *** [%s] [%s]" %( " ".join(self.board['FLOP']), " ".join(self.board['TURN'])))
        if self.actions['TURN']:
            for act in self.actions['TURN']:
                print >>fh, self.actionString(act)

        if self.board['RIVER']:
            print >>fh, ("*** RIVER *** [%s] [%s]" %(" ".join(self.board['FLOP']+self.board['TURN']), " ".join(self.board['RIVER']) ))
        if self.actions['RIVER']:
            for act in self.actions['RIVER']:
                print >>fh, self.actionString(act)


        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if self.shown:
            print >>fh, ("*** SHOW DOWN ***")
            for name in self.shown:
                # TODO: legacy importer can't handle only one holecard here, make sure there are 2 for holdem, 4 for omaha
                # TOOD: If HoldHand subclass supports more than omahahi, omahahilo, holdem, add them here
                numOfHoleCardsNeeded = None
                if self.gametype['category'] in ('omahahi','omahahilo'):
                    numOfHoleCardsNeeded = 4
                elif self.gametype['category'] in ('holdem'):
                    numOfHoleCardsNeeded = 2
                if len(self.holecards['PREFLOP'][name]) == numOfHoleCardsNeeded:
                    print >>fh, ("%s shows [%s] (a hand...)" % (name, " ".join(self.holecards['PREFLOP'][name][1])))

        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, ("Uncalled bet (%s%s) returned to %s" %(self.sym, self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, ("%s collected %s%s from pot" %(entry[0], self.sym, entry[1]))

        print >>fh, ("*** SUMMARY ***")
        print >>fh, "%s | Rake %s%.2f" % (self.pot, self.sym, self.rake)

        board = []
        for street in ["FLOP", "TURN", "RIVER"]:
            board += self.board[street]
        if board:   # sometimes hand ends preflop without a board
            print >>fh, ("Board [%s]" % (" ".join(board)))

        for player in [x for x in self.players if x[1] in players_who_act_preflop]:
            seatnum = player[0]
            name = player[1]
            if name in self.collectees and name in self.shown:
                print >>fh, ("Seat %d: %s showed [%s] and won (%s%s)" % (seatnum, name, " ".join(self.holecards['PREFLOP'][name][1]), self.sym, self.collectees[name]))
            elif name in self.collectees:
                print >>fh, ("Seat %d: %s collected (%s%s)" % (seatnum, name, self.sym, self.collectees[name]))
            #~ elif name in self.shown:
                #~ print >>fh, _("Seat %d: %s showed [%s]" % (seatnum, name, " ".join(self.holecards[name]['PREFLOP'])))
            elif name in self.folded:
                print >>fh, ("Seat %d: %s folded" % (seatnum, name))
            else:
                if name in self.shown:
                    print >>fh, ("Seat %d: %s showed [%s] and lost with..." % (seatnum, name, " ".join(self.holecards['PREFLOP'][name][1])))
                elif name in self.mucked:
                    print >>fh, ("Seat %d: %s mucked [%s] " % (seatnum, name, " ".join(self.holecards['PREFLOP'][name][1])))
                else:
                    print >>fh, ("Seat %d: %s mucked" % (seatnum, name))

        print >>fh, "\n\n"

class DrawHand(Hand):
    def __init__(self, config, hhc, sitename, gametype, handText, builtFrom = "HHC", handid=None):
        self.config = config
        if gametype['base'] != 'draw':
            pass # or indeed don't pass and complain instead
        self.streetList = ['BLINDSANTES', 'DEAL', 'DRAWONE']
        self.allStreets = ['BLINDSANTES', 'DEAL', 'DRAWONE']
        self.holeStreets = ['DEAL', 'DRAWONE']
        self.actionStreets = ['BLINDSANTES', 'DEAL', 'DRAWONE']
        if gametype['category'] in ["27_3draw","badugi", "a5_3draw"]:
            self.streetList += ['DRAWTWO', 'DRAWTHREE']
            self.allStreets += ['DRAWTWO', 'DRAWTHREE']
            self.holeStreets += ['DRAWTWO', 'DRAWTHREE']
            self.actionStreets += ['DRAWTWO', 'DRAWTHREE']
        self.discardStreets = self.holeStreets
        self.communityStreets = []
        Hand.__init__(self, self.config, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        if hasattr(hhc, "in_path"):
            self.in_path = hhc.in_path
        else:
            self.in_path = "database"
        # Populate the draw hand.
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            if self.gametype['type'] == 'tour':
                self.tablename = "%s %s" % (self.tourNo, self.tablename)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)
            # markStreets in Draw may match without dealing cards
            if self.streets['DEAL'] == None:
                log.error("DrawHand.__init__: " + _("Street 'DEAL' is empty. Was hand '%s' cancelled?") % self.handid)
                raise FpdbParseError
            hhc.readBlinds(self)
            hhc.readAntes(self)
            hhc.readButton(self)
            hhc.readHeroCards(self)
            hhc.readShowdownActions(self)
            # Read actions in street order
            for street in self.streetList:
                if self.streets[street]:
                    hhc.readAction(self, street)
                    self.pot.markTotal(street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self)
            self.pot.handid = self.handid # This is only required so Pot can throw it in totalPot
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            self.sittingOut()
            hhc.readOther(self)
            
        elif builtFrom == "DB":
            # Creator expected to call hhc.select(hid) to fill out object
            print "DEBUG: DrawHand initialised for select()"
            self.maxseats = 10

    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False, string=None):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
# TODO: Probably better to find the last street with action and add the hole cards to that street
            self.addHoleCards(self.actionStreets[-1], player, open=[], closed=cards, shown=shown, mucked=mucked, dealt=dealt)
        if string is not None:
            self.showdownStrings[player] = string

    def holecardsAsSet(self, street, player):
        """Return holdcards: (oc, nc) as set()"""
        (nc,oc) = self.holecards[street][player]
        nc = set(nc)
        oc = set(oc)
        return (nc, oc)

    def getStreetTotals(self):
        # street1Pot INT,                  /* pot size at flop/street4 */
        # street2Pot INT,                  /* pot size at turn/street5 */
        # street3Pot INT,                  /* pot size at river/street6 */
        # street4Pot INT,                  /* pot size at sd/street7 */
        # showdownPot INT,                 /* pot size at sd/street7 */
        return (0,0,0,0,0)

    def join_holecards(self, player, asList=False, street=False):
        """With asList = True it returns the set cards for a player including down cards if they aren't know"""
        holecards = [u'0x']*20
        
        for i, _street in enumerate(self.holeStreets):
            if player in self.holecards[_street].keys():
                allhole = self.holecards[_street][player][1] + self.holecards[_street][player][0]
                allhole = allhole[:5]
                for c in range(len(allhole)):
                    idx = c + (i*5)
                    holecards[idx] = allhole[c]

        if street == False:
            if asList == False:
                return " ".join(holecards)
            else:
                return holecards
        if street in self.holeStreets:
            if street == 'DEAL':
                return holecards[0:5] if asList else " ".join(holecards[0:5])
            elif street == 'DRAWONE':
                return holecards[5:10] if asList else " ".join(holecards[5:10])
            elif street == 'DRAWTWO':
                return holecards[10:15] if asList else " ".join(holecards[10:15])
            elif street == 'DRAWTHREE':
                return holecards[15:20] if asList else " ".join(holecards[15:20])


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        # HH output should not be translated
        super(DrawHand, self).writeHand(fh)

        players_who_act_ondeal = set(([x[0] for x in self.actions['DEAL']]+[x[0] for x in self.actions['BLINDSANTES']]))

        for player in [x for x in self.players if x[1] in players_who_act_ondeal]:
            #Only print stacks of players who do something on deal
            print >>fh, (("Seat %s: %s (%s%s in chips) ") % (player[0], player[1], self.sym, player[2]))

        if 'BLINDSANTES' in self.actions:
            for act in self.actions['BLINDSANTES']:
                print >>fh, ("%s: %s %s %s%s" % (act[0], act[1], act[2], self.sym, act[3]))

        if 'DEAL' in self.actions:
            print >>fh, ("*** DEALING HANDS ***")
            for player in [x[1] for x in self.players if x[1] in players_who_act_ondeal]:
                if 'DEAL' in self.holecards:
                    if self.holecards['DEAL'].has_key(player):
                        (nc,oc) = self.holecards['DEAL'][player]
                        print >>fh, ("Dealt to %s: [%s]") % (player, " ".join(nc))
            for act in self.actions['DEAL']:
                print >>fh, self.actionString(act, 'DEAL')

        if 'DRAWONE' in self.actions:
            print >>fh, ("*** FIRST DRAW ***")
            for act in self.actions['DRAWONE']:
                print >>fh, self.actionString(act, 'DRAWONE')
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecardsAsSet('DRAWONE', act[0])
                    dc = self.discards['DRAWONE'][act[0]]
                    kc = oc - dc
                    print >>fh, (("Dealt to %s [%s] [%s]") % (act[0], " ".join(kc), " ".join(nc)))

        if 'DRAWTWO' in self.actions:
            print >>fh, ("*** SECOND DRAW ***")
            for act in self.actions['DRAWTWO']:
                print >>fh, self.actionString(act, 'DRAWTWO')
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecardsAsSet('DRAWONE', act[0])
                    dc = self.discards['DRAWTWO'][act[0]]
                    kc = oc - dc
                    print >>fh, (("Dealt to %s [%s] [%s]") % (act[0], " ".join(kc), " ".join(nc)))

        if 'DRAWTHREE' in self.actions:
            print >>fh, ("*** THIRD DRAW ***")
            for act in self.actions['DRAWTHREE']:
                print >>fh, self.actionString(act, 'DRAWTHREE')
                if act[0] == self.hero and act[1] == 'discards':
                    (nc,oc) = self.holecardsAsSet('DRAWONE', act[0])
                    dc = self.discards['DRAWTHREE'][act[0]]
                    kc = oc - dc
                    print >>fh, (("Dealt to %s [%s] [%s]") % (act[0], " ".join(kc), " ".join(nc)))

        if 'SHOWDOWN' in self.actions:
            print >>fh, ("*** SHOW DOWN ***")
            #TODO: Complete SHOWDOWN

        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, ("Uncalled bet (%s%s) returned to %s" % (self.sym, self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, ("%s collected %s%s from pot" % (entry[0], self.sym, entry[1]))

        print >>fh, ("*** SUMMARY ***")
        print >>fh, "%s | Rake %s%.2f" % (self.pot, self.sym, self.rake)
        print >>fh, "\n\n"



class StudHand(Hand):
    def __init__(self, config, hhc, sitename, gametype, handText, builtFrom = "HHC", handid=None):
        self.config = config
        if gametype['base'] != 'stud':
            pass # or indeed don't pass and complain instead

        self.communityStreets = []
        if gametype['category'] == '5_studhi':
            self.allStreets = ['BLINDSANTES','SECOND', 'THIRD','FOURTH','FIFTH']
            self.actionStreets = ['BLINDSANTES','SECOND','THIRD','FOURTH','FIFTH']
            self.streetList = ['BLINDSANTES','SECOND','THIRD','FOURTH','FIFTH'] # a list of the observed street names in order
            self.holeStreets = ['SECOND','THIRD','FOURTH','FIFTH']
        else:
            self.allStreets = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
            self.actionStreets = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
            self.streetList = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH'] # a list of the observed street names in order
            self.holeStreets = ['THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
        self.discardStreets = self.holeStreets
        Hand.__init__(self, self.config, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
        if hasattr(hhc, "in_path"):
            self.in_path = hhc.in_path
        else:
            self.in_path = "database"
        #Populate the StudHand
        #Generally, we call a 'read' method here, which gets the info according to the particular filter (hhc)
        # which then invokes a 'addXXX' callback
        if builtFrom == "HHC":
            hhc.readHandInfo(self)
            if self.gametype['type'] == 'tour':
                self.tablename = "%s %s" % (self.tourNo, self.tablename)
            hhc.readPlayerStacks(self)
            hhc.compilePlayerRegexs(self)
            hhc.markStreets(self)
            hhc.readAntes(self)
            hhc.readBringIn(self)
            hhc.readHeroCards(self)
            # Read actions in street order
            for street in self.actionStreets:
                if street == 'BLINDSANTES': continue # OMG--sometime someone folds in the ante round
                if self.streets[street]:
                    log.debug(street + self.streets[street])
                    hhc.readAction(self, street)
                    self.pot.markTotal(street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self) # not done yet
            self.pot.handid = self.handid # This is only required so Pot can throw it in totalPot
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            self.sittingOut()
            hhc.readOther(self)
            
        elif builtFrom == "DB":
            # Creator expected to call hhc.select(hid) to fill out object
            print "DEBUG: StudHand initialised for select()"
            self.maxseats = 10

    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False, string=None):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
            if self.gametype['category'] == '5_studhi' and len(cards)>4:
                self.addHoleCards('SECOND', player, open=[cards[1]], closed=[cards[0]], shown=shown, mucked=mucked)
                self.addHoleCards('THIRD', player, open=[cards[2]], closed=[cards[1]], shown=shown, mucked=mucked)
                self.addHoleCards('FOURTH', player, open=[cards[3]], closed=cards[1:2],  shown=shown, mucked=mucked)
                self.addHoleCards('FIFTH', player, open=[cards[4]], closed=cards[1:3], shown=shown, mucked=mucked)
            if len(cards) > 6:
                self.addHoleCards('THIRD', player, open=[cards[2]], closed=cards[0:2], shown=shown, mucked=mucked)
                self.addHoleCards('FOURTH', player, open=[cards[3]], closed=[cards[2]],  shown=shown, mucked=mucked)
                self.addHoleCards('FIFTH', player, open=[cards[4]], closed=cards[2:4], shown=shown, mucked=mucked)
                self.addHoleCards('SIXTH', player, open=[cards[5]], closed=cards[2:5], shown=shown, mucked=mucked)
                self.addHoleCards('SEVENTH', player, open=[], closed=[cards[6]], shown=shown, mucked=mucked)
        if string is not None:
            self.showdownStrings[player] = string


    def addPlayerCards(self, player,  street,  open=[],  closed=[]):
        """
        Assigns observed cards to a player.
        player  (string) name of player
        street  (string) the street name (in streetList)
        open  list of card bigrams e.g. ['2h','Jc'], dealt face up
        closed    likewise, but known only to player
        """
        log.debug("addPlayerCards %s, o%s x%s" % (player,  open, closed))
        self.checkPlayerExists(player, 'addPlayerCards')
        self.holecards[street][player] = (open, closed)

    # TODO: def addComplete(self, player, amount):
    def addComplete(self, street, player, amountTo):
        # assert street=='THIRD'
        #     This needs to be called instead of addRaiseTo, and it needs to take account of self.lastBet['THIRD'] to determine the raise-by size
        """\
        Add a complete on [street] by [player] to [amountTo]
        """
        log.debug(_("%s %s completes %s") % (street, player, amountTo))
        amountTo = amountTo.replace(u',', u'') #some sites have commas
        self.checkPlayerExists(player, 'addComplete')
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        Rt = Decimal(amountTo)
        C = Bp - Bc
        Rb = Rt - C
        self._addRaise(street, player, C, Rb, Rt, 'completes')
        #~ self.bets[street][player].append(C + Rb)
        #~ self.stacks[player] -= (C + Rb)
        #~ act = (player, 'raises', Rb, Rt, C, self.stacks[player]==0)
        #~ self.actions[street].append(act)
        #~ self.lastBet[street] = Rt # TODO check this is correct
        #~ self.pot.addMoney(player, C+Rb)

    def addBringIn(self, player, bringin):
        if player is not None:
            if self.gametype['category']=='5_studhi':
                street = 'SECOND'
            else:
                street = 'THIRD'
            log.debug(_("Bringin: %s, %s") % (player , bringin))
            bringin = bringin.replace(u',', u'') #some sites have commas
            self.checkPlayerExists(player, 'addBringIn')
            bringin = Decimal(bringin)
            self.bets[street][player].append(bringin)
            self.stacks[player] -= bringin
            act = (player, 'bringin', bringin, self.stacks[player]==0)
            self.actions[street].append(act)
            self.lastBet[street] = bringin
            self.pot.addMoney(player, bringin)

    def getStreetTotals(self):
        # street1Pot INT,                  /* pot size at flop/street4 */
        # street2Pot INT,                  /* pot size at turn/street5 */
        # street3Pot INT,                  /* pot size at river/street6 */
        # street4Pot INT,                  /* pot size at sd/street7 */
        # showdownPot INT,                 /* pot size at sd/street7 */
        return (0,0,0,0,0)


    def writeHand(self, fh=sys.__stdout__):
        # PokerStars format.
        # HH output should not be translated
        super(StudHand, self).writeHand(fh)

        players_who_post_antes = set([x[0] for x in self.actions['BLINDSANTES']])

        for player in [x for x in self.players if x[1] in players_who_post_antes]:
            #Only print stacks of players who do something preflop
            print >>fh, ("Seat %s: %s (%s%s in chips)" %(player[0], player[1], self.sym, player[2]))

        if 'BLINDSANTES' in self.actions:
            for act in self.actions['BLINDSANTES']:
                print >>fh, ("%s: posts the ante %s%s" %(act[0], self.sym, act[3]))

        if 'THIRD' in self.actions:
            dealt = 0
            #~ print >>fh, ("*** 3RD STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if self.holecards['THIRD'].has_key(player):
                    (open,  closed) = self.holecards['THIRD'][player]
                    dealt+=1
                    if dealt==1:
                        print >>fh, ("*** 3RD STREET ***")
#                    print >>fh, ("Dealt to %s:%s%s") % (player, " [" + " ".join(closed) + "] " if closed else " ", "[" + " ".join(open) + "]" if open else "")
                    print >>fh, self.writeHoleCards('THIRD', player)
            for act in self.actions['THIRD']:
                #FIXME: Need some logic here for bringin vs completes
                print >>fh, self.actionString(act)

        if 'FOURTH' in self.actions:
            dealt = 0
            #~ print >>fh, ("*** 4TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if player in self.holecards['FOURTH']:
                    dealt+=1
                    if dealt==1:
                        print >>fh, ("*** 4TH STREET ***")
                    print >>fh, self.writeHoleCards('FOURTH', player)
            for act in self.actions['FOURTH']:
                print >>fh, self.actionString(act)

        if 'FIFTH' in self.actions:
            dealt = 0
            #~ print >>fh, ("*** 5TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if self.holecards['FIFTH'].has_key(player):
                    dealt+=1
                    if dealt==1:
                        print >>fh, ("*** 5TH STREET ***")
                    print >>fh, self.writeHoleCards('FIFTH', player)
            for act in self.actions['FIFTH']:
                print >>fh, self.actionString(act)

        if 'SIXTH' in self.actions:
            dealt = 0
            #~ print >>fh, ("*** 6TH STREET ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if self.holecards['SIXTH'].has_key(player):
                    dealt += 1
                    if dealt == 1:
                        print >>fh, ("*** 6TH STREET ***")
                    print >>fh, self.writeHoleCards('SIXTH', player)
            for act in self.actions['SIXTH']:
                print >>fh, self.actionString(act)

        if 'SEVENTH' in self.actions:
            # OK. It's possible that they're all in at an earlier street, but only closed cards are dealt.
            # Then we have no 'dealt to' lines, no action lines, but still 7th street should appear.
            # The only way I can see to know whether to print this line is by knowing the state of the hand
            # i.e. are all but one players folded; is there an allin showdown; and all that.
            print >>fh, ("*** RIVER ***")
            for player in [x[1] for x in self.players if x[1] in players_who_post_antes]:
                if self.holecards['SEVENTH'].has_key(player):
                    if self.writeHoleCards('SEVENTH', player):
                        print >>fh, self.writeHoleCards('SEVENTH', player)
            for act in self.actions['SEVENTH']:
                print >>fh, self.actionString(act)

        #Some sites don't have a showdown section so we have to figure out if there should be one
        # The logic for a showdown is: at the end of river action there are at least two players in the hand
        # we probably don't need a showdown section in pseudo stars format for our filtering purposes
        if 'SHOWDOWN' in self.actions:
            print >>fh, ("*** SHOW DOWN ***")
            # TODO: print showdown lines.

        # Current PS format has the lines:
        # Uncalled bet ($111.25) returned to s0rrow
        # s0rrow collected $5.15 from side pot
        # stervels: shows [Ks Qs] (two pair, Kings and Queens)
        # stervels collected $45.35 from main pot
        # Immediately before the summary.
        # The current importer uses those lines for importing winning rather than the summary
        for name in self.pot.returned:
            print >>fh, ("Uncalled bet (%s%s) returned to %s" %(self.sym, self.pot.returned[name],name))
        for entry in self.collected:
            print >>fh, ("%s collected %s%s from pot" %(entry[0], self.sym, entry[1]))

        print >>fh, ("*** SUMMARY ***")
        print >>fh, "%s | Rake %s%.2f" % (self.pot, self.sym, self.rake)
# TODO: side pots

        board = []
        for s in self.board.values():
            board += s
        if board:   # sometimes hand ends preflop without a board
            print >>fh, ("Board [%s]" % (" ".join(board)))

        for player in [x for x in self.players if x[1] in players_who_post_antes]:
            seatnum = player[0]
            name = player[1]
            if name in self.collectees and name in self.shown:
                print >>fh, ("Seat %d: %s showed [%s] and won (%s%s)" % (seatnum, name, self.join_holecards(name), self.sym, self.collectees[name]))
            elif name in self.collectees:
                print >>fh, ("Seat %d: %s collected (%s%s)" % (seatnum, name, self.sym, self.collectees[name]))
            elif name in self.shown:
                print >>fh, ("Seat %d: %s showed [%s]" % (seatnum, name, self.join_holecards(name)))
            elif name in self.mucked:
                print >>fh, ("Seat %d: %s mucked [%s]" % (seatnum, name, self.join_holecards(name)))
            elif name in self.folded:
                print >>fh, ("Seat %d: %s folded" % (seatnum, name))
            else:
                print >>fh, ("Seat %d: %s mucked" % (seatnum, name))

        print >>fh, "\n\n"


    def writeHoleCards(self, street, player):
        hc = "Dealt to %s [" % player
        if street == 'THIRD':
            if player == self.hero:
                return hc + " ".join(self.holecards[street][player][1]) + " " + " ".join(self.holecards[street][player][0]) + ']'
            else:
                return hc + " ".join(self.holecards[street][player][0]) + ']'

        if street == 'SEVENTH' and player != self.hero: return # only write 7th st line for hero, LDO
        return hc + " ".join(self.holecards[street][player][1]) + "] [" + " ".join(self.holecards[street][player][0]) + "]"

    def join_holecards(self, player, asList=False):
        """Function returns a string for the stud writeHand method by default
           With asList = True it returns the set cards for a player including down cards if they aren't know"""
        holecards = []
        for street in self.holeStreets:
            if self.holecards[street].has_key(player):
                if ((self.gametype['category']=='5_studhi' and street == 'SECOND') or 
                    (self.gametype['category']!='5_studhi' and street == 'THIRD')):
                    holecards = holecards + self.holecards[street][player][1] + self.holecards[street][player][0]
                elif street == 'SEVENTH':
                    if player == self.hero:
                        holecards = holecards + self.holecards[street][player][0]
                    else:
                        holecards = holecards + self.holecards[street][player][1]
                else:
                    holecards = holecards + self.holecards[street][player][0]
                #print "DEBUG:", street, holecards, player, self.holecards[street][player][0], self.holecards[street][player][1]

        if asList == False:
            return " ".join(holecards)
        else:
            if self.gametype['category']=='5_studhi':
                if len(holecards) < 2:
                    holecards = [u'0x'] + holecards
                return holecards
            else:
                if player == self.hero:
                    if len(holecards) < 3:
                        holecards = [u'0x', u'0x'] + holecards
                    else:
                        return holecards
                elif len(holecards) == 7:
                    return holecards
                elif len(holecards) <= 4:
                    #Non hero folded before showdown, add first two downcards
                    holecards = [u'0x', u'0x'] + holecards
                else:
                    log.warning(_("join_holecards: # of holecards should be either < 4, 4 or 7 - 5 and 6 should be impossible for anyone who is not a hero"))
                    log.warning("join_holcards: holecards(%s): %s" % (player, holecards))
                if holecards == [u'0x', u'0x']:
                    log.warning(_("join_holecards: Player '%s' appears not to have been dealt a card") % player)
                    # If a player is listed but not dealt a card in a cash game this can occur
                    # Noticed in FTP Razz hand. Return 3 empty cards in this case
                    holecards = [u'0x', u'0x', u'0x']
                return holecards


class Pot(object):


    def __init__(self):
        self.contenders   = set()
        self.committed    = {}
        self.streettotals = {}
        self.common       = {}
        self.antes        = {}
        self.total        = None
        self.returned     = {}
        self.sym          = u'$' # this is the default currency symbol
        self.pots         = []
        self.handid       = 0

    def setSym(self, sym):
        self.sym = sym

    def addPlayer(self,player):
        self.committed[player] = Decimal(0)
        self.common[player] = Decimal(0)
        self.antes[player] = Decimal(0)
        
    def removePlayer(self,player):
        del self.committed[player]
        del self.common[player]
        del self.antes[player]

    def addFold(self, player):
        # addFold must be called when a player folds
        self.contenders.discard(player)

    def addCommonMoney(self, player, amount):
        self.common[player] += amount
        
    def addAntes(self, player, amount):
        self.antes[player] += amount

    def addMoney(self, player, amount):
        # addMoney must be called for any actions that put money in the pot, in the order they occur
        #print "DEBUG: %s adds %s" %(player, amount)
        self.contenders.add(player)
        self.committed[player] += amount

    def markTotal(self, street):
        self.streettotals[street] = sum(self.committed.values()) + sum(self.common.values())

    def getTotalAtStreet(self, street):
        if street in self.streettotals:
            return self.streettotals[street]
        return 0

    def end(self):
        self.total = sum(self.committed.values()) + sum(self.common.values())

        # Return any uncalled bet.
        if sum(self.common.values())>0 and sum(self.common.values())==sum(self.antes.values()):
            common = sorted([ (v,k) for (k,v) in self.common.items()])
            try:
                lastcommon = common[-1][0] - common[-2][0]
                if lastcommon > 0: # uncalled
                    returntocommon = common[-1][1]
                    #print "DEBUG: returning %f to %s" % (lastbet, returnto)
                    self.total -= lastcommon
                    self.common[returntocommon] -= lastcommon
            except IndexError, e:
                log.error(_("Pot.end(): '%s': Major failure while calculating pot: '%s'") % (self.handid, e))
                raise FpdbParseError
        
        committed = sorted([ (v,k) for (k,v) in self.committed.items()])
        #print "DEBUG: committed: %s" % committed
        #ERROR below. lastbet is correct in most cases, but wrong when
        #             additional money is committed to the pot in cash games
        #             due to an additional sb being posted. (Speculate that
        #             posting sb+bb is also potentially wrong)
        try:
            lastbet = committed[-1][0] - committed[-2][0]
            if lastbet > 0: # uncalled
                returnto = committed[-1][1]
                #print "DEBUG: returning %f to %s" % (lastbet, returnto)
                self.total -= lastbet
                self.committed[returnto] -= lastbet
                self.returned[returnto] = lastbet
        except IndexError, e:
            log.error(_("Pot.end(): '%s': Major failure while calculating pot: '%s'") % (self.handid, e))
            raise FpdbParseError

        # Work out side pots
        commitsall = sorted([(v,k) for (k,v) in self.committed.items() if v >0])

        try:
            while len(commitsall) > 0:
                commitslive = [(v,k) for (v,k) in commitsall if k in self.contenders]
                v1 = commitslive[0][0]
                self.pots += [(sum([min(v,v1) for (v,k) in commitsall]), set(k for (v,k) in commitsall if k in self.contenders))]
                commitsall = [((v-v1),k) for (v,k) in commitsall if v-v1 >0]
        except IndexError, e:
            log.error(_("Pot.end(): '%s': Major failure while calculating pot: '%s'") % (self.handid, e))
            raise FpdbParseError
        

        # TODO: I think rake gets taken out of the pots.
        # so it goes:
        # total pot x. main pot y, side pot z. | rake r
        # and y+z+r = x
        # for example:
        # Total pot $124.30 Main pot $98.90. Side pot $23.40. | Rake $2

    def __str__(self):
        if self.sym is None:
            self.sym = "C"
        if self.total is None:
            # NB if I'm sure end() is idempotent, call it here.
            log.error(_("Error in printing Hand object"))
            raise FpdbParseError

        ret = "Total pot %s%.2f" % (self.sym, self.total)
        if len(self.pots) < 2:
            return ret;
        ret += " Main pot %s%.2f" % (self.sym, self.pots[0][0])

        return ret + ''.join([ (" Side pot %s%.2f." % (self.sym, self.pots[x][0]) ) for x in xrange(1, len(self.pots)) ])
        
def hand_factory(hand_id, config, db_connection):
    # a factory function to discover the base type of the hand
    # and to return a populated class instance of the correct hand
    
    gameinfo = db_connection.get_gameinfo_from_hid(hand_id)

    if gameinfo['base'] == 'hold':
        hand_instance = HoldemOmahaHand(config=config, hhc=None, sitename=gameinfo['sitename'],
         gametype = gameinfo, handText=None, builtFrom = "DB", handid=hand_id)
    elif gameinfo['base'] == 'stud':
        hand_instance = StudHand(config=config, hhc=None, sitename=gameinfo['sitename'],
         gametype = gameinfo, handText=None, builtFrom = "DB", handid=hand_id)
    elif gameinfo['base'] == 'draw':
        hand_instance = DrawHand(config=config, hhc=None, sitename=gameinfo['sitename'],
         gametype = gameinfo, handText=None, builtFrom = "DB", handid=hand_id)

    hand_instance.select(db_connection, hand_id)
    hand_instance.handid_selected = hand_id #hand_instance does not supply this, create it here
    
    return hand_instance


