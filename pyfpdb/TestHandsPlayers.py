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

def error_report( filename, hand, stat, ghash, testhash, player):
    print "Regression Test Error:"
    print "\tFile: %s" % filename
    print "\tStat: %s" % stat
    print "\tPlayer: %s" % player

def compare(leaf, importer):
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
                            error_report(filename, hand, stat, ghash, testhash, p)

        importer.clearFileList()



def walk_testfiles(dir, function, importer):
    """Walks a directory, and executes a callback on each file """
    dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
        nfile = os.path.join(dir,file)
        if os.path.isdir(nfile):
            walk_testfiles(nfile, compare, importer)
        else:
            compare(nfile, importer)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)
    sql = SQL.Sql(db_server = 'sqlite')
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_tv_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.setCallHud(False)
    importer.setFakeCacheHHC(True)
    
    walk_testfiles("regression-test-files/cash/Stars/", compare, importer)

if __name__ == '__main__':
    sys.exit(main())

