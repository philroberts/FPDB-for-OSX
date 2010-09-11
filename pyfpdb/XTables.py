#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XWindows specific methods for TableWindows Class.
"""
#    Copyright 2008 - 2010, Ray E. Barker

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
import subprocess

#    pyGTK modules
import gtk

#    Other Library modules
import Xlib.display

#    FPDB modules
from TableWindow import Table_Window

#    We might as well do this once and make them globals
disp = Xlib.display.Display()
root = disp.screen().root

class Table(Table_Window):

    def find_table_parameters(self):

        self.number = None
        for listing in os.popen('xwininfo -root -tree').readlines():
            if re.search(self.search_string, listing):
                mo = re.match('\s+([\dxabcdef]+) (.+):\s\(\"([a-zA-Z0-9\-.]+)\".+  (\d+)x(\d+)\+\d+\+\d+  \+(\d+)\+(\d+)', listing)
                title  = re.sub('\"', '', mo.group(2))
                if self.check_bad_words(title): continue
                self.number = int( mo.group(1), 0)
                self.title = title
                self.exe    = ""     # not used?
                self.hud    = None   # specified later
                break
        
        if self.number is None:
            return None
        
        self.window = self.get_window_from_xid(self.number)
        self.parent = self.window.query_tree().parent

        geo = self.get_geometry()
        if geo is None:  return None
        self.width  = geo['width']
        self.height = geo['height']
        self.x      = geo['x']
        self.y      = geo['y']

        self.game = self.get_game()
        self.gdk_handle = gtk.gdk.window_foreign_new(self.number)

    def get_window_from_xid(self, id):
        for outside in root.query_tree().children:
            if outside.id == id:
                return outside
            for inside in outside.query_tree().children:
                if inside.id == id:
                    return inside
        return None

    def get_geometry(self):
        try:
            my_geo = self.window.get_geometry()
            pa_geo = self.parent.get_geometry()
            return {'x'      : my_geo.x + pa_geo.x,
                    'y'      : my_geo.y + pa_geo.y,
                    'width'  : my_geo.width,
                    'height' : my_geo.height
                   }
        except:
            return None

    def get_window_title(self):
        proc = subprocess.Popen("xwininfo -wm -id %d" % self.number, shell = True, stdout = subprocess.PIPE)
        s = proc.stdout.read()
        mo = re.search('"(.+)"', s)
        try:
            return mo.group(1)
        except AttributeError:
            return None

    def topify(self, hud):
        hud.main_window.gdkhandle = gtk.gdk.window_foreign_new(hud.main_window.window.xid)
        hud.main_window.gdkhandle.set_transient_for(self.gdk_handle)
