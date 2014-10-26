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

import Queue

from PyQt5.QtGui import (QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QHBoxLayout, QRadioButton,
                             QTableView, QVBoxLayout, QWidget)

import os
import traceback
import logging
from itertools import groupby
from functools import partial
import Configuration
if __name__ == "__main__":
    Configuration.set_logfile("fpdb-log.txt")
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("logview")

MAX_LINES = 100000         # max lines to display in window
EST_CHARS_PER_LINE = 150   # used to guesstimate number of lines in log file
LOGFILES = [ [ _('Fpdb Errors'),        'fpdb-errors.txt',   False, 'log']  # label, filename, start value, path
           , [ _('Fpdb Log'),           'fpdb-log.txt',      True,  'log']
           , [ _('HUD Errors'),         'HUD-errors.txt',    False, 'log']
           , [ _('HUD Log'),            'HUD-log.txt',       False, 'log']
           , [ _('fpdb.exe log'),       'fpdb.exe.log',      False, 'pyfpdb']
           , [ _('HUD_main.exe Log'),   'HUD_main.exe.log ', False, 'pyfpdb']
           ]

class GuiLogView(QWidget):
    def __init__(self, config, mainwin, closeq):
        QWidget.__init__(self)
        self.config = config
        self.main_window = mainwin
        self.closeq = closeq

        self.logfile = os.path.join(self.config.dir_log, LOGFILES[1][1])

        self.resize(700, 400)

        self.setLayout(QVBoxLayout())

        self.liststore = QStandardItemModel(0, 4)
        self.listview = QTableView()
        self.listview.setModel(self.liststore)
        self.listview.setSelectionBehavior(QTableView.SelectRows)
        self.listview.setShowGrid(False)
        self.listview.verticalHeader().hide()
        self.layout().addWidget(self.listview)

        hb1 = QHBoxLayout()
        for logf in LOGFILES:
            rb = QRadioButton(logf[0], self)
            rb.setChecked(logf[2])
            rb.clicked.connect(partial(self.__set_logfile, filename=logf[0]))
            hb1.addWidget(rb)
            
        hb2 = QHBoxLayout()
        refreshbutton = QPushButton(_("Refresh"))
        refreshbutton.clicked.connect(self.refresh)
        hb2.addWidget(refreshbutton)
        
        copybutton = QPushButton(_("Copy to Clipboard"))
        copybutton.clicked.connect(self.copy_to_clipboard)
        hb2.addWidget(copybutton)
        
        self.layout().addLayout(hb1)
        self.layout().addLayout(hb2)

        self.loadLog()
        self.show()

    
    def copy_to_clipboard(self, checkState):
        text = ""
        for row, indexes in groupby(self.listview.selectedIndexes(), lambda i:i.row()):
            text += " ".join([i.data() for i in indexes]) + "\n"
        QApplication.clipboard().setText(text)
            
    def __set_logfile(self, checkState, filename):
        #print "w is", w, "file is", file, "active is", w.get_active()
        if checkState:
            for logf in LOGFILES:
                if logf[0] == filename:
                    if logf[3] == 'pyfpdb':
                        self.logfile = os.path.join(self.config.pyfpdb_path, logf[1])
                    else:
                        self.logfile = os.path.join(self.config.dir_log, logf[1])                        
            self.refresh(checkState)  # params are not used

    def dialog_response_cb(self, dialog, response_id):
        # this is called whether close button is pressed or window is closed
        self.closeq.put(self.__class__)
        dialog.destroy()

    def get_dialog(self):
        return self.dia

    def loadLog(self):
        self.liststore.clear()
        self.liststore.setHorizontalHeaderLabels([_("Date/Time"), _("Module"), _("Level"), _("Text")])

        # guesstimate number of lines in file
        if os.path.exists(self.logfile):
            stat_info = os.stat(self.logfile)
            lines = stat_info.st_size / EST_CHARS_PER_LINE

            # set startline to line number to start display from
            startline = 0
            if lines > MAX_LINES:
                # only display from startline if log file is large
                startline = lines - MAX_LINES

            l = 0
            for line in open(self.logfile):
                # example line in logfile format:
                # 2009-12-02 15:23:21,716 - config       DEBUG    config logger initialised
                l = l + 1
                if l > startline:
                    # NOTE selecting a sort column and then switching to a log file
                    # with several thousand rows will send cpu 100% for a prolonged period.
                    # reason is that the append() method seems to sort every record as it goes, rather than
                    # pulling in the whole file and sorting at the end.
                    # one fix is to check if a column sort has been selected, reset to date/time asc
                    # append all the rows and then reselect the required sort order.
                    # Note: there is no easy method available to revert the list to an "unsorted" state.
                    # always defaulting to date/time asc doesn't work, because some rows do not have date/time info
                    # and would end up sorted out of context.
                    tablerow = []
                    if len(line) > 49 and line[23:26] == ' - ' and line[34:39] == '     ':
                        tablerow = [line[0:23], line[26:32], line[39:46], line[48:].strip()]
                    else:
                        tablerow = ['', '', '', line.strip()]
                    tablerow = [QStandardItem(i) for i in tablerow]
                    for item in tablerow:
                        item.setEditable(False)
                    self.liststore.appendRow(tablerow)
            self.listview.resizeColumnsToContents()

    def refresh(self, checkState):
        self.loadLog()



if __name__=="__main__":
    config = Configuration.Config()

    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication([])
    main_window = QMainWindow()
    i = GuiLogView(config, main_window, None)
    main_window.show()
    main_window.resize(1400, 800)
    app.exec_()
