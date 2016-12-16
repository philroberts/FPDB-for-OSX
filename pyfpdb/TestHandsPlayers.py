#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Carl Gherardi
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
########################################################################

import sys
import os
import codecs
from Hand import *
import Configuration
import Database
import SQL
import Importer
import Options
import datetime
import pytz
import pprint
pp = pprint.PrettyPrinter(indent=4)

DEBUG = False

class FpdbError:
    expected = {   # Site     : { path: (stored, dups, partial, errs) }
                   'Absolute Poker' : {},
                   'Betfair' : {},
                   'BetOnline': {
                        "regression-test-files/cash/BetOnline/Flop/NLHE-10max-USD-0.25-0.05-201108.txt":(19,0,1,0),
                        "regression-test-files/tour/BetOnline/Flop/NLHE-10max-USD-MTT-2011-08.nobuyinfee.txt":(17,0,1,0),
                        "regression-test-files/cash/BetOnline/Flop/NLHE-10max-0.25-0.50-201203.unknown.player.wins.txt":(0,0,0,1), #This file really is broken
                    },
                   'Boss' : {},
                   'Bovada' : {},
                   'Cake' : {
                        "regression-test-files/tour/Cake/Flop/NLHE-USD-2-STT-201205.thousand.delimiter.txt":(1,0,1,0)},
                   'Enet' : {},
                   'Entraction' : {},
                   'Everleaf' : {},
                   'Everest Poker' : {},
                   'Full Tilt Poker' : {
                        "regression-test-files/cash/FTP/Draw/3-Draw-Limit-USD-20-40-201101.Partial.txt":(0,0,1,0),
                        "regression-test-files/cash/FTP/Draw/3-Draw-Limit-USD-10-20-201101.Dead.hand.txt":(0,0,1,0),
                        "regression-test-files/cash/FTP/Flop/NLHE-6max-USD-25-50.200610.Observed.No.player.stacks.txt":(0,0,1,0),
                     },
                   'iPoker' : {},
                   'Merge' : {
                        "regression-test-files/cash/Merge/Draw/3-Draw-PL-USD-0.05-0.10-201102.Cancelled.hand.txt":(0,0,1,0),
                        "regression-test-files/cash/Merge/Flop/NLHE-6max-USD-0.02-0.04.201107.no.community.xml":(0,0,1,0),
                        "regression-test-files/cash/Merge/Flop/FLHE-9max-USD-0.02-0.04.20110416.xml":(9,0,1,0),
                             },
                   'Microgaming': {},
                   'OnGame' : {},
                   'PKR' : {},
                   'PacificPoker' : { "regression-test-files/cash/PacificPoker/Flop/888-LHE-HU-USD-10-20-201202.cancelled.hand.txt":(0,0,1,0), },
                   'Party Poker' : {},
                   'PokerStars': { 
                        "regression-test-files/cash/Stars/Flop/LO8-6max-USD-0.05-0.10-20090315.Hand-cancelled.txt":(0,0,1,0),
                        "regression-test-files/cash/Stars/Draw/3-Draw-Limit-USD-1-2-200809.Hand.cancelled.txt":(0,0,1,0),
                                 },
                   'PokerTracker' : {},
                   'Winamax' : {},
                 }
    def __init__(self, sitename):
        self.site = sitename
        self.errorcount = 0
        self.histogram = {}
        self.statcount = {}
        self.parse_errors = []

    def error_report(self, filename, hand, stat, ghash, testhash, player):
        print "Regression Test Error:"
        print "\tFile: %s" % filename
        print "\tStat: %s" % stat
        print "\tPlayer: %s" % player
        if filename in self.histogram:
            self.histogram[filename] += 1
        else:
            self.histogram[filename] = 1

        if stat in self.statcount:
            self.statcount[stat] += 1
        else:
            self.statcount[stat] = 1

        if stat == "Parse":
            self.parse_errors.append([filename, hand]) # hand is a tuple

        self.errorcount += 1

    def print_histogram(self):
        print "%s:" % self.site
        for f in self.histogram:
            idx = f.find('regression')
            print "(%3d) : %s" %(self.histogram[f], self.reduce_pathname(f))

    def print_parse_list(self):
        VERBOSE = False
        if len(self.parse_errors) > 0:
            print "%s:" % self.site
            for filename, import_numbers in self.parse_errors:
                path = self.reduce_pathname(filename)
                if path in self.expected[self.site]:
                    if self.expected[self.site][path] == import_numbers:
                        if VERBOSE: print "(0): %s" %(path)
                    else:
                        print "(X): %s" %(path)
                else:
                    print "(X): %s" %(path)

    def reduce_pathname(self, path):
        idx = path.find('regression')
        return path[idx:]

def compare_gametypes_file(filename, importer, errors):
    hashfilename = filename + '.gt'

    in_fh = codecs.open(hashfilename, 'r', 'utf8')
    whole_file = in_fh.read()
    in_fh.close()

    testhash = eval(whole_file)

    hhc = importer.getCachedHHC()
    handlist = hhc.getProcessedHands()

    lookup = {
                0:'Gametype: siteId',
                1:'Gametype: currency',
                2:'Gametype: type',
                3:'Gametype: base',
                4:'Gametype: game',
                5:'Gametype: limit',
                6:'Gametype: hilo',
                7:'Gametype: mix',
                8:'Gametype: Small Blind',
                9:'Gametype: Big Blind',
                10:'Gametype: Small Bet',
                11:'Gametype: Big Bet',
                12:'Gametype: maxSeats',
                13:'Gametype: ante',
                14:'Gametype: cap',
                15:'Gametype: zoom'
            }

    for hand in handlist:
        ghash = hand.gametyperow
        for i in range(len(ghash)):
            #print "DEBUG: about to compare: '%s' and '%s'" %(ghash[i], testhash[i])
            if ghash[i] == testhash[i]:
                # The stats match - continue
                pass
            else:
                errors.error_report(filename, hand, lookup[i], ghash, testhash, None)
    pass

def compare_handsplayers_file(filename, importer, errors):
    hashfilename = filename + '.hp'

    in_fh = codecs.open(hashfilename, 'r', 'utf8')
    whole_file = in_fh.read()
    in_fh.close()

    testhash = eval(whole_file)


    hhc = importer.getCachedHHC()
    handlist = hhc.getProcessedHands()
    #We _really_ only want to deal with a single hand here.
    for hand in handlist:
        ghash = hand.stats.getHandsPlayers()
        for p in ghash:
            #print "DEBUG: player: '%s'" % p
            pstat = ghash[p]
            teststat = testhash[p]
            for stat in pstat:
                #print "pstat[%s][%s]: %s == %s" % (p, stat, pstat[stat], teststat[stat])
                try:
                    if pstat[stat] == teststat[stat]:
                        # The stats match - continue
                        pass
                    else:
                        ignorelist = ['tourneyTypeId', 'tourneysPlayersIds']
                        # 'allInEV', 'street0CalledRaiseDone', 'street0CalledRaiseChance'
                        if stat in ignorelist:
                            # Not and error
                            pass
                        else:
                            errors.error_report(filename, hand, stat, ghash, testhash, p)
                except KeyError, e:
                    errors.error_report(filename, False, "KeyError: '%s'" % stat, False, False, p)

def compare_hands_file(filename, importer, errors):
    hashfilename = filename + '.hands'

    in_fh = codecs.open(hashfilename, 'r', 'utf8')
    whole_file = in_fh.read()
    in_fh.close()

    testhash = eval(whole_file)

    hhc = importer.getCachedHHC()
    handlist = hhc.getProcessedHands()

    for hand in handlist:
        ghash = hand.stats.getHands()
        # Delete unused data from hash
        try:
            del ghash['gsc']
            del ghash['sc']
            del ghash['id']
        except KeyError:
            pass
        del ghash['boards']
        for datum in ghash:
            #print "DEBUG: hand: '%s'" % datum
            try:
                if ghash[datum] == testhash[datum]:
                    # The stats match - continue
                    pass
                else:
                    # Stats don't match. 
                    if (datum == "gametypeId" 
                        or datum == 'gameId' 
                        or datum == 'sessionId' 
                        or datum == 'id'
                        or datum == 'tourneyId' 
                        or datum == 'gameSessionId'
                        or datum == 'fileId'
                        or datum == 'runItTwice'):
                        # Not an error. gametypeIds are dependent on the order added to the db.
                        #print "DEBUG: Skipping mismatched gamtypeId"
                        pass
                    else:
                        errors.error_report(filename, hand, datum, ghash, testhash, None)
            except KeyError, e:
                errors.error_report(filename, False, "KeyError: '%s'" % datum, False, False, None)


def compare(leaf, importer, errors, site):
    filename = leaf
    #print "DEBUG: fileanme: %s" % filename

    # Test if this is a hand history file
    if filename.endswith('.txt') or filename.endswith('.xml'):
        # test if there is a .hp version of the file
        if DEBUG: print "Site: %s" % site
        if DEBUG: print "Filename: %s" % filename
        file_added = importer.addBulkImportImportFileOrDir(filename, site=site)
        if not file_added:
            errors.error_report(filename, (0, 0, 0, 1), "Parse", False, False, False)
            importer.clearFileList()
            return False
                
        (stored, dups, partial, skipped, errs, ttime) = importer.runImport()
        
        if errs > 0 or partial > 0:
            errors.error_report(filename, (stored, dups, partial, errs), "Parse", False, False, False)
        else:
            if os.path.isfile(filename + '.hp'):
                compare_handsplayers_file(filename, importer, errors)
            if os.path.isfile(filename + '.hands'):
                compare_hands_file(filename, importer, errors)
            if os.path.isfile(filename + '.gt'):
                compare_gametypes_file(filename, importer, errors)

        importer.clearFileList()



def walk_testfiles(dir, function, importer, errors, site):
    """Walks a directory, and executes a callback on each file """
    dir = os.path.abspath(dir)
    try:
        for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
            nfile = os.path.join(dir,file)
            if os.path.isdir(nfile):
                walk_testfiles(nfile, compare, importer, errors, site)
            else:
                function(nfile, importer, errors, site)
    except OSError as (errno, strerror):
        if errno == 20:
            # Error 20 is 'not a directory'
            function(dir, importer, errors, site)
        else:
            raise OSError(errno, strerror)

def usage():
    print "USAGE:"
    print "Run all tests:"
    print "\t./TestHandsPlayers.py"
    print "Run tests for a sinlge site:"
    print "\t./TestHandsPlayers -s <Sitename>"
    print "Run tests for a sinlge file in a site:"
    print "\t./TestHandsPlayers -s <Sitename> -f <filename>"
    sys.exit(0)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    Configuration.set_logfile("fpdb-log.txt")
    (options, argv) = Options.fpdb_options()

    test_all_sites = True

    if options.usage == True:
        usage()

    single_file_test = False

    if options.sitename:
        options.sitename = Options.site_alias(options.sitename)
        if options.sitename == False:
            usage()
        if options.filename:
            print "Testing single hand: '%s'" % options.filename
            single_file_test = True
        else:
            print "Only regression testing '%s' files" % (options.sitename)
        test_all_sites = False

    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()
    importer = Importer.Importer(False, settings, config, None)
    importer.setDropIndexes("don't drop")
    importer.setThreads(-1)
    importer.setCallHud(False)
    importer.setFakeCacheHHC(True)

    AbsoluteErrors    = FpdbError('Absolute Poker')
    BetfairErrors     = FpdbError('Betfair')
    BetOnlineErrors   = FpdbError('BetOnline')
    BossErrors        = FpdbError('Boss')
    BovadaErrors      = FpdbError('Bovada')
    CakeErrors        = FpdbError('Cake')
    EnetErrors        = FpdbError('Enet')
    EntractionErrors  = FpdbError('Entraction')
    EverleafErrors    = FpdbError('Everleaf Poker')
    EverestErrors     = FpdbError('Everest Poker')
    FTPErrors         = FpdbError('Full Tilt Poker')
    iPokerErrors      = FpdbError('iPoker')
    MergeErrors      = FpdbError('Merge')
    MicrogamingErrors = FpdbError('Microgaming')
    OnGameErrors      = FpdbError('OnGame')
    PacificPokerErrors= FpdbError('PacificPoker')
    PartyPokerErrors  = FpdbError('Party Poker')
    PokerStarsErrors  = FpdbError('PokerStars')
    PKRErrors         = FpdbError('PKR')
    PTErrors          = FpdbError('PokerTracker')
    WinamaxErrors     = FpdbError('Winamax')

    ErrorsList = [
                    AbsoluteErrors, BetfairErrors, BetOnlineErrors, BossErrors, CakeErrors, EntractionErrors,
                    EverleafErrors, EverestErrors, FTPErrors, iPokerErrors, MergeErrors, MicrogamingErrors,
                    OnGameErrors, PacificPokerErrors, PartyPokerErrors, PokerStarsErrors, PKRErrors,
                    PTErrors, WinamaxErrors, BovadaErrors, EnetErrors,
                ]

    sites = {
                'Absolute' : False,
                'Betfair' : False,
                'BetOnline': False,
                'Boss' : False,
                'Bovada' : False,
                'Cake' : False,
                'Enet' : False,
                'Entraction' : False,
                'Everleaf' : False,
                'Everest' : False,
                'Full Tilt Poker' : False,
                'iPoker' : False,
                'Merge' : False,
                'Microgaming': False,
                'OnGame' : False,
                'Pkr' : False,
                'PacificPoker' : False,
                'PartyPoker' : False,
                'PokerStars' : False,
                'PokerTracker' : False,
                'Winamax' : False,
            }

    if test_all_sites == True:
        for s in sites:
            sites[s] = True
    else:
        sites[options.sitename] = True

    if sites['PacificPoker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/PacificPoker/", compare, importer, PacificPokerErrors, "PacificPoker")
        walk_testfiles("regression-test-files/tour/PacificPoker/", compare, importer, PacificPokerErrors, "PacificPoker")
        walk_testfiles("regression-test-files/summaries/PacificPoker/", compare, importer, PacificPokerErrors, "PacificPoker")
    elif sites['PacificPoker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PacificPokerErrors, "PacificPoker")

    if sites['PokerStars'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Stars/", compare, importer, PokerStarsErrors, "PokerStars")
        walk_testfiles("regression-test-files/tour/Stars/", compare, importer, PokerStarsErrors, "PokerStars")
        walk_testfiles("regression-test-files/summaries/Stars/", compare, importer, PokerStarsErrors, "PokerStars")
    elif sites['PokerStars'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PokerStarsErrors, "PokerStars")

    if sites['Full Tilt Poker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/FTP/", compare, importer, FTPErrors, "Full Tilt Poker")
        walk_testfiles("regression-test-files/tour/FTP/", compare, importer, FTPErrors, "Full Tilt Poker")
        walk_testfiles("regression-test-files/summaries/FTP/", compare, importer, FTPErrors, "Full Tilt Poker")
    elif sites['Full Tilt Poker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, FTPErrors, "Full Tilt Poker")
    if sites['PartyPoker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/PartyPoker/", compare, importer, PartyPokerErrors, "PartyPoker")
        walk_testfiles("regression-test-files/tour/PartyPoker/", compare, importer, PartyPokerErrors, "PartyPoker")
    elif sites['PartyPoker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PartyPokerErrors, "PartyPoker")
    if sites['Betfair'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Betfair/", compare, importer, BetfairErrors, "Betfair")
    elif sites['Betfair'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, BetfairErrors, "Betfair")
    if sites['OnGame'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/OnGame/", compare, importer, OnGameErrors, "OnGame")
        walk_testfiles("regression-test-files/tour/OnGame/", compare, importer, OnGameErrors, "OnGame")
    elif sites['OnGame'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, OnGameErrors, "OnGame")
    if sites['Absolute'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Absolute/", compare, importer, AbsoluteErrors, "Absolute")
        walk_testfiles("regression-test-files/tour/Absolute/", compare, importer, AbsoluteErrors, "Absolute")
    elif sites['Absolute'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, AbsoluteErrors, "Absolute")
    if sites['Everleaf'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Everleaf/", compare, importer, EverleafErrors, "Everleaf")
        walk_testfiles("regression-test-files/tour/Everleaf/", compare, importer, EverleafErrors, "Everleaf")
    elif sites['Everleaf'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, EverleafErrors, "Everleaf")
    if sites['Everest'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Everest/", compare, importer, EverestErrors, "Everest")
        walk_testfiles("regression-test-files/tour/Everest/", compare, importer, EverestErrors, "Everest")
    elif sites['Everest'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, EverestErrors, "Everest")
    if sites['Merge'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Merge/", compare, importer, MergeErrors, "Merge")
        walk_testfiles("regression-test-files/tour/Merge/", compare, importer, MergeErrors, "Merge")
    elif sites['Merge'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, MergeErrors, "Merge")
    if sites['Pkr'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/PKR/", compare, importer, PKRErrors, "PKR")
        walk_testfiles("regression-test-files/tour/PKR/", compare, importer, PKRErrors, "PKR")
    elif sites['Pkr'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PKRErrors, "PKR")
    if sites['iPoker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/iPoker/", compare, importer, iPokerErrors, "iPoker")
        walk_testfiles("regression-test-files/tour/iPoker/", compare, importer, iPokerErrors, "iPoker")
    elif sites['iPoker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, iPokerErrors, "iPoker")
    if sites['Boss'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Boss/", compare, importer, BossErrors, "Boss")
        walk_testfiles("regression-test-files/tour/Boss/", compare, importer, BossErrors, "Boss")
    elif sites['Boss'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, BossErrors, "Boss")
    if sites['Entraction'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Entraction/", compare, importer, EntractionErrors, "Entraction")
        walk_testfiles("regression-test-files/tour/Entraction/", compare, importer, EntractionErrors, "Entraction")
    elif sites['Entraction'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, EntractionErrors, "Entraction")
    if sites['BetOnline'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/BetOnline/", compare, importer, BetOnlineErrors, "BetOnline")
        walk_testfiles("regression-test-files/tour/BetOnline/", compare, importer, BetOnlineErrors, "BetOnline")
    elif sites['BetOnline'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, BetOnlineErrors, "BetOnline")
    if sites['Microgaming'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Microgaming/", compare, importer, MicrogamingErrors, "Microgaming")
        walk_testfiles("regression-test-files/tour/Microgaming/", compare, importer, MicrogamingErrors, "Microgaming")
    elif sites['Microgaming'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, MicrogamingErrors, "Microgaming")
    if sites['Cake'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Cake/", compare, importer, CakeErrors, "Cake")
        walk_testfiles("regression-test-files/tour/Cake/", compare, importer, CakeErrors, "Cake")
    elif sites['Cake'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, CakeErrors, "Cake")
    if sites['PokerTracker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/PokerTracker/", compare, importer, PTErrors, "PokerTracker")
        walk_testfiles("regression-test-files/tour/PokerTracker/", compare, importer, PTErrors, "PokerTracker")
    elif sites['PokerTracker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PTErrors, "PokerTracker")
    if sites['Winamax'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Winamax/", compare, importer, WinamaxErrors, "Winamax")
        walk_testfiles("regression-test-files/tour/Winamax/", compare, importer, WinamaxErrors, "Winamax")
    elif sites['Winamax'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, WinamaxErrors, "Winamax")
    if sites['Bovada'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Bovada/", compare, importer, BovadaErrors, "Bovada")
        walk_testfiles("regression-test-files/tour/Bovada/", compare, importer, BovadaErrors, "Bovada")
    elif sites['Bovada'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, BovadaErrors, "Bovada")
    if sites['Enet'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Enet/", compare, importer, EnetErrors, "Enet")
    elif sites['Enet'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, EnetErrors, "Enet")



    totalerrors = 0

    for i, site in enumerate(ErrorsList):
        totalerrors += ErrorsList[i].errorcount

    for i, site in enumerate(ErrorsList):
        ErrorsList[i].print_histogram()

    # Merge the dicts of stats from the various error objects
    statdict = {}
    for i, site in enumerate(ErrorsList):
        tmp = ErrorsList[i].statcount
        for stat in tmp:
            if stat in statdict:
                statdict[stat] += tmp[stat]
            else:
                statdict[stat] = tmp[stat]

    print "\n"
    print "---------------------"
    print "Errors by stat:"
    print "---------------------"
    #for stat in statdict:
    #    print "(%3d) : %s" %(statdict[stat], stat)

    sortedstats = sorted([(value,key) for (key,value) in statdict.items()])
    for num, stat in sortedstats:
        print "(%3d) : %s" %(num, stat)

    print "---------------------"
    print "Total Errors: %d" % totalerrors
    print "---------------------"

    print "-------- Parse Error List --------"
    for i, site in enumerate(ErrorsList):
        ErrorsList[i].print_parse_list()

if __name__ == '__main__':
    sys.exit(main())

