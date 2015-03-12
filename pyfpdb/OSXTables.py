#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OSX specific methods for TableWindows Class.
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

#    Other Library modules
import ctypes

import AppKit # Work around some pyinstaller weirdness.

from AppKit import NSView, NSWindowAbove
from Quartz.CoreGraphics import (CGWindowListCreate,
                                 CGWindowListCreateDescriptionFromArray,
                                 kCGWindowBounds, kCGWindowName,
                                 kCGWindowNumber)

#    FPDB modules
from TableWindow import Table_Window

class Table(Table_Window):

    def find_table_parameters(self):

#    This is called by __init__(). Find the poker table window of interest,
#    given the self.search_string. Then populate self.number, self.title, 
#    self.window, and self.parent (if required).

        self.number = None
        WinList = CGWindowListCreate(0,0)
        WinListDict = CGWindowListCreateDescriptionFromArray(WinList)

        for d in WinListDict:
            if re.search(self.search_string, d.get(kCGWindowName, ""), re.I):
                title = d[kCGWindowName]
                if self.check_bad_words(title): continue
                self.number = int(d[kCGWindowNumber])
                self.title = title
                return self.title
        if self.number is None:
            return None
  
    def get_geometry(self):
        WinListDict = CGWindowListCreateDescriptionFromArray((self.number,))

        for d in WinListDict:
            if d[kCGWindowNumber] == self.number:
                return {'x'      : int(d[kCGWindowBounds]['X']),
                        'y'      : int(d[kCGWindowBounds]['Y']),
                        'width'  : int(d[kCGWindowBounds]['Width']),
                        'height' : int(d[kCGWindowBounds]['Height'])
                       }
        return None

    def get_window_title(self):
        WinListDict = CGWindowListCreateDescriptionFromArray((self.number,))

        for d in WinListDict:
            if d[kCGWindowNumber] == self.number:
                return d[kCGWindowName]
        return None

    def topify(self, window):
        winid = window.effectiveWinId()
        cvp = ctypes.c_void_p(int(winid))
        view = NSView(c_void_p=cvp)
        if window.isVisible():
            view.window().orderWindow_relativeTo_(NSWindowAbove, self.number)
