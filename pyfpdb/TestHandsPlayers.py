# -*- coding: utf-8 -*-
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


class FpdbError:
    def __init__(self, sitename):
        self.site = sitename
        self.errorcount = 0
        self.histogram = {}

    def error_report(self, filename, hand, stat, ghash, testhash, player):
        print "Regression Test Error:"
        print "\tFile: %s" % filename
        print "\tStat: %s" % stat
        print "\tPlayer: %s" % player
        if filename in self.histogram:
            self.histogram[filename] += 1
        else:
            self.histogram[filename] = 1
        self.errorcount += 1

    def print_histogram(self):
        print "%s:" % self.site
        for f in self.histogram:
            idx = f.find('regression')
            print "(%3d) : %s" %(self.histogram[f], f[idx:])

def compare(leaf, importer, errors):
    filename = leaf
    #print "DEBUG: fileanme: %s" % filename

    # Test if this is a hand history file
    if filename.endswith('.txt'):
        # test if there is a .hp version of the file
        importer.addBulkImportImportFileOrDir(filename, site="PokerStars")
        (stored, dups, partial, errs, ttime) = importer.runImport()
        if os.path.isfile(filename + '.hp'):
            # Compare them
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
                        if pstat[stat] == teststat[stat]:
                            # The stats match - continue
                            pass
                        else:
                            # Stats don't match - Doh!
                            errors.error_report(filename, hand, stat, ghash, testhash, p)

        importer.clearFileList()



def walk_testfiles(dir, function, importer, errors):
    """Walks a directory, and executes a callback on each file """
    dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
        nfile = os.path.join(dir,file)
        if os.path.isdir(nfile):
            walk_testfiles(nfile, compare, importer, errors)
        else:
            compare(nfile, importer, errors)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)
    sql = SQL.Sql(db_server = 'sqlite')
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.setCallHud(False)
    importer.setFakeCacheHHC(True)

    PokerStarsErrors = FpdbError('PokerStars')
    FTPErrors        = FpdbError('Full Tilt Poker')
    PartyPokerErrors = FpdbError('Party Poker')
    BetfairErrors    = FpdbError('Betfair')
    
    walk_testfiles("regression-test-files/cash/Stars/", compare, importer, PokerStarsErrors)
    walk_testfiles("regression-test-files/cash/FTP/", compare, importer, FTPErrors)
    walk_testfiles("regression-test-files/cash/PartyPoker/", compare, importer, PartyPokerErrors)
    walk_testfiles("regression-test-files/cash/Betfair/", compare, importer, BetfairErrors)

    totalerrors = PokerStarsErrors.errorcount + FTPErrors.errorcount + PartyPokerErrors.errorcount + BetfairErrors.errorcount

    print "---------------------"
    print "Total Errors: %d" % totalerrors
    print "---------------------"
    PokerStarsErrors.print_histogram()
    FTPErrors.print_histogram()
    PartyPokerErrors.print_histogram()
    BetfairErrors.print_histogram()

if __name__ == '__main__':
    sys.exit(main())

