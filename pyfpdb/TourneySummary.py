#!/usr/bin/python2
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

class TourneySummary(object):

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
        self.maxseats           = None
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
        self.subTourneyBuyin    = None
        self.subTourneyFee      = None
        self.rebuyChips         = 0
        self.addOnChips         = 0
        self.rebuyCost          = 0
        self.addOnCost          = 0
        self.totalRebuyCount    = 0
        self.totalAddOnCount    = 0
        self.koBounty           = 0
        self.tourneyComment     = None
        self.players            = []
        self.isSng              = False
        self.isSatellite        = False
        self.isDoubleOrNothing  = False
        self.guarantee          = 0

        # Collections indexed by player names
        self.finishPositions    = {}
        self.winnings           = {}
        self.winningsCurrency   = {}
        self.rebuyCounts        = {}
        self.addOnCounts        = {}
        self.koCounts            = {}

        # currency symbol for this summary
        self.sym = None
        #self.sym = self.SYMBOL[self.gametype['currency']] # save typing! delete this attr when done

    def __str__(self):
        #TODO : Update
        vars = ( ("SITE", self.sitename),
                 ("START TIME", self.startTime),
                 ("END TIME", self.endTime),
                 ("TOURNEY NAME", self.tourneyName),
                 ("TOURNEY NO", self.tourNo),
                 ("TOURNEY TYPE ID", self.tourneyTypeId),
                 ("TOURNEY ID", self.tourneyId),
                 ("BUYIN", self.buyin),
                 ("FEE", self.fee),
                 ("HERO", self.hero),
                 ("MAXSEATS", self.maxseats),
                 ("ENTRIES", self.entries),
                 ("SPEED", self.speed),
                 ("PRIZE POOL", self.prizepool),
                 ("STARTING CHIP COUNT", self.buyInChips),
                 ("MIXED", self.mixed),
                 ("REBUY", self.isRebuy),
                 ("ADDON", self.isAddOn),
                 ("KO", self.isKO),
                 ("MATRIX", self.isMatrix),
                 ("SHOOTOUT", self.isShootout),
                 ("MATRIX MATCH ID", self.matrixMatchId),
                 ("SUB TOURNEY BUY IN", self.subTourneyBuyin),
                 ("SUB TOURNEY FEE", self.subTourneyFee),
                 ("REBUY CHIPS", self.rebuyChips),
                 ("ADDON CHIPS", self.addOnChips),
                 ("REBUY COST", self.rebuyCost),
                 ("ADDON COST", self.addOnCost),
                 ("TOTAL REBUYS", self.totalRebuyCount),
                 ("TOTAL ADDONS", self.totalAddOnCount),
                 ("KO BOUNTY", self.koBounty),
                 ("TOURNEY COMMENT", self.tourneyComment),
                 ("SNG", self.isSng),
                 ("SATELLITE", self.isSatellite),
                 ("DOUBLE OR NOTHING", self.isDoubleOrNothing),
                 ("GUARANTEE", self.guarantee)
        )
 
        structs = ( ("GAMETYPE", self.gametype),
                    ("PLAYERS", self.players),
                    ("POSITIONS", self.finishPositions),                    
                    ("WINNINGS", self.winnings),
                    ("COUNT REBUYS", self.rebuyCounts),
                    ("COUNT ADDONS", self.addOnCounts),
                    ("NB OF KO", self.koCounts)
        )
        str = ''
        for (name, var) in vars:
            str = str + "\n%s = " % name + pprint.pformat(var)

        for (name, struct) in structs:
            str = str + "\n%s =\n" % name + pprint.pformat(struct, 4)
        return str

    def getSummaryText(self):
        return self.summaryText
    
    def insert(self, db):
        # Note that this method is not used by the PS tourney storage stuff - this is for summary files only
        
        # First : check all needed info is filled in the object, especially for the initial select

        # Notes on DB Insert
        # Some identified issues for tourneys already in the DB (which occurs when the HH file is parsed and inserted before the Summary)
        # Be careful on updates that could make the HH import not match the tourney inserted from a previous summary import !!
        # BuyIn/Fee can be at 0/0 => match may not be easy
        # Only one existinf Tourney entry for Matrix Tourneys, but multiple Summary files
        # Starttime may not match the one in the Summary file : HH = time of the first Hand / could be slighltly different from the one in the summary file
        # Note: If the TourneyNo could be a unique id .... this would really be a relief to deal with matrix matches ==> Ask on the IRC / Ask Fulltilt ??
        
        dbTourneyTypeId = db.getTourneyTypeId(self)
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


    def addPlayer(self, rank, name, winnings, winningsCurrency, rebuyCount, addOnCount, koCount):
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
        self.winningsCurrency.update( { name : winningsCurrency } )
        self.rebuyCounts.update( {name: Decimal(rebuyCount) } )
        self.addOnCounts.update( {name: Decimal(addOnCount) } )
        self.koCounts.update( {name : Decimal(koCount) } )
        

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
    #end def printSummary
#end class TourneySummary