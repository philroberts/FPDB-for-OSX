#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XWindows specific methods for TableWindows Class.
"""
#    Copyright 2008 - 2011, Ray E. Barker

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

import L10n
_ = L10n.get_translation()

#    Standard Library modules
import re
import os
import logging

#    pyGTK modules
import gtk

#    Other Library modules
import wnck

#    FPDB modules
from TableWindow import Table_Window
import Configuration

#    We might as well do this once and make them globals
root = wnck.screen_get_default()

c = Configuration.Config()
log = logging.getLogger("hud")

class Table(Table_Window):

    def find_table_parameters(self):

#    This is called by __init__(). Find the poker table window of interest,
#    given the self.search_string. Then populate self.number, self.title, 
#    self.window, and self.parent (if required).

        self.number = None
        self.wnck_table_w = None

        # Flush GTK event loop before calling wnck.get_*
        while gtk.events_pending():
            gtk.main_iteration(False)

        for win in root.get_windows():
            w_title = win.get_name()
            if re.search(self.search_string, w_title, re.I):
                log.info('"%s" matches: "%s"' % (w_title, self.search_string))
                title = w_title.replace('"', '')
                if self.check_bad_words(title): continue
                self.wnck_table_w = win
                self.number = int(win.get_xid())
                self.title = title
                break

        if self.number is None:
            log.warning(_("No match in XTables for table '%s'.") % self.search_string)
            return None

#    def get_window_from_xid(self, id):
#        for outside in root.query_tree().children:
#            if outside.id == id:
#                return (outside, outside.query_tree().parent)
#            for inside in outside.query_tree().children:
#                if inside.id == id:  # GNOME, Xfce
#                    return (inside, inside.query_tree().parent)
#                for wayinside in inside.query_tree().children:
#                    if wayinside.id == id:  # KDE
#                        parent = wayinside.query_tree().parent
#                        return (wayinside, parent.query_tree().parent)
#        return (None, None)

    #def get_geometry(self):
        #try:
            #my_geo = self.window.get_geometry()
            #if self.parent is None:
                #return {'x'      : my_geo.x,
                        #'y'      : my_geo.y,
                        #'width'  : my_geo.width,
                        #'height' : my_geo.height
                       #}
            #else:
                #pa_geo = self.parent.get_geometry()
                #return {'x'      : my_geo.x + pa_geo.x,
                        #'y'      : my_geo.y + pa_geo.y,
                        #'width'  : my_geo.width,
                        #'height' : my_geo.height
                       #}
        #except:
            #return None

    def get_geometry(self):
        (_x, _y, _h, _w) = self.wnck_table_w.get_client_window_geometry()
        try:
            return {'x'        : int(_x),
                    'y'        : int(_y),
                    'width'    : int(_w),
                    'height'   : int(_h)
                   }
        except AttributeError:
            return None

    def get_window_title(self):
        return self.wnck_table_w.get_title()


    def topify(self, window):
#    The idea here is to call set_transient_for on the HUD window, with the table window
#    as the argument. This should keep the HUD window on top of the table window, as if 
#    the hud window was a dialog belonging to the table.

#    This is the gdkhandle for the HUD window
        gdkwindow = gtk.gdk.window_foreign_new(window.window.xid)
        gdkwindow.set_transient_for(self.gdkhandle)

