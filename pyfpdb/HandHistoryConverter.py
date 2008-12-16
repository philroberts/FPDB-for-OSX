#!/usr/bin/python

#Copyright 2008 Carl Gherardi
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

import Configuration
import FpdbRegex
import Hand
import re
import sys
import traceback
import os
import os.path
import xml.dom.minidom
import codecs
from decimal import Decimal
import operator
from xml.dom.minidom import Node
from pokereval import PokerEval
from time import time
import gettext

#from pokerengine.pokercards import *
# provides letter2name{}, letter2names{}, visible_card(), not_visible_card(), is_visible(), card_value(), class PokerCards
# but it's probably not installed so here are the ones we may want:
letter2name = {
    'A': 'Ace',
    'K': 'King',
    'Q': 'Queen',
    'J': 'Jack',
    'T': 'Ten',
    '9': 'Nine',
    '8': 'Eight',
    '7': 'Seven',
    '6': 'Six',
    '5': 'Five',
    '4': 'Four',
    '3': 'Trey',
    '2': 'Deuce'
    }

letter2names = {
    'A': 'Aces',
    'K': 'Kings',
    'Q': 'Queens',
    'J': 'Jacks',
    'T': 'Tens',
    '9': 'Nines',
    '8': 'Eights',
    '7': 'Sevens',
    '6': 'Sixes',
    '5': 'Fives',
    '4': 'Fours',
    '3': 'Treys',
    '2': 'Deuces'
    }

import gettext
gettext.install('myapplication')



class HandHistoryConverter:
    eval = PokerEval()
    def __init__(self, config, file, sitename):
        print "HandHistory init called"
        self.c         = config
        self.sitename  = sitename
        self.obs       = ""             # One big string
        self.filetype  = "text"
        self.codepage  = "utf8"
        self.doc       = None     # For XML based HH files
        self.file      = file
        self.hhbase    = self.c.get_import_parameters().get("hhArchiveBase")
        self.hhbase    = os.path.expanduser(self.hhbase)
        self.hhdir     = os.path.join(self.hhbase,sitename)
        self.gametype  = []
#		self.ofile     = os.path.join(self.hhdir,file)
        self.rexx      = FpdbRegex.FpdbRegex()

    def __str__(self):
        tmp = "HandHistoryConverter: '%s'\n" % (self.sitename)
        tmp = tmp + "\thhbase:     '%s'\n" % (self.hhbase)
        tmp = tmp + "\thhdir:      '%s'\n" % (self.hhdir)
        tmp = tmp + "\tfiletype:   '%s'\n" % (self.filetype)
        tmp = tmp + "\tinfile:     '%s'\n" % (self.file)
#		tmp = tmp + "\toutfile:    '%s'\n" % (self.ofile)
#		tmp = tmp + "\tgametype:   '%s'\n" % (self.gametype[0])
#		tmp = tmp + "\tgamebase:   '%s'\n" % (self.gametype[1])
#		tmp = tmp + "\tlimit:      '%s'\n" % (self.gametype[2])
#		tmp = tmp + "\tsb/bb:      '%s/%s'\n" % (self.gametype[3], self.gametype[4])
        return tmp

    def processFile(self):
        starttime = time()
        if not self.sanityCheck():
            print "Cowardly refusing to continue after failed sanity check"
            return
        self.readFile(self.file)
        self.gametype = self.determineGameType()
        self.hands = self.splitFileIntoHands()
        for hand in self.hands:
            print "\nInput:\n"+hand.string
            self.readHandInfo(hand)
            self.readPlayerStacks(hand)
            self.markStreets(hand)
            self.readBlinds(hand)
            self.readHeroCards(hand) # want to generalise to draw games
            self.readCommunityCards(hand) # read community cards
            self.readShowdownActions(hand)
            # Read action (Note: no guarantee this is in hand order.
            for street in hand.streets.groupdict():
                if hand.streets.group(street) is not None:
                    self.readAction(hand, street)

            self.readCollectPot(hand)

            # finalise it (total the pot)
            hand.totalPot()
            self.getRake(hand)

            hand.writeHand(sys.stderr)
            #if(hand.involved == True):
                #self.writeHand("output file", hand)
                #hand.printHand()
            #else:
                #pass #Don't write out observed hands

        endtime = time()
        print "Processed %d hands in %d seconds" % (len(self.hands), endtime-starttime)

    #####
    # These functions are parse actions that may be overridden by the inheriting class
    #
    
    def readSupportedGames(self): abstract

    # should return a list
    #   type  base limit
    # [ ring, hold, nl   , sb, bb ]
    # Valid types specified in docs/tabledesign.html in Gametypes
    def determineGameType(self): abstract

    # Read any of:
    # HID		HandID
    # TABLE		Table name
    # SB 		small blind
    # BB		big blind
    # GAMETYPE	gametype
    # YEAR MON DAY HR MIN SEC 	datetime
    # BUTTON	button seat number
    def readHandInfo(self, hand): abstract

    # Needs to return a list of lists in the format
    # [['seat#', 'player1name', 'stacksize'] ['seat#', 'player2name', 'stacksize'] [...]]
    def readPlayerStacks(self, hand): abstract

    # Needs to return a MatchObject with group names identifying the streets into the Hand object
    # so groups are called by street names 'PREFLOP', 'FLOP', 'STREET2' etc
    # blinds are done seperately
    def markStreets(self, hand): abstract

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb, 
    # addtional players are assumed to post a bb oop
    def readBlinds(self, hand): abstract
    def readHeroCards(self, hand): abstract
    def readAction(self, hand, street): abstract
    def readCollectPot(self, hand): abstract
    
    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand):
        hand.rake = hand.totalpot - hand.totalcollected #  * Decimal('0.05') # probably not quite right
    
    
    def sanityCheck(self):
        sane = False
        base_w = False
        #Check if hhbase exists and is writable
        #Note: Will not try to create the base HH directory
        if not (os.access(self.hhbase, os.W_OK) and os.path.isdir(self.hhbase)):
            print "HH Sanity Check: Directory hhbase '" + self.hhbase + "' doesn't exist or is not writable"
        else:
            #Check if hhdir exists and is writable
            if not os.path.isdir(self.hhdir):
                # In first pass, dir may not exist. Attempt to create dir
                print "Creating directory: '%s'" % (self.hhdir)
                os.mkdir(self.hhdir)
                sane = True
            elif os.access(self.hhdir, os.W_OK):
                sane = True
            else:
                print "HH Sanity Check: Directory hhdir '" + self.hhdir + "' or its parent directory are not writable"

        return sane

    # Functions not necessary to implement in sub class
    def setFileType(self, filetype = "text", codepage='utf8'):
        self.filetype = filetype
        self.codepage = codepage

    def splitFileIntoHands(self):
        hands = []
        self.obs.strip()
        list = self.rexx.split_hand_re.split(self.obs)
        list.pop() #Last entry is empty
        for l in list:
#			print "'" + l + "'"
            hands = hands + [Hand.Hand(self.sitename, self.gametype, l)]
        return hands

    def readFile(self, filename):
        """Read file"""
        print "Reading file: '%s'" %(filename)
        if(self.filetype == "text"):
            infile=codecs.open(filename, "rU", self.codepage)
            self.obs = infile.read()
            infile.close()
        elif(self.filetype == "xml"):
            try:
                doc = xml.dom.minidom.parse(filename)
                self.doc = doc
            except:
                traceback.print_exc(file=sys.stderr)


#takes a poker float (including , for thousand seperator and converts it to an int
    def float2int (self, string):
        pos=string.find(",")
        if (pos!=-1): #remove , the thousand seperator
            string=string[0:pos]+string[pos+1:]

        pos=string.find(".")
        if (pos!=-1): #remove decimal point
            string=string[0:pos]+string[pos+1:]

        result = int(string)
        if pos==-1: #no decimal point - was in full dollars - need to multiply with 100
            result*=100
        return result
#end def float2int
