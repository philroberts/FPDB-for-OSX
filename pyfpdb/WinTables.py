#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WinTables.py

Routines for detecting and handling poker client windows for MS Windows.
"""
#    Copyright 2008-2010, Ray E. Barker

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

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import pygtk
import gtk

#    Other Library modules
import win32gui
import win32process
import win32api
import win32con
import win32security

#    FreePokerTools modules
from TableWindow import Table_Window

#    We don't know the border width or title bar height
#    so we guess here. We can probably get these from a windows call.
b_width = 3
tb_height = 29

class Table(Table_Window):

    def find_table_parameters(self, search_string):
        """Finds poker client window with the given table name."""
        titles = {}
        win32gui.EnumWindows(win_enum_handler, titles)
        for hwnd in titles:
            if titles[hwnd] == "": continue
            # print "searching ", search_string, " in ", titles[hwnd]
            if re.search(search_string, titles[hwnd]):
                if 'History for table:' in titles[hwnd]: continue # Everleaf Network HH viewer window
                if 'HUD:' in titles[hwnd]: continue # FPDB HUD window
                if 'Chat:' in titles[hwnd]: continue # Some sites (FTP? PS? Others?) have seperable or seperately constructed chat windows
                if 'FPDBHUD' in titles[hwnd]: continue # can't attach to ourselves!
                self.window = hwnd
                break

        try:
            if self.window == None:
                log.error( "Window %s not found. Skipping." % search_string )
                return None
        except AttributeError:
            log.error( "self.window doesn't exist? why?" )
            return None

        (x, y, width, height) = win32gui.GetWindowRect(hwnd)
        log.debug("x = %s y = %s width = %s height = %s" % (x, y, width, height))
        self.x      = int(x) + b_width
        self.y      = int(y) + tb_height
        self.width  = width - x
        self.height = height - y
        log.debug("x = %s y = %s width = %s height = %s" % (self.x, self.y, self.width, self.height))
        #self.height = int(height) - b_width - tb_height
        #self.width  = int(width) - 2*b_width

        self.exe    = self.get_nt_exe(hwnd)
        self.title  = titles[hwnd]
        self.site   = ""
        self.hud    = None
        self.number = hwnd
        self.gdkhandle = gtk.gdk.window_foreign_new(long(self.window))

    def get_geometry(self):
        if not win32gui.IsWindow(self.number):  # window closed
            return None

        try:
            (x, y, width, height) = win32gui.GetWindowRect(self.number)
            width = width - x
            height = height - y
            return {'x'      : int(x) + b_width,
                    'y'      : int(y) + tb_height,
                    'width'  : int(height) - b_width - tb_height,
                    'height' : int(width) - 2*b_width
                   }
        except:
            return None

    def get_window_title(self):
        return win32gui.GetWindowText(self.window)

    def get_nt_exe(self, hwnd):
        """Finds the name of the executable that the given window handle belongs to."""

        # Request privileges to enable "debug process", so we can later use PROCESS_VM_READ, retardedly required to GetModuleFileNameEx()
        priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
        hToken = win32security.OpenProcessToken (win32api.GetCurrentProcess(), priv_flags)
        # enable "debug process"
        privilege_id = win32security.LookupPrivilegeValue (None, win32security.SE_DEBUG_NAME)
        old_privs = win32security.AdjustTokenPrivileges (hToken, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)])

        # Open the process, and query it's filename
        processid = win32process.GetWindowThreadProcessId(hwnd)
        pshandle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, processid[1])
        exename = win32process.GetModuleFileNameEx(pshandle, 0)

        # clean up
        win32api.CloseHandle(pshandle)
        win32api.CloseHandle(hToken)

        return exename
    def topify(self, hud):
        """Set the specified gtk window to stayontop in MS Windows."""

#        def windowEnumerationHandler(hwnd, resultList):
#            '''Callback for win32gui.EnumWindows() to generate list of window handles.'''
#            resultList.append((hwnd, win32gui.GetWindowText(hwnd)))
#
#        unique_name = 'unique name for finding this window'
#        real_name = hud.main_window.get_title()
#        hud.main_window.set_title(unique_name)
#        tl_windows = []
#        win32gui.EnumWindows(windowEnumerationHandler, tl_windows)
#
#        for w in tl_windows:
#            if w[1] == unique_name:
#                hud.main_window.gdkhandle = gtk.gdk.window_foreign_new(w[0])
        hud.main_window.gdkhandle = hud.main_window.window
        hud.main_window.gdkhandle.set_transient_for(self.gdkhandle)
        rect = self.gdkhandle.get_frame_extents()
        (innerx, innery) = self.gdkhandle.get_origin()
        b_width = rect.x - innerx
        tb_height = rect.y - innery
#
#                style = win32gui.GetWindowLong(self.number, win32con.GWL_EXSTYLE)
#                style |= win32con.WS_CLIPCHILDREN
#                win32gui.SetWindowLong(self.number, win32con.GWL_EXSTYLE, style)
#                break

#        hud.main_window.set_title(real_name)

def win_enum_handler(hwnd, titles):
    titles[hwnd] = win32gui.GetWindowText(hwnd)
