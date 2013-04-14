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

import re
import sys
import traceback
from optparse import OptionParser
import os
import os.path
import xml.dom.minidom
import codecs
from decimal_wrapper import Decimal
import operator
from xml.dom.minidom import Node

import time
import datetime

from pytz import timezone
import pytz

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")


import Hand
from Exceptions import *
import Configuration

class HandHistoryConverter():

    READ_CHUNK_SIZE = 10000 # bytes to read at a time from file in tail mode

    # filetype can be "text" or "xml"
    # so far always "text"
    # subclass HHC_xml for xml parsing
    filetype = "text"

    # codepage indicates the encoding of the text file.
    # cp1252 is a safe default
    # "utf_8" is more likely if there are funny characters
    codepage = "cp1252"

    re_tzOffset = re.compile('^\w+[+-]\d{4}$')
    copyGameHeader = False
    summaryInFile  = False

    # maybe archive params should be one archive param, then call method in specific converter.   if archive:  convert_archive()
    def __init__( self, config, in_path = '-', out_path = '-', index=0
                , autostart=True, starsArchive=False, ftpArchive=False, sitename="PokerStars"):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
"""

        self.config = config
        self.import_parameters = self.config.get_import_parameters()
        self.sitename = sitename
        log.info("HandHistory init - %s site, %s subclass, in_path '%r'; out_path '%r'"
                 % (self.sitename, self.__class__, in_path, out_path) ) # should use self.filter, not self.sitename

        self.index     = index
        self.starsArchive = starsArchive
        self.ftpArchive = ftpArchive

        self.in_path = in_path
        self.out_path = out_path
        self.kodec = None

        self.processedHands = []
        self.numHands = 0
        self.numErrors = 0
        self.numPartial = 0
        self.isCarraige = False
        self.autoPop = False

        # Tourney object used to store TourneyInfo when called to deal with a Summary file
        self.tourney = None

        if in_path == '-':
            self.in_fh = sys.stdin
        self.out_fh = get_out_fh(out_path, self.import_parameters)

        self.compiledPlayers   = set()
        self.maxseats  = 0

        self.status = True

        self.parsedObjectType = "HH"      #default behaviour : parsing HH files, can be "Summary" if the parsing encounters a Summary File
        

        if autostart:
            self.start()

    def __str__(self):
        return """
HandHistoryConverter: '%(sitename)s'  
    filetype    '%(filetype)s'
    in_path     '%(in_path)s'
    out_path    '%(out_path)s'
    """ %  locals()

    def start(self):
        """Process a hand at a time from the input specified by in_path."""
        starttime = time.time()
        if not self.sanityCheck():
            log.warning(_("Failed sanity check"))
            return
        
        self.numHands = 0
        self.numPartial = 0
        self.numErrors = 0
        lastParsed = None
        handsList = self.allHandsAsList()
        log.debug( _("Hands list is:") + str(handsList))
        log.info(_("Parsing %d hands") % len(handsList))
        # Determine if we're dealing with a HH file or a Summary file
        # quick fix : empty files make the handsList[0] fail ==> If empty file, go on with HH parsing
        if len(handsList) == 0 or self.isSummary(handsList[0]) == False:
            self.parsedObjectType = "HH"
            for handText in handsList:
                try:
                    self.processedHands.append(self.processHand(handText))
                    lastParsed = 'stored'
                except FpdbHandPartial, e:
                    self.numPartial += 1
                    lastParsed = 'partial'
                    log.debug("%s" % e)
                except FpdbParseError:
                    self.numErrors += 1
                    lastParsed = 'error'
                    log.error(_("FpdbParseError for file '%s'") % self.in_path)
            if lastParsed in ('partial', 'error') and self.autoPop:
                self.index -= len(handsList[-1])
                if self.isCarraige:
                     self.index -= handsList[-1].count('\n')
                handsList.pop()
                if lastParsed=='partial':
                    self.numPartial -= 1
                else:
                    self.numErrors -= 1
                log.info(_("Removing partially written hand & resetting index"))
            self.numHands = len(handsList)
            endtime = time.time()
            log.info(_("Read %d hands (%d failed) in %.3f seconds") % (self.numHands, (self.numErrors + self.numPartial), endtime - starttime))
        else:
            self.parsedObjectType = "Summary"
            summaryParsingStatus = self.readSummaryInfo(handsList)
            endtime = time.time()
            if summaryParsingStatus :
                log.info(_("Summary file '%s' correctly parsed (took %.3f seconds)") % (self.in_path, endtime - starttime))
            else :
                log.warning(_("Error converting summary file '%s' (took %.3f seconds)") % (self.in_path, endtime - starttime))
    
    def setAutoPop(self, value):
        self.autoPop = value
                
    def progressNotify(self):
        "A callback to the interface while events are pending"
        import gtk, pygtk
        while gtk.events_pending():
            gtk.main_iteration(False)

    def allHandsAsList(self):
        """Return a list of handtexts in the file at self.in_path"""
        #TODO : any need for this to be generator? e.g. stars support can email one huge file of all hands in a year. Better to read bit by bit than all at once.
        self.readFile()
        lenobs = len(self.obs)
        self.obs = self.obs.rstrip()
        self.index -= (lenobs - len(self.obs))
        self.obs = self.obs.lstrip()
        lenobs = len(self.obs)
        self.obs = self.obs.replace('\r\n', '\n')
        if lenobs != len(self.obs):
            self.isCarraige = True
        # maybe archive params should be one archive param, then call method in specific converter?
        # if self.archive:
        #     self.obs = self.convert_archive(self.obs)
        if self.starsArchive == True:
            m = re.compile('^Hand #\d+', re.MULTILINE)
            self.obs = m.sub('', self.obs)

        if self.ftpArchive == True:
            # Remove  ******************** # 1 *************************
            m = re.compile('\*{20}\s#\s\d+\s\*{20,25}\s+', re.MULTILINE)
            self.obs = m.sub('', self.obs)
    
        if self.obs is None or self.obs == "":
            log.info(_("Read no hands from file: '%s'") % self.in_path)
            return []
        handlist = re.split(self.re_SplitHands,  self.obs)
        # Some HH formats leave dangling text after the split
        # ie. </game> (split) </session>EOL
        # Remove this dangler if less than 50 characters and warn in the log
        if len(handlist[-1]) <= 50:
            self.index -= len(handlist[-1])
            if self.isCarraige:
                self.index -= handlist[-1].count('\n')
            handlist.pop()
            log.info(_("Removing text < 50 characters & resetting index"))
        return handlist

    def processHand(self, handText):
        if self.isPartial(handText):
            raise FpdbHandPartial(_("Could not identify as a %s hand") % self.sitename)
        if self.copyGameHeader:
            gametype = self.parseHeader(handText, self.whole_file)
        else:
            gametype = self.determineGameType(handText)
        hand = None
        l = None
        if gametype is None:
            gametype = "unmatched"
            # TODO: not ideal, just trying to not error. Throw ParseException?
            self.numErrors += 1
        else:
            # See if gametype is supported.
            if 'mix' not in gametype: gametype['mix'] = 'none'
            if 'ante' not in gametype: gametype['ante'] = 0
            if 'zoom' not in gametype: gametype['zoom'] = False
            if 'cap' not in gametype: gametype['cap'] = False
            type = gametype['type']
            base = gametype['base']
            limit = gametype['limitType']
            l = [type] + [base] + [limit]

        if l in self.readSupportedGames():
            if gametype['base'] == 'hold':
                hand = Hand.HoldemOmahaHand(self.config, self, self.sitename, gametype, handText)
            elif gametype['base'] == 'stud':
                hand = Hand.StudHand(self.config, self, self.sitename, gametype, handText)
            elif gametype['base'] == 'draw':
                hand = Hand.DrawHand(self.config, self, self.sitename, gametype, handText)
        else:
            log.error(_("%s Unsupported game type: %s") % (self.sitename, gametype))
            raise FpdbParseError

        if hand:
            #hand.writeHand(self.out_fh)
            return hand
        else:
            log.error(_("%s Unsupported game type: %s") % (self.sitename, gametype))
            # TODO: pity we don't know the HID at this stage. Log the entire hand?
            
    def isPartial(self, handText):
        count = 0
        for m in self.re_Identify.finditer(handText):
            count += 1
        if count!=1:
            return True
        return False
    
    # These functions are parse actions that may be overridden by the inheriting class
    # This function should return a list of lists looking like:
    # return [["ring", "hold", "nl"], ["tour", "hold", "nl"]]
    # Showing all supported games limits and types

    def readSupportedGames(self): abstract

    # should return a list
    #   type  base limit
    # [ ring, hold, nl   , sb, bb ]
    # Valid types specified in docs/tabledesign.html in Gametypes
    def determineGameType(self, handText): abstract
    """return dict with keys/values:
    'type'       in ('ring', 'tour')
    'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl')
    'base'       in ('hold', 'stud', 'draw')
    'category'   in ('holdem', 'omahahi', omahahilo', 'razz', 'studhi', 'studhilo', 'fivedraw', '27_1draw', '27_3draw', 'badugi')
    'hilo'       in ('h','l','s')
    'mix'        in (site specific, or 'none')
    'smallBlind' int?
    'bigBlind'   int?
    'smallBet'
    'bigBet'
    'currency'  in ('USD', 'EUR', 'T$', <countrycode>)
or None if we fail to get the info """
    #TODO: which parts are optional/required?

    def readHandInfo(self, hand): abstract
    """Read and set information about the hand being dealt, and set the correct 
    variables in the Hand object 'hand

    * hand.startTime - a datetime object
    * hand.handid - The site identified for the hand - a string.
    * hand.tablename
    * hand.buttonpos
    * hand.maxseats
    * hand.mixed

    Tournament fields:

    * hand.tourNo - The site identified tournament id as appropriate - a string.
    * hand.buyin
    * hand.fee
    * hand.buyinCurrency
    * hand.koBounty
    * hand.isKO
    * hand.level
    """
    #TODO: which parts are optional/required?

    def readPlayerStacks(self, hand): abstract
    """This function is for identifying players at the table, and to pass the 
    information on to 'hand' via Hand.addPlayer(seat, name, chips)

    At the time of writing the reference function in the PS converter is:
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    Which is pretty simple because the hand history format is consistent. Other hh formats aren't so nice.

    This is the appropriate place to identify players that are sitting out and ignore them

    *** NOTE: You may find this is a more appropriate place to set hand.maxseats ***
    """

    def compilePlayerRegexs(self): abstract
    """Compile dynamic regexes -- compile player dependent regexes.

    Depending on the ambiguity of lines you may need to match, and the complexity of 
    player names - we found that we needed to recompile some regexes for player actions so that they actually contained the player names.

    eg.
    We need to match the ante line:
    <Player> antes $1.00

    But <Player> is actually named

    YesI antes $4000 - A perfectly legal playername

    Giving:

    YesI antes $4000 antes $1.00

    Which without care in your regexes most people would match 'YesI' and not 'YesI antes $4000'
    """

    # Needs to return a MatchObject with group names identifying the streets into the Hand object
    # so groups are called by street names 'PREFLOP', 'FLOP', 'STREET2' etc
    # blinds are done seperately
    def markStreets(self, hand): abstract
    """For dividing the handText into sections.

    The function requires you to pass a MatchObject with groups specifically labeled with
    the 'correct' street names.

    The Hand object will use the various matches for assigning actions to the correct streets.

    Flop Based Games:
    PREFLOP, FLOP, TURN, RIVER

    Draw Based Games:
    PREDEAL, DEAL, DRAWONE, DRAWTWO, DRAWTHREE

    Stud Based Games:
    ANTES, THIRD, FOURTH, FIFTH, SIXTH, SEVENTH

    The Stars HHC has a good reference implementation
    """

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb,
    # addtional players are assumed to post a bb oop
    def readBlinds(self, hand): abstract
    """Function for reading the various blinds from the hand history.

    Pass any small blind to hand.addBlind(<name>, "small blind", <value>)
    - unless it is a single dead small blind then use:
        hand.addBlind(<name>, 'secondsb', <value>)
    Pass any big blind to hand.addBlind(<name>, "big blind", <value>)
    Pass any play posting both big and small blinds to hand.addBlind(<name>, 'both', <vale>)
    """
    def readAntes(self, hand): abstract
    """Function for reading the antes from the hand history and passing the hand.addAnte"""
    def readBringIn(self, hand): abstract
    def readButton(self, hand): abstract
    def readHeroCards(self, hand): abstract
    def readPlayerCards(self, hand, street): abstract
    def readAction(self, hand, street): abstract
    def readCollectPot(self, hand): abstract
    def readShownCards(self, hand): abstract
    def readTourneyResults(self, hand): abstract
    """This function is for future use in parsing tourney results directly from a hand"""
    
    # EDIT: readOther is depreciated
    # Some sites do odd stuff that doesn't fall in to the normal HH parsing.
    # e.g., FTP doesn't put mixed game info in the HH, but puts in in the
    # file name. Use readOther() to clean up those messes.
    def readOther(self, hand): pass

    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand):
        hand.rake = hand.totalpot - hand.totalcollected #  * Decimal('0.05') # probably not quite right
        round = -1 if hand.gametype['type'] == "tour" else -0.01
        if hand.rake < 0 and (not hand.roundPenny or hand.rake < round):
            log.error(_("hhc.getRake(): '%s': Amount collected (%s) is greater than the pot (%s)") % (hand.handid,str(hand.totalcollected), str(hand.totalpot)))
            raise FpdbParseError
        elif hand.totalpot > 0 and Decimal(hand.totalpot/4) < hand.rake:
            log.error(_("hhc.getRake(): '%s': Suspiciously high rake (%s) > 25 pct of pot (%s)") % (hand.handid,str(hand.rake), str(hand.totalpot)))
            raise FpdbParseError

    def sanityCheck(self):
        """Check we aren't going to do some stupid things"""
        sane = False
        base_w = False

        # Make sure input and output files are different or we'll overwrite the source file
        if True: # basically.. I don't know
            sane = True

        if self.in_path != '-' and self.out_path == self.in_path:
            print(_("Output and input files are the same, check config."))
            sane = False

        return sane

    # Functions not necessary to implement in sub class
    def setFileType(self, filetype = "text", codepage='utf8'):
        self.filetype = filetype
        self.codepage = codepage

    def __listof(self, x):
        if isinstance(x, list) or isinstance(x, tuple):
            return x
        else:
            return [x]

    def readFile(self):
        """Open in_path according to self.codepage. Exceptions caught further up"""

        if self.filetype == "text":
            for kodec in self.__listof(self.codepage):
                #print "trying", kodec
                try:
                    in_fh = codecs.open(self.in_path, 'r', kodec)
                    self.whole_file = in_fh.read()
                    in_fh.close()
                    self.obs = self.whole_file[self.index:]
                    self.index = len(self.whole_file)
                    self.kodec = kodec
                    return True
                except:
                    pass
            else:
                print _("unable to read file with any codec in list!"), self.in_path
                self.obs = ""
                return False
        elif self.filetype == "xml":
            doc = xml.dom.minidom.parse(filename)
            self.doc = doc

    def guessMaxSeats(self, hand):
        """Return a guess at maxseats when not specified in HH."""
        # if some other code prior to this has already set it, return it
        if not self.copyGameHeader and hand.gametype['type']=='tour':
            return 10
            
        if self.maxseats > 1 and self.maxseats < 11:
            return self.maxseats
        
        mo = self.maxOccSeat(hand)

        if mo == 10: return 10 #that was easy

        if hand.gametype['base'] == 'stud':
            if mo <= 8: return 8

        if hand.gametype['base'] == 'draw':
            if mo <= 6: return 6
            
        return 10

    def maxOccSeat(self, hand):
        max = 0
        for player in hand.players:
            if player[0] > max:
                max = player[0]
        return max

    def getStatus(self):
        #TODO: Return a status of true if file processed ok
        return self.status

    def getProcessedHands(self):
        return self.processedHands

    def getProcessedFile(self):
        return self.out_path

    def getLastCharacterRead(self):
        return self.index

    def isSummary(self, topline):
        return " Tournament Summary " in topline

    def getParsedObjectType(self):
        return self.parsedObjectType

    #returns a status (True/False) indicating wether the parsing could be done correctly or not
    def readSummaryInfo(self, summaryInfoList): abstract

    def getTourney(self):
        return self.tourney
        
    @staticmethod
    def changeTimezone(time, givenTimezone, wantedTimezone):
        """Takes a givenTimezone in format AAA or AAA+HHMM where AAA is a standard timezone
           and +HHMM is an optional offset (+/-) in hours (HH) and minutes (MM)
           (See OnGameToFpdb.py for example use of the +HHMM part)
           Tries to convert the time parameter (with no timezone) from the givenTimezone to 
           the wantedTimeZone (currently only allows "UTC")
        """
        #log.debug("raw time: " + str(time) + " given time zone: " + str(givenTimezone))
        if wantedTimezone=="UTC":
            wantedTimezone = pytz.utc
        else:
            log.error(_("Unsupported target timezone: ") + givenTimezone)
            raise FpdbParseError(_("Unsupported target timezone: ") + givenTimezone)

        givenTZ = None
        if HandHistoryConverter.re_tzOffset.match(givenTimezone):
            offset = int(givenTimezone[-5:])
            givenTimezone = givenTimezone[0:-5]
            #log.debug("changeTimeZone: offset=") + str(offset))
        else: offset=0

        if (givenTimezone=="ET" or givenTimezone=="EST" or givenTimezone=="EDT"):
            givenTZ = timezone('US/Eastern')
        elif givenTimezone in ("CET", "CEST", "MESZ", "HAEC"):
            #since CEST will only be used in summer time it's ok to treat it as identical to CET.
            givenTZ = timezone('Europe/Berlin')
            #Note: Daylight Saving Time is standardised across the EU so this should be fine
        elif givenTimezone == 'GMT': # GMT is always the same as UTC
            givenTZ = timezone('GMT')
            # GMT cannot be treated as WET because some HH's are explicitly
            # GMT+-delta so would be incorrect during the summertime 
            # if substituted as WET+-delta
        elif givenTimezone == 'BST':
             givenTZ = timezone('Europe/London')
        elif givenTimezone == 'WET': # WET is GMT with daylight saving delta
            givenTZ = timezone('WET')
        elif givenTimezone == 'HST': # Hawaiian Standard Time
            givenTZ = timezone('US/Hawaii')
        elif givenTimezone == 'AKT': # Alaska Time
            givenTZ = timezone('US/Alaska')
        elif givenTimezone == 'PT': # Pacific Time
            givenTZ = timezone('US/Pacific')
        elif givenTimezone == 'MT': # Mountain Time
            givenTZ = timezone('US/Mountain')
        elif givenTimezone == 'CT': # Central Time
            givenTZ = timezone('US/Central')
        elif givenTimezone == 'AT': # Atlantic Time
            givenTZ = timezone('Canada/Atlantic')
        elif givenTimezone == 'NT': # Newfoundland Time
            givenTZ = timezone('Canada/Newfoundland')
        elif givenTimezone == 'ART': # Argentinian Time
            givenTZ = timezone('America/Argentina/Buenos_Aires')
        elif givenTimezone == 'BRT': # Brasilia Time
            givenTZ = timezone('America/Sao_Paulo')
        elif givenTimezone == 'COT':
            givenTZ = timezone('America/Bogota')
        elif givenTimezone in ('EET', 'EEST'): # Eastern European Time
            givenTZ = timezone('Europe/Bucharest')
        elif givenTimezone in ('MSK', 'MESZ', 'MSKS'): # Moscow Standard Time
            givenTZ = timezone('Europe/Moscow')
        elif givenTimezone in ('YEKT','YEKST'):
            givenTZ = timezone('Asia/Yekaterinburg')
        elif givenTimezone in ('KRAT','KRAST'):
            givenTZ = timezone('Asia/Krasnoyarsk')
        elif givenTimezone == 'IST': # India Standard Time
            givenTZ = timezone('Asia/Kolkata')
        elif givenTimezone == 'ICT':
            givenTZ = timezone('Asia/Bangkok')
        elif givenTimezone == 'CCT': # China Coast Time
            givenTZ = timezone('Australia/West')
        elif givenTimezone == 'JST': # Japan Standard Time
            givenTZ = timezone('Asia/Tokyo')
        elif givenTimezone == 'AWST': # Australian Western Standard Time
            givenTZ = timezone('Australia/West')
        elif givenTimezone == 'ACST': # Australian Central Standard Time
            givenTZ = timezone('Australia/Darwin')
        elif givenTimezone == 'AEST': # Australian Eastern Standard Time
            # Each State on the East Coast has different DSTs.
            # Melbournce is out because I don't like AFL, Queensland doesn't have DST
            # ACT is full of politicians and Tasmania will never notice.
            # Using Sydney. 
            givenTZ = timezone('Australia/Sydney')
        elif givenTimezone == 'NZT': # New Zealand Time
            givenTZ = timezone('Pacific/Auckland')

        if givenTZ is None:
            # do not crash if timezone not in list, just return UTC localized time
            log.error(_("Timezone conversion not supported") + ": " + givenTimezone + " " + str(time))
            givenTZ = pytz.UTC
            return givenTZ.localize(time)

        localisedTime = givenTZ.localize(time)
        utcTime = localisedTime.astimezone(wantedTimezone) + datetime.timedelta(seconds=-3600*(offset/100)-60*(offset%100))
        #log.debug("utcTime: " + str(utcTime))
        return utcTime
    #end @staticmethod def changeTimezone

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        if type=="tour":
            return ( re.escape(str(tournament)) + ".+\\Table " + re.escape(str(table_number)) )
        else:
            return re.escape(table_name)

    @staticmethod
    def getTableNoRe(tournament):
        "Returns string to search window title for tournament table no."
# Full Tilt:  $30 + $3 Tournament (181398949), Table 1 - 600/1200 Ante 100 - Limit Razz
# PokerStars: WCOOP 2nd Chance 02: $1,050 NLHE - Tournament 307521826 Table 1 - Blinds $30/$60
        return "%s.+(?:Table|Torneo) (\d+)" % (tournament, )

    @staticmethod
    def clearMoneyString(money):
        """Converts human readable string representations of numbers like
        '1 200', '2,000', '0,01' to more machine processable form - no commas, 1 decimal point
        """
        if not money:
            return money
        money = money.replace(' ', '')
        money = money.replace(u'\xa0', u'')
        if 'K' in money:
            money = money.replace('K', '000')
        if 'M' in money:
            money = money.replace('M', '000000')
        if money[-1] in ('.', ','):
            money = money[:-1]
        if len(money) < 3:
            return money # No commas until 0,01 or 1,00
        if money[-3] == ',':
            money = money[:-3] + '.' + money[-2:]
        if len(money) > 7:
            if money[-7] == '.':
                money = money[:-7] + ',' + money[-6:]
        if len(money) > 4:
            if money[-4] == '.':
                money = money[:-4] + ',' + money[-3:]

        return money.replace(',', '')

def getTableTitleRe(config, sitename, *args, **kwargs):
    "Returns string to search in windows titles for current site"
    return getSiteHhc(config, sitename).getTableTitleRe(*args, **kwargs)

def getTableNoRe(config, sitename, *args, **kwargs):
    "Returns string to search window titles for tournament table no."
    return getSiteHhc(config, sitename).getTableNoRe(*args, **kwargs)



def getSiteHhc(config, sitename):
    "Returns HHC class for current site"
    hhcName = config.hhcs[sitename].converter
    hhcModule = __import__(hhcName)
    return getattr(hhcModule, hhcName[:-6])

def get_out_fh(out_path, parameters):
    if out_path == '-':
        return(sys.stdout)
    elif parameters['saveStarsHH']:
        out_dir = os.path.dirname(out_path) 
        if not os.path.isdir(out_dir) and out_dir != '': 
            try: 
                os.makedirs(out_dir) 
            except: # we get a WindowsError here in Windows.. pretty sure something else for Linux :D 
                log.error(_("Unable to create output directory %s for HHC!") % out_dir) 
                print(_("Unable to create output directory %s for HHC!") % out_dir)
            else: 
                log.info(_("Created directory '%s'") % out_dir) 
        try: 
            return(codecs.open(out_path, 'w', 'utf8')) 
        except: 
            log.error(_("Output path %s couldn't be opened.") % (out_path)) 
    else:
        return(sys.stdout)
