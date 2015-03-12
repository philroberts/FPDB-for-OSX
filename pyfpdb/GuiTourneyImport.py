#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
import os
import sys
from time import time
import traceback
import datetime
import codecs
import re

#    fpdb/FreePokerTools modules
import Configuration
import Database
import Options
from Exceptions import FpdbParseError

import logging
if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")


class GuiTourneyImport():
    def progressNotify(self):
        "A callback to the interface while events are pending"
        while gtk.events_pending():
            gtk.main_iteration(False)


    def load_clicked(self, widget, data=None):
        stored = None
        dups = None
        partial = None
        errs = None
        ttime = None

        if self.settings['global_lock'].acquire(wait=False, source="GuiTourneyImport"):
            selected = self.chooser.get_filenames()

            sitename = self.cbfilter.get_model()[self.cbfilter.get_active()][0]

            for selection in selected:
                self.importer.addImportFileOrDir(selection, site = sitename)
            starttime = time()
            (stored, errs) = self.importer.runImport()

            ttime = time() - starttime
            if ttime == 0:
                ttime = 1
            print _('Tourney import done: Stored: %d, Errors: %d in %s seconds - %.0f/sec')\
                     % (stored, errs, ttime, (stored+0.0) / ttime)
            self.importer.clearFileList()

            self.settings['global_lock'].release()
        else:
            print _("tourney import aborted - global lock not available")

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.vbox

    def __init__(self, settings, config, sql = None, parent = None):
        self.settings = settings
        self.config = config
        self.parent = parent

        self.importer = SummaryImporter(config, sql, parent, self)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.show()

        self.chooser = gtk.FileChooserWidget()
        self.chooser.set_filename(self.settings['bulkImport-defaultPath'])
        self.chooser.set_select_multiple(True)
        self.chooser.set_show_hidden(True)
        self.vbox.add(self.chooser)
        self.chooser.show()

#    Table widget to hold the settings
        self.table = gtk.Table(rows=5, columns=5, homogeneous=False)
        self.vbox.add(self.table)
        self.table.show()

#    label - tsc 
        self.lab_filter = gtk.Label(_("Site filter:"))
        self.table.attach(self.lab_filter, 1, 2, 2, 3, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_filter.show()
        self.lab_filter.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_filter.set_alignment(1.0, 0.5)

#    ComboBox - filter
        self.cbfilter = gtk.combo_box_new_text()
        disabled_sites = []                                # move disabled sites to bottom of list
        for w in self.config.hhcs:
            print "%s = '%s'" %(w, self.config.hhcs[w].summaryImporter)
            try:
                # Include sites with a tourney summary importer, and enabled
                if self.config.supported_sites[w].enabled and self.config.hhcs[w].summaryImporter != '':
                    self.cbfilter.append_text(w)
                else:
                    disabled_sites.append(w)
            except: # self.supported_sites[w] may not exist if hud_config is bad
                disabled_sites.append(w)
        for w in disabled_sites:
            if self.config.hhcs[w].summaryImporter != '':
                self.cbfilter.append_text(w)
        self.cbfilter.set_active(0)
        self.table.attach(self.cbfilter, 2, 3, 2, 3, xpadding=10, ypadding=1,
                          yoptions=gtk.SHRINK)
        self.cbfilter.show()

#    button - Import
        self.load_button = gtk.Button(_('Bulk Import'))  # todo: rename variables to import too
        self.load_button.connect('clicked', self.load_clicked,
                                 _('Import clicked'))
        self.table.attach(self.load_button, 2, 3, 4, 5, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.load_button.show()

#    label - spacer (keeps rows 3 & 5 apart)
        self.lab_spacer = gtk.Label()
        self.table.attach(self.lab_spacer, 3, 5, 3, 4, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_spacer.show()

class SummaryImporter:
    def __init__(self, config, sql = None, parent = None, caller = None):
        self.config     = config
        self.database   = Database.Database(self.config)
        self.sql        = sql
        self.parent     = parent
        self.caller     = caller
        self.settings   = { 'testData':False }

        self.filelist   = {}
        self.dirlist    = {}

        self.updatedsize = {}
        self.updatedtime = {}

    def setPrintTestData(self, value):
        self.settings['testData'] = value

    def addImportFile(self, filename, site = "default", tsc = "passthrough"):
        if filename in self.filelist or not os.path.exists(filename):
            print "DEBUG: addImportFile: File exists, or path non-existent"
            return
        self.filelist[filename] = [site] + [tsc]

    def addImportDirectory(self,dir,monitor=False, site="default", tsc="passthrough"):
        if os.path.isdir(dir):
            if monitor == True:
                self.monitor = True
                self.dirlist[site] = [dir] + [tsc]

            for file in os.listdir(dir):
                self.addImportFile(os.path.join(dir, file), site, tsc)
        else:
            log.warning(_("Attempted to add non-directory '%s' as an import directory") % str(dir))

    def addImportFileOrDir(self, inputPath, site = "PokerStars"):
        
        #for windows platform, force os.walk variable to be unicode
        # see fpdb-main post 9th July 2011
        
        if self.config.posix:
            pass
        else:
            inputPath = unicode(inputPath)
            
        tsc = self.config.hhcs[site].summaryImporter
        if os.path.isdir(inputPath):
            for subdir in os.walk(inputPath):
                for file in subdir[2]:
                    self.addImportFile(os.path.join(subdir[0], file),
                                       site=site, tsc=tsc)
        else:
            self.addImportFile(inputPath, site=site, tsc=tsc)

    def runImport(self):
        start = datetime.datetime.now()
        starttime = time()
        log.info(_("Tourney Summary Import started at %s - %d files to import.") % (start, len(self.filelist)))

        total_errors = 0
        total_imported = 0
        ProgressDialog = ProgressBar(len(self.filelist), self.parent)
        for f in self.filelist:
            ProgressDialog.progress_update(f, str(total_imported))
            if self.parent: self.caller.progressNotify()
            if os.path.exists(f):
                (site, tsc) = self.filelist[f]
                imported, errs = self.importFile(f, tsc, site)
                total_errors += errs
                total_imported += imported
            else:
                print "Unable to access: %s" % f
        del ProgressDialog
        self.database.cleanUpTourneyTypes()
        return (total_imported, total_errors)
            

    def runUpdated(self):
        pass

    def importFile(self, filename, tsc = "PokerStarsSummary", site = "PokerStars"):
        mod = __import__(tsc)
        obj = getattr(mod, tsc, None)
        if callable(obj):
            errors = 0
            imported = 0

            foabs = obj.readFile(obj, filename)
            if len(foabs) == 0:
                log.error("Found: '%s' with 0 characters... skipping" % filename)
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
                    log.warn(_("TourneyImport: Removing text < 100 characters from end of file"))
    
                if len(summaryTexts[0]) <= 130:
                    del summaryTexts[0]
                    log.warn(_("TourneyImport: Removing text < 100 characters from start of file"))

            ####Lock Placeholder####
            for j, summaryText in enumerate(summaryTexts, start=1):
                doinsert = len(summaryTexts)==j
                try:
                    conv = obj(db=self.database, config=self.config, siteName=site, summaryText=summaryText, in_path = filename)
                    self.database.resetBulkCache(False)
                    conv.insertOrUpdate(printtest = self.settings['testData'])
                except FpdbParseError, e:
                    log.error(_("Tourney import parse error in file: %s") % filename)
                    errors += 1
                if j != 1:
                    print _("Finished importing %s/%s tournament summaries") %(j, len(summaryTexts))
                imported = j
            ####Lock Placeholder####
        return (imported - errors, errors)

    def clearFileList(self):
        self.updatedsize = {}
        self.updatetime = {}
        self.filelist = {}

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


    def progress_update(self, file, count):
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

        self.count.set_text(_("Number of Tourneys:") + " " + count)

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

        self.count = gtk.Label()
        align.add(self.count)
        self.count.show()

        align = gtk.Alignment(0, 0, 0, 0)
        vbox.pack_start(align, False, True, 0)
        align.show()

        self.progresstext = gtk.Label()
        self.progresstext.set_line_wrap(True)
        self.progresstext.set_selectable(True)
        align.add(self.progresstext)
        self.progresstext.show()

        self.progress.show()

def usage():
    print _("USAGE:")
    print "./GuiTourneyImport.py -k <Site> -f <" + _("Filename") + ">"
    print "./GuiTourneyImport.py -k PokerStars -f <" + _("Filename") + ">"
    print "./GuiTourneyImport.py -k 'Full Tilt Poker' -f <" + _("Filename") + ">"

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    import SQL
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        usage()
        sys.exit(0)

    if options.hhc == "PokerStarsToFpdb":
        print _("Need to define a converter")
        usage()
        exit(0)

    config = Configuration.Config("HUD_config.test.xml")
    sql = SQL.Sql(db_server = 'sqlite')

    if options.filename == None:
        print _("Need a filename to import")
        usage()
        exit(0)

    importer = SummaryImporter(config, sql, None, None)

    importer.addImportFileOrDir(options.filename, site = options.hhc)
    if options.testData:
        importer.setPrintTestData(True)
    starttime = time()
    (stored, errs) = importer.runImport()

    ttime = time() - starttime
    if ttime == 0:
        ttime = 1
    print _('Tourney import done: Stored: %d, Errors: %d in %s seconds - %.0f/sec')\
                     % (stored, errs, ttime, (stored+0.0) / ttime)
    importer.clearFileList()

    


if __name__  == '__main__':
    sys.exit(main())
