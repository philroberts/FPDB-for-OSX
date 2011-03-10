#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010, Carl Gherardi
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
import pprint
import PokerStarsToFpdb
from Hand import *
import Configuration
import Database
import SQL
import fpdb_import
import Options
import datetime
import pytz


class FpdbError:
    def __init__(self, sitename):
        self.site = sitename
        self.errorcount = 0
        self.histogram = {}
        self.statcount = {}

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
        self.errorcount += 1

    def print_histogram(self):
        print "%s:" % self.site
        for f in self.histogram:
            idx = f.find('regression')
            print "(%3d) : %s" %(self.histogram[f], f[idx:])

def compare_gametypes_file(filename, importer, errors):
    hashfilename = filename + '.gt'

    in_fh = codecs.open(hashfilename, 'r', 'utf8')
    whole_file = in_fh.read()
    in_fh.close()

    testhash = eval(whole_file)

    hhc = importer.getCachedHHC()
    handlist = hhc.getProcessedHands()

    lookup = {
                0:'siteId',
                1:'currency',
                2:'type',
                3:'base',
                4:'game',
                5:'limit',
                6:'hilo',
                7:'Small Blind',
                8:'Big Blind',
                9:'Small Bet',
                10:'Big Bet',
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
                        if stat == 'tourneyTypeId' or stat == 'tourneysPlayersIds':
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
        for datum in ghash:
            #print "DEBUG: hand: '%s'" % datum
            try:
                if ghash[datum] == testhash[datum]:
                    # The stats match - continue
                    pass
                else:
                    # Stats don't match. 
                    if datum == "gametypeId" or datum == 'sessionId' or datum == 'tourneyId':
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
    if filename.endswith('.txt'):
        # test if there is a .hp version of the file
        importer.addBulkImportImportFileOrDir(filename, site=site)
        (stored, dups, partial, errs, ttime) = importer.runImport()

        if errs > 0:
            errors.error_report(filename, False, "Parse", False, False, False)
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
    print "\t./TestHandsPlayers -s <Sitename> -f <filname>"
    sys.exit(0)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

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
    sql = SQL.Sql(db_server = 'sqlite')
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config, None)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.setCallHud(False)
    importer.setFakeCacheHHC(True)

    PokerStarsErrors  = FpdbError('PokerStars')
    FTPErrors         = FpdbError('Full Tilt Poker')
    PartyPokerErrors  = FpdbError('Party Poker')
    BetfairErrors     = FpdbError('Betfair')
    OnGameErrors      = FpdbError('OnGame')
    AbsoluteErrors    = FpdbError('Absolute Poker')
    UltimateBetErrors = FpdbError('Ultimate Bet')
    EverleafErrors    = FpdbError('Everleaf Poker')
    EverestErrors     = FpdbError('Everest Poker')
    CarbonErrors      = FpdbError('Carbon')
    PKRErrors         = FpdbError('PKR')
    iPokerErrors      = FpdbError('iPoker')
    Win2dayErrors     = FpdbError('Win2day')
    WinamaxErrors     = FpdbError('Winamax')

    ErrorsList = [
                    PokerStarsErrors, FTPErrors, PartyPokerErrors,
                    BetfairErrors, OnGameErrors, AbsoluteErrors,
                    EverleafErrors, CarbonErrors, PKRErrors,
                    iPokerErrors, WinamaxErrors, UltimateBetErrors,
                    Win2dayErrors, EverestErrors,
                ]

    sites = {
                'PokerStars' : False,
                'Full Tilt Poker' : False,
                'PartyPoker' : False,
                'Betfair' : False,
                'OnGame' : False,
                'Absolute' : False,
                'UltimateBet' : False,
                'Everleaf' : False,
                'Carbon' : False,
                #'PKR' : False,
                'iPoker' : False,
                'Win2day' : False,
                'Winamax' : False,
                'Everest' : False,
            }

    if test_all_sites == True:
        for s in sites:
            sites[s] = True
    else:
        sites[options.sitename] = True

    if sites['PokerStars'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Stars/", compare, importer, PokerStarsErrors, "PokerStars")
        walk_testfiles("regression-test-files/tour/Stars/", compare, importer, PokerStarsErrors, "PokerStars")
    elif sites['PokerStars'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, PokerStarsErrors, "PokerStars")

    if sites['Full Tilt Poker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/FTP/", compare, importer, FTPErrors, "Full Tilt Poker")
        walk_testfiles("regression-test-files/tour/FTP/", compare, importer, FTPErrors, "Full Tilt Poker")
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
    elif sites['OnGame'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, OnGameErrors, "OnGame")
    if sites['Absolute'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Absolute/", compare, importer, AbsoluteErrors, "Absolute")
        walk_testfiles("regression-test-files/tour/Absolute/", compare, importer, AbsoluteErrors, "Absolute")
    elif sites['Absolute'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, AbsoluteErrors, "Absolute")
    if sites['UltimateBet'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/UltimateBet/", compare, importer, UltimateBetErrors, "Absolute")
    elif sites['UltimateBet'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, UltimateBetErrors, "Absolute")
    if sites['Everleaf'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Everleaf/", compare, importer, EverleafErrors, "Everleaf")
    elif sites['Everleaf'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, EverleafErrors, "Everleaf")
    if sites['Carbon'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Carbon/", compare, importer, CarbonErrors, "Carbon")
    elif sites['Carbon'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, CarbonErrors, "Carbon")
    #if sites['PKR'] == True and not single_file_test:
    #    walk_testfiles("regression-test-files/cash/PKR/", compare, importer, PKRErrors, "PKR")
    if sites['iPoker'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/iPoker/", compare, importer, iPokerErrors, "iPoker")
    elif sites['iPoker'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, iPokerErrors, "iPoker")
    if sites['Winamax'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Winamax/", compare, importer, WinamaxErrors, "Winamax")
        walk_testfiles("regression-test-files/tour/Winamax/", compare, importer, WinamaxErrors, "Winamax")
    elif sites['Winamax'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, WinamaxErrors, "Winamax")
    if sites['Win2day'] == True and not single_file_test:
        walk_testfiles("regression-test-files/cash/Win2day/", compare, importer, Win2dayErrors, "Win2day")
    elif sites['Win2day'] == True and single_file_test:
        walk_testfiles(options.filename, compare, importer, Win2dayErrors, "Win2day")

    totalerrors = 0

    for i, site in enumerate(ErrorsList):
        totalerrors += ErrorsList[i].errorcount

    print "---------------------"
    print "Total Errors: %d" % totalerrors
    print "---------------------"
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


if __name__ == '__main__':
    sys.exit(main())

