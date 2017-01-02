#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Stephane Alessio
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

import L10n
_ = L10n.get_translation()

# TODO: check to keep only the needed modules

import re
import sys
import logging
import os
import os.path
from decimal_wrapper import Decimal
import operator
import time, datetime
from copy import deepcopy
from Exceptions import *
import codecs

import pprint
import DerivedStats
import Card
import Database
from HandHistoryConverter import HandHistoryConverter

log = logging.getLogger("parser")

try:
    import xlrd
except:
    xlrd = None
    log.info(_("xlrd not found. Required for importing Excel tourney results files"))

class TourneySummary(object):

################################################################
#    Class Variables
    UPS = {'a':'A', 't':'T', 'j':'J', 'q':'Q', 'k':'K', 'S':'s', 'C':'c', 'H':'h', 'D':'d'}     # SAL- TO KEEP ??
    LCS = {'H':'h', 'D':'d', 'C':'c', 'S':'s'}                                                  # SAL- TO KEEP ??
    SYMBOL = {'USD': '$', 'EUR': u'$', 'T$': '', 'play': ''}
    MS = {'horse' : 'HORSE', '8game' : '8-Game', 'hose'  : 'HOSE', 'ha': 'HA'}
    SITEIDS = {'Fulltilt':1, 'Full Tilt Poker':1, 'PokerStars':2, 'Everleaf':3, 'Boss':4, 'OnGame':5,
               'UltimateBet':6, 'Betfair':7, 'Absolute':8, 'PartyPoker':9, 'PacificPoker':10,
               'Partouche':11, 'Merge':12, 'PKR':13, 'iPoker':14, 'Winamax':15, 'Everest':16,
               'Cake':17, 'Entraction':18, 'BetOnline':19, 'Microgaming':20, 'Bovada':21, 'Enet':22,
               'SealsWithClubs': 23, 'WinningPoker': 24}


    def __init__(self, db, config, siteName, summaryText, in_path='-', builtFrom="HHC", header=""):
        self.db = db
        self.config = config
        self.import_parameters = self.config.get_import_parameters()
        self.siteName = siteName
        self.siteId = None
        if siteName in self.SITEIDS:
            self.siteId = self.SITEIDS[siteName]
        self.in_path = in_path
        self.header = header
        
        self.summaryText = summaryText
        self.tourneyName = None
        self.tourneyTypeId = None
        self.tourneyId = None
        self.startTime = None
        self.endTime = None
        self.tourNo = None
        self.currency = None
        self.buyinCurrency = None
        self.buyin = 0
        self.fee = 0
        self.hero = None
        self.maxseats = 0
        self.entries = 0
        self.speed = "Normal"
        self.prizepool = 0  # Make it a dict in order to deal (eventually later) with non-money winnings : {'MONEY' : amount, 'OTHER' : Value ??}
        self.buyInChips = 0
        self.mixed = None
        self.isRebuy = False
        self.isAddOn = False
        self.isKO = False
        self.isProgressive = False
        self.isMatrix = False
        self.isShootout = False
        self.isFast = False
        self.rebuyChips = None
        self.addOnChips = None
        self.rebuyCost = 0
        self.addOnCost = 0
        self.totalRebuyCount = None
        self.totalAddOnCount = None
        self.koBounty = 0
        self.isSng = False
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
        self.gametype = {'category':None, 'limitType':None, 'mix':'none'}
        self.players = {}
        self.comment = None
        self.commentTs = None

        # Collections indexed by player names
        self.playerIds = {}
        self.tourneysPlayersIds = {}
        self.ranks = {}
        self.winnings = {}
        self.winningsCurrency = {}
        self.rebuyCounts = {}
        self.addOnCounts = {}
        self.koCounts = {}

        # currency symbol for this summary
        self.sym = None
        
        if builtFrom == "IMAP":
            # Fix line endings?
            pass
        if self.db == None:
            self.db = Database.Database(config)

        self.parseSummary()
    #end def __init__

    def __str__(self):
        #TODO : Update
        vars = ((_("SITE"), self.siteName),
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
                 (_("MAX SEATS"), self.maxseats),
                 (_("ENTRIES"), self.entries),
                 (_("SPEED"), self.speed),
                 (_("PRIZE POOL"), self.prizepool),
                 (_("STARTING CHIP COUNT"), self.buyInChips),
                 (_("MIXED"), self.mixed),
                 (_("REBUY"), self.isRebuy),
                 (_("ADDON"), self.isAddOn),
                 (_("KO"), self.isKO),
                 (_("MATRIX"), self.isMatrix),
                 (_("SHOOTOUT"), self.isShootout),
                 (_("REBUY CHIPS"), self.rebuyChips),
                 (_("ADDON CHIPS"), self.addOnChips),
                 (_("REBUY COST"), self.rebuyCost),
                 (_("ADDON COST"), self.addOnCost),
                 (_("TOTAL REBUYS"), self.totalRebuyCount),
                 (_("TOTAL ADDONS"), self.totalAddOnCount),
                 (_("KO BOUNTY"), self.koBounty),
                 (_("SNG"), self.isSng),
                 (_("SATELLITE"), self.isSatellite),
                 (_("DOUBLE OR NOTHING"), self.isDoubleOrNothing),
                 (_("GUARANTEEAMT"), self.guaranteeAmt),
                 (_("ADDED"), self.added),
                 (_("ADDED CURRENCY"), self.addedCurrency),
                 (_("COMMENT"), self.comment),
                 (_("COMMENT TIMESTAMP"), self.commentTs)
        )
 
        structs = ((_("PLAYER IDS"), self.playerIds),
                    (_("PLAYERS"), self.players),
                    (_("TOURNEYS PLAYERS IDS"), self.tourneysPlayersIds),
                    (_("RANKS"), self.ranks),
                    (_("WINNINGS"), self.winnings),
                    (_("WINNINGS CURRENCY"), self.winningsCurrency),
                    (_("COUNT REBUYS"), self.rebuyCounts),
                    (_("COUNT ADDONS"), self.addOnCounts),
                    (_("COUNT KO"), self.koCounts)
        )
        str = ''
        for (name, var) in vars:
            str = str + "\n%s = " % name + pprint.pformat(var)

        for (name, struct) in structs:
            str = str + "\n%s =\n" % name + pprint.pformat(struct, 4)
        return str
    #end def __str__

    def getSplitRe(self, head): abstract
    """Function to return a re object to split the summary text into separate tourneys, based on head of file"""
    
    def parseSummary(self): abstract
    """should fill the class variables with the parsed information"""

    def getSummaryText(self):
        return self.summaryText
    
    @staticmethod
    def clearMoneyString(money):
        "Renders 'numbers' like '1 200' and '2,000'"
        money = money.strip(u'€&euro;\u20ac$ ')
        return HandHistoryConverter.clearMoneyString(money)
    
    def insertOrUpdate(self, printtest=False):
        # First : check all needed info is filled in the object, especially for the initial select

        # Notes on DB Insert
        # Some identified issues for tourneys already in the DB (which occurs when the HH file is parsed and inserted before the Summary)
        # Be careful on updates that could make the HH import not match the tourney inserted from a previous summary import !!
        # BuyIn/Fee can be at 0/0 => match may not be easy
        # Only one existinf Tourney entry for Matrix Tourneys, but multiple Summary files
        # Starttime may not match the one in the Summary file : HH = time of the first Hand / could be slighltly different from the one in the summary file
        # Note: If the TourneyNo could be a unique id .... this would really be a relief to deal with matrix matches ==> Ask on the IRC / Ask Fulltilt ??
        self.db.set_printdata(printtest)
        
        self.playerIds = self.db.getSqlPlayerIDs(self.players.keys(), self.siteId, self.hero)
        #for player in self.players:
        #    id=self.db.get_player_id(self.config, self.siteName, player)
        #    if not id:
        #        id=self.db.insertPlayer(unicode(player), self.siteId)
        #    self.playerIds.update({player:id})
        
        #print "TS.insert players",self.players,"playerIds",self.playerIds
        self.dbid_pids = self.playerIds #TODO:rename this field in Hand so this silly renaming can be removed
        
        #print "TS.self before starting insert",self
        self.tourneyTypeId = self.db.createOrUpdateTourneyType(self)
        self.tourneyId = self.db.createOrUpdateTourney(self)
        self.db.createOrUpdateTourneysPlayers(self)
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


    def addPlayer(self, rank, name, winnings, winningsCurrency, rebuyCount, addOnCount, koCount, entryId=1):
        """\
Adds a player to the tourney, and initialises data structures indexed by player.
rank        (int) indicating the finishing rank (can be -1 if unknown)
name        (string) player name
winnings    (int) the money the player ended the tourney with (can be 0, or -1 if unknown)
"""
        log.debug("addPlayer: rank:%s - name : '%s' - Winnings (%s)" % (rank, name, winnings))
        if self.players.get(name) != None:
            if entryId in self.players[name]:
                entries = self.players[name][-1]
                self.players[name].append(entries + 1)
            else:
                self.players[name].append(entryId)
            if rank:
                self.ranks[name].append(rank)
                self.winnings[name].append(winnings)
                self.winningsCurrency[name].append(winningsCurrency)
            else:
                self.ranks[name].append(None)
                self.winnings[name].append(None)
                self.winningsCurrency[name].append(None)
            self.rebuyCounts[name].append(None)
            self.addOnCounts[name].append(None)
            self.koCounts[name].append(None)
        else:
            self.players[name] = [entryId]
            if rank:
                self.ranks.update({ name : [rank] })
                self.winnings.update({ name : [winnings] })
                self.winningsCurrency.update({ name : [winningsCurrency] })
            else:
                self.ranks.update({ name : [None] })
                self.winnings.update({ name : [None] })
                self.winningsCurrency.update({ name : [None] })                
            self.rebuyCounts.update({name: [rebuyCount] })
            self.addOnCounts.update({name: [addOnCount] })
            self.koCounts.update({name : [koCount] })
    #end def addPlayer

    def writeSummary(self, fh=sys.__stdout__):
        print >> fh, "Override me"

    def printSummary(self):
        self.writeSummary(sys.stdout)
        
    @staticmethod            
    def summaries_from_excel(filenameXLS, tourNoField):
        wb = xlrd.open_workbook(filenameXLS)
        sh = wb.sheet_by_index(0)
        summaryTexts, rows, header, keys, entries = [], [], None, None, {}
        for rownum in xrange(sh.nrows):
            if rownum==0:
                header = sh.row_values(rownum)[0]
            elif tourNoField in sh.row_values(rownum):
                keys = [unicode(c).encode('utf-8') for c in sh.row_values(rownum)]
            elif keys!=None:
                rows.append([unicode(c).encode('utf-8') for c in sh.row_values(rownum)])
        for row in rows:
            data = dict(zip(keys, row))
            data['header'] = header
            if len(data[tourNoField])>0:
                if entries.get(data[tourNoField])==None:
                    entries[data[tourNoField]] = []
                entries[data[tourNoField]].append(data)
        for k, item in entries.iteritems():
            summaryTexts.append(item)
        return summaryTexts

    @staticmethod
    def readFile(self, filename):
        whole_file = None
        for kodec in self.codepage:
            try:
                in_fh = codecs.open(filename, 'r', kodec)
                whole_file = in_fh.read()
                in_fh.close()
                break
            except UnicodeDecodeError, e:
                log.warning("TS.readFile: '%s' : '%s'" % (filename, e))
            except UnicodeError, e:
                log.warning("TS.readFile: '%s' : '%s'" % (filename, e))

        return whole_file
