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

import sys

try:
    import MySQLdb
    mysqlLibFound=True
except:
    pass
    
try:
    import psycopg2
    pgsqlLibFound=True
except:
    pass

import traceback
import math
import os
import datetime
import re
import fpdb_simple
import fpdb_parse_logic
from time import time

class Importer:

    def __init__(self, caller, settings, config):
        """Constructor"""
        self.settings=settings
        self.caller=caller
        self.config = config
        self.db = None
        self.cursor = None
        self.filelist = {}
        self.dirlist = {}
        self.monitor = False
        self.updated = {}       #Time last import was run {file:mtime}
        self.lines = None
        self.faobs = None       #File as one big string
        self.pos_in_file = {} # dict to remember how far we have read in the file
        #Set defaults
        self.callHud = self.config.get_import_parameters().get("callFpdbHud")
        if not self.settings.has_key('minPrint'):
            #TODO: Is this value in the xml file?
            self.settings['minPrint'] = 30
        if not self.settings.has_key('handCount'):
            #TODO: Is this value in the xml file?
            self.settings['handCount'] = 0
        self.dbConnect()

    # XXX: Why is this here, when fpdb_db.connect() already does the
    # same?
    def dbConnect(self):
        #connect to DB
        if self.settings['db-backend'] == 2:
            if not mysqlLibFound:
                raise fpdb_simple.FpdbError("interface library MySQLdb not found but MySQL selected as backend - please install the library or change the config file")
            self.db = MySQLdb.connect(self.settings['db-host'], self.settings['db-user'],
                            self.settings['db-password'], self.settings['db-databaseName'])
        elif self.settings['db-backend'] == 3:
            if not pgsqlLibFound:
                raise fpdb_simple.FpdbError("interface library psycopg2 not found but PostgreSQL selected as backend - please install the library or change the config file")
            print self.settings
            if self.settings.has_key('db-host') and \
                        self.settings.has_key('db-user'):
                self.db = psycopg2.connect(host = self.settings['db-host'],
                                       user = self.settings['db-user'],
                                       password = self.settings['db-password'],
                                       database = self.settings['db-databaseName'])
            else:
                dbname = self.settings['db-databaseName']
                self.db = psycopg2.connect(database = dbname)
        elif self.settings['db-backend'] == 4:
            pass
        else:
            pass
        self.cursor = self.db.cursor()

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

#   def setWatchTime(self):
#       self.updated = time()

    def clearFileList(self):
        self.filelist = {}

    #Add an individual file to filelist
    def addImportFile(self, filename, site = "default", filter = "passthrough"):
        #TODO: test it is a valid file
        self.filelist[filename] = [site] + [filter]

    #Add a directory of files to filelist
    #Only one import directory per site supported.
    #dirlist is a hash of lists:
    #dirlist{ 'PokerStars' => ["/path/to/import/", "filtername"] }
    def addImportDirectory(self,dir,monitor = False, site = "default", filter = "passthrough"):
        if os.path.isdir(dir):
            if monitor == True:
                self.monitor = True
                self.dirlist[site] = [dir] + [filter]

            for file in os.listdir(dir):
                self.addImportFile(os.path.join(dir, file), site, filter)
        else:
            print "Warning: Attempted to add: '" + str(dir) + "' as an import directory"

    #Run full import on filelist
    def runImport(self):
        for file in self.filelist:
            self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])

    #Run import on updated files, then store latest update time.
    def runUpdated(self):
        #Check for new files in directory
        #todo: make efficient - always checks for new file, should be able to use mtime of directory
        # ^^ May not work on windows
        for site in self.dirlist:
            self.addImportDirectory(self.dirlist[site][0], False, site, self.dirlist[site][1])

        for file in self.filelist:
            stat_info = os.stat(file)
            try: 
                lastupdate = self.updated[file]
                if stat_info.st_mtime > lastupdate:
                    self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])
                    self.updated[file] = time()
            except:
                self.updated[file] = time()
                # This codepath only runs first time the file is found, if modified in the last
                # minute run an immediate import.
                if (time() - stat_info.st_mtime) < 60:
                    self.import_file_dict(file, self.filelist[file][0], self.filelist[file][1])

    # This is now an internal function that should not be called directly.
    def import_file_dict(self, file, site, filter):
        if(filter == "passthrough"):
            self.import_fpdb_file(file, site)
        else:
            #Load filter, and run filtered file though main importer
            self.import_fpdb_file(file, site)


    def import_fpdb_file(self, file, site):
        starttime = time()
        last_read_hand=0
        loc = 0
        if (file=="stdin"):
            inputFile=sys.stdin
        else:
            inputFile=open(file, "rU")
            try: loc = self.pos_in_file[file]
            except: pass

        # Read input file into class and close file
        inputFile.seek(loc)
        self.lines=fpdb_simple.removeTrailingEOL(inputFile.readlines())
        self.pos_in_file[file] = inputFile.tell()
        inputFile.close()

        try: # sometimes we seem to be getting an empty self.lines, in which case, we just want to return.
            firstline = self.lines[0]
        except:
#           print "import_fpdb_file", file, site, self.lines, "\n"
            return

        if firstline.find("Tournament Summary")!=-1:
            print "TODO: implement importing tournament summaries"
            #self.faobs = readfile(inputFile)
            #self.parseTourneyHistory()
            return 0
        
        site=fpdb_simple.recogniseSite(firstline)
        category=fpdb_simple.recogniseCategory(firstline)

        startpos=0
        stored=0 #counter
        duplicates=0 #counter
        partial=0 #counter
        errors=0 #counter

        for i in range (len(self.lines)): #main loop, iterates through the lines of a file and calls the appropriate parser method
            if (len(self.lines[i])<2):
                endpos=i
                hand=self.lines[startpos:endpos]
        
                if (len(hand[0])<2):
                    hand=hand[1:]
        
                cancelled=False
                damaged=False
                if (site=="ftp"):
                    for i in range (len(hand)):
                        if (hand[i].endswith(" has been canceled")): #this is their typo. this is a typo, right?
                            cancelled=True
                        
                        seat1=hand[i].find("Seat ") #todo: make this recover by skipping this line
                        if (seat1!=-1):
                            if (hand[i].find("Seat ", seat1+3)!=-1):
                                damaged=True
                
                if (len(hand)<3):
                    pass
                    #todo: the above 2 lines are kind of a dirty hack, the mentioned circumstances should be handled elsewhere but that doesnt work with DOS/Win EOL. actually this doesnt work.
                elif (hand[0].endswith(" (partial)")): #partial hand - do nothing
                    partial+=1
                elif (hand[1].find("Seat")==-1 and hand[2].find("Seat")==-1 and hand[3].find("Seat")==-1):#todo: should this be or instead of and?
                    partial+=1
                elif (cancelled or damaged):
                    partial+=1
                else: #normal processing
                    isTourney=fpdb_simple.isTourney(hand[0])
                    if not isTourney:
                        fpdb_simple.filterAnteBlindFold(site,hand)
                    hand=fpdb_simple.filterCrap(site, hand, isTourney)
                    self.hand=hand
                    
                    try:
                        handsId=fpdb_parse_logic.mainParser(self.settings['db-backend'], self.db
                                                           ,self.cursor, site, category, hand)
                        self.db.commit()
                        
                        stored+=1
                        self.db.commit()
                        if self.callHud:
                            #print "call to HUD here. handsId:",handsId
                            #pipe the Hands.id out to the HUD
                            self.caller.pipe_to_hud.stdin.write("%s" % (handsId) + os.linesep)
                    except fpdb_simple.DuplicateError:
                        duplicates+=1
                    except (ValueError), fe:
                        errors+=1
                        self.printEmailErrorMessage(errors, file, hand)
                
                        if (self.settings['failOnError']):
                            self.db.commit() #dont remove this, in case hand processing was cancelled.
                            raise
                    except (fpdb_simple.FpdbError), fe:
                        errors+=1
                        self.printEmailErrorMessage(errors, file, hand)

                        #fe.printStackTrace() #todo: get stacktrace
                        self.db.rollback()
                        
                        if (self.settings['failOnError']):
                            self.db.commit() #dont remove this, in case hand processing was cancelled.
                            raise
                    if (self.settings['minPrint']!=0):
                        if ((stored+duplicates+partial+errors)%self.settings['minPrint']==0):
                            print "stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors
            
                    if (self.settings['handCount']!=0):
                        if ((stored+duplicates+partial+errors)>=self.settings['handCount']):
                            if (not self.settings['quiet']):
                                print "quitting due to reaching the amount of hands to be imported"
                                print "Total stored:", stored, "duplicates:", duplicates, "partial/damaged:", partial, "errors:", errors, " time:", (time() - starttime)
                            sys.exit(0)
                startpos=endpos
        print "Total stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors, " time:", (time() - starttime)
        
        if stored==0:
            if duplicates>0:
                for line_no in range(len(self.lines)):
                    if self.lines[line_no].find("Game #")!=-1:
                        final_game_line=self.lines[line_no]
                handsId=fpdb_simple.parseSiteHandNo(final_game_line)
            else:
                print "failed to read a single hand from file:", inputFile
                handsId=0
            #todo: this will cause return of an unstored hand number if the last hand was error or partial
        self.db.commit()
        self.handsId=handsId
        return handsId
#end def import_file_dict

    def parseTourneyHistory(self):
        print "Tourney history parser stub"
        #Find tournament boundaries.
        #print self.foabs
        

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
