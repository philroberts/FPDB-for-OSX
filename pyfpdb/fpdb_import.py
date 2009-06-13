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
from time import time, strftime
import traceback
import math
import datetime
import re

#    fpdb/FreePokerTools modules

import fpdb_simple
import fpdb_db
import fpdb_parse_logic
import Configuration

#    database interface modules
try:
    import MySQLdb
    mysqlLibFound=True
except:
    pass
    
try:
    import psycopg2
    pgsqlLibFound=True
    import psycopg2.extensions 
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

except:
    pass

class Importer:

    def __init__(self, caller, settings, config):
        """Constructor"""
        self.settings   = settings
        self.caller     = caller
        self.config     = config
        self.fdb        = None
        self.cursor     = None
        self.filelist   = {}
        self.dirlist    = {}
        self.siteIds    = {}
        self.addToDirList = {}
        self.removeFromFileList = {} # to remove deleted files
        self.monitor    = False
        self.updated    = {}         #Time last import was run {file:mtime}
        self.lines      = None
        self.faobs      = None       # File as one big string
        self.pos_in_file = {}        # dict to remember how far we have read in the file
        #Set defaults
        self.callHud    = self.config.get_import_parameters().get("callFpdbHud")
        
        self.settings.setdefault("minPrint", 30)
        self.settings.setdefault("handCount", 0)
        
        self.fdb = fpdb_db.fpdb_db()   # sets self.fdb.db self.fdb.cursor and self.fdb.sql
        self.fdb.do_connect(self.config)
        self.fdb.db.rollback()

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

    def setDropIndexes(self, value):
        self.settings['dropIndexes'] = value

#   def setWatchTime(self):
#       self.updated = time()

    def clearFileList(self):
        self.filelist = {}

    #Add an individual file to filelist
    def addImportFile(self, filename, site = "default", filter = "passthrough"):
        #TODO: test it is a valid file -> put that in config!!
        self.filelist[filename] = [site] + [filter]
        if site not in self.siteIds:
            # Get id from Sites table in DB
            self.fdb.cursor.execute(self.fdb.sql.query['getSiteId'], (site,))
            result = self.fdb.cursor.fetchall()
            if len(result) == 1:
                self.siteIds[site] = result[0][0]
            else:
                if len(result) == 0:
                    print "[ERROR] Database ID for %s not found" % site
                else:
                    print "[ERROR] More than 1 Database ID found for %s - Multiple currencies not implemented yet" % site


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
                    self.addImportFile(os.path.join(inputPath, subdir[0], file), site=site, filter=filter)
        else:
            self.addImportFile(inputPath, site=site, filter=filter)
    #Add a directory of files to filelist
    #Only one import directory per site supported.
    #dirlist is a hash of lists:
    #dirlist{ 'PokerStars' => ["/path/to/import/", "filtername"] }
    def addImportDirectory(self,dir,monitor = False, site = "default", filter = "passthrough"):
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
            print "Warning: Attempted to add non-directory: '" + str(dir) + "' as an import directory"

    def runImport(self):
        """"Run full import on self.filelist."""
        start = datetime.datetime.now()
        print "started at", start, "--", len(self.filelist), "files to import.", self.settings['dropIndexes']
        if self.settings['dropIndexes'] == 'auto':
            self.settings['dropIndexes'] = self.calculate_auto2(10.0, 500.0)
        if self.settings['dropIndexes'] == 'drop':
            self.fdb.prepareBulkImport()
        #self.settings['updateHudCache'] = self.calculate_auto2(10.0, 500.0)
        totstored = 0
        totdups = 0
        totpartial = 0
        toterrors = 0
        tottime = 0
#        if threads <= 1: do this bit
        for file in self.filelist:
            (stored, duplicates, partial, errors, ttime) = self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])
            totstored += stored
            totdups += duplicates
            totpartial += partial
            toterrors += errors
            tottime += ttime
        if self.settings['dropIndexes'] == 'drop':
            self.fdb.afterBulkImport()
        self.fdb.analyzeDB()
        return (totstored, totdups, totpartial, toterrors, tottime)
#        else: import threaded

    def calculate_auto(self):
        """An heuristic to determine a reasonable value of drop/don't drop"""
        if len(self.filelist) == 1:            return "don't drop"
        if 'handsInDB' not in self.settings:
            try:
                tmpcursor = self.fdb.db.cursor()
                tmpcursor.execute("Select count(1) from Hands;")
                self.settings['handsInDB'] = tmpcursor.fetchone()[0]
            except:
                pass # if this fails we're probably doomed anyway
        if self.settings['handsInDB'] < 5000:  return "drop"
        if len(self.filelist) < 50:            return "don't drop"      
        if self.settings['handsInDB'] > 50000: return "don't drop"
        return "drop"

    def calculate_auto2(self, scale, increment):
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
                tmpcursor = self.fdb.db.cursor()
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
        #print "auto2: handsindb =", self.settings['handsInDB'], "total_size =", total_size, "size_per_hand =", \
        #      size_per_hand, "inc =", increment
        if self.settings['handsInDB'] < scale * (total_size/size_per_hand) + increment:
            return "drop"
        return "don't drop"

    #Run import on updated files, then store latest update time.
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
                try: 
                    lastupdate = self.updated[file]
                    #rulog.writelines("lastupdate = %d, mtime = %d" % (lastupdate,stat_info.st_mtime))
                    if stat_info.st_mtime > lastupdate:
                        self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])
                        self.updated[file] = time()
                except:
                    self.updated[file] = time()
                    # If modified in the last minute run an immediate import.
                    # This codepath only runs first time the file is found.
                    if os.path.isdir(file) or (time() - stat_info.st_mtime) < 60:
                        # TODO attach a HHC thread to the file
                        # TODO import the output of the HHC thread  -- this needs to wait for the HHC to block?
                        self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])
                # TODO we also test if directory, why?
                #if os.path.isdir(file):
                    #self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])
            else:
                self.removeFromFileList[file] = True
        self.addToDirList = filter(lambda x: self.addImportDirectory(x, True, self.addToDirList[x][0], self.addToDirList[x][1]), self.addToDirList)

        for file in self.removeFromFileList:
            if file in self.filelist:
                del self.filelist[file]
        
        self.addToDirList = {}
        self.removeFromFileList = {}
        self.fdb.db.rollback()
        #rulog.writelines("  finished\n")
        #rulog.close()

    # This is now an internal function that should not be called directly.
    def import_file_dict(self, file, site, filter):
        if os.path.isdir(file):
            self.addToDirList[file] = [site] + [filter]
            return
        if filter == "passthrough" or filter == "":
            (stored, duplicates, partial, errors, ttime) = self.import_fpdb_file(file, site)
        else:
            conv = None
            # Load filter, process file, pass returned filename to import_fpdb_file
            
            print "\nConverting %s" % file
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
                conv = obj(in_path = file, out_path = out_path)
                if(conv.getStatus()):
                    (stored, duplicates, partial, errors, ttime) = self.import_fpdb_file(out_path, site)
                else:
                    # conversion didn't work
                    # TODO: appropriate response?
                    return (0, 0, 0, 1, 0)
            else:
                print "Unknown filter filter_name:'%s' in filter:'%s'" %(filter_name, filter)
                return

        #This will barf if conv.getStatus != True
        return (stored, duplicates, partial, errors, ttime)


    def import_fpdb_file(self, file, site):
        starttime = time()
        last_read_hand = 0
        loc = 0
        #print "file =", file
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
            except:
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

        try: # sometimes we seem to be getting an empty self.lines, in which case, we just want to return.
            firstline = self.lines[0]
        except:
            # just skip the debug message and return silently:
            #print "DEBUG: import_fpdb_file: failed on self.lines[0]: '%s' '%s' '%s' '%s' " %( file, site, self.lines, loc)
            return (0,0,0,1,0)

        if firstline.find("Tournament Summary")!=-1:
            print "TODO: implement importing tournament summaries"
            #self.faobs = readfile(inputFile)
            #self.parseTourneyHistory()
            return (0,0,0,1,0)

        category=fpdb_simple.recogniseCategory(firstline)

        startpos = 0
        stored = 0 #counter
        duplicates = 0 #counter
        partial = 0 #counter
        errors = 0 #counter

        for i in xrange (len(self.lines)):
            if (len(self.lines[i])<2): #Wierd way to detect for '\r\n' or '\n'
                endpos=i
                hand=self.lines[startpos:endpos]
        
                if (len(hand[0])<2):
                    hand=hand[1:]

        
                if (len(hand)<3):
                    pass
                    #TODO: This is ugly - we didn't actually find the start of the
                    # hand with the outer loop so we test again...
                else:
                    isTourney=fpdb_simple.isTourney(hand[0])
                    if not isTourney:
                        hand = fpdb_simple.filterAnteBlindFold(hand)
                    self.hand=hand

                    try:
                        handsId = fpdb_parse_logic.mainParser(self.settings, self.fdb.db
                                                           ,self.fdb.cursor, self.siteIds[site], category, hand, self.config)
                        self.fdb.db.commit()

                        stored += 1
                        if self.callHud:
                            #print "call to HUD here. handsId:",handsId
                            #pipe the Hands.id out to the HUD
                            print "sending hand to hud", handsId, "pipe =", self.caller.pipe_to_hud
                            self.caller.pipe_to_hud.stdin.write("%s" % (handsId) + os.linesep)
                    except fpdb_simple.DuplicateError:
                        duplicates += 1
                        self.fdb.db.rollback()
                    except (ValueError), fe:
                        errors += 1
                        self.printEmailErrorMessage(errors, file, hand)

                        if (self.settings['failOnError']):
                            self.fdb.db.commit() #dont remove this, in case hand processing was cancelled.
                            raise
                        else:
                            self.fdb.db.rollback()
                    except (fpdb_simple.FpdbError), fe:
                        errors += 1
                        self.printEmailErrorMessage(errors, file, hand)
                        self.fdb.db.rollback()

                        if self.settings['failOnError']:
                            self.fdb.db.commit() #dont remove this, in case hand processing was cancelled.
                            raise

                    if self.settings['minPrint']:
                        if not ((stored+duplicates+errors) % self.settings['minPrint']):
                            print "stored:", stored, "duplicates:", duplicates, "errors:", errors
            
                    if self.settings['handCount']:
                        if ((stored+duplicates+errors) >= self.settings['handCount']):
                            if not self.settings['quiet']:
                                print "quitting due to reaching the amount of hands to be imported"
                                print "Total stored:", stored, "duplicates:", duplicates, "errors:", errors, " time:", (time() - starttime)
                            sys.exit(0)
                startpos = endpos
        ttime = time() - starttime
        print "\rTotal stored:", stored, "duplicates:", duplicates, "errors:", errors, " time:", ttime
        
        if not stored:
            if duplicates:
                for line_no in xrange(len(self.lines)):
                    if self.lines[line_no].find("Game #")!=-1:
                        final_game_line=self.lines[line_no]
                handsId=fpdb_simple.parseSiteHandNo(final_game_line)
            else:
                print "failed to read a single hand from file:", inputFile
                handsId=0
            #todo: this will cause return of an unstored hand number if the last hand was error
        self.fdb.db.commit()
        self.handsId=handsId
        return (stored, duplicates, partial, errors, ttime)

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
