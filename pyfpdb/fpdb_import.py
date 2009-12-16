#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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

#see status.txt for site/games support info

#    Standard Library modules

import os  # todo: remove this once import_dir is in fpdb_import
import sys
from time import time, strftime, sleep, clock
import traceback
import math
import datetime
import re
import Queue
from collections import deque # using Queue for now
import threading

import pygtk
import gtk

#    fpdb/FreePokerTools modules

import fpdb_simple
import fpdb_db
import Database
import fpdb_parse_logic
import Configuration
import Exceptions

log = Configuration.get_logger("logging.conf", "importer")

#    database interface modules
try:
    import MySQLdb
except ImportError:
    log.debug("Import database module: MySQLdb not found")
else:
    mysqlLibFound = True

try:
    import psycopg2
except ImportError:
    log.debug("Import database module: psycopg2 not found")
else:
    import psycopg2.extensions
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

class Importer:
    def __init__(self, caller, settings, config, sql = None):
        """Constructor"""
        self.settings   = settings
        self.caller     = caller
        self.config     = config
        self.sql        = sql

        self.filelist   = {}
        self.dirlist    = {}
        self.siteIds    = {}
        self.addToDirList = {}
        self.removeFromFileList = {} # to remove deleted files
        self.monitor    = False
        self.updatedsize = {}
        self.updatedtime = {}
        self.lines      = None
        self.faobs      = None       # File as one big string
        self.pos_in_file = {}        # dict to remember how far we have read in the file
        #Set defaults
        self.callHud    = self.config.get_import_parameters().get("callFpdbHud")

        # CONFIGURATION OPTIONS
        self.settings.setdefault("minPrint", 30)
        self.settings.setdefault("handCount", 0)
        #self.settings.setdefault("allowHudcacheRebuild", True) # NOT USED NOW
        #self.settings.setdefault("forceThreads", 2)            # NOT USED NOW
        self.settings.setdefault("writeQSize", 1000)           # no need to change
        self.settings.setdefault("writeQMaxWait", 10)          # not used
        self.settings.setdefault("dropIndexes", "don't drop")
        self.settings.setdefault("dropHudCache", "don't drop")

        self.writeq = None
        self.database = Database.Database(self.config, sql = self.sql)
        self.writerdbs = []
        self.settings.setdefault("threads", 1) # value set by GuiBulkImport
        for i in xrange(self.settings['threads']):
            self.writerdbs.append( Database.Database(self.config, sql = self.sql) )

        self.NEWIMPORT = Configuration.NEWIMPORT

        clock() # init clock in windows

    #Set functions
    def setCallHud(self, value):
        self.callHud = value

    def setMinPrint(self, value):
        self.settings['minPrint'] = int(value)

    def setHandCount(self, value):
        self.settings['handCount'] = int(value)

    def setQuiet(self, value):
        self.settings['quiet'] = value

    def setFailOnError(self, value):
        self.settings['failOnError'] = value

    def setHandsInDB(self, value):
        self.settings['handsInDB'] = value

    def setThreads(self, value):
        self.settings['threads'] = value
        if self.settings["threads"] > len(self.writerdbs):
            for i in xrange(self.settings['threads'] - len(self.writerdbs)):
                self.writerdbs.append( Database.Database(self.config, sql = self.sql) )

    def setDropIndexes(self, value):
        self.settings['dropIndexes'] = value

    def setDropHudCache(self, value):
        self.settings['dropHudCache'] = value

#   def setWatchTime(self):
#       self.updated = time()

    def clearFileList(self):
        self.updatedsize = {}
        self.updatetime = {}
        self.pos_in_file = {}
        self.filelist = {}

    def closeDBs(self):
        self.database.disconnect()
        for i in xrange(len(self.writerdbs)):
            self.writerdbs[i].disconnect()

    #Add an individual file to filelist
    def addImportFile(self, filename, site = "default", filter = "passthrough"):
        #TODO: test it is a valid file -> put that in config!!
        if filename in self.filelist or not os.path.exists(filename):
            return
        self.filelist[filename] = [site] + [filter]
        if site not in self.siteIds:
            # Get id from Sites table in DB
            result = self.database.get_site_id(site)
            if len(result) == 1:
                self.siteIds[site] = result[0][0]
            else:
                if len(result) == 0:
                    log.error("Database ID for %s not found" % site)
                else:
                    log.error("[ERROR] More than 1 Database ID found for %s - Multiple currencies not implemented yet" % site)


    # Called from GuiBulkImport to add a file or directory.
    def addBulkImportImportFileOrDir(self, inputPath, site = "PokerStars"):
        """Add a file or directory for bulk import"""
        filter = self.config.hhcs[site].converter
        # Bulk import never monitors
        # if directory, add all files in it. Otherwise add single file.
        # TODO: only add sane files?
        if os.path.isdir(inputPath):
            for subdir in os.walk(inputPath):
                for file in subdir[2]:
                    self.addImportFile(os.path.join(subdir[0], file), site=site,
                                       filter=filter)
        else:
            self.addImportFile(inputPath, site=site, filter=filter)
    #Add a directory of files to filelist
    #Only one import directory per site supported.
    #dirlist is a hash of lists:
    #dirlist{ 'PokerStars' => ["/path/to/import/", "filtername"] }
    def addImportDirectory(self,dir,monitor=False, site="default", filter="passthrough"):
        #gets called by GuiAutoImport.
        #This should really be using os.walk
        #http://docs.python.org/library/os.html
        if os.path.isdir(dir):
            if monitor == True:
                self.monitor = True
                self.dirlist[site] = [dir] + [filter]

            #print "addImportDirectory: checking files in", dir
            for file in os.listdir(dir):
                #print "                    adding file ", file
                self.addImportFile(os.path.join(dir, file), site, filter)
        else:
            log.warning("Attempted to add non-directory: '%s' as an import directory" % str(dir))

    def runImport(self):
        """"Run full import on self.filelist. This is called from GuiBulkImport.py"""
        #if self.settings['forceThreads'] > 0:  # use forceThreads until threading enabled in GuiBulkImport
        #    self.setThreads(self.settings['forceThreads'])

        # Initial setup
        start = datetime.datetime.now()
        starttime = time()
        log.info("Started at %s -- %d files to import. indexes: %s" % (start, len(self.filelist), self.settings['dropIndexes']))
        if self.settings['dropIndexes'] == 'auto':
            self.settings['dropIndexes'] = self.calculate_auto2(self.database, 12.0, 500.0)
        if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'auto':
            self.settings['dropHudCache'] = self.calculate_auto2(self.database, 25.0, 500.0)    # returns "drop"/"don't drop"

        if self.settings['dropIndexes'] == 'drop':
            self.database.prepareBulkImport()
        else:
            log.debug("No need to drop indexes.")
        #print "dropInd =", self.settings['dropIndexes'], "  dropHudCache =", self.settings['dropHudCache']

        if self.settings['threads'] <= 0:
            (totstored, totdups, totpartial, toterrors) = self.importFiles(self.database, None)
        else:
            # create queue (will probably change to deque at some point):
            self.writeq = Queue.Queue( self.settings['writeQSize'] )
            # start separate thread(s) to read hands from queue and write to db:
            for i in xrange(self.settings['threads']):
                t = threading.Thread( target=self.writerdbs[i].insert_queue_hands
                                    , args=(self.writeq, self.settings["writeQMaxWait"])
                                    , name="dbwriter-"+str(i) )
                t.setDaemon(True)
                t.start()
            # read hands and write to q:
            (totstored, totdups, totpartial, toterrors) = self.importFiles(self.database, self.writeq)

            if self.writeq.empty():
                print "writers finished already"
                pass
            else:
                print "waiting for writers to finish ..."
                #for t in threading.enumerate():
                #    print "    "+str(t)
                #self.writeq.join()
                #using empty() might be more reliable:
                while not self.writeq.empty() and len(threading.enumerate()) > 1:
                    # TODO: Do we need to actually tell the progress indicator to move, or is it already moving, and we just need to process events...
                    while gtk.events_pending(): # see http://faq.pygtk.org/index.py?req=index for more hints (3.7)
                        gtk.main_iteration(False)
                    sleep(0.5)
                print "                              ... writers finished"

        # Tidying up after import
        if self.settings['dropIndexes'] == 'drop':
            self.database.afterBulkImport()
        else:
            print "No need to rebuild indexes."
        if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'drop':
            self.database.rebuild_hudcache()
        else:
            print "No need to rebuild hudcache."
        self.database.analyzeDB()
        endtime = time()
        return (totstored, totdups, totpartial, toterrors, endtime-starttime)
    # end def runImport

    def importFiles(self, db, q):
        """"Read filenames in self.filelist and pass to import_file_dict().
            Uses a separate database connection if created as a thread (caller
            passes None or no param as db)."""

        totstored = 0
        totdups = 0
        totpartial = 0
        toterrors = 0
        tottime = 0
        for file in self.filelist:
            (stored, duplicates, partial, errors, ttime) = self.import_file_dict(db, file
                                               ,self.filelist[file][0], self.filelist[file][1], q)
            totstored += stored
            totdups += duplicates
            totpartial += partial
            toterrors += errors

        for i in xrange( self.settings['threads'] ):
            print "sending finish msg qlen =", q.qsize()
            db.send_finish_msg(q)

        return (totstored, totdups, totpartial, toterrors)
    # end def importFiles

    # not used currently
    def calculate_auto(self, db):
        """An heuristic to determine a reasonable value of drop/don't drop"""
        if len(self.filelist) == 1:            return "don't drop"
        if 'handsInDB' not in self.settings:
            try:
                tmpcursor = db.get_cursor()
                tmpcursor.execute("Select count(1) from Hands;")
                self.settings['handsInDB'] = tmpcursor.fetchone()[0]
            except:
                pass # if this fails we're probably doomed anyway
        if self.settings['handsInDB'] < 5000:  return "drop"
        if len(self.filelist) < 50:            return "don't drop"
        if self.settings['handsInDB'] > 50000: return "don't drop"
        return "drop"

    def calculate_auto2(self, db, scale, increment):
        """A second heuristic to determine a reasonable value of drop/don't drop
           This one adds up size of files to import to guess number of hands in them
           Example values of scale and increment params might be 10 and 500 meaning
           roughly: drop if importing more than 10% (100/scale) of hands in db or if
           less than 500 hands in db"""
        size_per_hand = 1300.0  # wag based on a PS 6-up FLHE file. Actual value not hugely important
                                # as values of scale and increment compensate for it anyway.
                                # decimal used to force float arithmetic

        # get number of hands in db
        if 'handsInDB' not in self.settings:
            try:
                tmpcursor = db.get_cursor()
                tmpcursor.execute("Select count(1) from Hands;")
                self.settings['handsInDB'] = tmpcursor.fetchone()[0]
            except:
                pass # if this fails we're probably doomed anyway

        # add up size of import files
        total_size = 0.0
        for file in self.filelist:
            if os.path.exists(file):
                stat_info = os.stat(file)
                total_size += stat_info.st_size

        # if hands_in_db is zero or very low, we want to drop indexes, otherwise compare
        # import size with db size somehow:
        ret = "don't drop"
        if self.settings['handsInDB'] < scale * (total_size/size_per_hand) + increment:
            ret = "drop"
        #print "auto2: handsindb =", self.settings['handsInDB'], "total_size =", total_size, "size_per_hand =", \
        #      size_per_hand, "inc =", increment, "return:", ret
        return ret

    #Run import on updated files, then store latest update time. Called from GuiAutoImport.py
    def runUpdated(self):
        #Check for new files in monitored directories
        #todo: make efficient - always checks for new file, should be able to use mtime of directory
        # ^^ May not work on windows

        #rulog = open('runUpdated.txt', 'a')
        #rulog.writelines("runUpdated ... ")
        for site in self.dirlist:
            self.addImportDirectory(self.dirlist[site][0], False, site, self.dirlist[site][1])

        for file in self.filelist:
            if os.path.exists(file):
                stat_info = os.stat(file)
                #rulog.writelines("path exists ")
                if file in self.updatedsize: # we should be able to assume that if we're in size, we're in time as well
                    if stat_info.st_size > self.updatedsize[file] or stat_info.st_mtime > self.updatedtime[file]:
#                        print "file",counter," updated", os.path.basename(file), stat_info.st_size, self.updatedsize[file], stat_info.st_mtime, self.updatedtime[file]
                        try:
                            if not os.path.isdir(file):
                                self.caller.addText("\n"+os.path.basename(file))
                        except KeyError: # TODO: What error happens here?
                            pass
                        (stored, duplicates, partial, errors, ttime) = self.import_file_dict(self.database, file, self.filelist[file][0], self.filelist[file][1], None)
                        try:
                            if not os.path.isdir(file):
                                self.caller.addText(" %d stored, %d duplicates, %d partial, %d errors (time = %f)" % (stored, duplicates, partial, errors, ttime))
                        except KeyError: # TODO: Again, what error happens here? fix when we find out ..
                            pass
                        self.updatedsize[file] = stat_info.st_size
                        self.updatedtime[file] = time()
                else:
                    if os.path.isdir(file) or (time() - stat_info.st_mtime) < 60:
                        self.updatedsize[file] = 0
                        self.updatedtime[file] = 0
                    else:
                        self.updatedsize[file] = stat_info.st_size
                        self.updatedtime[file] = time()
            else:
                self.removeFromFileList[file] = True

        self.addToDirList = filter(lambda x: self.addImportDirectory(x, True, self.addToDirList[x][0], self.addToDirList[x][1]), self.addToDirList)

        for file in self.removeFromFileList:
            if file in self.filelist:
                del self.filelist[file]

        self.addToDirList = {}
        self.removeFromFileList = {}
        self.database.rollback()
        #rulog.writelines("  finished\n")
        #rulog.close()

    # This is now an internal function that should not be called directly.
    def import_file_dict(self, db, file, site, filter, q=None):
        #print "import_file_dict"

        if os.path.isdir(file):
            self.addToDirList[file] = [site] + [filter]
            return (0,0,0,0,0)

        conv = None
        (stored, duplicates, partial, errors, ttime) = (0, 0, 0, 0, 0)

        file =  file.decode(fpdb_simple.LOCALE_ENCODING)

        # Load filter, process file, pass returned filename to import_fpdb_file
        if self.settings['threads'] > 0 and self.writeq is not None:
            log.info("Converting " + file + " (" + str(q.qsize()) + ")")
        else:
            log.info("Converting " + file)
        hhbase    = self.config.get_import_parameters().get("hhArchiveBase")
        hhbase    = os.path.expanduser(hhbase)
        hhdir     = os.path.join(hhbase,site)
        try:
            out_path     = os.path.join(hhdir, file.split(os.path.sep)[-2]+"-"+os.path.basename(file))
        except:
            out_path     = os.path.join(hhdir, "x"+strftime("%d-%m-%y")+os.path.basename(file))

        filter_name = filter.replace("ToFpdb", "")

        mod = __import__(filter)
        obj = getattr(mod, filter_name, None)
        if callable(obj):
            hhc = obj(in_path = file, out_path = out_path, index = 0) # Index into file 0 until changeover
            if hhc.getStatus() and self.NEWIMPORT == False:
                (stored, duplicates, partial, errors, ttime) = self.import_fpdb_file(db, out_path, site, q)
            elif hhc.getStatus() and self.NEWIMPORT == True:
                #This code doesn't do anything yet
                handlist = hhc.getProcessedHands()
                self.pos_in_file[file] = hhc.getLastCharacterRead()

                for hand in handlist:
                    #try, except duplicates here?
                    hand.prepInsert(self.database)
                    hand.insert(self.database)
                    if self.callHud and hand.dbid_hands != 0:
                        #print "DEBUG: call to HUD: handsId: %s" % hand.dbid_hands
                        #pipe the Hands.id out to the HUD
                        print "fpdb_import: sending hand to hud", hand.dbid_hands, "pipe =", self.caller.pipe_to_hud
                        self.caller.pipe_to_hud.stdin.write("%s" % (hand.dbid_hands) + os.linesep)
                self.database.commit()

                errors = getattr(hhc, 'numErrors')
                stored = getattr(hhc, 'numHands')
            else:
                # conversion didn't work
                # TODO: appropriate response?
                return (0, 0, 0, 1, 0)
        else:
            log.warning("Unknown filter filter_name:'%s' in filter:'%s'" %(filter_name, filter))
            return (0, 0, 0, 1, 0)

        #This will barf if conv.getStatus != True
        return (stored, duplicates, partial, errors, ttime)


    def import_fpdb_file(self, db, file, site, q):
        starttime = time()
        last_read_hand = 0
        loc = 0
        (stored, duplicates, partial, errors, ttime) = (0, 0, 0, 0, 0)
        # print "file =", file
        if file == "stdin":
            inputFile = sys.stdin
        else:
            if os.path.exists(file):
                inputFile = open(file, "rU")
            else:
                self.removeFromFileList[file] = True
                return (0, 0, 0, 1, 0)
            try:
                loc = self.pos_in_file[file]
                #size = os.path.getsize(file)
                #print "loc =", loc, 'size =', size
            except KeyError:
                pass
        # Read input file into class and close file
        inputFile.seek(loc)
        #tmplines = inputFile.readlines()
        #if tmplines == None or tmplines == []:
        #    print "tmplines = ", tmplines
        #else:
        #    print "tmplines[0] =", tmplines[0]
        self.lines = fpdb_simple.removeTrailingEOL(inputFile.readlines())
        self.pos_in_file[file] = inputFile.tell()
        inputFile.close()

        x = clock()
        (stored, duplicates, partial, errors, ttime, handsId) = self.import_fpdb_lines(db, self.lines, starttime, file, site, q)

        db.commit()
        y = clock()
        ttime = y - x
        #ttime = time() - starttime
        if q is None:
            log.info("Total stored: %(stored)d\tduplicates:%(duplicates)d\terrors:%(errors)d\ttime:%(ttime)s" % locals())

        if not stored:
            if duplicates:
                for line_no in xrange(len(self.lines)):
                    if self.lines[line_no].find("Game #") != -1:
                        final_game_line = self.lines[line_no]
                handsId=fpdb_simple.parseSiteHandNo(final_game_line)
            else:
                print "failed to read a single hand from file:", inputFile
                handsId = 0
            #todo: this will cause return of an unstored hand number if the last hand was error
        self.handsId = handsId

        return (stored, duplicates, partial, errors, ttime)
    # end def import_fpdb_file


    def import_fpdb_lines(self, db, lines, starttime, file, site, q = None):
        """Import an fpdb hand history held in the list lines, could be one hand or many"""

        #db.lock_for_insert() # should be ok when using one thread, but doesn't help??
        while gtk.events_pending():
            gtk.main_iteration(False)

        try: # sometimes we seem to be getting an empty self.lines, in which case, we just want to return.
            firstline = lines[0]
        except:
            # just skip the debug message and return silently:
            #print "DEBUG: import_fpdb_file: failed on lines[0]: '%s' '%s' '%s' '%s' " %( file, site, lines, loc)
            return (0,0,0,1,0,0)

        if "Tournament Summary" in firstline:
            print "TODO: implement importing tournament summaries"
            #self.faobs = readfile(inputFile)
            #self.parseTourneyHistory()
            return (0,0,0,1,0,0)

        category = fpdb_simple.recogniseCategory(firstline)

        startpos = 0
        stored = 0 #counter
        duplicates = 0 #counter
        partial = 0 #counter
        errors = 0 #counter
        ttime = 0
        handsId = 0

        for i in xrange(len(lines)):
            if len(lines[i]) < 2: #Wierd way to detect for '\r\n' or '\n'
                endpos = i
                hand = lines[startpos:endpos]

                if len(hand[0]) < 2:
                    hand=hand[1:]

                if len(hand) < 3:
                    pass
                    #TODO: This is ugly - we didn't actually find the start of the
                    # hand with the outer loop so we test again...
                else:
                    isTourney = fpdb_simple.isTourney(hand[0])
                    if not isTourney:
                        hand = fpdb_simple.filterAnteBlindFold(hand)
                    self.hand = hand

                    try:
                        handsId = fpdb_parse_logic.mainParser( self.settings, self.siteIds[site]
                                                             , category, hand, self.config
                                                             , db, q )
                        db.commit()

                        stored += 1
                        if self.callHud:
                            #print "call to HUD here. handsId:",handsId
                            #pipe the Hands.id out to the HUD
                            # print "fpdb_import: sending hand to hud", handsId, "pipe =", self.caller.pipe_to_hud
                            try:
                                self.caller.pipe_to_hud.stdin.write("%s" % (handsId) + os.linesep)
                            except IOError: # hud closed
                                self.callHud = False
                                pass # continue import without hud
                    except Exceptions.DuplicateError:
                        duplicates += 1
                        db.rollback()
                    except (ValueError), fe:
                        errors += 1
                        self.printEmailErrorMessage(errors, file, hand)

                        if (self.settings['failOnError']):
                            db.commit() #dont remove this, in case hand processing was cancelled.
                            raise
                        else:
                            db.rollback()
                    except (fpdb_simple.FpdbError), fe:
                        errors += 1
                        self.printEmailErrorMessage(errors, file, hand)
                        db.rollback()

                        if self.settings['failOnError']:
                            db.commit() #dont remove this, in case hand processing was cancelled.
                            raise

                    if self.settings['minPrint']:
                        if not ((stored+duplicates+errors) % self.settings['minPrint']):
                            print "stored:", stored, "   duplicates:", duplicates, "errors:", errors

                    if self.settings['handCount']:
                        if ((stored+duplicates+errors) >= self.settings['handCount']):
                            if not self.settings['quiet']:
                                print "quitting due to reaching the amount of hands to be imported"
                                print "Total stored:", stored, "duplicates:", duplicates, "errors:", errors, " time:", (time() - starttime)
                            sys.exit(0)
                startpos = endpos
        return (stored, duplicates, partial, errors, ttime, handsId)
    # end def import_fpdb_lines

    def printEmailErrorMessage(self, errors, filename, line):
        traceback.print_exc(file=sys.stderr)
        print "Error No.",errors,", please send the hand causing this to steffen@sycamoretest.info so I can fix it."
        print "Filename:", filename
        print "Here is the first line so you can identify it. Please mention that the error was a ValueError:"
        print self.hand[0]
        print "Hand logged to hand-errors.txt"
        logfile = open('hand-errors.txt', 'a')
        for s in self.hand:
            logfile.write(str(s) + "\n")
        logfile.write("\n")
        logfile.close()

if __name__ == "__main__":
    print "CLI for fpdb_import is now available as CliFpdb.py"
