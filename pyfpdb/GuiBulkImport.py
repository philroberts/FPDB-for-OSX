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
import os
import sys
from time import time
from optparse import OptionParser
import traceback

#    pyGTK modules
import pygtk
pygtk.require('2.0')
import gtk
import gobject

#    fpdb/FreePokerTools modules
import Options
import Importer
import Configuration
import Exceptions

import logging
if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("importer")

class GuiBulkImport():

    # CONFIGURATION  -  update these as preferred:
    allowThreads = False  # set to True to try out the threads field

    def dopulse(self):
        self.progressbar.pulse()
        return True

    def load_clicked(self, widget, data=None):

        stored = None
        dups = None
        partial = None
        errs = None
        ttime = None
        # Does the lock acquisition need to be more sophisticated for multiple dirs?
        # (see comment above about what to do if pipe already open)
        if self.settings['global_lock'].acquire(wait=False, source="GuiBulkImport"):   # returns false immediately if lock not acquired
            #try:
                self.progressbar.set_text(_("Importing"))
                self.progressbar.pulse()
                while gtk.events_pending(): # see http://faq.pygtk.org/index.py?req=index for more hints (3.7)
                    gtk.main_iteration(False)
                self.timer = gobject.timeout_add(100, self.dopulse)

                #    get the dir to import from the chooser
                selected = self.chooser.get_filenames()

                #    get the import settings from the gui and save in the importer
                
                self.importer.setHandsInDB(self.n_hands_in_db)
                self.importer.setMode('bulk')

                sitename = 'auto'

 
                for selection in selected:
                    self.importer.addBulkImportImportFileOrDir(selection, site = sitename)
                self.importer.setCallHud(False)
                
                starttime = time()

                (stored, dups, partial, errs, ttime) = self.importer.runImport()

                gobject.source_remove(self.timer)

                ttime = time() - starttime
                if ttime == 0:
                    ttime = 1
                    
                completionMessage = _('Bulk import done: Stored: %d, Duplicates: %d, Partial: %d, Errors: %d, Time: %s seconds, Stored/second: %.0f')\
                    % (stored, dups, partial, errs, ttime, (stored+0.0) / ttime)
                print completionMessage
                log.info(completionMessage)

                self.importer.clearFileList()
                
                self.progressbar.set_text(_("Import Complete"))
                self.progressbar.set_fraction(0)
           
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

        self.importer = Importer.Importer(self, self.settings, config, sql, parent)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.show()

        self.chooser = gtk.FileChooserWidget()
        self.chooser.set_filename(self.settings['bulkImport-defaultPath'])
        self.chooser.set_select_multiple(True)
        self.chooser.set_show_hidden(True)
        self.vbox.add(self.chooser)
        self.chooser.show()

#    Table widget to hold the progress bar and load button
        #self.table = gtk.Table(rows=5, columns=5, homogeneous=False)
        self.table = gtk.Table(rows=2, columns=4, homogeneous=False)
        self.vbox.add(self.table)
        self.table.show()

#    label - spacer (fills in column one in table)
        self.lab_spacer = gtk.Label()
#         self.table.attach(self.lab_spacer, 3, 5, 3, 4, xpadding=0, ypadding=0,
#                           yoptions=gtk.SHRINK)
        self.table.attach(self.lab_spacer,1,2,1,2, xpadding=0, ypadding=0, yoptions=gtk.SHRINK)
        self.lab_spacer.show()

#    button - Import
        self.load_button = gtk.Button(_('_Bulk Import'))  # todo: rename variables to import too
        self.load_button.connect('clicked', self.load_clicked,
                                 _('Import clicked'))
#         self.table.attach(self.load_button, 2, 3, 4, 5, xpadding=0, ypadding=0,
#                           yoptions=gtk.SHRINK)
        self.table.attach(self.load_button, 2, 3, 1, 2, xpadding=0, ypadding=0, yoptions=gtk.SHRINK)
        self.load_button.show()

#    label - info

        self.progressbar = gtk.ProgressBar()
        self.table.attach(self.progressbar, 3, 4, 1, 2, xpadding=0, ypadding=0, yoptions=gtk.SHRINK)
        self.progressbar.set_text(_("Waiting..."))
        self.progressbar.set_fraction(0)
        self.progressbar.show()

#    see how many hands are in the db and adjust accordingly
        tcursor = self.importer.database.cursor
        tcursor.execute("Select count(1) from Hands")
        row = tcursor.fetchone()
        tcursor.close()
        self.importer.database.rollback()
        self.n_hands_in_db = row[0]

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    if argv is None:
        argv = sys.argv[1:]

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    Configuration.set_logfile("fpdb-log.txt")
    (options, argv) = Options.fpdb_options()

    if options.sitename:
        options.sitename = Options.site_alias(options.sitename)

    if options.usage == True:
        #Print usage examples and exit
        print _("USAGE:")
        sys.exit(0)

    Configuration.set_logfile("GuiBulkImport-log.txt")
    if options.config:
        config = Configuration.Config(options.config)
    else:
        config = Configuration.Config()

    settings = {}
    if os.name == 'nt': settings['os'] = 'windows'
    else:               settings['os'] = 'linuxmac'

    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    #Do something useful
    importer = Importer.Importer(False,settings, config, None)
    importer.addBulkImportImportFileOrDir(os.path.expanduser(options.filename))
    importer.setCallHud(False)
    if options.archive:
        importer.setStarsArchive(True)
        importer.setFTPArchive(True)
    if options.testData:
        importer.setPrintTestData(True)
    (stored, dups, partial, errs, ttime) = importer.runImport()
    importer.clearFileList()
    print(_('Bulk import done: Stored: %d, Duplicates: %d, Partial: %d, Errors: %d, Time: %s seconds, Stored/second: %.0f')\
                     % (stored, dups, partial, errs, ttime, (stored+0.0) / ttime))


if __name__ == '__main__':
    sys.exit(main())
