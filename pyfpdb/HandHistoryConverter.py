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

try:
    from pytz import timezone
    import pytz
except ImportError:
    print _("ImportError: Unable to import PYTZ library.  Please install PYTZ from http://pypi.python.org/pypi/pytz/")
    raw_input(_("Press ENTER to continue."))
    exit()   

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")


import Hand
from Exceptions import FpdbParseError
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

    # maybe archive params should be one archive param, then call method in specific converter.   if archive:  convert_archive()
    def __init__( self, config, in_path = '-', out_path = '-', follow=False, index=0
                , autostart=True, starsArchive=False, ftpArchive=False, sitename="PokerStars" ):
        """\
in_path   (default '-' = sys.stdin)
out_path  (default '-' = sys.stdout)
follow :  whether to tail -f the input"""

        self.config = config
        self.import_parameters = self.config.get_import_parameters()
        self.sitename = sitename
        #log = Configuration.get_logger("logging.conf", "parser", log_dir=self.config.dir_log)
        log.info("HandHistory init - %s site, %s subclass, in_path '%s'; out_path '%s'" 
                 % (self.sitename, self.__class__, in_path, out_path) ) # should use self.filter, not self.sitename

        self.index     = index
        self.starsArchive = starsArchive
        self.ftpArchive = ftpArchive

        self.in_path = in_path
        self.out_path = out_path

        self.processedHands = []
        self.numHands = 0
        self.numErrors = 0

        # Tourney object used to store TourneyInfo when called to deal with a Summary file
        self.tourney = None

        if in_path == '-':
            self.in_fh = sys.stdin
        self.out_fh = get_out_fh(out_path, self.import_parameters)

        self.follow = follow
        self.compiledPlayers   = set()
        self.maxseats  = 10

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
    follow      '%(follow)s'
    """ %  locals()

    def start(self):
        """Process a hand at a time from the input specified by in_path.
If in follow mode, wait for more data to turn up.
Otherwise, finish at EOF.

"""
        starttime = time.time()
        if not self.sanityCheck():
            log.warning(_("Failed sanity check"))
            return

        try:
            self.numHands = 0
            self.numErrors = 0
            if self.follow:
                #TODO: See how summary files can be handled on the fly (here they should be rejected as before)
                log.info(_("Tailing '%s'") % self.in_path)
                for handText in self.tailHands():
                    try:
                        self.processHand(handText)
                        self.numHands += 1
                    except FpdbParseError, e:
                        self.numErrors += 1
                        log.warning(_("HHC.start(follow): processHand failed: Exception msg: '%s'") % e)
                        log.debug(handText)
            else:
                handsList = self.allHandsAsList()
                log.debug( _("handsList is ") + str(handsList) )
                log.info("Parsing %d hands" % len(handsList))
                # Determine if we're dealing with a HH file or a Summary file
                # quick fix : empty files make the handsList[0] fail ==> If empty file, go on with HH parsing
                if len(handsList) == 0 or self.isSummary(handsList[0]) == False:
                    self.parsedObjectType = "HH"
                    for handText in handsList:
                        try:
                            self.processedHands.append(self.processHand(handText))
                        except FpdbParseError, e:
                            self.numErrors += 1
                            log.warning(_("HHC.start(): processHand failed: Exception msg: '%s'") % e)
                            log.debug(handText)
                    self.numHands = len(handsList)
                    endtime = time.time()
                    log.info(_("Read %d hands (%d failed) in %.3f seconds") % (self.numHands, self.numErrors, endtime - starttime))
                else:
                        self.parsedObjectType = "Summary"
                        summaryParsingStatus = self.readSummaryInfo(handsList)
                        endtime = time.time()
                        if summaryParsingStatus :
                            log.info(_("Summary file '%s' correctly parsed  (took %.3f seconds)") % (self.in_path, endtime - starttime))
                        else :
                            log.warning(_("Error converting summary file '%s' (took %.3f seconds)") % (self.in_path, endtime - starttime))

        except IOError, ioe:
            log.exception(_("Error converting '%s'") % self.in_path)
        finally:
            if self.out_fh != sys.stdout:
                self.out_fh.close()
                
    def progressNotify(self):
        "A callback to the interface while events are pending"
        import gtk, pygtk
        while gtk.events_pending():
            gtk.main_iteration(False)

    def tailHands(self):
        """Generator of handTexts from a tailed file:
Tail the in_path file and yield handTexts separated by re_SplitHands.
This requires a regex that greedily groups and matches the 'splitter' between hands,
which it expects to find at self.re_TailSplitHands -- see for e.g. Everleaf.py.

"""
        if self.in_path == '-':
            raise StopIteration
        interval = 1.0 # seconds to sleep between reads for new data
        fd = codecs.open(self.in_path,'r', self.codepage)
        data = ''
        while 1:
            where = fd.tell()
            newdata = fd.read(self.READ_CHUNK_SIZE)
            if not newdata:
                fd_results = os.fstat(fd.fileno())
                try:
                    st_results = os.stat(self.in_path)
                except OSError:
                    st_results = fd_results
                if st_results[1] == fd_results[1]:
                    time.sleep(interval)
                    fd.seek(where)
                else:
                    log.debug(_("%s changed inode numbers from %d to %d") % (self.in_path, fd_results[1], st_results[1]))
                    fd = codecs.open(self.in_path, 'r', self.codepage)
                    fd.seek(where)
            else:
                # yield hands
                data = data + newdata
                result = self.re_TailSplitHands.split(data)
                result = iter(result)
                data = ''
                # --x       data (- is bit of splitter, x is paragraph)     yield,...,keep
                # [,--,x]    result of re.split (with group around splitter)
                # ,x        our output: yield nothing, keep x
                #
                # --x--x    [,--,x,--,x]  x,x
                # -x--x     [-x,--,x]     x,x
                # x-        [x-]          ,x-
                # x--       [x,--,]       x,--
                # x--x      [x,--,x]      x,x
                # x--x--    [x,--,x,--,]  x,x,--

                # The length is always odd.
                # 'odd' indices are always splitters.
                # 'even' indices are always paragraphs or ''
                # We want to discard all the ''
                # We want to discard splitters unless the final item is '' (because the splitter could grow with new data)
                # We want to yield all paragraphs followed by a splitter, i.e. all even indices except the last.
                for para in result:
                    try:
                        result.next()
                        splitter = True
                    except StopIteration:
                        splitter = False
                    if splitter: # para is followed by a splitter
                        if para: yield para # para not ''
                    else:
                        data = para # keep final partial paragraph


    def allHandsAsList(self):
        """Return a list of handtexts in the file at self.in_path"""
        #TODO : any need for this to be generator? e.g. stars support can email one huge file of all hands in a year. Better to read bit by bit than all at once.
        self.readFile()
        self.obs = self.obs.strip()
        self.obs = self.obs.replace('\r\n', '\n')
        # maybe archive params should be one archive param, then call method in specific converter?
        # if self.archive:
        #     self.obs = self.convert_archive(self.obs)
        if self.starsArchive == True:
            log.debug(_("Converting starsArchive format to readable"))
            m = re.compile('^Hand #\d+', re.MULTILINE)
            self.obs = m.sub('', self.obs)

        if self.ftpArchive == True:
            log.debug(_("Converting ftpArchive format to readable"))
            # Remove  ******************** # 1 *************************
            m = re.compile('\*{20}\s#\s\d+\s\*{20,25}\s+', re.MULTILINE)
            self.obs = m.sub('', self.obs)

        if self.obs is None or self.obs == "":
            log.error(_("Read no hands."))
            return []
        handlist = re.split(self.re_SplitHands,  self.obs)
        # Some HH formats leave dangling text after the split
        # ie. </game> (split) </session>EOL
        # Remove this dangler if less than 50 characters and warn in the log
        if len(handlist[-1]) <= 50:
            handlist.pop()
            log.warn(_("Removing text < 50 characters"))
        return handlist

    def processHand(self, handText):
        gametype = self.determineGameType(handText)
        log.debug("gametype %s" % gametype)
        hand = None
        l = None
        if gametype is None:
            gametype = "unmatched"
            # TODO: not ideal, just trying to not error. Throw ParseException?
            self.numErrors += 1
        else:
            # See if gametype is supported.
            type = gametype['type']
            base = gametype['base']
            limit = gametype['limitType']
            l = [type] + [base] + [limit]

        if l in self.readSupportedGames():
            if gametype['base'] == 'hold':
                log.debug("hand = Hand.HoldemOmahaHand(self, self.sitename, gametype, handtext)")
                hand = Hand.HoldemOmahaHand(self.config, self, self.sitename, gametype, handText)
            elif gametype['base'] == 'stud':
                hand = Hand.StudHand(self.config, self, self.sitename, gametype, handText)
            elif gametype['base'] == 'draw':
                hand = Hand.DrawHand(self.config, self, self.sitename, gametype, handText)
        else:
            log.error(_("Unsupported game type: %s") % gametype)
            raise FpdbParseError(_("Unsupported game type: %s") % gametype)

        if hand:
            #hand.writeHand(self.out_fh)
            return hand
        else:
            log.error(_("Unsupported game type: %s") % gametype)
            # TODO: pity we don't know the HID at this stage. Log the entire hand?


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

    # Some sites do odd stuff that doesn't fall in to the normal HH parsing.
    # e.g., FTP doesn't put mixed game info in the HH, but puts in in the
    # file name. Use readOther() to clean up those messes.
    def readOther(self, hand): pass

    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand):
        hand.rake = hand.totalpot - hand.totalcollected #  * Decimal('0.05') # probably not quite right


    def sanityCheck(self):
        """Check we aren't going to do some stupid things"""
        sane = False
        base_w = False

        # Make sure input and output files are different or we'll overwrite the source file
        if True: # basically.. I don't know
            sane = True

        if self.in_path != '-' and self.out_path == self.in_path:
            print _("HH Sanity Check: output and input files are the same, check config")
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
            if self.in_path == '-':
                # read from stdin
                log.debug(_("Reading stdin with %s") % self.codepage) # is this necessary? or possible? or what?
                in_fh = codecs.getreader('cp1252')(sys.stdin)
            else:
                for kodec in self.__listof(self.codepage):
                    #print "trying", kodec
                    try:
                        in_fh = codecs.open(self.in_path, 'r', kodec)
                        whole_file = in_fh.read()
                        in_fh.close()
                        self.obs = whole_file[self.index:]
                        self.index = len(whole_file)
                        break
                    except:
                        pass
                else:
                    print _("unable to read file with any codec in list!"), self.in_path
                    self.obs = ""
        elif self.filetype == "xml":
            doc = xml.dom.minidom.parse(filename)
            self.doc = doc

    def guessMaxSeats(self, hand):
        """Return a guess at maxseats when not specified in HH."""
        # if some other code prior to this has already set it, return it
        if self.maxseats > 1 and self.maxseats < 11:
            return self.maxseats
        mo = self.maxOccSeat(hand)

        if mo == 10: return 10 #that was easy

        if hand.gametype['base'] == 'stud':
            if mo <= 8: return 8
            else: return mo

        if hand.gametype['base'] == 'draw':
            if mo <= 6: return 6
            else: return mo

        if mo == 2: return 2
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
        log.debug( _("raw time:")+str(time) + _(" given TZ:")+str(givenTimezone) )
        if wantedTimezone=="UTC":
            wantedTimezone = pytz.utc
        else:
            raise Error #TODO raise appropriate error

        givenTZ = None
        if HandHistoryConverter.re_tzOffset.match(givenTimezone):
            offset = int(givenTimezone[-5:])
            givenTimezone = givenTimezone[0:-5]
            log.debug( _("changeTimeZone: offset=") + str(offset) )
        else: offset=0

        if givenTimezone=="ET":
            givenTZ = timezone('US/Eastern')
        elif givenTimezone=="CET":
            givenTZ = timezone('Europe/Berlin')
            #Note: Daylight Saving Time is standardised across the EU so this should be fine
        elif givenTimezone == 'GMT': # Greenwich Mean Time (same as UTC - no change to time)
            givenTZ = timezone('GMT')
        elif givenTimezone == 'HST': # Hawaiian Standard Time
            pass
        elif givenTimezone == 'AKT': # Alaska Time
            pass
        elif givenTimezone == 'PT': # Pacific Time
            pass
        elif givenTimezone == 'MT': # Mountain Time
            pass
        elif givenTimezone == 'CT': # Central Time
            pass
        elif givenTimezone == 'AT': # Atlantic Time
            pass
        elif givenTimezone == 'NT': # Newfoundland Time
            pass
        elif givenTimezone == 'ART': # Argentinian Time
            pass
        elif givenTimezone == 'BRT': # Brasilia Time
            pass
        elif givenTimezone == 'AKT': # Alaska Time
            pass
        elif givenTimezone == 'WET': # Western European Time
            pass
        elif givenTimezone == 'EET': # Eastern European Time
            pass
        elif givenTimezone == 'MSK': # Moscow Standard Time
            pass
        elif givenTimezone == 'IST': # India Standard Time
            pass
        elif givenTimezone == 'CCT': # China Coast Time
            givenTZ = timezone('Australia/West')
        elif givenTimezone == 'JST': # Japan Standard Time
            pass
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
            pass
        else:
            raise Error #TODO raise appropriate error
        
        if givenTZ is None:
            raise Error #TODO raise appropriate error
                        # (or just return time unchanged?)

        localisedTime = givenTZ.localize(time)
        utcTime = localisedTime.astimezone(wantedTimezone) + datetime.timedelta(seconds=-3600*(offset/100)-60*(offset%100))
        log.debug( _("utcTime:")+str(utcTime) )
        return utcTime
    #end @staticmethod def changeTimezone

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        if type=="tour":
            return "%s.+Table %s" % (tournament, table_number)
        else:
            return table_name

    @staticmethod
    def getTableNoRe(tournament):
        "Returns string to search window title for tournament table no."
# Full Tilt:  $30 + $3 Tournament (181398949), Table 1 - 600/1200 Ante 100 - Limit Razz
# PokerStars: WCOOP 2nd Chance 02: $1,050 NLHE - Tournament 307521826 Table 1 - Blinds $30/$60
        return "%s.+(?:Table|Torneo) (\d+)" % (tournament, )

    @staticmethod
    def clearMoneyString(money):
        "Renders 'numbers' like '1 200' and '2,000'"
        return money.replace(' ', '').replace(',', '')

def getTableTitleRe(config, sitename, *args, **kwargs):
    "Returns string to search in windows titles for current site"
    return getSiteHhc(config, sitename).getTableTitleRe(*args, **kwargs)

def getTableNoRe(config, sitename, *args, **kwargs):
    "Returns string to search window titles for tournament table no."
    return getSiteHhc(config, sitename).getTableNoRe(*args, **kwargs)



def getSiteHhc(config, sitename):
    "Returns HHC class for current site"
    hhcName = config.supported_sites[sitename].converter
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
                print _("*** ERROR: UNABLE TO CREATE OUTPUT DIRECTORY"), out_dir 
            else: 
                log.info(_("Created directory '%s'") % out_dir) 
        try: 
            return(codecs.open(out_path, 'w', 'utf8')) 
        except: 
            log.error(_("out_path %s couldn't be opened") % (out_path)) 
    else:
        return(sys.stdout)
