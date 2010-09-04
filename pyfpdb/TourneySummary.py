#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Stephane Alessio
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

"""parses and stores summary sections from e.g. eMail or summary files"""

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

import locale
lang=locale.getdefaultlocale()[0][0:2]
if lang=="en":
    def _(string): return string
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
    except IOError:
        def _(string): return string

import pprint
import DerivedStats
import Card

log = logging.getLogger("parser")

class TourneySummary(object):

################################################################
#    Class Variables
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}     # SAL- TO KEEP ??
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}                                                  # SAL- TO KEEP ??
    SYMBOL = {'USD': '$', 'EUR': u'$', 'T$': '', 'play': ''}
    MS = {'horse' : 'HORSE', '8game' : '8-Game', 'hose'  : 'HOSE', 'ha': 'HA'}
    SITEIDS = {'Fulltilt':1, 'PokerStars':2, 'Everleaf':3, 'Win2day':4, 'OnGame':5, 'UltimateBet':6, 'Betfair':7, 'Absolute':8, 'PartyPoker':9 }


    def __init__(self, db, config, siteName, summaryText, builtFrom = "HHC"):
        self.db                 = db
        self.config             = config
        self.siteName           = siteName
        self.siteId             = self.SITEIDS[siteName]
        
        self.summaryText        = summaryText
        self.tourneyName        = None
        self.tourneyTypeId      = None
        self.tourneyId          = None
        self.startTime          = None
        self.endTime            = None
        self.tourNo             = None
        self.currency           = None
        self.buyin              = None
        self.fee                = None
        self.hero               = None
        self.maxseats           = 0
        self.entries            = 0
        self.speed              = "Normal"
        self.prizepool          = 0  # Make it a dict in order to deal (eventually later) with non-money winnings : {'MONEY' : amount, 'OTHER' : Value ??}
        self.buyInChips         = 0
        self.mixed              = None
        self.isRebuy            = False
        self.isAddOn            = False
        self.isKO               = False
        self.isMatrix           = False
        self.isShootout         = False
        self.matrixMatchId      = None  # For Matrix tourneys : 1-4 => match tables (traditionnal), 0 => Positional winnings info
        self.matrixIdProcessed  = None
        self.subTourneyBuyin    = None
        self.subTourneyFee      = None
        self.rebuyChips         = None
        self.addOnChips         = None
        self.rebuyCost          = None
        self.addOnCost          = None
        self.totalRebuyCount    = None
        self.totalAddOnCount    = None
        self.koBounty           = None
        self.tourneyComment     = None
        self.players            = []
        self.isSng              = False
        self.isSatellite        = False
        self.isDoubleOrNothing  = False
        self.guarantee          = None
        self.added              = None
        self.addedCurrency      = None
        self.gametype           = {'category':None, 'limitType':None}
        self.comment            = None
        self.commentTs          = None

        # Collections indexed by player names
        self.playerIds          = {}
        self.tourneysPlayersIds = {}
        self.ranks              = {}
        self.winnings           = {}
        self.winningsCurrency   = {}
        self.rebuyCounts        = {}
        self.addOnCounts        = {}
        self.koCounts           = {}

        # currency symbol for this summary
        self.sym = None
        
        if builtFrom=="IMAP":
            self.parseSummary()
            self.insertOrUpdate()
        elif builtFrom == "file":
            self.parseSummaryFile()
            self.insertOrUpdate()
    #end def __init__

    def __str__(self):
        #TODO : Update
        vars = ( (_("SITE"), self.siteName),
                 (_("START TIME"), self.startTime),
                 (_("END TIME"), self.endTime),
                 (_("TOURNEY NAME"), self.tourneyName),
                 (_("TOURNEY NO"), self.tourNo),
                 (_("TOURNEY TYPE ID"), self.tourneyTypeId),
                 (_("TOURNEY ID"), self.tourneyId),
                 (_("BUYIN"), self.buyin),
                 (_("FEE"), self.fee),
                 (_("CURRENCY"), self.currency),
                 (_("HERO"), self.hero),
                 (_("MAXSEATS"), self.maxseats),
                 (_("ENTRIES"), self.entries),
                 (_("SPEED"), self.speed),
                 (_("PRIZE POOL"), self.prizepool),
                 (_("STARTING CHIP COUNT"), self.buyInChips),
                 (_("MIXED"), self.mixed),
                 (_("REBUY"), self.isRebuy),
                 (_("ADDON"), self.isAddOn),
                 (_("KO"), self.isKO),
                 (_("MATRIX"), self.isMatrix),
                 (_("MATRIX ID PROCESSED"), self.matrixIdProcessed),
                 (_("SHOOTOUT"), self.isShootout),
                 (_("MATRIX MATCH ID"), self.matrixMatchId),
                 (_("SUB TOURNEY BUY IN"), self.subTourneyBuyin),
                 (_("SUB TOURNEY FEE"), self.subTourneyFee),
                 (_("REBUY CHIPS"), self.rebuyChips),
                 (_("ADDON CHIPS"), self.addOnChips),
                 (_("REBUY COST"), self.rebuyCost),
                 (_("ADDON COST"), self.addOnCost),
                 (_("TOTAL REBUYS"), self.totalRebuyCount),
                 (_("TOTAL ADDONS"), self.totalAddOnCount),
                 (_("KO BOUNTY"), self.koBounty),
                 (_("TOURNEY COMMENT"), self.tourneyComment),
                 (_("SNG"), self.isSng),
                 (_("SATELLITE"), self.isSatellite),
                 (_("DOUBLE OR NOTHING"), self.isDoubleOrNothing),
                 (_("GUARANTEE"), self.guarantee),
                 (_("ADDED"), self.added),
                 (_("ADDED CURRENCY"), self.addedCurrency),
                 (_("COMMENT"), self.comment),
                 (_("COMMENT TIMESTAMP"), self.commentTs)
        )
 
        structs = ( (_("PLAYER IDS"), self.playerIds),
                    (_("PLAYERS"), self.players),
                    (_("TOURNEYS PLAYERS IDS"), self.tourneysPlayersIds),
                    (_("RANKS"), self.ranks),                    
                    (_("WINNINGS"), self.winnings),
                    (_("WINNINGS CURRENCY"), self.winningsCurrency),
                    (_("COUNT REBUYS"), self.rebuyCounts),
                    (_("COUNT ADDONS"), self.addOnCounts),
                    (_("NB OF KO"), self.koCounts)
        )
        str = ''
        for (name, var) in vars:
            str = str + "\n%s = " % name + pprint.pformat(var)

        for (name, struct) in structs:
            str = str + "\n%s =\n" % name + pprint.pformat(struct, 4)
        return str
    #end def __str__
    
    def parseSummary(self): abstract
    """should fill the class variables with the parsed information"""

    def getSummaryText(self):
        return self.summaryText
    
    def insertOrUpdate(self):
        # First : check all needed info is filled in the object, especially for the initial select

        # Notes on DB Insert
        # Some identified issues for tourneys already in the DB (which occurs when the HH file is parsed and inserted before the Summary)
        # Be careful on updates that could make the HH import not match the tourney inserted from a previous summary import !!
        # BuyIn/Fee can be at 0/0 => match may not be easy
        # Only one existinf Tourney entry for Matrix Tourneys, but multiple Summary files
        # Starttime may not match the one in the Summary file : HH = time of the first Hand / could be slighltly different from the one in the summary file
        # Note: If the TourneyNo could be a unique id .... this would really be a relief to deal with matrix matches ==> Ask on the IRC / Ask Fulltilt ??
        
        for player in self.players:
            id=self.db.get_player_id(self.config, self.siteName, player)
            if not id:
                id=self.db.insertPlayer(unicode(player), self.siteId)
            self.playerIds.update({player:id})
        
        #print "TS.insert players",self.players,"playerIds",self.playerIds
        
        self.buyinCurrency=self.currency
        self.dbid_pids=self.playerIds #TODO:rename this field in Hand so this silly renaming can be removed
        
        #print "TS.self before starting insert",self
        self.tourneyTypeId = self.db.createTourneyType(self)
        self.db.commit()
        self.tourneyId = self.db.createOrUpdateTourney(self, "TS")
        self.db.commit()
        self.tourneysPlayersIds = self.db.createOrUpdateTourneysPlayers(self, "TS")
        self.db.commit()
        
        logging.debug(_("Tourney Insert/Update done"))
        
        # TO DO : Return what has been done (tourney created, updated, nothing)
        # ?? stored = 1 if tourney is fully created / duplicates = 1, if everything was already here and correct / partial=1 if some things were already here (between tourney, tourneysPlayers and handsPlayers)
        # if so, prototypes may need changes to know what has been done or make some kind of dict in Tourney object that could be updated during the insert process to store that information
        stored = 0
        duplicates = 0
        partial = 0
        errors = 0
        ttime = 0
        return (stored, duplicates, partial, errors, ttime)


    def addPlayer(self, rank, name, winnings, winningsCurrency, rebuyCount, addOnCount, koCount):
        """\
Adds a player to the tourney, and initialises data structures indexed by player.
rank        (int) indicating the finishing rank (can be -1 if unknown)
name        (string) player name
winnings    (decimal) the money the player ended the tourney with (can be 0, or -1 if unknown)
"""
        log.debug(_("addPlayer: rank:%s - name : '%s' - Winnings (%s)") % (rank, name, winnings))
        self.players.append(name)
        if rank:
            self.ranks.update( { name : Decimal(rank) } )
            self.winnings.update( { name : Decimal(winnings) } )
            self.winningsCurrency.update( { name : winningsCurrency } )
        else:
            self.ranks.update( { name : None } )
            self.winnings.update( { name : None } )
            self.winningsCurrency.update( { name : None } )
        if rebuyCount:
            self.rebuyCounts.update( {name: Decimal(rebuyCount) } )
        else:
            self.rebuyCounts.update( {name: None } )
        
        if addOnCount:
            self.addOnCounts.update( {name: Decimal(addOnCount) } )
        else:
            self.addOnCounts.update( {name: None } )
        
        if koCount:
            self.koCounts.update( {name : Decimal(koCount) } )
        else:
            self.koCounts.update( {name: None } )
    #end def addPlayer

    def incrementPlayerWinnings(self, name, additionnalWinnings):
        log.debug(_("incrementPlayerWinnings: name : '%s' - Add Winnings (%s)") % (name, additionnalWinnings))
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

    def writeSummary(self, fh=sys.__stdout__):
        print >>fh, "Override me"

    def printSummary(self):
        self.writeSummary(sys.stdout)


def assemble(cnxn, tourneyId): #TODO: move this method to Hand or Database
    # TODO !!
    c = cnxn.cursor()
    
    # We need at least siteName, gametype, handid
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
    h = HoldemOmahaHand(hhc = None, siteName=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
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
    h.startTime as startTime
FROM
    Hands as h
WHERE h.id = %(handid)s
""", {'handid':handid})
    res = c.fetchone()
    h.handid = res[0]
    h.tablename = res[1]
    h.startTime = res[2] # automatically a datetime
    
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

