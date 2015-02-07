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

import xml.dom.minidom
from xml.dom.minidom import Node

from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem)
from PyQt5.QtCore import Qt

import Configuration

rewrite = { 'general' : _('General'),                   'supported_databases' : _('Databases')
          , 'import'  : _('Import'),                    'hud_ui' : _('HUD')
          , 'supported_sites' : _('Sites'),             'supported_games' : _('Games')
          , 'popup_windows' : _('Popup Windows'),       'pu' : _('Window')
          , 'pu_name' : _('Popup Name'),                'pu_stat' : _('Stat')
          , 'pu_stat_name' : _('Stat Name')
          , 'aux_windows' : _('Auxiliary Windows'),     'aw stud_mucked' : _('Stud mucked')
          , 'aw mucked' : _('Mucked'),                  'hhcs' : _('Hand History Converters')
          , 'gui_cash_stats' : _('Ring Player Stats'),  'field_type' : _('Field Type')
          , 'col_title' : _('Column Heading'),          'xalignment' : _('Left/Right Align')
          , 'disp_all' : _('Show in Summaries'),        'disp_posn' : _('Show in Position Stats')
          , 'col_name' : _('Stat Name'),                'field_format' : _('Format')
          }

class GuiPrefs(QDialog):

    def __init__(self, config, parentwin):
        QDialog.__init__(self, parentwin)
        self.resize(600, 350)
        self.config = config
        self.setLayout(QVBoxLayout())


        self.doc = self.config.get_doc()

        self.configView = QTreeWidget()
        self.configView.setColumnCount(2)
        self.configView.setHeaderLabels([_("Setting"), _("Value (double-click to change)")])

        if self.doc.documentElement.tagName == 'FreePokerToolsConfig':
            self.root = QTreeWidgetItem(["fpdb", None])
            self.configView.addTopLevelItem(self.root)
            self.root.setExpanded(True)
            for elem in self.doc.documentElement.childNodes:
                self.addTreeRows(self.root, elem)
        self.layout().addWidget(self.configView)
        self.configView.resizeColumnToContents(0)

        self.configView.itemChanged.connect(self.updateConf)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.layout().addWidget(btns)

    def updateConf(self, item, column):
        if column != 1:
            return
        item.data(1, Qt.UserRole).value = item.data(1, Qt.DisplayRole)

    def rewriteText(self, s):
        upd = False
        if s in rewrite:
            s = rewrite[s]
            upd = True
        return( (s,upd) )

    def addTreeRows(self, parent, node):
        if (node.nodeType == node.ELEMENT_NODE):
            (setting, value) = (node.nodeName, None)
        elif (node.nodeType == node.TEXT_NODE):
            # text nodes hold the whitespace (or whatever) between the xml elements, not used here
            (setting, value) = ("TEXT: ["+node.nodeValue+"|"+node.nodeValue+"]", node.data)
        else:
            (setting, value) = ("?? "+node.nodeValue, "type="+str(node.nodeType))
        
        if node.nodeType != node.TEXT_NODE and node.nodeType != node.COMMENT_NODE:
            name = ""
            item = QTreeWidgetItem(parent, [setting, value])
            if node.hasAttributes():
                for i in xrange(node.attributes.length):
                    localName,updated = self.rewriteText( node.attributes.item(i).localName )
                    attritem = QTreeWidgetItem(item, [localName, node.attributes.item(i).value])
                    attritem.setData(1, Qt.UserRole, node.attributes.item(i))
                    attritem.setFlags(attritem.flags() | Qt.ItemIsEditable)

                    if node.attributes.item(i).localName in ('site_name', 'game_name', 'stat_name', 'name', 'db_server', 'site', 'col_name'):
                        name = " " + node.attributes.item(i).value

            label,updated = self.rewriteText(setting+name)
            if name != "" or updated:
                item.setData(0, 0, label)

            if node.hasChildNodes():
                for elem in node.childNodes:
                    self.addTreeRows(item, elem)

if __name__=="__main__":
    Configuration.set_logfile("fpdb-log.txt")

    config = Configuration.Config()

    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication([])
    main_window = QMainWindow()
    main_window.show()
    prefs = GuiPrefs(config, main_window)
    prefs.exec_()
    app.exec_()
