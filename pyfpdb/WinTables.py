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
# to do
# for win7 the fixed b_width and tb_height are not correct - need to discover these from os
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
            
            if re.search(self.search_string, titles[hwnd], re.I):
                if self.check_bad_words(titles[hwnd]):
                    continue

                self.window = hwnd
                break

        try:
            if self.window == None:
                log.error(_("Window %s not found. Skipping.") % self.search_string)
                return None
        except AttributeError:
            log.error(_("Error:") + " " + _("%s doesn't exist.") % "self.window")
            return None

        self.title = titles[hwnd]
        self.hud = None
        self.number = hwnd
        if self.gdkhandle is None:
            try:   # Windows likes this here - Linux doesn't
                self.gdkhandle = gtk.gdk.window_foreign_new(self.number)
            except AttributeError:
                pass

    def get_geometry(self):
        try:
            if win32gui.IsWindow(self.number):
                (x, y, width, height) = win32gui.GetWindowRect(self.number)
                #log.debug(("newhud - get_geo w h x y",str(width), str(height), str(x), str(y)))
                #print "x=", x, "y=", y, "width=", width, "height=", height
                                
                # this apparently returns x = far left side of window, width = far right side of window, y = top of window, height = bottom of window
                # so apparently we have to subtract x from "width" to get actual width, and y from "height" to get actual height ?
                # it definitely gives slightly different results than the GTK code that does the same thing.

                # minimised windows are given -32000 (x,y) value,
                #   so just zeroise to avoid downstream confusion
                if x < 0: x = 0
                if y < 0: y = 0
                
                width = width - x
                height = height - y
                
                #determine system titlebar and border setting constant values
                # see http://stackoverflow.com/questions/431470/window-border-width-and-height-in-win32-how-do-i-get-it
                try:
                    self.b_width; self.tb_height
                except:
                    self.b_width = win32api.GetSystemMetrics(win32con.SM_CXSIZEFRAME) # bordersize
                    self.tb_height = win32api.GetSystemMetrics(win32con.SM_CYCAPTION) # titlebar height (excl border)

                #fixme - x and y must _not_ be adjusted by the b_width if the window has been maximised
                return {
                    'x'      : int(x) + self.b_width,
                    'y'      : int(y) + self.tb_height + self.b_width,
                    'height' : int(height),
                    'width'  : int(width)
                }
            else:
                log.debug("newhud - WinTables window not found")
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

    def topify(self, window):
        """Set the specified gtk window to stayontop in MS Windows."""

        """
        self is the poker table window object (the poker client)
        self.number is the windows handle
        self.gdkhandle is a gdkhandle associated with the poker client
         
        window is a seat_window object from Mucked (a gtk window)
        window.window is a gtk.gdk.window object
        """
        
        #window.set_focus_on_map(False)
        #window.set_accept_focus(False)

        if self.gdkhandle is None:
            self.gdkhandle = gtk.gdk.window_foreign_new(int(self.number))
        #    Then call set_transient_for on the gdk handle of the HUD window
        #    with the gdk handle of the table window as the argument.
        window.window.set_transient_for(self.gdkhandle)
        

def win_enum_handler(hwnd, titles):
    titles[hwnd] = win32gui.GetWindowText(hwnd)
