#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2009 Stephane Alessio
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

# TODO: check to keep only the needed modules

import re
import sys
import traceback
import logging
import os
import os.path
from decimal import Decimal
import operator
import time,datetime
from copy import deepcopy
from Exceptions import *
import pprint
import DerivedStats
import Card

log = logging.getLogger("parser")

class Tourney(object):

################################################################
#    Class Variables
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}     # SAL- TO KEEP ??
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}                                                  # SAL- TO KEEP ??
    SYMBOL = {'USD': '$', 'EUR': u'$', 'T$': '', 'play': ''}
    MS = {'horse' : 'HORSE', '8game' : '8-Game', 'hose'  : 'HOSE', 'ha': 'HA'}
    SITEIDS = {'Fulltilt':1, 'PokerStars':2, 'Everleaf':3, 'Win2day':4, 'OnGame':5, 'UltimateBet':6, 'Betfair':7, 'Absolute':8, 'PartyPoker':9 }


    def __init__(self, sitename, gametype, summaryText, builtFrom = "HHC"):
        self.sitename           = sitename
        self.siteId             = self.SITEIDS[sitename]
        self.gametype           = gametype
        self.starttime          = None
        self.endtime            = None
        self.summaryText        = summaryText
        self.tourneyName        = None
        self.tourNo             = None
        self.buyin              = None
        self.fee                = None  # the Database code is looking for this one .. ?
        self.hero               = None
        self.maxseats           = None
        self.entries            = 0
        self.speed              = "Normal"
        self.prizepool          = None  # Make it a dict in order to deal (eventually later) with non-money winnings : {'MONEY' : amount, 'OTHER' : Value ??}
        self.buyInChips         = None
        self.mixed              = None
        self.isRebuy            = False
        self.isKO               = False
        self.isHU               = False
        self.isMatrix           = False
        self.isShootout         = False
        self.matrixMatchId      = None  # For Matrix tourneys : 1-4 => match tables (traditionnal), 0 => Positional winnings info
        self.subTourneyBuyin    = None
        self.subTourneyFee      = None
        self.rebuyChips         = 0
        self.addOnChips         = 0
        self.rebuyAmount        = 0
        self.addOnAmount        = 0
        self.totalRebuyCount    = 0
        self.totalAddOnCount    = 0
        self.koBounty           = 0
        self.tourneyComment     = None
        self.players            = []

        # Collections indexed by player names
        self.finishPositions    = {}
        self.winnings           = {}
        self.payinAmounts       = {}
        self.countRebuys        = {}
        self.countAddOns        = {}
        self.countKO            = {}

        # currency symbol for this summary
        self.sym = None
        #self.sym = self.SYMBOL[self.gametype['currency']] # save typing! delete this attr when done

    def __str__(self):
        #TODO : Update
        vars = ( ("SITE", self.sitename),
                 ("START TIME", self.starttime),
                 ("END TIME", self.endtime),
                 ("TOURNEY NAME", self.tourneyName),
                 ("TOURNEY NO", self.tourNo),
                 ("BUYIN", self.buyin),
                 ("FEE", self.fee),
                 ("HERO", self.hero),
                 ("MAXSEATS", self.maxseats),
                 ("ENTRIES", self.entries),
                 ("SPEED", self.speed),
                 ("PRIZE POOL", self.prizepool),
                 ("STARTING CHIP COUNT", self.buyInChips),
                 ("MIXED", self.mixed),
                 ("REBUY ADDON", self.isRebuy),
                 ("KO", self.isKO),
                 ("HU", self.isHU),
                 ("MATRIX", self.isMatrix),
                 ("SHOOTOUT", self.isShootout),
                 ("MATRIX MATCH ID", self.matrixMatchId),
                 ("SUB TOURNEY BUY IN", self.subTourneyBuyin),
                 ("SUB TOURNEY FEE", self.subTourneyFee),
                 ("REBUY CHIPS", self.rebuyChips),
                 ("ADDON CHIPS", self.addOnChips),
                 ("REBUY AMOUNT", self.rebuyAmount),
                 ("ADDON AMOUNT", self.addOnAmount),
                 ("TOTAL REBUYS", self.totalRebuyCount),
                 ("TOTAL ADDONS", self.totalAddOnCount),
                 ("KO BOUNTY", self.koBounty),
                 ("TOURNEY COMMENT", self.tourneyComment)
        )
 
        structs = ( ("GAMETYPE", self.gametype),
                    ("PLAYERS", self.players),
                    ("PAYIN AMOUNTS", self.payinAmounts),
                    ("POSITIONS", self.finishPositions),                    
                    ("WINNINGS", self.winnings),
                    ("COUNT REBUYS", self.countRebuys),
                    ("COUNT ADDONS", self.countAddOns),
                    ("NB OF KO", self.countKO)
        )
        str = ''
        for (name, var) in vars:
            str = str + "\n%s = " % name + pprint.pformat(var)

        for (name, struct) in structs:
            str = str + "\n%s =\n" % name + pprint.pformat(struct, 4)
        return str

    def getSummaryText(self):
        return self.summaryText

    def prepInsert(self, db):
        pass

    def insert(self, db):
        # First : check all needed info is filled in the object, especially for the initial select

        # Notes on DB Insert
        # Some identified issues for tourneys already in the DB (which occurs when the HH file is parsed and inserted before the Summary)
        # Be careful on updates that could make the HH import not match the tourney inserted from a previous summary import !!
        # BuyIn/Fee can be at 0/0 => match may not be easy
        # Only one existinf Tourney entry for Matrix Tourneys, but multiple Summary files
        # Starttime may not match the one in the Summary file : HH = time of the first Hand / could be slighltly different from the one in the summary file
        # Note: If the TourneyNo could be a unique id .... this would really be a relief to deal with matrix matches ==> Ask on the IRC / Ask Fulltilt ??
        
        dbTourneyTypeId = db.tRecogniseTourneyType(self)
        logging.debug("Tourney Type ID = %d" % dbTourneyTypeId)
        dbTourneyId = db.tRecognizeTourney(self, dbTourneyTypeId)
        logging.debug("Tourney ID = %d" % dbTourneyId)
        dbTourneysPlayersIds = db.tStoreTourneysPlayers(self, dbTourneyId)
        logging.debug("TourneysPlayersId = %s" % dbTourneysPlayersIds) 
        db.tUpdateTourneysHandsPlayers(self, dbTourneysPlayersIds, dbTourneyTypeId)
        logging.debug("tUpdateTourneysHandsPlayers done")
        logging.debug("Tourney Insert done")
        
        # TO DO : Return what has been done (tourney created, updated, nothing)
        # ?? stored = 1 if tourney is fully created / duplicates = 1, if everything was already here and correct / partial=1 if some things were already here (between tourney, tourneysPlayers and handsPlayers)
        # if so, prototypes may need changes to know what has been done or make some kind of dict in Tourney object that could be updated during the insert process to store that information
        stored = 0
        duplicates = 0
        partial = 0
        errors = 0
        ttime = 0
        return (stored, duplicates, partial, errors, ttime)

    
    def old_insert_from_Hand(self, db):
        """ Function to insert Hand into database
Should not commit, and do minimal selects. Callers may want to cache commits
db: a connected Database object"""
        # TODO:
        # Players - base playerid and siteid tuple
        sqlids = db.getSqlPlayerIDs([p[1] for p in self.players], self.siteId)

        #Gametypes
        gtid = db.getGameTypeId(self.siteId, self.gametype)

        # HudCache data to come from DerivedStats class
        # HandsActions - all actions for all players for all streets - self.actions
        # Hands - Summary information of hand indexed by handId - gameinfo
        #This should be moved to prepInsert
        hh = {}
        hh['siteHandNo'] =  self.handid
        hh['handStart'] = self.starttime
        hh['gameTypeId'] = gtid
        # seats TINYINT NOT NULL,
        hh['tableName'] = self.tablename
        hh['maxSeats'] = self.maxseats
        hh['seats'] = len(sqlids)
        # Flop turn and river may all be empty - add (likely) too many elements and trim with range
        boardcards = self.board['FLOP'] + self.board['TURN'] + self.board['RIVER'] + [u'0x', u'0x', u'0x', u'0x', u'0x']
        cards = [Card.encodeCard(c) for c in boardcards[0:5]]
        hh['boardcard1'] = cards[0]
        hh['boardcard2'] = cards[1]
        hh['boardcard3'] = cards[2]
        hh['boardcard4'] = cards[3]
        hh['boardcard5'] = cards[4]

             # texture smallint,
             # playersVpi SMALLINT NOT NULL,         /* num of players vpi */
                # Needs to be recorded
             # playersAtStreet1 SMALLINT NOT NULL,   /* num of players seeing flop/street4 */
                # Needs to be recorded
             # playersAtStreet2 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtStreet3 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtStreet4 SMALLINT NOT NULL,
                # Needs to be recorded
             # playersAtShowdown SMALLINT NOT NULL,
                # Needs to be recorded
             # street0Raises TINYINT NOT NULL, /* num small bets paid to see flop/street4, including blind */
                # Needs to be recorded
             # street1Raises TINYINT NOT NULL, /* num small bets paid to see turn/street5 */
                # Needs to be recorded
             # street2Raises TINYINT NOT NULL, /* num big bets paid to see river/street6 */
                # Needs to be recorded
             # street3Raises TINYINT NOT NULL, /* num big bets paid to see sd/street7 */
                # Needs to be recorded
             # street4Raises TINYINT NOT NULL, /* num big bets paid to see showdown */
                # Needs to be recorded

        #print "DEBUG: self.getStreetTotals = (%s, %s, %s, %s, %s)" %  self.getStreetTotals()
        #FIXME: Pot size still in decimal, needs to be converted to cents
        (hh['street1Pot'], hh['street2Pot'], hh['street3Pot'], hh['street4Pot'], hh['showdownPot']) = self.getStreetTotals()

             # comment TEXT,
             # commentTs DATETIME
        #print hh
        handid = db.storeHand(hh)
        # HandsPlayers - ? ... Do we fix winnings?
        # Tourneys ?
        # TourneysPlayers

        pass

    def select(self, tourneyId):
        """ Function to create Tourney object from database """
        
        

    def addPlayer(self, rank, name, winnings, payinAmount, nbRebuys, nbAddons, nbKO):
        """\
Adds a player to the tourney, and initialises data structures indexed by player.
rank        (int) indicating the finishing rank (can be -1 if unknown)
name        (string) player name
winnings    (decimal) the money the player ended the tourney with (can be 0, or -1 if unknown)
"""
        log.debug("addPlayer: rank:%s - name : '%s' - Winnings (%s)" % (rank, name, winnings))
        self.players.append(name)
        self.finishPositions.update( { name : Decimal(rank) } )
        self.winnings.update( { name : Decimal(winnings) } )
        self.payinAmounts.update( {name : Decimal(payinAmount) } )
        self.countRebuys.update( {name: Decimal(nbRebuys) } )
        self.countAddOns.update( {name: Decimal(nbAddons) } )
        self.countKO.update( {name : Decimal(nbKO) } )
        

    def incrementPlayerWinnings(self, name, additionnalWinnings):
        log.debug("incrementPlayerWinnings: name : '%s' - Add Winnings (%s)" % (name, additionnalWinnings))
        oldWins = 0
        if self.winnings.has_key(name):
            oldWins = self.winnings[name]
        else:
            self.players.append([-1, name, 0])
            
        self.winnings[name] = oldWins + Decimal(additionnalWinnings)

    def checkPlayerExists(self,player):
        if player not in [p[1] for p in self.players]:
            print "checkPlayerExists", player, "fail"
            raise FpdbParseError


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


    def writeSummary(self, fh=sys.__stdout__):
        print >>fh, "Override me"

    def printSummary(self):
        self.writeSummary(sys.stdout)


def assemble(cnxn, tourneyId):
    # TODO !!
    c = cnxn.cursor()
    
    # We need at least sitename, gametype, handid
    # for the Hand.__init__
    c.execute("""
select
    s.name,
    g.category,
    g.base,
    g.type,
    g.limitType,
    g.hilo,
    round(g.smallBlind / 100.0,2),
    round(g.bigBlind / 100.0,2),
    round(g.smallBet / 100.0,2),
    round(g.bigBet / 100.0,2),
    s.currency,
    h.boardcard1,
    h.boardcard2,
    h.boardcard3,
    h.boardcard4,
    h.boardcard5
from
    hands as h,
    sites as s,
    gametypes as g,
    handsplayers as hp,
    players as p
where
    h.id = %(handid)s
and g.id = h.gametypeid
and hp.handid = h.id
and p.id = hp.playerid
and s.id = p.siteid
limit 1""", {'handid':handid})
    #TODO: siteid should be in hands table - we took the scenic route through players here.
    res = c.fetchone()
    gametype = {'category':res[1],'base':res[2],'type':res[3],'limitType':res[4],'hilo':res[5],'sb':res[6],'bb':res[7], 'currency':res[10]}
    h = HoldemOmahaHand(hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
    cards = map(Card.valueSuitFromCard, res[11:16] )
    if cards[0]:
        h.setCommunityCards('FLOP', cards[0:3])
    if cards[3]:
        h.setCommunityCards('TURN', [cards[3]])
    if cards[4]:      
        h.setCommunityCards('RIVER', [cards[4]])
    #[Card.valueSuitFromCard(x) for x in cards]
    
    # HandInfo : HID, TABLE
    # BUTTON - why is this treated specially in Hand?
    # answer: it is written out in hand histories
    # still, I think we should record all the active seat positions in a seat_order array
    c.execute("""
SELECT
    h.sitehandno as hid,
    h.tablename as table,
    h.handstart as starttime
FROM
    hands as h
WHERE h.id = %(handid)s
""", {'handid':handid})
    res = c.fetchone()
    h.handid = res[0]
    h.tablename = res[1]
    h.starttime = res[2] # automatically a datetime
    
    # PlayerStacks
    c.execute("""
SELECT
    hp.seatno,
    round(hp.winnings / 100.0,2) as winnings,
    p.name,
    round(hp.startcash / 100.0,2) as chips,
    hp.card1,hp.card2,
    hp.position
FROM
    handsplayers as hp,
    players as p
WHERE
    hp.handid = %(handid)s
and p.id = hp.playerid
""", {'handid':handid})
    for (seat, winnings, name, chips, card1,card2, position) in c.fetchall():
        h.addPlayer(seat,name,chips)
        if card1 and card2:
            h.addHoleCards(map(Card.valueSuitFromCard, (card1,card2)), name, dealt=True)
        if winnings > 0:
            h.addCollectPot(name, winnings)
        if position == 'B':
            h.buttonpos = seat
    

    # actions
    c.execute("""
SELECT
    (ha.street,ha.actionno) as actnum,
    p.name,
    ha.street,
    ha.action,
    ha.allin,
    round(ha.amount / 100.0,2)
FROM
    handsplayers as hp,
    handsactions as ha,
    players as p
WHERE
    hp.handid = %(handid)s
and ha.handsplayerid = hp.id
and p.id = hp.playerid
ORDER BY
    ha.street,ha.actionno
""", {'handid':handid})
    res = c.fetchall()
    for (actnum,player, streetnum, act, allin, amount) in res:
        act=act.strip()
        street = h.allStreets[streetnum+1]
        if act==u'blind':
            h.addBlind(player, 'big blind', amount)
            # TODO: The type of blind is not recorded in the DB.
            # TODO: preflop street name anomalies in Hand
        elif act==u'fold':
            h.addFold(street,player)
        elif act==u'call':
            h.addCall(street,player,amount)
        elif act==u'bet':
            h.addBet(street,player,amount)
        elif act==u'check':
            h.addCheck(street,player)
        elif act==u'unbet':
            pass
        else:
            print act, player, streetnum, allin, amount
            # TODO : other actions

    #hhc.readShowdownActions(self)
    #hc.readShownCards(self)
    h.totalPot()
    h.rake = h.totalpot - h.totalcollected
    

    return h

