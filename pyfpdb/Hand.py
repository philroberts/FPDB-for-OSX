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
import pprint

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")


import Configuration
from Exceptions import *
import DerivedStats
import Card

class Hand(object):

###############################################################3
#    Class Variables
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}
    SYMBOL = {'USD': '$', 'EUR': u'$', 'GBP': '$', 'T$': '', 'play': ''}
    MS = {'horse' : 'HORSE', '8game' : '8-Game', 'hose'  : 'HOSE', 'ha': 'HA'}
    ACTION = {'ante': 1, 'small blind': 2, 'secondsb': 3, 'big blind': 4, 'both': 5, 'calls': 6, 'raises': 7,
              'bets': 8, 'stands pat': 9, 'folds': 10, 'checks': 11, 'discards': 12, 'bringin': 13, 'completes': 14}


    def __init__(self, config, sitename, gametype, handText, builtFrom = "HHC"):
        #log.debug( _("Hand.init(): handText is ") + str(handText) )
        self.config = config
        self.saveActions = self.config.get_import_parameters().get('saveActions')
        self.cacheSessions = self.config.get_import_parameters().get("cacheSessions")
        #log = Configuration.get_logger("logging.conf", "db", log_dir=self.config.dir_log)
        self.sitename = sitename
        self.siteId = self.config.get_site_id(sitename)
        self.stats = DerivedStats.DerivedStats(self)
        self.gametype = gametype
        self.startTime = 0
        self.handText = handText
        self.handid = 0
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
        self.isRebuy = False
        self.isAddOn = False
        self.isKO = False
        self.koBounty = None
        self.isMatrix = False
        self.isShootout = False
        self.added = None
        self.addedCurrency = None
        self.tourneyComment = None

        self.seating = []
        self.players = []
        self.posted = []
        self.tourneysPlayersIds = []

        # Collections indexed by street names
        self.bets = {}
        self.lastBet = {}
        self.streets = {}
        self.actions = {} # [['mct','bets','$10'],['mika','folds'],['carlg','raises','$20']]
        self.board = {} # dict from street names to community cards
        self.holecards = {}
        self.discards = {}
        for street in self.allStreets:
            self.streets[street] = "" # portions of the handText, filled by markStreets()
            self.actions[street] = []
        for street in self.actionStreets:
            self.bets[street] = {}
            self.lastBet[street] = 0
            self.board[street] = []
        for street in self.holeStreets:
            self.holecards[street] = {} # dict from player names to holecards
            self.discards[street] = {} # dict from player names to dicts by street ... of tuples ... of discarded holecards
        # Collections indexed by player names
        self.stacks = {}
        self.collected = [] #list of ?
        self.collectees = {} # dict from player names to amounts collected (?)

        # Sets of players
        self.folded = set()
        self.dealt = set()  # 'dealt to' line to be printed
        self.shown = set()  # cards were shown
        self.mucked = set() # cards were mucked at showdown

        # Things to do with money
        self.pot = Pot()
        self.totalpot = None
        self.totalcollected = None
        self.rake = None
        # currency symbol for this hand
        self.sym = self.SYMBOL[self.gametype['currency']] # save typing! delete this attr when done
        self.pot.setSym(self.sym)
        self.is_duplicate = False  # i.e. don't update hudcache if true

    def __str__(self):
        vars = ( (_("BB"), self.bb),
                 (_("SB"), self.sb),
                 (_("BUTTONPOS"), self.buttonpos),
                 (_("HAND NO."), self.handid),
                 (_("SITE"), self.sitename),
                 (_("TABLE NAME"), self.tablename),
                 (_("HERO"), self.hero),
                 (_("MAXSEATS"), self.maxseats),
                 (_("LEVEL"), self.level),
                 (_("MIXED"), self.mixed),
                 (_("LASTBET"), self.lastBet),
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
                 (_("TOURNEY COMMENT"), self.tourneyComment),
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
        """\
Assigns observed holecards to a player.
cards   list of card bigrams e.g. ['2h','Jc']
player  (string) name of player
shown   whether they were revealed at showdown
mucked  whether they were mucked at showdown
dealt   whether they were seen in a 'dealt to' line
"""
#        log.debug("addHoleCards %s %s" % (open + closed, player))
        try:
            self.checkPlayerExists(player)
        except FpdbParseError, e:
            print _("[ERROR] Tried to add holecards for unknown player: %s") % (player,)
            return

        if dealt:  self.dealt.add(player)
        if shown:  self.shown.add(player)
        if mucked: self.mucked.add(player)

        self.holecards[street][player] = [open, closed]

    def prepInsert(self, db, printtest = False):
        #####
        # Players, Gametypes, TourneyTypes are all shared functions that are needed for additional tables
        # These functions are intended for prep insert eventually
        #####
        # Players - base playerid and siteid tuple
        self.dbid_pids = db.getSqlPlayerIDs([p[1] for p in self.players], self.siteId)

        #Gametypes
        hilo = "h"
        if self.gametype['category'] in ['studhilo', 'omahahilo']:
            hilo = "s"
        elif self.gametype['category'] in ['razz','27_3draw','badugi', '27_1draw']:
            hilo = "l"

        self.gametyperow = (self.siteId, self.gametype['currency'], self.gametype['type'], self.gametype['base'],
                                    self.gametype['category'], self.gametype['limitType'], hilo,
                                    int(Decimal(self.gametype['sb'])*100), int(Decimal(self.gametype['bb'])*100),
                                    int(Decimal(self.gametype['bb'])*100), int(Decimal(self.gametype['bb'])*200))
        # Note: the above data is calculated in db.getGameTypeId
        #       Only being calculated above so we can grab the testdata
        self.dbid_gt = db.getGameTypeId(self.siteId, self.gametype, printdata = printtest)

        if self.tourNo!=None:
            self.tourneyTypeId = db.createTourneyType(self)
            db.commit()
            self.tourneyId = db.createOrUpdateTourney(self, "HHC")
            db.commit()
            self.tourneysPlayersIds = db.createOrUpdateTourneysPlayers(self, "HHC")
            db.commit()
    #end def prepInsert

    def insert(self, db, hp_data = None, ha_data = None, insert_data=False, printtest = False):
        """ Function to insert Hand into database
Should not commit, and do minimal selects. Callers may want to cache commits
db: a connected Database object"""


        self.stats.getStats(self)

        #####
        # End prep functions
        #####
        hh = self.stats.getHands()
        hp_inserts, ha_inserts = [], []

        if not db.isDuplicate(self.dbid_gt, hh['siteHandNo']):
            # Hands - Summary information of hand indexed by handId - gameinfo
            hh['gametypeId'] = self.dbid_gt
            # seats TINYINT NOT NULL,
            hh['seats'] = len(self.dbid_pids)
            
            hp = self.stats.getHandsPlayers()
            
            if self.cacheSessions:
                hh['sessionId'] = db.storeSessionsCache(self.dbid_pids, self.startTime, self.gametype, hp)            

            self.dbid_hands = db.storeHand(hh, printdata = printtest)
            
            hp_inserts = db.storeHandsPlayers(self.dbid_hands, self.dbid_pids, hp,
                                               insert=insert_data, hp_bulk = hp_data, printdata = printtest)
            
            if self.saveActions:
                ha_inserts = db.storeHandsActions(self.dbid_hands, self.dbid_pids, self.stats.getHandsActions(),
                                                   insert=insert_data, ha_bulk = ha_data, printdata = printtest)
        else:
            log.info(_("Hand.insert(): hid #: %s is a duplicate") % hh['siteHandNo'])
            self.is_duplicate = True  # i.e. don't update hudcache
            raise FpdbHandDuplicate(hh['siteHandNo'])
        
        return hp_inserts, ha_inserts

    def updateHudCache(self, db):
        db.storeHudCache(self.dbid_gt, self.dbid_pids, self.startTime, self.stats.getHandsPlayers())
        
    def updateSessionsCache(self, db):
        db.storeSessionsCache(self.dbid_pids, self.startTime, self.gametype, self.stats.getHandsPlayers())

    def select(self, db, handId):
        """ Function to create Hand object from database """
        c = db.get_cursor()
        q = """SELECT
                        hp.seatno,
                        round(hp.winnings / 100.0,2) as winnings,
                        p.name,
                        round(hp.startCash / 100.0,2) as chips,
                        hp.card1,hp.card2,hp.card3,hp.card4,
                        hp.position
                    FROM
                        HandsPlayers as hp,
                        Players as p
                    WHERE
                        hp.handId = %s
                        and p.id = hp.playerId
                    ORDER BY
                        hp.seatno
                """
        q = q.replace('%s', db.sql.query['placeholder'])

        # PlayerStacks
        c.execute(q, (handId,))
        for (seat, winnings, name, chips, card1, card2, card3, card4, position) in c.fetchall():
            #print "DEBUG: addPlayer(%s, %s, %s)" %(seat,name,str(chips))
            self.addPlayer(seat,name,str(chips))
            #print "DEBUG: card1: %s" % card1
            # map() should work, but is returning integers... FIXME later
            #cardlist = map(Card.valueSuitFromCard, [card1, card2, card3, card4])
            cardlist = [Card.valueSuitFromCard(card1), Card.valueSuitFromCard(card2), Card.valueSuitFromCard(card3), Card.valueSuitFromCard(card4)]
            #print "DEUBG: cardlist: '%s'" % cardlist
            if cardlist[0] == '':
                pass
            elif self.gametype['category'] == 'holdem':
                self.addHoleCards('PREFLOP', name, closed=cardlist[0:2], shown=False, mucked=False, dealt=True)
            elif self.gametype['category'] == 'omaha':
                self.addHoleCards('PREFLOP', name, closed=cardlist, shown=False, mucked=False, dealt=True)
            if winnings > 0:
                self.addCollectPot(name, str(winnings))
            if position == 'B':
                self.buttonpos = seat


        # HandInfo
        q = """SELECT *
                    FROM Hands
                    WHERE id = %s
            """
        q = q.replace('%s', db.sql.query['placeholder'])
        c.execute(q, (handId,))

        # NOTE: This relies on row_factory = sqlite3.Row (set in connect() params)
        #       Need to find MySQL and Postgres equivalents
        #       MySQL maybe: cursorclass=MySQLdb.cursors.DictCursor
        #res = c.fetchone()

        # Using row_factory is global, and affects the rest of fpdb. The following 2 line achieves
        # a similar result
        res = [dict(line) for line in [zip([ column[0] for column in c.description], row) for row in c.fetchall()]]
        res = res[0]

        #res['tourneyId'] #res['seats'] #res['rush']
        self.tablename = res['tableName']
        self.handid    = res['siteHandNo']
        #print "DBEUG: res['startTime']: %s" % res['startTime']
        self.startTime = datetime.datetime.strptime(res['startTime'], "%Y-%m-%d %H:%M:%S+00:00")
        self.maxseats = res['maxSeats']

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
        q = """SELECT
                      ha.actionNo,
                      p.name,
                      ha.street,
                      ha.actionId,
                      ha.allIn,
                      round(ha.amount / 100.0,2) as bet
                FROM
                      HandsActions as ha,
                      HandsPlayers as hp,
                      Players as p,
                      Hands as h
                WHERE
                          h.id = %s
                      AND ha.handId = h.id
                      AND ha.playerId = hp.playerid
                      AND hp.playerId = p.id
                      AND h.id = hp.handId
                ORDER BY
                      ha.id ASC
"""

        q = q.replace('%s', db.sql.query['placeholder'])
        c.execute(q, (handId,))
        res = [dict(line) for line in [zip([ column[0] for column in c.description], row) for row in c.fetchall()]]
        for row in res:
            name = row['name']
            street = row['street']
            act = row['actionId']
            # allin True/False if row['allIn'] == 0
            bet = row['bet']
            street = self.allStreets[int(street)+1]
            #print "DEBUG: name: '%s' street: '%s' act: '%s' bet: '%s'" %(name, street, act, bet)
            if   act == 2: # Small Blind
                self.addBlind(name, 'small blind', str(bet))
            elif act == 4: # Big Blind
                self.addBlind(name, 'big blind', str(bet))
            elif act == 6: # Call
                self.addCall(street, name, str(bet))
            elif act == 8: # Bet
                self.addBet(street, name, str(bet))
            elif act == 10: # Fold
                self.addFold(street, name)
            elif act == 11: # Check
                self.addCheck(street, name)
            elif act == 7: # Raise
                self.addRaiseBy(street, name, str(bet))
            else:
                print "DEBUG: unknown action: '%s'" % act

        self.totalPot()
        self.rake = self.totalpot - self.totalcollected
        self.writeHand()

        #hhc.readShowdownActions(self)
        #hc.readShownCards(self)


    def addPlayer(self, seat, name, chips):
        """\
Adds a player to the hand, and initialises data structures indexed by player.
seat    (int) indicating the seat
name    (string) player name
chips   (string) the chips the player has at the start of the hand (can be None)
If a player has None chips he won't be added."""
        log.debug("addPlayer: %s %s (%s)" % (seat, name, chips))
        if chips is not None:
            chips = chips.replace(u',', u'') #some sites have commas
            self.players.append([seat, name, chips])
            self.stacks[name] = Decimal(chips)
            self.pot.addPlayer(name)
            for street in self.actionStreets:
                self.bets[street][name] = []
                #self.holecards[name] = {} # dict from street names.
                #self.discards[name] = {} # dict from street names.


    def addStreets(self, match):
        # go through m and initialise actions to empty list for each street.
        if match:
            self.streets.update(match.groupdict())
            log.debug("markStreets:\n"+ str(self.streets))
        else:
            tmp = self.handText[0:100]
            log.error(_("markstreets didn't match - Assuming hand %s was cancelled") % self.handid)
            self.cancelled = True
            raise FpdbParseError(_("markStreets appeared to fail: First 100 chars: '%s'") % tmp)

    def checkPlayerExists(self,player):
        if player not in [p[1] for p in self.players]:
            print (_("DEBUG: ") + _("checkPlayerExists: %s fail on hand number %s") % (player, self.handid))
            raise FpdbParseError(_("checkPlayerExists: %s fail on hand number %s") % (player, self.handid))

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
        """\
For sites (currently only Carbon Poker) which record "all in" as a special action, which can mean either "calls and is all in" or "raises all in".
"""
        self.checkPlayerExists(player)
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
            self._addRaise(street, player, C, Rb, Ai)

    def addAnte(self, player, ante):
        log.debug("%s %s antes %s" % ('BLINDSANTES', player, ante))
        if player is not None:
            ante = ante.replace(u',', u'') #some sites have commas
            ante = Decimal(ante)
            self.bets['BLINDSANTES'][player].append(ante)
            self.stacks[player] -= ante
            act = (player, 'ante', ante, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)
#            self.pot.addMoney(player, ante)
            self.pot.addCommonMoney(player, ante)
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
            amount = amount.replace(u',', u'') #some sites have commas
            amount = Decimal(amount)
            self.stacks[player] -= amount
            act = (player, blindtype, amount, self.stacks[player]==0)
            self.actions['BLINDSANTES'].append(act)

            if blindtype == 'both':
                # work with the real amount. limit games are listed as $1, $2, where
                # the SB 0.50 and the BB is $1, after the turn the minimum bet amount is $2....
                amount = Decimal(self.bb)
                sb = Decimal(self.sb)
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)

            if blindtype == 'secondsb':
                amount = Decimal(0)
                sb = Decimal(self.sb)
                self.bets['BLINDSANTES'][player].append(sb)
                self.pot.addCommonMoney(player, sb)

            street = 'BLAH'

            if self.gametype['base'] == 'hold':
                street = 'PREFLOP'
            elif self.gametype['base'] == 'draw':
                street = 'DEAL'

            self.bets[street][player].append(amount)
            self.pot.addMoney(player, amount)
            self.lastBet[street] = amount
            self.posted = self.posted + [[player,blindtype]]



    def addCall(self, street, player=None, amount=None):
        if amount:
            amount = amount.replace(u',', u'') #some sites have commas
        log.debug(_("%s %s calls %s") %(street, player, amount))
        # Potentially calculate the amount of the call if not supplied
        # corner cases include if player would be all in
        if amount is not None:
            amount = Decimal(amount)
            self.bets[street][player].append(amount)
            #self.lastBet[street] = amount
            self.stacks[player] -= amount
            #print "DEBUG %s calls %s, stack %s" % (player, amount, self.stacks[player])
            act = (player, 'calls', amount, self.stacks[player] == 0)
            self.actions[street].append(act)
            self.pot.addMoney(player, amount)

    def addRaiseBy(self, street, player, amountBy):
        """\
Add a raise by amountBy on [street] by [player]
"""
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
        self.checkPlayerExists(player)
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
        """\
For sites which by "raises x" mean "calls and raises putting a total of x in the por". """
        self.checkPlayerExists(player)
        amount = amount.replace(u',', u'') #some sites have commas
        CRb = Decimal(amount)
        Bp = self.lastBet[street]
        Bc = sum(self.bets[street][player])
        C = Bp - Bc
        Rb = CRb - C
        Rt = Bp + Rb

        self._addRaise(street, player, C, Rb, Rt)

    def addRaiseTo(self, street, player, amountTo):
        """\
Add a raise on [street] by [player] to [amountTo]
"""
        #CG - No idea if this function has been test/verified
        self.checkPlayerExists(player)
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
        self.checkPlayerExists(player)
        self.bets[street][player].append(amount)
        self.stacks[player] -= amount
        #print "DEBUG %s bets %s, stack %s" % (player, amount, self.stacks[player])
        act = (player, 'bets', amount, self.stacks[player]==0)
        self.actions[street].append(act)
        self.lastBet[street] = amount
        self.pot.addMoney(player, amount)


    def addStandsPat(self, street, player):
        self.checkPlayerExists(player)
        act = (player, 'stands pat')
        self.actions[street].append(act)


    def addFold(self, street, player):
        log.debug(_("%s %s folds") % (street, player))
        self.checkPlayerExists(player)
        self.folded.add(player)
        self.pot.addFold(player)
        self.actions[street].append((player, 'folds'))


    def addCheck(self, street, player):
        #print "DEBUG: %s %s checked" % (street, player)
        logging.debug(_("%s %s checks") % (street, player))
        self.checkPlayerExists(player)
        self.actions[street].append((player, 'checks'))


    def addCollectPot(self,player, pot):
        log.debug("%s collected %s" % (player, pot))
        self.checkPlayerExists(player)
        self.collected = self.collected + [[player, pot]]
        if player not in self.collectees:
            self.collectees[player] = Decimal(pot)
        else:
            self.collectees[player] += Decimal(pot)


    def addShownCards(self, cards, player, holeandboard=None, shown=True, mucked=False):
        """\
For when a player shows cards for any reason (for showdown or out of choice).
Card ranks will be uppercased
"""
        log.debug(_("addShownCards %s hole=%s all=%s") % (player, cards,  holeandboard))
        if cards is not None:
            self.addHoleCards(cards,player,shown, mucked)
        elif holeandboard is not None:
            holeandboard = set([self.card(c) for c in holeandboard])
            board = set([c for s in self.board.values() for c in s])
            self.addHoleCards(holeandboard.difference(board),player,shown, mucked)

    def totalPot(self):
        """If all bets and blinds have been added, totals up the total pot size"""

        # This gives us the total amount put in the pot
        if self.totalpot is None:
            self.pot.end()
            self.totalpot = self.pot.total

        # This gives us the amount collected, i.e. after rake
        if self.totalcollected is None:
            self.totalcollected = 0;
            #self.collected looks like [[p1,amount][px,amount]]
            for entry in self.collected:
                self.totalcollected += Decimal(entry[1])

    def getGameTypeAsString(self):
        """\
Map the tuple self.gametype onto the pokerstars string describing it
"""
        # currently it appears to be something like ["ring", "hold", "nl", sb, bb]:
        gs = {"holdem"     : "Hold'em",
              "omahahi"    : "Omaha",
              "omahahilo"  : "Omaha Hi/Lo",
              "razz"       : "Razz",
              "studhi"     : "7 Card Stud",
              "studhilo"   : "7 Card Stud Hi/Lo",
              "fivedraw"   : "5 Card Draw",
              "27_1draw"   : "FIXME",
              "27_3draw"   : "Triple Draw 2-7 Lowball",
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
        elif act[1] == 'completea':
            return ("%s: completes to %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'posts':
            if(act[2] == "small blind"):
                return ("%s: posts small blind %s%s%s" %(act[0], self.sym, act[3], ' and is all-in' if act[4] else ''))
            elif(act[2] == "big blind"):
                return ("%s: posts big blind %s%s%s" %(act[0], self.sym, act[3], ' and is all-in' if act[4] else ''))
            elif(act[2] == "both"):
                return ("%s: posts small & big blinds %s%s%s" %(act[0], self.sym, act[3], ' and is all-in' if act[4] else ''))
            elif(act[2] == "ante"):
                return ("%s: posts the ante %s%s%s" %(act[0], self.sym, act[3], ' and is all-in' if act[4] else ''))
        elif act[1] == 'bringin':
            return ("%s: brings in for %s%s%s" %(act[0], self.sym, act[2], ' and is all-in' if act[3] else ''))
        elif act[1] == 'discards':
            return ("%s: discards %s %s%s" %(act[0], act[2], 'card' if act[2] == 1 else 'cards' , " [" + " ".join(self.discards[street][act[0]]) + "]" if self.hero == act[0] else ''))
        elif act[1] == 'stands pat':
            return ("%s: stands pat" %(act[0]))

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
        self.communityStreets = ['FLOP', 'TURN', 'RIVER']
        self.actionStreets = ['BLINDSANTES','PREFLOP','FLOP','TURN','RIVER']
        Hand.__init__(self, self.config, sitename, gametype, handText, builtFrom = "HHC")
        self.sb = gametype['sb']
        self.bb = gametype['bb']

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
            for street in self.communityStreets:
                if self.streets[street]:
                    hhc.readCommunityCards(self, street)
            for street in self.actionStreets:
                if self.streets[street]:
                    hhc.readAction(self, street)
                    self.pot.markTotal(street)
            hhc.readCollectPot(self)
            hhc.readShownCards(self)
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            hhc.readOther(self)
            #print "\nHand:\n"+str(self)
        elif builtFrom == "DB":
            #if handid is not None:
            #    self.select(handid) # Will need a handId
            #else:
            #    log.warning(_("HoldemOmahaHand.__init__:Can't assemble hand from db without a handid"))
            print "DEBUG: HoldemOmaha hand initialised for select()"
        else:
            log.warning(_("HoldemOmahaHand.__init__:Neither HHC nor DB+handid provided"))
            pass


    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
            if len(cards) in (2, 4):  # avoid adding board by mistake (Everleaf problem)
                self.addHoleCards('PREFLOP', player, open=[], closed=cards, shown=shown, mucked=mucked, dealt=dealt)
            elif len(cards) == 5:     # cards holds a winning hand, not hole cards
                # filter( lambda x: x not in b, a )		# calcs a - b where a and b are lists
                # so diff is set to the winning hand minus the board cards, if we're lucky that leaves the hole cards
                diff = filter( lambda x: x not in self.board['FLOP']+self.board['TURN']+self.board['RIVER'], cards )
                if len(diff) == 2 and self.gametype['category'] in ('holdem'):
                    self.addHoleCards('PREFLOP', player, open=[], closed=diff, shown=shown, mucked=mucked, dealt=dealt)

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
        hcs = [u'0x', u'0x', u'0x', u'0x']

        for street in self.holeStreets:
            if player in self.holecards[street].keys():
                hcs[0] = self.holecards[street][player][1][0]
                hcs[1] = self.holecards[street][player][1][1]
                try:
                    hcs[2] = self.holecards[street][player][1][2]
                    hcs[3] = self.holecards[street][player][1][3]
                except IndexError:
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
            print >>fh, ("%s collected %s%s from x pot" %(entry[0], self.sym, entry[1]))

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
    def __init__(self, config, hhc, sitename, gametype, handText, builtFrom = "HHC"):
        self.config = config
        if gametype['base'] != 'draw':
            pass # or indeed don't pass and complain instead
        self.streetList = ['BLINDSANTES', 'DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.allStreets = ['BLINDSANTES', 'DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.holeStreets = ['DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.actionStreets =  ['BLINDSANTES', 'DEAL', 'DRAWONE', 'DRAWTWO', 'DRAWTHREE']
        self.communityStreets = []
        Hand.__init__(self, self.config, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
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
                raise FpdbParseError(_("DrawHand.__init__: street 'DEAL' is empty. Hand cancelled? HandID: '%s'") % self.handid)
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
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            hhc.readOther(self)
        elif builtFrom == "DB":
            self.select("dummy") # Will need a handId

    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
# TODO: Probably better to find the last street with action and add the hole cards to that street
            self.addHoleCards('DRAWTHREE', player, open=[], closed=cards, shown=shown, mucked=mucked, dealt=dealt)


    def discardDrawHoleCards(self, cards, player, street):
        log.debug("discardDrawHoleCards '%s' '%s' '%s'" % (cards, player, street))
        self.discards[street][player] = set([cards])


    def addDiscard(self, street, player, num, cards):
        self.checkPlayerExists(player)
        if cards:
            act = (player, 'discards', Decimal(num), cards)
            self.discardDrawHoleCards(cards, player, street)
        else:
            act = (player, 'discards', Decimal(num))
        self.actions[street].append(act)

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

    def join_holecards(self, player, asList=False):
        """With asList = True it returns the set cards for a player including down cards if they aren't know"""
        # FIXME: This should actually return
        holecards = [u'0x', u'0x', u'0x', u'0x', u'0x']

        if asList == False:
            return " ".join(holecards)
        else:
            return holecards


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
            print >>fh, ("%s collected %s%s from x pot" % (entry[0], self.sym, entry[1]))

        print >>fh, ("*** SUMMARY ***")
        print >>fh, "%s | Rake %s%.2f" % (self.pot, self.sym, self.rake)
        print >>fh, "\n\n"



class StudHand(Hand):
    def __init__(self, config, hhc, sitename, gametype, handText, builtFrom = "HHC"):
        self.config = config
        if gametype['base'] != 'stud':
            pass # or indeed don't pass and complain instead

        self.allStreets = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
        self.communityStreets = []
        self.actionStreets = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']

        self.streetList = ['BLINDSANTES','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH'] # a list of the observed street names in order
        self.holeStreets = ['THIRD','FOURTH','FIFTH','SIXTH','SEVENTH']
        Hand.__init__(self, self.config, sitename, gametype, handText)
        self.sb = gametype['sb']
        self.bb = gametype['bb']
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
            self.totalPot() # finalise it (total the pot)
            hhc.getRake(self)
            if self.maxseats is None:
                self.maxseats = hhc.guessMaxSeats(self)
            hhc.readOther(self)
        elif builtFrom == "DB":
            self.select("dummy") # Will need a handId

    def addShownCards(self, cards, player, shown=True, mucked=False, dealt=False):
        if player == self.hero: # we have hero's cards just update shown/mucked
            if shown:  self.shown.add(player)
            if mucked: self.mucked.add(player)
        else:
            self.addHoleCards('THIRD',   player, open=[cards[2]], closed=cards[0:2], shown=shown, mucked=mucked)
            self.addHoleCards('FOURTH',  player, open=[cards[3]], closed=[cards[2]],  shown=shown, mucked=mucked)
            self.addHoleCards('FIFTH',   player, open=[cards[4]], closed=cards[2:4], shown=shown, mucked=mucked)
            self.addHoleCards('SIXTH',   player, open=[cards[5]], closed=cards[2:5], shown=shown, mucked=mucked)
            if len(cards) > 6:
                self.addHoleCards('SEVENTH', player, open=[],         closed=[cards[6]], shown=shown, mucked=mucked)


    def addPlayerCards(self, player,  street,  open=[],  closed=[]):
        """\
Assigns observed cards to a player.
player  (string) name of player
street  (string) the street name (in streetList)
open  list of card bigrams e.g. ['2h','Jc'], dealt face up
closed    likewise, but known only to player
"""
        log.debug("addPlayerCards %s, o%s x%s" % (player,  open, closed))
        try:
            self.checkPlayerExists(player)
            self.holecards[street][player] = (open, closed)
        except FpdbParseError, e:
            print _("[ERROR] Tried to add holecards for unknown player: %s") % (player,)

    # TODO: def addComplete(self, player, amount):
    def addComplete(self, street, player, amountTo):
        # assert street=='THIRD'
        #     This needs to be called instead of addRaiseTo, and it needs to take account of self.lastBet['THIRD'] to determine the raise-by size
        """\
Add a complete on [street] by [player] to [amountTo]
"""
        log.debug(_("%s %s completes %s") % (street, player, amountTo))
        amountTo = amountTo.replace(u',', u'') #some sites have commas
        self.checkPlayerExists(player)
        Bp = self.lastBet['THIRD']
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
            log.debug(_("Bringin: %s, %s") % (player , bringin))
            bringin = bringin.replace(u',', u'') #some sites have commas
            bringin = Decimal(bringin)
            self.bets['THIRD'][player].append(bringin)
            self.stacks[player] -= bringin
            act = (player, 'bringin', bringin, self.stacks[player]==0)
            self.actions['THIRD'].append(act)
            self.lastBet['THIRD'] = bringin
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
            print >>fh, ("%s collected %s%s from x pot" %(entry[0], self.sym, entry[1]))

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
                if street == 'THIRD':
                    holecards = holecards + self.holecards[street][player][1] + self.holecards[street][player][0]
                elif street == 'SEVENTH':
                    if player == self.hero:
                        holecards = holecards + self.holecards[street][player][0]
                    else:
                        holecards = holecards + self.holecards[street][player][1]
                else:
                    holecards = holecards + self.holecards[street][player][0]

        if asList == False:
            return " ".join(holecards)
        else:
            if player == self.hero or len(holecards) == 7:
                return holecards
            elif len(holecards) <= 4:
                #Non hero folded before showdown, add first two downcards
                holecards = [u'0x', u'0x'] + holecards
            else:
                log.warning(_("join_holecards: # of holecards should be either < 4, 4 or 7 - 5 and 6 should be impossible for anyone who is not a hero"))
                log.warning(_("join_holcards: holecards(%s): %s") %(player, holecards))
            if holecards == [u'0x', u'0x']:
                log.warning(_("join_holecards: Player '%s' appears not to have been dealt a card"))
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
        self.total        = None
        self.returned     = {}
        self.sym          = u'$' # this is the default currency symbol

    def setSym(self, sym):
        self.sym = sym

    def addPlayer(self,player):
        self.committed[player] = Decimal(0)
        self.common[player] = Decimal(0)

    def addFold(self, player):
        # addFold must be called when a player folds
        self.contenders.discard(player)

    def addCommonMoney(self, player, amount):
        self.common[player] += amount

    def addMoney(self, player, amount):
        # addMoney must be called for any actions that put money in the pot, in the order they occur
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
        committed = sorted([ (v,k) for (k,v) in self.committed.items()])
        #print "DEBUG: committed: %s" % committed
        #ERROR below. lastbet is correct in most cases, but wrong when
        #             additional money is committed to the pot in cash games
        #             due to an additional sb being posted. (Speculate that
        #             posting sb+bb is also potentially wrong)
        lastbet = committed[-1][0] - committed[-2][0]
        if lastbet > 0: # uncalled
            returnto = committed[-1][1]
            #print "DEBUG: returning %f to %s" % (lastbet, returnto)
            self.total -= lastbet
            self.committed[returnto] -= lastbet
            self.returned[returnto] = lastbet


        # Work out side pots
        commitsall = sorted([(v,k) for (k,v) in self.committed.items() if v >0])

        self.pots = []
        try:
            while len(commitsall) > 0:
                commitslive = [(v,k) for (v,k) in commitsall if k in self.contenders]
                v1 = commitslive[0][0]
                self.pots += [sum([min(v,v1) for (v,k) in commitsall])]
                commitsall = [((v-v1),k) for (v,k) in commitsall if v-v1 >0]
        except IndexError, e:
            log.error(_("Pot.end(): Major failure while calculating pot: '%s'") % e)
            raise FpdbParseError(_("Pot.end(): Major failure while calculating pot: '%s'") % e)

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
            print (_("DEBUG: ") + _("call Pot.end() before printing pot total"))
            # NB if I'm sure end() is idempotent, call it here.
            raise FpdbParseError(_("Error in printing Hand object"))

        ret = "Total pot %s%.2f" % (self.sym, self.total)
        if len(self.pots) < 2:
            return ret;
        ret += " Main pot %s%.2f" % (self.sym, self.pots[0])

        return ret + ''.join([ (" Side pot %s%.2f." % (self.sym, self.pots[x]) ) for x in xrange(1, len(self.pots)) ])
