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

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog

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

class GuiBulkImport(QWidget):
    # CONFIGURATION  -  update these as preferred:
    allowThreads = False  # set to True to try out the threads field

    def load_clicked(self):
        stored = None
        dups = None
        partial = None
        skipped = None
        errs = None
        ttime = None
        # Does the lock acquisition need to be more sophisticated for multiple dirs?
        # (see comment above about what to do if pipe already open)
        if self.settings['global_lock'].acquire(wait=False, source="GuiBulkImport"):   # returns false immediately if lock not acquired
            #try:
                #    get the dir to import from the chooser
                selected = self.importDir.text()

                #    get the import settings from the gui and save in the importer
                
                self.importer.setHandsInDB(self.n_hands_in_db)
                self.importer.setMode('bulk')

                self.importer.addBulkImportImportFileOrDir(selected, site = 'auto')
                self.importer.setCallHud(False)
                
                starttime = time()

                (stored, dups, partial, skipped, errs, ttime) = self.importer.runImport()

                ttime = time() - starttime
                if ttime == 0:
                    ttime = 1
                    
                completionMessage = _('Bulk import done: Stored: %d, Duplicates: %d, Partial: %d, Skipped: %d, Errors: %d, Time: %s seconds, Stored/second: %.0f')\
                    % (stored, dups, partial, skipped, errs, ttime, (stored+0.0) / ttime)
                print completionMessage
                log.info(completionMessage)

                self.importer.clearFileList()
                
                self.settings['global_lock'].release()
        else:
            print _("bulk import aborted - global lock not available")

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.layout()

    def __init__(self, settings, config, sql = None, parent = None):
        QWidget.__init__(self, parent)
        self.settings = settings
        self.config = config

        self.importer = Importer.Importer(self, self.settings, config, sql, self)

        self.setLayout(QVBoxLayout())

        self.importDir = QLineEdit(self.settings['bulkImport-defaultPath'])
        hbox = QHBoxLayout()
        hbox.addWidget(self.importDir)
        self.chooseButton = QPushButton('Browse...')
        self.chooseButton.clicked.connect(self.browseClicked)
        hbox.addWidget(self.chooseButton)
        self.layout().addLayout(hbox)

        self.load_button = QPushButton(_('Bulk Import'))
        self.load_button.clicked.connect(self.load_clicked)
        self.layout().addWidget(self.load_button)

#    see how many hands are in the db and adjust accordingly
        tcursor = self.importer.database.cursor
        tcursor.execute("Select count(1) from Hands")
        row = tcursor.fetchone()
        tcursor.close()
        self.importer.database.rollback()
        self.n_hands_in_db = row[0]

    def browseClicked(self):
        newdir = QFileDialog.getExistingDirectory(self, caption=_("Please choose the path that you want to Auto Import"),
                                            directory=self.importDir.text())
        if newdir:
            self.importDir.setText(newdir)

if __name__ == '__main__':
    config = Configuration.Config()
    settings = {}
    if os.name == 'nt': settings['os'] = 'windows'
    else:               settings['os'] = 'linuxmac'

    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    import interlocks, string
    settings['global_lock'] = interlocks.InterProcessLock(name="fpdb_global_lock")
    settings['cl_options'] = string.join(sys.argv[1:])

    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication([])
    main_window = QMainWindow()
    main_window.setCentralWidget(GuiBulkImport(settings, config))
    main_window.show()
    main_window.resize(600, 100)
    app.exec_()
