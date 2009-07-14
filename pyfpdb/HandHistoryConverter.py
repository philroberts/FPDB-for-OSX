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

import Hand
import re
import sys
import traceback
import logging
from optparse import OptionParser
import os
import os.path
import xml.dom.minidom
import codecs
from decimal import Decimal
import operator
from xml.dom.minidom import Node
import time
import datetime

import gettext
gettext.install('fpdb')

class HandHistoryConverter():

    READ_CHUNK_SIZE = 10000 # bytes to read at a time from file (in tail mode)
    def __init__(self, in_path = '-', out_path = '-', sitename = None, follow=False):
        logging.info("HandHistory init")
        
        # default filetype and codepage. Subclasses should set these properly.
        self.filetype  = "text"
        self.codepage  = "utf8"

        self.in_path = in_path
        self.out_path = out_path
        
        if in_path == '-':
            self.in_fh = sys.stdin

        if out_path == '-':
            self.out_fh = sys.stdout
        else:
            # TODO: out_path should be sanity checked.
            self.out_fh = open(self.out_path, 'w')

        self.sitename  = sitename
        self.follow = follow
        self.compiledPlayers   = set()
        self.maxseats  = 10

    def __str__(self):
        return """
HandHistoryConverter: '%(sitename)s'
    filetype:   '%(filetype)s'
    in_path:    '%(in_path)s'
    out_path:   '%(out_path)s'
    """ % { 'sitename':self.sitename, 'filetype':self.filetype, 'in_path':self.in_path, 'out_path':self.out_path }

    def start(self):
        """process a hand at a time from the input specified by in_path.
If in follow mode, wait for more data to turn up.
Otherwise, finish at eof.

"""        
        starttime = time.time()
        if not self.sanityCheck():
            print "Cowardly refusing to continue after failed sanity check"
            return

        if self.follow:
            numHands = 0
            for handText in self.tailHands():
                numHands+=1
                self.processHand(handText)
        else:
            handsList = self.allHandsAsList()
            logging.info("Parsing %d hands" % len(handsList))
            for handText in handsList:
                self.processHand(handText)
            numHands=  len(handsList)
        endtime = time.time()
        print "read %d hands in %.3f seconds" % (numHands, endtime - starttime)
        if self.out_fh != sys.stdout:
            self.out_fh.close()


    def tailHands(self):
        """Generator of handTexts from a tailed file:
Tail the in_path file and yield handTexts separated by re_SplitHands.
This requires a regex that greedily groups and matches the 'splitter' between hands,
which it expects to find at self.re_TailSplitHands -- see for e.g. Everleaf.py.

"""
        if self.in_path == '-': raise StopIteration
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
                    logging.debug("%s changed inode numbers from %d to %d" % (self.in_path, fd_results[1], st_results[1]))
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
        if self.obs == "" or self.obs == None:
            logging.info("Read no hands.")
            return
        return re.split(self.re_SplitHands,  self.obs)
        
    def processHand(self, handText):
        gametype = self.determineGameType(handText)
        logging.debug("gametype %s" % gametype)
        if gametype is None: 
            l = None
            gametype = "unmatched"
            # TODO: not ideal, just trying to not error.
            # TODO: Need to count failed hands.
        else:
            # See if gametype is supported.
            type = gametype['type']
            base = gametype['base']
            limit = gametype['limitType']
            l = [type] + [base] + [limit]
        if l in self.readSupportedGames():
            hand = None
            if gametype['base'] == 'hold':
                logging.debug("hand = Hand.HoldemOmahaHand(self, self.sitename, gametype, handtext)")
                hand = Hand.HoldemOmahaHand(self, self.sitename, gametype, handText)
            elif gametype['base'] == 'stud':
                hand = Hand.StudHand(self, self.sitename, gametype, handText)
            elif gametype['base'] == 'draw':
                hand = Hand.DrawHand(self, self.sitename, gametype, handText)
        else:
            logging.info("Unsupported game type: %s" % gametype)

        if hand:
#            print hand
            hand.writeHand(self.out_fh)
        else:
            logging.info("Unsupported game type: %s" % gametype)
            # TODO: pity we don't know the HID at this stage. Log the entire hand?
            # From the log we can deduce that it is the hand after the one before :)


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

    # Read any of:
    # HID       HandID
    # TABLE     Table name
    # SB        small blind
    # BB        big blind
    # GAMETYPE  gametype
    # YEAR MON DAY HR MIN SEC   datetime
    # BUTTON    button seat number
    def readHandInfo(self, hand): abstract

    # Needs to return a list of lists in the format
    # [['seat#', 'player1name', 'stacksize'] ['seat#', 'player2name', 'stacksize'] [...]]
    def readPlayerStacks(self, hand): abstract
    
    def compilePlayerRegexs(self): abstract
    """Compile dynamic regexes -- these explicitly match known player names and must be updated if a new player joins"""
    
    # Needs to return a MatchObject with group names identifying the streets into the Hand object
    # so groups are called by street names 'PREFLOP', 'FLOP', 'STREET2' etc
    # blinds are done seperately
    def markStreets(self, hand): abstract

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb, 
    # addtional players are assumed to post a bb oop
    def readBlinds(self, hand): abstract
    def readAntes(self, hand): abstract
    def readBringIn(self, hand): abstract
    def readButton(self, hand): abstract
    def readHeroCards(self, hand): abstract
    def readPlayerCards(self, hand, street): abstract
    def readAction(self, hand, street): abstract
    def readCollectPot(self, hand): abstract
    def readShownCards(self, hand): abstract
    
    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand):
        hand.rake = hand.totalpot - hand.totalcollected #  * Decimal('0.05') # probably not quite right
    
    
    def sanityCheck(self):
        """Check we aren't going to do some stupid things"""
        #TODO: the hhbase stuff needs to be in fpdb_import
        sane = False
        base_w = False
        #~ #Check if hhbase exists and is writable
        #~ #Note: Will not try to create the base HH directory
        #~ if not (os.access(self.hhbase, os.W_OK) and os.path.isdir(self.hhbase)):
            #~ print "HH Sanity Check: Directory hhbase '" + self.hhbase + "' doesn't exist or is not writable"
        #~ else:
            #~ #Check if hhdir exists and is writable
            #~ if not os.path.isdir(self.hhdir):
                #~ # In first pass, dir may not exist. Attempt to create dir
                #~ print "Creating directory: '%s'" % (self.hhdir)
                #~ os.mkdir(self.hhdir)
                #~ sane = True
            #~ elif os.access(self.hhdir, os.W_OK):
                #~ sane = True
            #~ else:
                #~ print "HH Sanity Check: Directory hhdir '" + self.hhdir + "' or its parent directory are not writable"

        # Make sure input and output files are different or we'll overwrite the source file
        if True: # basically.. I don't know
            sane = True
        
        if(self.in_path != '-' and self.out_path == self.in_path):
            print "HH Sanity Check: output and input files are the same, check config"
            sane = False


        return sane

    # Functions not necessary to implement in sub class
    def setFileType(self, filetype = "text", codepage='utf8'):
        self.filetype = filetype
        self.codepage = codepage

    def splitFileIntoHands(self):
        hands = []
        self.obs = self.obs.strip()
        list = self.re_SplitHands.split(self.obs)
        list.pop() #Last entry is empty
        for l in list:
#           print "'" + l + "'"
            hands = hands + [Hand.Hand(self.sitename, self.gametype, l)]
        return hands

    def readFile(self):
        """open in_path according to self.codepage"""
        
        if(self.filetype == "text"):
            if self.in_path == '-':
                # read from stdin
                logging.debug("Reading stdin with %s" % self.codepage) # is this necessary? or possible? or what?
                in_fh = codecs.getreader('cp1252')(sys.stdin)
            else:
                logging.debug("Opening %s with %s" % (self.in_path, self.codepage))
                in_fh = codecs.open(self.in_path, 'r', self.codepage)
            self.obs = in_fh.read()
            in_fh.close()
        elif(self.filetype == "xml"):
            try:
                doc = xml.dom.minidom.parse(filename)
                self.doc = doc
            except:
                traceback.print_exc(file=sys.stderr)


    def getStatus(self):
        #TODO: Return a status of true if file processed ok
        return True

    def getProcessedFile(self):
        return self.out_path
