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
        if self.cbfilter.get_model()[self.cbfilter.get_active()][0] == (_("Please select site")):
            self.progressbar.set_text(_("Please select site"))
            return
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
                self.importer.setHandCount(int(self.spin_hands.get_text()))
                self.importer.setQuiet(self.chk_st_st.get_active())
                self.importer.setThreads(int(self.spin_threads.get_text()))
                self.importer.setHandsInDB(self.n_hands_in_db)
                self.importer.setMode('bulk')
                cb_model = self.cb_dropindexes.get_model()
                cb_index = self.cb_dropindexes.get_active()
#                 cb_hmodel = self.cb_drophudcache.get_model()
#                 cb_hindex = self.cb_drophudcache.get_active()

                #self.lab_info.set_markup('<span foreground="blue">Importing ...</span>') # uses pango markup!

                if cb_index:
                    self.importer.setDropIndexes(cb_model[cb_index][0])
                else:
                    self.importer.setDropIndexes("auto")

#                 if cb_hindex:
#                     self.importer.setDropHudCache(cb_hmodel[cb_hindex][0])
#                 else:
#                     self.importer.setDropHudCache("auto")
                #sitename = self.cbfilter.get_model()[self.cbfilter.get_active()][0]
                sitename = 'auto'

                #self.importer.setFailOnError(self.chk_fail.get_active())
                if self.is_archive.get_active():
                    if sitename == "PokerStars":
                        self.importer.setStarsArchive(True)
                    if sitename == "Full Tilt Poker":
                        self.importer.setFTPArchive(True)

                for selection in selected:
                    self.importer.addBulkImportImportFileOrDir(selection, site = sitename)
                self.importer.setCallHud(self.cb_testmode.get_active())
                self.importer.bHudTest = self.cb_testmode.get_active()
                starttime = time()
#                try:
                (stored, dups, partial, errs, ttime) = self.importer.runImport()
#                except:
#                    print "*** EXCEPTION DURING BULKIMPORT!!!"
#                    raise Exceptions.FpdbError
#                finally:
                gobject.source_remove(self.timer)

                ttime = time() - starttime
                if ttime == 0:
                    ttime = 1
                    
                completionMessage = _('Bulk import done: Stored: %d, Duplicates: %d, Partial: %d, Errors: %d, Time: %s seconds, Stored/second: %.0f')\
                    % (stored, dups, partial, errs, ttime, (stored+0.0) / ttime)
                print completionMessage
                log.info(completionMessage)

                self.importer.clearFileList()
                
                if self.n_hands_in_db == 0 and stored > 0:
                    self.cb_dropindexes.set_sensitive(True)
                    self.cb_dropindexes.set_active(0)
                    self.lab_drop.set_sensitive(True)
#                     self.cb_drophudcache.set_sensitive(True)
#                     self.cb_drophudcache.set_active(0)
#                    self.lab_hdrop.set_sensitive(True)

                self.progressbar.set_text(_("Import Complete"))
                self.progressbar.set_fraction(0)
            #except:
                #err = traceback.extract_tb(sys.exc_info()[2])[-1]
                #print "*** BulkImport Error: "+err[2]+"("+str(err[1])+"): "+str(sys.exc_info()[1])
            #self.settings['global_lock'].release()
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

#    Table widget to hold the settings
        self.table = gtk.Table(rows=5, columns=5, homogeneous=False)
        self.vbox.add(self.table)
        self.table.show()

#    checkbox - print start/stop?
        self.chk_st_st = gtk.CheckButton(_('Print Start/Stop Info'))
        self.table.attach(self.chk_st_st, 0, 1, 0, 1, xpadding=10, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.chk_st_st.show()
        self.chk_st_st.set_active(True)

#    label - status
        self.lab_status = gtk.Label(_("Hands/status print:"))
        self.table.attach(self.lab_status, 1, 2, 0, 1, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_status.show()
        self.lab_status.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_status.set_alignment(1.0, 0.5)

#    spin button - status
        status_adj = gtk.Adjustment(value=100, lower=0, upper=300, step_incr=10,
                                    page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_status = gtk.SpinButton(adjustment=status_adj, climb_rate=0.0,
                                          digits=0)
        self.table.attach(self.spin_status, 2, 3, 0, 1, xpadding=10, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.spin_status.show()

#    label - threads
        self.lab_threads = gtk.Label(_("Number of threads:"))
        self.table.attach(self.lab_threads, 3, 4, 0, 1, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_threads.show()
        if not self.allowThreads:
            self.lab_threads.set_sensitive(False)
        self.lab_threads.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_threads.set_alignment(1.0, 0.5)

#    spin button - threads
        threads_adj = gtk.Adjustment(value=0, lower=0, upper=32, step_incr=1,
                                     page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_threads = gtk.SpinButton(adjustment=threads_adj, climb_rate=0.0, digits=0)
        self.table.attach(self.spin_threads, 4, 5, 0, 1, xpadding=10, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.spin_threads.show()
        if not self.allowThreads:
            self.spin_threads.set_sensitive(False)

#    checkbox - archive file?
        self.is_archive = gtk.CheckButton(_('Archive File'))
        self.table.attach(self.is_archive, 0, 1, 1, 2, xpadding=10, ypadding=0, yoptions=gtk.SHRINK)
        self.is_archive.show()

#    label - hands
        self.lab_hands = gtk.Label(_("Hands/file:"))
        self.table.attach(self.lab_hands, 1, 2, 1, 2, xpadding=0, ypadding=0, yoptions=gtk.SHRINK)
        self.lab_hands.show()
        self.lab_hands.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_hands.set_alignment(1.0, 0.5)

#    spin button - hands to import
        hands_adj = gtk.Adjustment(value=0, lower=0, upper=10, step_incr=1,
                                   page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_hands = gtk.SpinButton(adjustment=hands_adj, climb_rate=0.0, digits=0)
        self.table.attach(self.spin_hands, 2, 3, 1, 2, xpadding=10, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.spin_hands.show()

#    label - drop indexes
        self.lab_drop = gtk.Label(_("Drop indexes:"))
        self.table.attach(self.lab_drop, 3, 4, 1, 2, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_drop.show()
        self.lab_drop.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_drop.set_alignment(1.0, 0.5)

#    ComboBox - drop indexes
        self.cb_dropindexes = gtk.combo_box_new_text()
        self.cb_dropindexes.append_text(_('auto'))
        self.cb_dropindexes.append_text(_("don't drop"))
        self.cb_dropindexes.append_text(_('drop'))
        self.cb_dropindexes.set_active(0)
        self.table.attach(self.cb_dropindexes, 4, 5, 1, 2, xpadding=10,
                          ypadding=0, yoptions=gtk.SHRINK)
        self.cb_dropindexes.show()

        self.cb_testmode = gtk.CheckButton(_('HUD Test mode'))
        self.table.attach(self.cb_testmode, 0, 1, 2, 3, xpadding=10, ypadding=0, yoptions=gtk.SHRINK)
        self.cb_testmode.show()

#    label - filter
        self.lab_filter = gtk.Label(_("Site filter:"))
        self.table.attach(self.lab_filter, 1, 2, 2, 3, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
        self.lab_filter.show()
        self.lab_filter.set_justify(gtk.JUSTIFY_RIGHT)
        self.lab_filter.set_alignment(1.0, 0.5)

#    ComboBox - filter
        self.cbfilter = gtk.combo_box_new_text()
        disabled_sites = []                                # move disabled sites to bottom of list
        #self.cbfilter.append_text(_("Please select site"))
        self.cbfilter.append_text("auto")
        #for w in self.config.hhcs:
        #    try:
        #        if self.config.supported_sites[w].enabled: # include enabled ones first
        #            print w
        #            self.cbfilter.append_text(w)
        #        else:
        #            disabled_sites.append(w)
        #    except: # self.supported_sites[w] may not exist if hud_config is bad
        #        disabled_sites.append(w)
        #for w in disabled_sites:                           # then disabled ones
        #    print w
        #    self.cbfilter.append_text(w)

        self.cbfilter.set_active(0)
        self.table.attach(self.cbfilter, 2, 3, 2, 3, xpadding=10, ypadding=1,
                          yoptions=gtk.SHRINK)
        self.lab_threads.set_sensitive(False) # grey out
        self.cbfilter.show()

# #    label - drop hudcache
#         self.lab_hdrop = gtk.Label(_("Drop HudCache:"))
#         self.table.attach(self.lab_hdrop, 3, 4, 2, 3, xpadding=0, ypadding=0,
#                           yoptions=gtk.SHRINK)
#         self.lab_hdrop.show()
#         self.lab_hdrop.set_justify(gtk.JUSTIFY_RIGHT)
#         self.lab_hdrop.set_alignment(1.0, 0.5)
# 
# #    ComboBox - drop hudcache
#         self.cb_drophudcache = gtk.combo_box_new_text()
#         self.cb_drophudcache.append_text(_('auto'))
#         self.cb_drophudcache.append_text(_("don't drop"))
#         self.cb_drophudcache.append_text(_('drop'))
#         self.cb_drophudcache.set_active(0)
#         self.table.attach(self.cb_drophudcache, 4, 5, 2, 3, xpadding=10,
#                           ypadding=0, yoptions=gtk.SHRINK)
#         self.cb_drophudcache.show()

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

#    label - info
#        self.lab_info = gtk.Label()
#        self.table.attach(self.lab_info, 3, 5, 4, 5, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
#        self.lab_info.show()
        self.progressbar = gtk.ProgressBar()
        self.table.attach(self.progressbar, 3, 5, 4, 5, xpadding=0, ypadding=0,
                          yoptions=gtk.SHRINK)
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
        if self.n_hands_in_db == 0:
            self.cb_dropindexes.set_active(2)
            self.cb_dropindexes.set_sensitive(False)
            self.lab_drop.set_sensitive(False)
#             self.cb_drophudcache.set_active(2)
#             self.cb_drophudcache.set_sensitive(False)
#            self.lab_hdrop.set_sensitive(False)

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
