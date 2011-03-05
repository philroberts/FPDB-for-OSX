#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Carl Gherardi
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

#    pyGTK modules
import pygtk
pygtk.require('2.0')
import gtk
import gobject

#    fpdb/FreePokerTools modules
import Configuration
import Options
from Exceptions import FpdbParseError

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")


class GuiTourneyImport():

    def load_clicked(self, widget, data=None):
        print "DEBUG: load_clicked"
        stored = None
        dups = None
        partial = None
        errs = None
        ttime = None

        if self.settings['global_lock'].acquire(wait=False, source="GuiTourneyImport"):
            print "DEBUG: got global lock"
            #    get the dir to import from the chooser
            selected = self.chooser.get_filenames()
            print "DEBUG: Files selected: %s" % selected

            sitename = self.cbfilter.get_model()[self.cbfilter.get_active()][0]

            for selection in selected:
                self.importer.addImportFileOrDir(selection, site = sitename)
            starttime = time()
            (stored, errs) = self.importer.runImport()

            ttime = time() - starttime
            if ttime == 0:
                ttime = 1
            print _('GuiTourneyImport.load done: Stored: %d\tErrors: %d in %s seconds - %.0f/sec')\
                     % (stored, errs, ttime, (stored+0.0) / ttime)
            self.importer.clearFileList()

            self.settings['global_lock'].release()
        else:
            print _("bulk import aborted - global lock not available")

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.vbox

    def __init__(self, settings, config, sql = None, parent = None):
        self.settings = settings
        self.config = config
        self.parent = parent

        self.importer = SummaryImporter(config, sql, parent)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.show()

        self.chooser = gtk.FileChooserWidget()
        self.chooser.set_filename(self.settings['bulkImport-defaultPath'])
        self.chooser.set_select_multiple(True)
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
        self.load_button = gtk.Button(_('_Bulk Import'))  # todo: rename variables to import too
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
    def __init__(self, config, sql = None, parent = None):
        self.config     = config
        self.sql        = sql
        self.parent     = parent

        self.filelist   = {}
        self.dirlist    = {}

        self.updatedsize = {}
        self.updatedtime = {}

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
        tsc = self.config.hhcs[site].summaryImporter
        if os.path.isdir(inputPath):
            for subdir in os.walk(inputPath):
                for file in subdir[2]:
                    self.addImportFile(unicode(os.path.join(subdir[0], file),'utf-8'),
                                       site=site, tsc=tsc)
        else:
            self.addImportFile(unicode(inputPath,'utf-8'), site=site, tsc=tsc)
        pass

    def runImport(self):
        start = datetime.datetime.now()
        starttime = time()
        log.info(_("Tourney Summary Import started at %s - %d files to import.") % (start, len(self.filelist)))

        total_errors = 0
        total_imported = 0
        for f in self.filelist:
            (site, tsc) = self.filelist[f]
            imported, errs = self.importFile(f, tsc, site)
            total_errors += errs
            total_imported += imported
        return (total_imported, total_errors)
            

    def runUpdated(self):
        pass

    def importFile(self, filename, tsc = "PokerStarsSummary", site = "PokerStars"):
        mod = __import__(tsc)
        obj = getattr(mod, tsc, None)
        if callable(obj):
            foabs = self.readFile(obj, filename)
            summaryTexts = re.split(obj.re_SplitTourneys, foabs)

            # The summary files tend to have a header or footer
            # Remove the first and/or last entry if it has < 100 characters
            if len(summaryTexts[-1]) <= 100:
                summaryTexts.pop()
                log.warn(_("TourneyImport: Removing text < 100 characters from end of file"))

            if len(summaryTexts[0]) <= 130:
                del summaryTexts[0]
                log.warn(_("TourneyImport: Removing text < 100 characters from start of file"))

            print "Found %s summaries" %(len(summaryTexts))
            errors = 0
            imported = 0
            for j, summaryText in enumerate(summaryTexts, start=1):
                try:
                    conv = obj(db=None, config=self.config, siteName=site, summaryText=summaryText, builtFrom = "IMAP")
                except FpdbParseError, e:
                    errors += 1
                print _("Finished importing %s/%s tournament summaries") %(j, len(summaryTexts))
                imported = j
        return (imported - errors, errors)

    def clearFileList(self):
        self.updatedsize = {}
        self.updatetime = {}
        self.filelist = {}

    def readFile(self, tsc, filename):
        codepage = ["utf8", "utf16"]
        whole_file = None
        tsc.codepage

        for kodec in codepage:
            try:
                in_fh = codecs.open(filename, 'r', kodec)
                whole_file = in_fh.read()
                in_fh.close()
                break
            except UnicodeDecodeError, e:
                log.warn(_("GTI.readFile: '%s'") % e)
                pass

        return whole_file

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    import SQL
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        print _("USAGE:")
        sys.exit(0)

    if options.hhc == "PokerStarsToFpdb":
        print _("Need to define a converter")
        exit(0)

    config = Configuration.Config("HUD_config.test.xml")
    sql = SQL.Sql(db_server = 'sqlite')

    if options.filename == None:
        print _("Need a filename to import")
        exit(0)

    importer = SummaryImporter(config, sql, None)

    importer.addImportFileOrDir(options.filename, site = options.hhc)
    starttime = time()
    (stored, errs) = importer.runImport()

    ttime = time() - starttime
    if ttime == 0:
        ttime = 1
    print _('GuiTourneyImport.load done: Stored: %d\tErrors: %d in %s seconds - %.0f/sec')\
                     % (stored, errs, ttime, (stored+0.0) / ttime)
    importer.clearFileList()

    


if __name__  == '__main__':
    sys.exit(main())
