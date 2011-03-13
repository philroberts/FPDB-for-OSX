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

#    pyGTK modules
import gtk

#    Other Library modules
import Xlib.display

#    FPDB modules
from TableWindow import Table_Window
import Configuration

#    We might as well do this once and make them globals
disp = Xlib.display.Display()
root = disp.screen().root

c = Configuration.Config()
log = Configuration.get_logger("logging.conf", "hud", log_dir=c.dir_log, log_file='HUD-log.txt')

class Table(Table_Window):

    def find_table_parameters(self):

#    This is called by __init__(). Find the poker table window of interest,
#    given the self.search_string. Then populate self.number, self.title, 
#    self.window, and self.parent (if required).

        reg = '''
                \s+(?P<XID>[\dxabcdef]+)    # XID in hex
                \s(?P<TITLE>.+):            # window title
            '''

        self.number = None
        for listing in os.popen('xwininfo -root -tree').readlines():
            if re.search(self.search_string, listing, re.I):
                log.info(listing)
                mo = re.match(reg, listing, re.VERBOSE)
                title  = re.sub('\"', '', mo.groupdict()["TITLE"])
                if self.check_bad_words(title): continue
                self.number = int( mo.groupdict()["XID"], 0 )
                self.title = title
                if self.number is None:
                    log.warning(_("Could not retrieve XID from table xwininfo. xwininfo is %s") % listing)
                break

        if self.number is None:
            log.warning(_("No match in XTables for table '%s'.") % self.search_string)
            return None
        (self.window, self.parent) = self.get_window_from_xid(self.number)

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

    def get_window_from_xid(self, id):
        for top_level in root.query_tree().children:
            if top_level.id == id:
                return (top_level, None)
            for w in treewalk(top_level):
                if w.id == id:
                    return (w, top_level)

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
        geo_re = '''
                Absolute\supper-left\sX: \s+ (?P<X>\d+)   # x
                .+
                Absolute\supper-left\sY: \s+ (?P<Y>\d+)   # y
                .+
                Width: \s+ (?P<W>\d+)                   # width
                .+
                Height: \s+ (?P<H>\d+)                  # height
            '''
        des_re = 'No such window with id'

        listing = os.popen("xwininfo -id %d -stats" % (self.number)).read()
        if listing == "": return
        mo = re.search(des_re, listing)
        if mo is not None:
            return None      # table has been destroyed

        mo = re.search(geo_re, listing, re.VERBOSE|re.DOTALL)
        try:
            return {'x'        : int(mo.groupdict()['X']),
                    'y'        : int(mo.groupdict()['Y']),
                    'width'    : int(mo.groupdict()['W']),
                    'height'   : int(mo.groupdict()['H'])
                   }
        except AttributeError:
            return None

    def get_window_title(self):
        s = os.popen("xwininfo -wm -id %d" % self.number).read()
        mo = re.search('"(.+)"', s)
        try:
            return mo.group(1)
        except AttributeError:
            return None
        
    def topify(self, window):
#    The idea here is to call set_transient_for on the HUD window, with the table window
#    as the argument. This should keep the HUD window on top of the table window, as if 
#    the hud window was a dialog belonging to the table.

#    This is the gdkhandle for the HUD window
        gdkwindow = gtk.gdk.window_foreign_new(window.window.xid)
        gdkwindow.set_transient_for(self.gdkhandle)

def treewalk(parent):
    for w in parent.query_tree().children:
        for ww in treewalk(w):
            yield ww
        yield w
