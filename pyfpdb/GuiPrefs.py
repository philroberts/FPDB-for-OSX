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

import pygtk
pygtk.require('2.0')
import gtk
import gobject

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

class GuiPrefs:

    def __init__(self, config, mainwin, dia, parentwin):
        self.config = config
        self.main_window = mainwin
        self.dialog = dia
        self.parent_window = parentwin #need to pass reference of parent, to set transient

        self.tree_box = gtk.ScrolledWindow()
        self.tree_box.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.dialog.add(self.tree_box)
        self.dialog.show()

        self.doc = None
        self.configStore = None
        self.configView = None

        self.fillFrames()

    def fillFrames(self):
        self.doc = self.config.get_doc()

        self.configStore = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.configView = gtk.TreeView(self.configStore)
        self.configView.set_enable_tree_lines(True)

        configColumn = gtk.TreeViewColumn(_("Setting"))
        self.configView.append_column(configColumn)
        cRender = gtk.CellRendererText()
        configColumn.pack_start(cRender, True)
        configColumn.add_attribute(cRender, 'text', 1)

        configColumn = gtk.TreeViewColumn(_("Value (double-click to change)"))
        self.configView.append_column(configColumn)
        cRender = gtk.CellRendererText()
        configColumn.pack_start(cRender, True)
        configColumn.add_attribute(cRender, 'text', 2)

        if self.doc.documentElement.tagName == 'FreePokerToolsConfig':
            self.configStore.clear()
            self.root = self.configStore.append( None, [self.doc.documentElement, "fpdb", None] )
            for elem in self.doc.documentElement.childNodes:
                iter = self.addTreeRows(self.root, elem)
            if self.root != None:
                self.configView.expand_row(self.configStore.get_path(self.root), False)
            self.configView.connect("row-activated", self.rowChosen)
            self.configView.show()
            self.tree_box.add(self.configView)
            self.tree_box.show()
            self.dialog.show()

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
        
        #iter = self.configStore.append( parent, [node.nodeValue, None] )
        iter = None
        if node.nodeType != node.TEXT_NODE and node.nodeType != node.COMMENT_NODE:
            name = ""
            iter = self.configStore.append( parent, [node, setting, value] )
            if node.hasAttributes():
                for i in xrange(node.attributes.length):
                    localName,updated = self.rewriteText( node.attributes.item(i).localName )
                    self.configStore.append( iter, [node, localName, node.attributes.item(i).value] )
                    if node.attributes.item(i).localName in ('site_name', 'game_name', 'stat_name', 'name', 'db_server', 'site', 'col_name'):
                        name = " " + node.attributes.item(i).value

            label,updated = self.rewriteText(setting+name)
            if name != "" or updated:
                self.configStore.set_value(iter, 1, label)

            if node.hasChildNodes():
                for elem in node.childNodes:
                    self.addTreeRows(iter, elem)
        return iter

    def rowChosen(self, tview, path, something2, data=None):
        # tview should= self.configStore
        tmodel = tview.get_model()
        iter = tmodel.get_iter(path)
        if tmodel.iter_has_child(iter):
            # toggle children display
            if tview.row_expanded(path):
                tview.collapse_row(tmodel.get_path(iter))
            else:
                tview.expand_row(tmodel.get_path(iter), False)
        else:
            # display value and allow edit
            name = tmodel.get_value( iter, 1 )
            val = tmodel.get_value( iter, 2 )
            dia_edit = gtk.Dialog(name,
                                  self.parent_window,
                                  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
            #dia_edit.set_default_size(350, 100)
            entry = gtk.Entry()
            if val:
                entry.set_text(val)
            entry.set_width_chars(40)
            dia_edit.vbox.pack_start(entry, False, False, 0)
            entry.show()
            entry.connect("activate", self.__set_entry, dia_edit)
            response = dia_edit.run()
            if response == gtk.RESPONSE_ACCEPT:
                # update configStore
                new_val = entry.get_text()
                tmodel.set_value(iter, 2, new_val)
                tmodel.get_value(iter, 0).setAttribute(name, new_val)
            dia_edit.destroy()

    def __set_entry(self, w, dia=None):
        if dia is not None:
            dia.response(gtk.RESPONSE_ACCEPT)

if __name__=="__main__":
    Configuration.set_logfile("fpdb-log.txt")

    config = Configuration.Config()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title(_("Advanced Preferences"))
    win.set_border_width(1)
    win.set_default_size(600, 500)
    win.set_resizable(True)

    dia = gtk.Dialog(_("Advanced Preferences"),
                     win,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
    dia.set_default_size(700, 500)
    pw=dia      #pass parent window 
    prefs = GuiPrefs(config, win, dia.vbox,pw)
    response = dia.run()
    if response == gtk.RESPONSE_ACCEPT:
        # save updated config
        config.save()
    dia.destroy()
