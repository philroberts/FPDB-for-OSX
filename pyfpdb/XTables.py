#!/usr/bin/env python
"""Discover_Tables.py

Inspects the currently open windows and finds those of interest to us--that is
poker table windows from supported sites.  Returns a list
of Table_Window objects representing the windows found.
"""
#    Copyright 2008 - 2009, Ray E. Barker

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

#    Standard Library modules
import re
import os

#    pyGTK modules
import pygtk
import gtk

#    Other Library modules
import Xlib
import Xlib.display

#    FreePokerTools modules
from TableWindow import Table_Window

#    We might as well do this once and make them globals
disp = Xlib.display.Display()
root = disp.screen().root
name_atom = disp.get_atom("WM_NAME", 1)

class Table(Table_Window):

    def find_table_parameters(self, search_string):
#        self.window = None
#        done_looping = False
#        for outside in root.query_tree().children:
#            for inside in outside.query_tree().children:
#                if done_looping: break
#                prop = inside.get_property(name_atom, Xlib.Xatom.STRING, 0, 1000)
#                print prop
#                if prop is None: continue
#                if prop.value and re.search(search_string, prop.value):
#                    if self.check_bad_words(prop.value): continue
##                if inside.get_wm_name() and re.search(search_string, inside.get_wm_name()):
##                    if self.check_bad_words(inside.get_wm_name()):
##                        print "bad word =", inside.get_wm_name() 
##                        continue
#                    self.window = inside
#                    self.parent = outside
#                    done_looping = True
#                    break

        window_number = None
        for listing in os.popen('xwininfo -root -tree').readlines():
            if re.search(search_string, listing):
                print listing
                mo = re.match('\s+([\dxabcdef]+) (.+):\s\(\"([a-zA-Z.]+)\".+  (\d+)x(\d+)\+\d+\+\d+  \+(\d+)\+(\d+)', listing)
                self.number = int( mo.group(1), 0)
                self.width  = int( mo.group(4) )
                self.height = int( mo.group(5) )
                self.x      = int( mo.group(6) )
                self.y      = int( mo.group(7) )
                self.title  = re.sub('\"', '', mo.group(2))
                self.exe    = "" # not used?
                self.hud    = None
#        done_looping = False
#        for outside in root.query_tree().children:
#            for inside in outside.query_tree().children:
#                if done_looping: break
#                if inside.id == window_number:
#                    self.window = inside
#                    self.parent = outside
#                    done_looping = True
#                    break

        if window_number is None:
            return None

#        my_geo = self.window.get_geometry()
#        pa_geo = self.parent.get_geometry()
#
#        self.x      = pa_geo.x + my_geo.x
#        self.y      = pa_geo.y + my_geo.y
#        self.width  = my_geo.width
#        self.height = my_geo.height
#        self.exe    = self.window.get_wm_class()[0]
#        self.title  = self.window.get_wm_name()
#        self.site   = ""
#        self.hud    = None

#        window_string = str(self.window)
        mo = re.match('Xlib\.display\.Window\(([\dxabcdef]+)', window_string)
        if not mo:
            print "Not matched"
            self.gdk_handle = None
        else:
            self.number = int( mo.group(1), 0)
            print "number =", self.number
#            self.gdk_handle = gtk.gdk.window_foreign_new(int(self.number))

    def get_geometry(self):
        try:
            my_geo = self.window.get_geometry()
            pa_geo = self.parent.get_geometry()
            return {'x'      : pa_geo.x + my_geo.x,
                    'y'      : pa_geo.y + my_geo.y,
                    'width'  : my_geo.width,
                    'height' : my_geo.height
                   }
        except:
            return None

    def get_window_title(self):
        return self.window.get_wm_name()
    
    def topify(self, hud):
        hud.main_window.gdkhandle = gtk.gdk.window_foreign_new(hud.main_window.window.xid)
        hud.main_window.gdkhandle.set_transient_for(self.gdk_handle)
