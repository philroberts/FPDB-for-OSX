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
from time import time, sleep, clock
import datetime
import Queue
import shutil
import re

import logging, traceback

import gtk

#    fpdb/FreePokerTools modules
import Database
import Configuration
import IdentifySite
from Exceptions import FpdbParseError, FpdbHandDuplicate

if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")

class Importer:
    def __init__(self, caller, settings, config, sql = None, parent = None):
        """Constructor"""
        self.settings   = settings
        self.caller     = caller
        self.config     = config
        self.sql        = sql
        self.parent     = parent

        self.idsite = IdentifySite.IdentifySite(config)

        self.filelist   = {}
        self.dirlist    = {}
        self.siteIds    = {}
        self.removeFromFileList = {} # to remove deleted files
        self.monitor    = False
        self.updatedsize = {}
        self.updatedtime = {}
        self.lines      = None
        self.faobs      = None       # File as one big string
        self.mode       = None
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
    def setMode(self, value):
        self.mode = value
        
    def setCallHud(self, value):
        self.callHud = value
        
    def setCacheSessions(self, value):
        self.cacheSessions = value

    def setHandCount(self, value):
        self.settings['handCount'] = int(value)

    def setQuiet(self, value):
        self.settings['quiet'] = value

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

    def logImport(self, type, file, stored, dups, partial, errs, ttime, id):
        hands = stored + dups + partial + errs
        now = datetime.datetime.utcnow()
        ttime100 = ttime * 100
        self.database.updateFile([type, now, now, hands, stored, dups, partial, errs, ttime100, True, id])
        self.database.commit()
    
    def addFileToList(self, fpdbfile):
        """FPDBFile"""
        file = os.path.splitext(os.path.basename(fpdbfile.path))[0]
        try: #TODO: this is a dirty hack. GBI needs it, GAI fails with it.
            file = unicode(file, "utf8", "replace")
        except TypeError:
            pass
        fpdbfile.fileId = self.database.get_id(file)
        if not fpdbfile.fileId:
            now = datetime.datetime.utcnow()
            fpdbfile.fileId = self.database.storeFile([file, fpdbfile.site.name, now, now, 0, 0, 0, 0, 0, 0, False])
            self.database.commit()
            
    #Add an individual file to filelist
    def addImportFile(self, filename, site = "auto"):
        #print "addimportfile: filename is a", filename.__class__
        # filename not guaranteed to be unicode
        if self.filelist.get(filename)!=None or not os.path.exists(filename):
            return False

        self.idsite.processFile(filename)
        if self.idsite.get_fobj(filename):
            fpdbfile = self.idsite.filelist[filename]
        else:
            log.error("Importer.addImportFile: siteId Failed for: '%s'" % filename)
            return False
        
        self.addFileToList(fpdbfile)
        self.filelist[filename] = fpdbfile
        if site not in self.siteIds:
            # Get id from Sites table in DB
            result = self.database.get_site_id(fpdbfile.site.name)
            if len(result) == 1:
                self.siteIds[fpdbfile.site.name] = result[0][0]
            else:
                if len(result) == 0:
                    log.error(_("Database ID for %s not found") % fpdbfile.site.name)
                else:
                    log.error(_("More than 1 Database ID found for %s") % fpdbfile.site.name)

        return True
    # Called from GuiBulkImport to add a file or directory. Bulk import never monitors
    def addBulkImportImportFileOrDir(self, inputPath, site = "auto"):
        """Add a file or directory for bulk import"""
        #for windows platform, force os.walk variable to be unicode
        # see fpdb-main post 9th July 2011
        if self.config.posix:
            pass
        else:
            inputPath = unicode(inputPath)

        # TODO: only add sane files?
        if os.path.isdir(inputPath):
            for subdir in os.walk(inputPath):
                for file in subdir[2]:
                    self.addImportFile(os.path.join(subdir[0], file), site=site)
            return True
        else:
            return self.addImportFile(inputPath, site=site)

    #Add a directory of files to filelist
    #Only one import directory per site supported.
    #dirlist is a hash of lists:
    #dirlist{ 'PokerStars' => ["/path/to/import/", "filtername"] }
    def addImportDirectory(self,dir,monitor=False, site=("default","hh"), filter="passthrough"):
        #gets called by GuiAutoImport.
        #This should really be using os.walk
        #http://docs.python.org/library/os.html
        if os.path.isdir(dir):
            if monitor == True:
                self.monitor = True
                self.dirlist[site] = [dir] + [filter]

            #print "addImportDirectory: checking files in", dir
            for subdir in os.walk(dir):
                for file in subdir[2]:
                    filename = os.path.join(subdir[0], file)
                    if (time() - os.stat(filename).st_mtime)<= 43200: # look all files modded in the last 12 hours
                                                                    # need long time because FTP in Win does not
                                                                    # update the timestamp on the HH during session
                        self.addImportFile(filename, "auto")
        else:
            log.warning(_("Attempted to add non-directory '%s' as an import directory") % str(dir))

    def runImport(self):
        """"Run full import on self.filelist. This is called from GuiBulkImport.py"""

        # Initial setup
        start = datetime.datetime.now()
        starttime = time()
        log.info(_("Started at %s -- %d files to import. indexes: %s") % (start, len(self.filelist), self.settings['dropIndexes']))
        if self.settings['dropIndexes'] == 'auto':
            self.settings['dropIndexes'] = self.calculate_auto2(self.database, 12.0, 500.0)
        if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'auto':
            self.settings['dropHudCache'] = self.calculate_auto2(self.database, 25.0, 500.0)    # returns "drop"/"don't drop"

        (totstored, totdups, totpartial, toterrors) = self.importFiles(None)

        # Tidying up after import
        #if 'dropHudCache' in self.settings and self.settings['dropHudCache'] == 'drop':
        #    log.info(_("rebuild_caches"))
        #    self.database.rebuild_caches()
        #else:
        #    log.info(_("runPostImport"))
        self.runPostImport()
        self.database.analyzeDB()
        endtime = time()
        return (totstored, totdups, totpartial, toterrors, endtime-starttime)
    # end def runImport
    
    def runPostImport(self):
        self.database.cleanUpTourneyTypes()
        self.database.cleanUpWeeksMonths()
        self.database.resetClean()

    def importFiles(self, q):
        """"Read filenames in self.filelist and pass to despatcher."""

        totstored = 0
        totdups = 0
        totpartial = 0
        toterrors = 0
        tottime = 0
        filecount = 0
        fileerrorcount = 0
        moveimportedfiles = False #TODO need to wire this into GUI and make it prettier
        movefailedfiles = False #TODO and this too
        
        #prepare progress popup window
        ProgressDialog = ProgressBar(len(self.filelist), self.parent)
        
        for f in self.filelist:
            filecount = filecount + 1
            ProgressDialog.progress_update(f, str(self.database.getHandCount()))

            (stored, duplicates, partial, errors, ttime) = self._import_despatch(self.filelist[f])
            totstored += stored
            totdups += duplicates
            totpartial += partial
            toterrors += errors

            if moveimportedfiles and movefailedfiles:
                try:
                    if moveimportedfiles:
                        shutil.move(file, "c:\\fpdbimported\\%d-%s" % (filecount, os.path.basename(file[3:]) ) )
                except:
                    fileerrorcount = fileerrorcount + 1
                    if movefailedfiles:
                        shutil.move(file, "c:\\fpdbfailed\\%d-%s" % (fileerrorcount, os.path.basename(file[3:]) ) )
            
            self.logImport('bulk', f, stored, duplicates, partial, errors, ttime, self.filelist[f].fileId)
            
        del ProgressDialog
        
        return (totstored, totdups, totpartial, toterrors)
    # end def importFiles

    def _import_despatch(self, fpdbfile):
        stored, duplicates, partial, errors, ttime = 0,0,0,0,0
        if fpdbfile.ftype in ("hh", "both"):
            (stored, duplicates, partial, errors, ttime) = self._import_hh_file(fpdbfile)
        if fpdbfile.ftype == "summary":
            (stored, duplicates, partial, errors, ttime) = self._import_summary_file(fpdbfile)
        if fpdbfile.ftype == "both" and fpdbfile.path not in self.updatedsize:
            self._import_summary_file(fpdbfile)
        #    pass
        print "DEBUG: _import_summary_file.ttime: %.3f %s" % (ttime, fpdbfile.ftype)
        return (stored, duplicates, partial, errors, ttime)


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
        """Check for new files in monitored directories"""
        for (site,type) in self.dirlist:
            self.addImportDirectory(self.dirlist[(site,type)][0], False, (site,type), self.dirlist[(site,type)][1])

        for f in self.filelist:
            if os.path.exists(f):
                stat_info = os.stat(f)
                if f in self.updatedsize: # we should be able to assume that if we're in size, we're in time as well
                    if stat_info.st_size > self.updatedsize[f] or stat_info.st_mtime > self.updatedtime[f]:
                        try:
                            if not os.path.isdir(f):
                                self.caller.addText("\n"+os.path.basename(f))
                        except KeyError:
                            log.error("File '%s' seems to have disappeared" % f)
                        (stored, duplicates, partial, errors, ttime) = self._import_despatch(self.filelist[f])
                        self.logImport('auto', f, stored, duplicates, partial, errors, ttime, self.filelist[f].fileId)
                        self.database.commit()
                        try:
                            if not os.path.isdir(f): # Note: This assumes that whatever calls us has an "addText" func
                                self.caller.addText(" %d stored, %d duplicates, %d partial, %d errors (time = %f)" % (stored, duplicates, partial, errors, ttime))
                        except KeyError: # TODO: Again, what error happens here? fix when we find out ..
                            pass
                        self.updatedsize[f] = stat_info.st_size
                        self.updatedtime[f] = time()
                else:
                    if os.path.isdir(f) or (time() - stat_info.st_mtime) < 60:
                        self.updatedsize[f] = 0
                        self.updatedtime[f] = 0
                    else:
                        self.updatedsize[f] = stat_info.st_size
                        self.updatedtime[f] = time()
            else:
                self.removeFromFileList[f] = True

        for file in self.removeFromFileList:
            if file in self.filelist:
                del self.filelist[file]

        self.removeFromFileList = {}
        self.database.rollback()
        self.runPostImport()

    def _import_hh_file(self, fpdbfile):
        """Function for actual import of a hh file
            This is now an internal function that should not be called directly."""

        (stored, duplicates, partial, errors, ttime) = (0, 0, 0, 0, time())

        # Load filter, process file, pass returned filename to import_fpdb_file
        log.info(_("Converting %s") % fpdbfile.path)
            
        filter_name = fpdbfile.site.filter_name
        mod = __import__(fpdbfile.site.hhc_fname)
        obj = getattr(mod, filter_name, None)
        if callable(obj):
            
            if fpdbfile.path in self.pos_in_file:  idx = self.pos_in_file[fpdbfile.path]
            else: self.pos_in_file[fpdbfile.path], idx = 0, 0
                
            hhc = obj( self.config, in_path = fpdbfile.path, index = idx, autostart=False
                      ,starsArchive = fpdbfile.archive
                      ,ftpArchive   = fpdbfile.archive
                      ,sitename     = fpdbfile.site.name)
            hhc.setAutoPop(self.mode=='auto')
            hhc.start()
            
            self.pos_in_file[file] = hhc.getLastCharacterRead()
            #Tally the results
            partial  = getattr(hhc, 'numPartial')
            errors   = getattr(hhc, 'numErrors')
            stored   = getattr(hhc, 'numHands')
            stored -= errors
            stored -= partial
            
            if stored > 0:
                if self.caller: self.progressNotify()
                handlist = hhc.getProcessedHands()
                self.database.resetBulkCache(True)
                self.pos_in_file[fpdbfile.path] = hhc.getLastCharacterRead()
                (phands, ahands, ihands, to_hud) = ([], [], [], [])
                self.database.resetBulkCache()
                
                ####Lock Placeholder####
                for hand in handlist:
                    hand.prepInsert(self.database, printtest = self.settings['testData'])
                    ahands.append(hand)
                self.database.commit()
                ####Lock Placeholder####
                
                for hand in ahands:
                    hand.assembleHand()
                    phands.append(hand)
                
                ####Lock Placeholder####
                backtrack = False
                id = self.database.nextHandId()
                sctimer, ihtimer, cctimer, pctimer, hctimer = 0,0,0,0,0
                for i in range(len(phands)):
                    doinsert = len(phands)==i+1
                    hand = phands[i]
                    try:
                        id = hand.getHandId(self.database, id)
                        stime = time()
                        hand.updateSessionsCache(self.database, None, doinsert)
                        sctimer += time() - stime
                        stime = time()
                        hand.insertHands(self.database, fpdbfile.fileId, doinsert, self.settings['testData'])
                        ihtimer = time() - stime
                        stime = time()
                        hand.updateCardsCache(self.database, None, doinsert)
                        cctimer = time() - stime
                        stime = time()
                        hand.updatePositionsCache(self.database, None, doinsert) 
                        pctimer = time() - stime
                        stime = time()
                        hand.updateHudCache(self.database, doinsert)
                        hctimer = time() - stime
                        ihands.append(hand)
                        to_hud.append(hand.dbid_hands)
                    except FpdbHandDuplicate:
                        duplicates += 1
                        if (doinsert and ihands): backtrack = True
                    except:
                        error_trace = ''
                        formatted_lines = traceback.format_exc().splitlines()
                        for line in formatted_lines:
                            error_trace += line
                        tmp = hand.handText[0:200]
                        log.error(_("Importer._import_hh_file: '%r' Fatal error: '%r'") % (file, error_trace))
                        log.error(_("'%r'") % tmp)
                        if (doinsert and ihands): backtrack = True
                    if backtrack: #If last hand in the file is a duplicate this will backtrack and insert the new hand records
                        hand = ihands[-1]
                        hp, hero = hand.handsplayers, hand.hero
                        hand.hero, self.database.hbulk, hand.handsplayers  = 0, self.database.hbulk[:-1], [] #making sure we don't insert data from this hand
                        hand.updateSessionsCache(self.database, None, doinsert)
                        hand.insertHands(self.database, fpdbfile.fileId, doinsert, self.settings['testData'])
                        hand.updateCardsCache(self.database, None, doinsert)
                        hand.updatePositionsCache(self.database, None, doinsert)
                        hand.updateHudCache(self.database, doinsert)
                        hand.handsplayers, hand.hero = hp, hero
                #log.debug("DEBUG: hand.updateSessionsCache: %s" % (t5tot))
                #log.debug("DEBUG: hand.insertHands: %s" % (t6tot))
                #log.debug("DEBUG: hand.updateHudCache: %s" % (t7tot))
                self.database.commit()
                ####Lock Placeholder####
                
                for i in range(len(ihands)):
                    doinsert = len(ihands)==i+1
                    hand = ihands[i]
                    hand.insertHandsPlayers(self.database, doinsert, self.settings['testData'])
                    hand.insertHandsActions(self.database, doinsert, self.settings['testData'])
                    hand.insertHandsStove(self.database, doinsert)
                self.database.commit()

                #pipe the Hands.id out to the HUD
                if self.callHud:
                    for hid in to_hud:
                        try:
                            print _("fpdb_import: sending hand to hud"), hid, "pipe =", self.caller.pipe_to_hud
                            self.caller.pipe_to_hud.stdin.write("%s" % (hid) + os.linesep)
                        except IOError, e:
                            log.error(_("Failed to send hand to HUD: %s") % e)
                # Really ugly hack to allow testing Hands within the HHC from someone
                # with only an Importer objec
                if self.settings['cacheHHC']:
                    self.handhistoryconverter = hhc
        elif (self.mode=='auto'):
            return (0, 0, partial, errors, time() - ttime)
        
        stored -= duplicates
        
        if stored>0 and ihands[0].gametype['type']=='tour':
            if hhc.summaryInFile:
                fpdbfile.ftype = "both"

        ttime = time() - ttime
        return (stored, duplicates, partial, errors, ttime)
    
    def autoSummaryGrab(self, force = False):
        for f, fpdbfile in self.filelist.items():
            stat_info = os.stat(f)
            if ((time() - stat_info.st_mtime)> 300 or force) and fpdbfile.ftype == "both":
                self._import_summary_file(fpdbfile)
                fpdbfile.ftype = "hh"

    def _import_summary_file(self, fpdbfile):
        (stored, duplicates, partial, errors, ttime) = (0, 0, 0, 0, time())
        mod = __import__(fpdbfile.site.summary)
        obj = getattr(mod, fpdbfile.site.summary, None)
        if callable(obj):
            if self.caller: self.progressNotify()
            errors = 0
            imported = 0

            foabs = obj.readFile(obj, fpdbfile.path)
            if len(foabs) == 0:
                log.error("Found: '%s' with 0 characters... skipping" % fpbdfile.path)
                return (0, 1) # File had 0 characters
            re_Split = obj.getSplitRe(obj,foabs[:1000])
            summaryTexts = re.split(re_Split, foabs)

            # The summary files tend to have a header or footer
            # Remove the first and/or last entry if it has < 100 characters
            if not len(summaryTexts[0]):
                del summaryTexts[0]

            if len(summaryTexts)>1:
                if len(summaryTexts[-1]) <= 100:
                    summaryTexts.pop()
                    log.warn(_("Importer._import_summary_file: Removing text < 100 characters from end of file"))

                if len(summaryTexts[0]) <= 130:
                    del summaryTexts[0]
                    log.warn(_("Importer._import_summary_file: Removing text < 100 characters from start of file"))

            ####Lock Placeholder####
            for j, summaryText in enumerate(summaryTexts, start=1):
                doinsert = len(summaryTexts)==j
                try:
                    conv = obj(db=self.database, config=self.config, siteName=fpdbfile.site.name, summaryText=summaryText, in_path = fpdbfile.path)
                    self.database.resetBulkCache(False)
                    conv.insertOrUpdate(printtest = self.settings['testData'])
                except FpdbParseError, e:
                    log.error(_("Summary import parse error in file: %s") % fpdbfile.path)
                    errors += 1
                if j != 1:
                    print _("Finished importing %s/%s tournament summaries") %(j, len(summaryTexts))
                imported = j
            ####Lock Placeholder####

        ttime = time() - ttime
        return (imported - errors, duplicates, partial, errors, ttime)

    def progressNotify(self):
        "A callback to the interface while events are pending"
        while gtk.events_pending():
            gtk.main_iteration(False)
        
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
        
        self.handcount.set_text(_("Database Statistics") + " - " + _("Number of Hands:") + " " + handcount)
        
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

