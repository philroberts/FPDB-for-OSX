#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")

import pygtk
import gtk

#    fpdb/FreePokerTools modules
import Database
import Configuration
import Exceptions


#    database interface modules
try:
    import MySQLdb
except ImportError:
    log.debug(_("Import database module: MySQLdb not found"))
else:
    mysqlLibFound = True

try:
    import psycopg2
except ImportError:
    log.debug(_("Import database module: psycopg2 not found"))
else:
    import psycopg2.extensions
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

class Importer:
    def __init__(self, caller, settings, config, sql = None, parent = None):
        """Constructor"""
        self.settings   = settings
        self.caller     = caller
        self.config     = config
        self.sql        = sql
        self.parent     = parent

        #log = Configuration.get_logger("logging.conf", "importer", log_dir=self.config.dir_log)
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
        self.settings.setdefault("handCount", 0)
        #self.settings.setdefault("allowHudcacheRebuild", True) # NOT USED NOW
        #self.settings.setdefault("forceThreads", 2)            # NOT USED NOW
        self.settings.setdefault("writeQSize", 1000)           # no need to change
        self.settings.setdefault("writeQMaxWait", 10)          # not used
        self.settings.setdefault("dropIndexes", "don't drop")
        self.settings.setdefault("dropHudCache", "don't drop")
        self.settings.setdefault("starsArchive", False)
        self.settings.setdefault("ftpArchive", False)
        self.settings.setdefault("testData", False)
        self.settings.setdefault("cacheHHC", False)

        self.writeq = None
        self.database = Database.Database(self.config, sql = self.sql)
        self.writerdbs = []
        self.settings.setdefault("threads", 1) # value set by GuiBulkImport
        for i in xrange(self.settings['threads']):
            self.writerdbs.append( Database.Database(self.config, sql = self.sql) )

        clock() # init clock in windows

    #Set functions
    def setCallHud(self, value):
        self.callHud = value
        
    def setCacheSessions(self, value):
        self.cacheSessions = value

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

    def setStarsArchive(self, value):
        self.settings['starsArchive'] = value

    def setFTPArchive(self, value):
        self.settings['ftpArchive'] = value

    def setPrintTestData(self, value):
        self.settings['testData'] = value

    def setFakeCacheHHC(self, value):
        self.settings['cacheHHC'] = value

    def getCachedHHC(self):
        return self.handhistoryconverter

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
            
    def logImport(self, type, file, stored, dups, partial, errs, ttime, id):
        hands = stored + dups + partial + errs
        now = datetime.datetime.utcnow()
        ttime100 = ttime * 100
        self.database.updateFile([type, now, now, hands, stored, dups, partial, errs, ttime100, True, id])
    
    def addFileToList(self, file, site, filter):
        now = datetime.datetime.utcnow()
        file = os.path.splitext(os.path.basename(file))[0]
        try: #TODO: this is a dirty hack. GBI needs it, GAI fails with it.
            file = unicode(file, "utf8", "replace")
        except TypeError:
            pass
        id = self.database.storeFile([file, site, now, now, 0, 0, 0, 0, 0, 0, False])
        self.database.commit()
        return [site] + [filter] + [id]

    #Add an individual file to filelist
    def addImportFile(self, filename, site = "default", filter = "passthrough"):
        #TODO: test it is a valid file -> put that in config!!
        #print "addimportfile: filename is a", filename.__class__
        # filename not guaranteed to be unicode
        if filename in self.filelist or not os.path.exists(filename):
            return
        self.filelist[filename] = self.addFileToList(filename, site, filter)
        if site not in self.siteIds:
            # Get id from Sites table in DB
            result = self.database.get_site_id(site)
            if len(result) == 1:
                self.siteIds[site] = result[0][0]
            else:
                if len(result) == 0:
                    log.error(_("Database ID for %s not found") % site)
                else:
                    log.error(_("[ERROR] More than 1 Database ID found for %s - Multiple currencies not implemented yet") % site)


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
                    self.addImportFile(os.path.join(subdir[0], file), site=site, filter=filter)
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
            log.warning(_("Attempted to add non-directory '%s' as an import directory") % str(dir))

    def runImport(self):
        """"Run full import on self.filelist. This is called from GuiBulkImport.py"""
        #if self.settings['forceThreads'] > 0:  # use forceThreads until threading enabled in GuiBulkImport
        #    self.setThreads(self.settings['forceThreads'])

        # Initial setup
        start = datetime.datetime.now()
        starttime = time()
        log.info(_("Started at %s -- %d files to import. indexes: %s") % (start, len(self.filelist), self.settings['dropIndexes']))
        if self.settings['dropIndexes'] == 'auto':
            self.settings['dropIndexes'] = self.calculate_auto2(self.database, 12.0, 500.0)
        if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'auto':
            self.settings['dropHudCache'] = self.calculate_auto2(self.database, 25.0, 500.0)    # returns "drop"/"don't drop"

        if self.settings['dropIndexes'] == 'drop':
            self.database.prepareBulkImport()
        else:
            log.info(_("No need to drop indexes."))
        #print "dropInd =", self.settings['dropIndexes'], "  dropHudCache =", self.settings['dropHudCache']

        if self.settings['threads'] <= 0:
            (totstored, totdups, totpartial, toterrors) = self.importFiles(None)
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
            (totstored, totdups, totpartial, toterrors) = self.importFiles(self.writeq)

            if self.writeq.empty():
                print _("writers finished already")
                pass
            else:
                print _("waiting for writers to finish ...")
                #for t in threading.enumerate():
                #    print "    "+str(t)
                #self.writeq.join()
                #using empty() might be more reliable:
                while not self.writeq.empty() and len(threading.enumerate()) > 1:
                    # TODO: Do we need to actually tell the progress indicator to move, or is it already moving, and we just need to process events...
                    while gtk.events_pending(): # see http://faq.pygtk.org/index.py?req=index for more hints (3.7)
                        gtk.main_iteration(False)
                    sleep(0.5)
                print _("                              ... writers finished")

        # Tidying up after import
        if self.settings['dropIndexes'] == 'drop':
            self.database.afterBulkImport()
        else:
            log.info (_("No need to rebuild indexes."))
        if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'drop':
            self.database.rebuild_hudcache()
        else:
            log.info (_("No need to rebuild hudcache."))
        self.database.analyzeDB()
        endtime = time()
        return (totstored, totdups, totpartial, toterrors, endtime-starttime)
    # end def runImport

    def importFiles(self, q):
        """"Read filenames in self.filelist and pass to import_file_dict().
            Uses a separate database connection if created as a thread (caller
            passes None or no param as db)."""

        totstored = 0
        totdups = 0
        totpartial = 0
        toterrors = 0
        tottime = 0
        
        #prepare progress popup window
        ProgressDialog = ProgressBar(len(self.filelist), self.parent)
        
        for file in self.filelist:
            
            ProgressDialog.progress_update(file, str(self.database.getHandCount()))
            
            (stored, duplicates, partial, errors, ttime) = self.import_file_dict(file, self.filelist[file][0]
                                                           ,self.filelist[file][1], self.filelist[file][2], q)
            totstored += stored
            totdups += duplicates
            totpartial += partial
            toterrors += errors
            
            self.logImport('bulk', file, stored, duplicates, partial, errors, ttime, self.filelist[file][2])
        self.database.commit()
        del ProgressDialog
        
        for i in xrange( self.settings['threads'] ):
            print _("sending finish message queue length ="), q.qsize()
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
#                        print "file",file," updated", os.path.basename(file), stat_info.st_size, self.updatedsize[file], stat_info.st_mtime, self.updatedtime[file]
                        try:
                            if not os.path.isdir(file):
                                self.caller.addText("\n"+os.path.basename(file))
                        except KeyError: # TODO: What error happens here?
                            pass
                        (stored, duplicates, partial, errors, ttime) = self.import_file_dict(file, self.filelist[file][0]
                                                                      ,self.filelist[file][1], self.filelist[file][2], None)
                        self.logImport('auto', file, stored, duplicates, partial, errors, ttime, self.filelist[file][2])
                        try:
                            if not os.path.isdir(file): # Note: This assumes that whatever calls us has an "addText" func
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
    def import_file_dict(self, file, site, filter, fileId, q=None):

        if os.path.isdir(file):
            self.addToDirList[file] = [site] + [filter]
            return (0,0,0,0,0)

        (stored, duplicates, partial, errors, ttime) = (0, 0, 0, 0, time())

        # Load filter, process file, pass returned filename to import_fpdb_file
        if self.settings['threads'] > 0 and self.writeq is not None:
              log.info((_("Converting %s") % file) + " (" + str(q.qsize()) + ")")
        else: log.info(_("Converting %s") % file)
            
        filter_name = filter.replace("ToFpdb", "")
        mod = __import__(filter)
        obj = getattr(mod, filter_name, None)
        if callable(obj):
            
            if file in self.pos_in_file:  idx = self.pos_in_file[file]
            else: self.pos_in_file[file], idx = 0, 0
                
            hhc = obj( self.config, in_path = file, index = idx
                      ,starsArchive = self.settings['starsArchive']
                      ,ftpArchive   = self.settings['ftpArchive']
                      ,sitename     = site)
            
            if hhc.getStatus():
                if self.caller: hhc.progressNotify()
                handlist = hhc.getProcessedHands()
                self.pos_in_file[file] = hhc.getLastCharacterRead()
                (hbulk, hpbulk, habulk, hcbulk, phands, ihands, to_hud) = ([], [], [], [], [], [], [])
                sc, gsc = {'bk': []}, {'bk': []}
                
                ####Lock Placeholder####
                for hand in handlist:
                    hand.prepInsert(self.database, printtest = self.settings['testData'])
                    self.database.commit()
                    phands.append(hand)
                ####Lock Placeholder####
                
                for hand in phands:
                    hand.assembleHand()
                
                ####Lock Placeholder####
                id = self.database.nextHandId()
                for i in range(len(phands)):
                    doinsert = len(phands)==i+1
                    hand = phands[i]
                    try:
                        id = hand.getHandId(self.database, id)
                        sc, gsc = hand.updateSessionsCache(self.database, sc, gsc, None, doinsert)
                        hbulk = hand.insertHands(self.database, hbulk, fileId, doinsert, self.settings['testData'])
                        hcbulk = hand.updateHudCache(self.database, hcbulk, doinsert)
                        ihands.append(hand)
                        to_hud.append(hand.dbid_hands)
                    except Exceptions.FpdbHandDuplicate:
                        duplicates += 1
                self.database.commit()
                ####Lock Placeholder####
                
                for i in range(len(ihands)):
                    doinsert = len(ihands)==i+1
                    hand = ihands[i]
                    hpbulk = hand.insertHandsPlayers(self.database, hpbulk, doinsert, self.settings['testData'])
                    habulk = hand.insertHandsActions(self.database, habulk, doinsert, self.settings['testData'])
                self.database.commit()

                #pipe the Hands.id out to the HUD
                if self.callHud:
                    for hid in to_hud:
                        try:
                            print _("fpdb_import: sending hand to hud"), hid, "pipe =", self.caller.pipe_to_hud
                            self.caller.pipe_to_hud.stdin.write("%s" % (hid) + os.linesep)
                        except IOError, e:
                            log.error(_("Failed to send hand to HUD: %s") % e)

                errors = getattr(hhc, 'numErrors')
                stored = getattr(hhc, 'numHands')
                stored -= duplicates
                stored -= errors
                # Really ugly hack to allow testing Hands within the HHC from someone
                # with only an Importer objec
                if self.settings['cacheHHC']:
                    self.handhistoryconverter = hhc
            else:
                # conversion didn't work
                # TODO: appropriate response?
                return (0, 0, 0, 1, time() - ttime)
        else:
            log.warning(_("Unknown filter filter_name:'%s' in filter:'%s'") %(filter_name, filter))
            return (0, 0, 0, 1, time() - ttime)

        ttime = time() - ttime

        #This will barf if conv.getStatus != True
        return (stored, duplicates, partial, errors, ttime)


    def printEmailErrorMessage(self, errors, filename, line):
        traceback.print_exc(file=sys.stderr)
        print (_("Error No.%s please send the hand causing this to fpdb-main@lists.sourceforge.net so we can fix the problem.") % errors)
        print _("Filename:"), filename
        print _("Here is the first line of the hand so you can identify it. Please mention that the error was a ValueError:")
        print self.hand[0]
        print _("Hand logged to hand-errors.txt")
        logfile = open('hand-errors.txt', 'a')
        for s in self.hand:
            logfile.write(str(s) + "\n")
        logfile.write("\n")
        logfile.close()
        
        
class ProgressBar:

    """
    Popup window to show progress
    
    Init method sets up total number of expected iterations
    If no parent is passed to init, command line
    mode assumed, and does not create a progress bar
    """
    
    def __del__(self):
        
        if self.parent:
            self.progress.destroy()


    def progress_update(self, file, handcount):

        if not self.parent:
            #nothing to do
            return
            
        self.fraction += 1
        #update sum if fraction exceeds expected total number of iterations
        if self.fraction > self.sum: 
            sum = self.fraction
        
        #progress bar total set to 1 plus the number of items,to prevent it
        #reaching 100% prior to processing fully completing

        progress_percent = float(self.fraction) / (float(self.sum) + 1.0)
        progress_text = (self.title + " " 
                            + str(self.fraction) + " / " + str(self.sum))

        self.pbar.set_fraction(progress_percent)
        self.pbar.set_text(progress_text)
        
        self.handcount.set_text(_("Database Statistics") + " - " + _("Number of Hands: ") + handcount)
        
        now = datetime.datetime.now()
        now_formatted = now.strftime("%H:%M:%S")
        self.progresstext.set_text(now_formatted + " - "+self.title+ " " +file+"\n")


    def __init__(self, sum, parent):

        self.parent = parent
        if not self.parent:
            #no parent is passed, assume this is being run from the 
            #command line, so return immediately
            return
        
        self.fraction = 0
        self.sum = sum
        self.title = _("Importing")
            
        self.progress = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.progress.set_size_request(500,150)

        self.progress.set_resizable(False)
        self.progress.set_modal(True)
        self.progress.set_transient_for(self.parent)
        self.progress.set_decorated(True)
        self.progress.set_deletable(False)
        self.progress.set_title(self.title)
        
        vbox = gtk.VBox(False, 5)
        vbox.set_border_width(10)
        self.progress.add(vbox)
        vbox.show()
  
        align = gtk.Alignment(0, 0, 0, 0)
        vbox.pack_start(align, False, True, 2)
        align.show()

        self.pbar = gtk.ProgressBar()
        align.add(self.pbar)
        self.pbar.show()

        align = gtk.Alignment(0, 0, 0, 0)
        vbox.pack_start(align, False, True, 2)
        align.show()

        self.handcount = gtk.Label()
        align.add(self.handcount)
        self.handcount.show()
        
        align = gtk.Alignment(0, 0, 0, 0)
        vbox.pack_start(align, False, True, 0)
        align.show()
        
        self.progresstext = gtk.Label()
        self.progresstext.set_line_wrap(True)
        self.progresstext.set_selectable(True)
        align.add(self.progresstext)
        self.progresstext.show()
        
        self.progress.show()


if __name__ == "__main__":
    print _("CLI for importing hands is GuiBulkImport.py")
