#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test program to see if XTables.py will correctly id the poker client.
"""
#    Copyright 2010-2011, Ray E. Barker

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

#  ====EXAMPLE OUTPUT FROM MY SYSTEM====
#enter table xid find (in hex): 
#0x3600018    <---GET THIS BY RUNNING xwininfo FROM A TERMINAL.
#Window information from xwininfo:
#-------------------------------------------------------
#
#xwininfo: Window id: 0x3600018 "Baseline Rd(26128925) - $100/$200 - Limit Hold'em"
#
#  Root window id: 0x107 (the root window) (has no name)
#  Parent window id: 0xe6e0a2 (has no name)
#     1 child:
#     0x3600019 (has no name): ()  792x573+0+0  +2171+192
#
#
#-------------------------------------------------------
#
#
#Window information from functions:
#matched inside
#window = Xlib.display.Window(0x03600018) title = "Baseline Rd(26128925) - $100/$200 - Limit Hold'em"
#
#parent = Xlib.display.Window(0x00e6e0a2)

import sys
import os
import re

#    Other Library modules
import Xlib.display

disp = Xlib.display.Display()
root = disp.screen().root
name_atom = disp.get_atom("WM_NAME", 1)

def get_window_from_xid(id):
    for outside in root.query_tree().children:
        if outside.id == id:
            print "matched outside"
            return outside
        for inside in outside.query_tree().children:
            if inside.id == id:
                print "matched inside"
                return inside
    return None

def get_window_title(xid):
    s = os.popen("xwininfo -children -id %d" % xid).read()
    mo = re.search('"(.+)"', s)
    try:
        return mo.group(1)
    except AttributeError:
        return None

if __name__== "__main__":

    print "enter table xid find (in hex): "
    xid = sys.stdin.readline()

    print "Window information from xwininfo:"
    s = os.popen("xwininfo -children -id %d" % int(xid, 0)).read()
    print "-------------------------------------------------------"
    print s
    print "-------------------------------------------------------\n\n"

    print "Window information from functions:"
    window = get_window_from_xid(int(xid, 0))
    print "window =", window, "title = \"" + get_window_title(int(xid, 0)) + "\"\n"

    print "parent =", window.query_tree().parent
