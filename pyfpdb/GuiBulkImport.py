#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2008 Steffen Jobbagy-Felso
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# In the "official" distribution you can find the license in
# agpl-3.0.txt in the docs folder of the package.

#    Standard Library modules
import os
import sys
from time import time
from optparse import OptionParser

#    pyGTK modules
import pygtk
pygtk.require('2.0')
import gtk

#    fpdb/FreePokerTools modules
import fpdb_simple
import fpdb_import
import fpdb_db
import Configuration

class GuiBulkImport():

    def import_dir(self):
        """imports a directory, non-recursive. todo: move this to fpdb_import so CLI can use it"""

        self.path = self.inputFile
        self.importer.addImportDirectory(self.path)
        self.importer.setCallHud(False)
        starttime = time()
        if not self.importer.settings['threads'] > 1:
            (stored, dups, partial, errs, ttime) = self.importer.runImport()
            print 'GuiBulkImport.import_dir done: Stored: %d Duplicates: %d Partial: %d Errors: %d in %s seconds - %d/sec'\
                 % (stored, dups, partial, errs, ttime, stored / ttime)
        else:
            self.importer.RunImportThreaded()

    def load_clicked(self, widget, data=None):
#    get the dir to import from the chooser
        self.inputFile = self.chooser.get_filename()

#    get the import settings from the gui and save in the importer
        self.importer.setHandCount(int(self.spin_hands.get_text()))
        self.importer.setMinPrint(int(self.spin_hands.get_text()))
        self.importer.setQuiet(self.chk_st_st.get_active())
        self.importer.setFailOnError(self.chk_fail.get_active())
        self.importer.setThreads(int(self.spin_threads.get_text()))
        self.importer.setHandsInDB(self.n_hands_in_db)
        cb_model = self.cb_dropindexes.get_model()
        cb_index = self.cb_dropindexes.get_active()
        if cb_index:
            self.importer.setDropIndexes(cb_model[cb_index][0])
        else:
            self.importer.setDropIndexes("auto")
        hhc=self.cbfilter.get_model()[self.cbfilter.get_active()][0]
        self.lab_info.set_text("Importing")
        
        self.importer.addBulkImportImportFileOrDir(self.inputFile,filter=hhc)
        self.importer.setCallHud(False)
        starttime = time()
        (stored, dups, partial, errs, ttime) = self.importer.runImport()
        print 'GuiBulkImport.import_dir done: Stored: %d \tDuplicates: %d \tPartial: %d \tErrors: %d in %s seconds - %d/sec'\
             % (stored, dups, partial, errs, ttime, stored / ttime)
        self.importer.clearFileList()

        self.lab_info.set_text("Import finished")

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.vbox

    def __init__(self, db, settings, config):
        self.db = db # this is an instance of fpdb_db
        self.settings = settings
        self.config = config
        self.importer = fpdb_import.Importer(self, self.settings,
                config)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.show()

        self.chooser = gtk.FileChooserWidget()
        self.chooser.set_filename(self.settings['bulkImport-defaultPath'])
        self.vbox.add(self.chooser)
        self.chooser.show()

#    Table widget to hold the settings
        self.table = gtk.Table(rows = 3, columns = 5, homogeneous = False)
        self.vbox.add(self.table)
        self.table.show()

#    checkbox - print start/stop?
        self.chk_st_st = gtk.CheckButton('Print Start/Stop Info')
        self.table.attach(self.chk_st_st, 0, 1, 0, 1, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.chk_st_st.show()
        self.chk_st_st.set_active(True)

#    label - status
        self.lab_status = gtk.Label("Hands/status print:")
        self.table.attach(self.lab_status, 1, 2, 0, 1, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_status.show()
        self.lab_status.set_justify(gtk.JUSTIFY_RIGHT)

#    spin button - status
        status_adj = gtk.Adjustment(value=100, lower=0, upper=300, step_incr=10, page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_status = gtk.SpinButton(adjustment=status_adj, climb_rate=0.0, digits=0)
        self.table.attach(self.spin_status, 2, 3, 0, 1, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.spin_status.show()

#    label - threads
        self.lab_threads = gtk.Label("Number of threads:")
        self.table.attach(self.lab_threads, 3, 4, 0, 1, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_threads.show()
        self.lab_threads.set_sensitive(False)
        self.lab_threads.set_justify(gtk.JUSTIFY_RIGHT)

#    spin button - threads
        threads_adj = gtk.Adjustment(value=0, lower=0, upper=10, step_incr=1, page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_threads = gtk.SpinButton(adjustment=threads_adj, climb_rate=0.0, digits=0)
        self.table.attach(self.spin_threads, 4, 5, 0, 1, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.spin_threads.show()
        self.spin_threads.set_sensitive(False)

#    checkbox - fail on error?
        self.chk_fail = gtk.CheckButton('Fail on error')
        self.table.attach(self.chk_fail, 0, 1, 1, 2, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.chk_fail.show()

#    label - hands
        self.lab_hands = gtk.Label("Hands/file:")
        self.table.attach(self.lab_hands, 1, 2, 1, 2, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_hands.show()
        self.lab_hands.set_justify(gtk.JUSTIFY_RIGHT)

#    spin button - hands to import
        hands_adj = gtk.Adjustment(value=0, lower=0, upper=10, step_incr=1, page_incr=1, page_size=0) #not sure what upper value should be!
        self.spin_hands = gtk.SpinButton(adjustment=hands_adj, climb_rate=0.0, digits=0)
        self.table.attach(self.spin_hands, 2, 3, 1, 2, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.spin_hands.show()

#    label - drop indexes
        self.lab_drop = gtk.Label("Drop indexes:")
        self.table.attach(self.lab_drop, 3, 4, 1, 2, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_drop.show()
        self.lab_drop.set_justify(gtk.JUSTIFY_RIGHT)

#    ComboBox - drop indexes
        self.cb_dropindexes = gtk.combo_box_new_text()
        self.cb_dropindexes.append_text('auto')
        self.cb_dropindexes.append_text("don't drop")
        self.cb_dropindexes.append_text('drop')
        self.cb_dropindexes.set_active(0)
        self.table.attach(self.cb_dropindexes, 4, 5, 1, 2, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.cb_dropindexes.show()

#    label - filter
        self.lab_filter = gtk.Label("Site filter:")
        self.table.attach(self.lab_filter, 2, 3, 2, 3, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_filter.show()
        self.lab_filter.set_justify(gtk.JUSTIFY_RIGHT)

#    ComboBox - filter
        self.cbfilter = gtk.combo_box_new_text()
        self.cbfilter.append_text("passthrough")
        self.cbfilter.append_text("BetfairToFpdb")
        self.cbfilter.append_text("EverleafToFpdb")
        self.cbfilter.append_text("FulltiltToFpdb")
        self.cbfilter.append_text("PokerStarsToFpdb")
        self.cbfilter.set_active(0)
        self.table.attach(self.cbfilter, 3, 4, 2, 3, xpadding = 10, ypadding = 0, yoptions=gtk.SHRINK)
        self.cbfilter.show()

#    label - info
        self.lab_info = gtk.Label()
        self.table.attach(self.lab_info, 0, 4, 2, 3, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.lab_info.show()

#    button - Import
        self.load_button = gtk.Button('Import')  # todo: rename variables to import too
        self.load_button.connect('clicked', self.load_clicked,
                                 'Import clicked')
        self.table.attach(self.load_button, 4, 5, 2, 3, xpadding = 0, ypadding = 0, yoptions=gtk.SHRINK)
        self.load_button.show()

#    see how many hands are in the db and adjust accordingly
        tcursor = db.db.cursor()
        tcursor.execute("Select count(1) from Hands;")
        row = tcursor.fetchone()
        tcursor.close()
        self.n_hands_in_db = row[0]
        if self.n_hands_in_db == 0:
            self.cb_dropindexes.set_active(2)
            self.cb_dropindexes.set_sensitive(False)
            self.lab_drop.set_sensitive(False)

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument.
>>>import GuiBulkImport
>>>GuiBulkImport.main("-f ~/data/hands")"""
    if argv is None:
        argv = sys.argv[1:]
    else:
        argv = argv.split(" ")

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", metavar="FILE", default=None,
                    help="Input file in quiet mode")
    parser.add_option("-q", "--quiet", action="store_false", dest="gui", default=True,
                    help="don't start gui; deprecated (just give a filename with -f).")
    parser.add_option("-c", "--convert", dest="filtername", default="passthrough", metavar="FILTER",
                    help="Conversion filter (*passthrough, FullTiltToFpdb, PokerStarsToFpdb, EverleafToFpdb)")
    parser.add_option("-x", "--failOnError", action="store_true", default=False,
                    help="If this option is passed it quits when it encounters any error")
    parser.add_option("-m", "--minPrint", "--status", dest="minPrint", default="0", type="int",
                    help="How often to print a one-line status report (0 (default) means never)")
    (options, sys.argv) = parser.parse_args(args = argv)

    config = Configuration.Config()
    db = fpdb_db.fpdb_db()

    settings = {}
    settings['minPrint'] = options.minPrint
    if os.name == 'nt': settings['os'] = 'windows'
    else:               settings['os'] = 'linuxmac'

    settings.update(config.get_db_parameters('fpdb'))
    settings.update(config.get_tv_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    if not options.gui:
        print """-q is deprecated. Just use "-f filename" instead"""
        # This is because -q on its own causes an error, so -f is necessary and sufficient for cmd line use
    if not options.filename:
        i = GuiBulkImport(db, settings, config)
        main_window = gtk.Window()
        main_window.connect('destroy', destroy)
        main_window.add(i.vbox)
        main_window.show()
        gtk.main()
    else:
        #Do something useful
        importer = fpdb_import.Importer(False,settings, config) 
        importer.setDropIndexes("auto")
        importer.setFailOnError(options.failOnError)
        importer.addBulkImportImportFileOrDir(os.path.expanduser(options.filename), filter=options.filtername)
        importer.setCallHud(False)
        importer.runImport()
        importer.clearFileList()


if __name__ == '__main__':
    sys.exit(main())

