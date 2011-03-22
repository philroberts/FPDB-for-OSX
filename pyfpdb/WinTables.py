#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Routines for detecting and handling poker client windows for MS Windows.
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

import L10n
_ = L10n.get_translation()

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

    def find_table_parameters(self):
        """Finds poker client window with the given table name."""
        titles = {}
        win32gui.EnumWindows(win_enum_handler, titles)
        for hwnd in titles:
            if titles[hwnd] == "":
                continue
            if re.search(self.search_string, titles[hwnd], re.I):
                if self.check_bad_words(titles[hwnd]):
                    continue
                # if window not visible, probably not a table
                if not win32gui.IsWindowVisible(hwnd): 
                    continue
                # if window is a child of another window, probably not a table
                if win32gui.GetParent(hwnd) != 0:
                    continue
                HasNoOwner = win32gui.GetWindow(hwnd, win32con.GW_OWNER) == 0
                WindowStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if HasNoOwner and WindowStyle & win32con.WS_EX_TOOLWINDOW != 0:
                    continue
                if not HasNoOwner and WindowStyle & win32con.WS_EX_APPWINDOW == 0:
                    continue

                self.window = hwnd
                break

        try:
            if self.window == None:
                log.error(_("Window %s not found. Skipping.") % self.search_string)
                return None
        except AttributeError:
            log.error(_("self.window doesn't exist? why?"))
            return None

        self.title = titles[hwnd]
        self.hud = None
        self.number = hwnd
        if self.gdkhandle is not None:
            try:   # Windows likes this here - Linux doesn't
                self.gdkhandle = gtk.gdk.window_foreign_new(self.number)
            except AttributeError:
                pass

    def get_geometry(self):
        try:
            if win32gui.IsWindow(self.number):
                (x, y, width, height) = win32gui.GetWindowRect(self.number)
                # this apparently returns x = far left side of window, width = far right side of window, y = top of window, height = bottom of window
                # so apparently we have to subtract x from "width" to get actual width, and y from "height" to get actual height ?
                # it definitely gives slightly different results than the GTK code that does the same thing.
                #print "x=", x, "y=", y, "width=", width, "height=", height
                width = width - x
                height = height - y
                return {
                    'x'      : int(x) + b_width,
                    'y'      : int(y) + tb_height,
                    'height' : int(height) - y,
                    'width'  : int(width) - x
                }
        except AttributeError:
            return None

    def get_window_title(self):
        try: # after window is destroyed, self.window = attribute error
            return win32gui.GetWindowText(self.window)
        except AttributeError:
            return ""

#    def get_nt_exe(self, hwnd):
#        """Finds the name of the executable that the given window handle belongs to."""
#
#        # Request privileges to enable "debug process", so we can later use PROCESS_VM_READ, retardedly required to GetModuleFileNameEx()
#        priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
#        hToken = win32security.OpenProcessToken (win32api.GetCurrentProcess(), priv_flags)
#        # enable "debug process"
#        privilege_id = win32security.LookupPrivilegeValue (None, win32security.SE_DEBUG_NAME)
#        old_privs = win32security.AdjustTokenPrivileges (hToken, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)])
#
#        # Open the process, and query it's filename
#        processid = win32process.GetWindowThreadProcessId(hwnd)
#        pshandle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, processid[1])
#        exename = win32process.GetModuleFileNameEx(pshandle, 0)
#
#        # clean up
#        win32api.CloseHandle(pshandle)
#        win32api.CloseHandle(hToken)
#
#        return exename

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
#        rect = self.gdkhandle.get_frame_extents()
#        (innerx, innery) = self.gdkhandle.get_origin()
#        b_width = rect.x - innerx
#        tb_height = rect.y - innery
#
#                style = win32gui.GetWindowLong(self.number, win32con.GWL_EXSTYLE)
#                style |= win32con.WS_CLIPCHILDREN
#                win32gui.SetWindowLong(self.number, win32con.GWL_EXSTYLE, style)
#                break

#        hud.main_window.set_title(real_name)


def win_enum_handler(hwnd, titles):
    titles[hwnd] = win32gui.GetWindowText(hwnd)
