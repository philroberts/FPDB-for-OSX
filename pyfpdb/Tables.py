#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Discover_Tables.py

Inspects the currently open windows and finds those of interest to us--that is
poker table windows from supported sites.  Returns a list
of Table_Window objects representing the windows found.
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
import os
import sys
import re

import locale
lang=locale.getdefaultlocale()[0][0:2]
if lang=="en":
    def _(string): return string
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
    except IOError:
        def _(string): return string

#    Win32 modules
if os.name == 'nt':
    import win32gui
    import win32process
    import win32api
    import win32con
    import win32security

#    FreePokerTools modules
import Configuration

#    Each TableWindow object must have the following attributes correctly populated:
#    tw.name = the table name from the title bar, which must to match the table name
#              from the corresponding hand history.
#    tw.site = the site name, e.g. PokerStars, FullTilt.  This must match the site
#            name specified in the config file.
#    tw.number = This is the system id number for the client table window in the 
#                format that the system presents it.  This is Xid in Xwindows and
#                hwnd in Microsoft Windows.
#    tw.title = The full title from the window title bar.
#    tw.width, tw.height = The width and height of the window in pixels.  This is 
#            the internal width and height, not including the title bar and 
#            window borders.
#    tw.x, tw.y = The x, y (horizontal, vertical) location of the window relative 
#            to the top left of the display screen.  This also does not include the
#            title bar and window borders.  To put it another way, this is the 
#            screen location of (0, 0) in the working window.

class Table_Window:
    def __init__(self, info = {}):
        if 'number' in info:    self.number = info['number']
        if 'exe' in info:       self.exe    = info['exe']
        if 'width' in info:     self.width  = info['width']
        if 'height' in info:    self.height = info['height']
        if 'x' in info:         self.x      = info['x']
        if 'y' in info:         self.y      = info['y']
        if 'site' in info:      self.site   = info['site']
        if 'title' in info:     self.title  = info['title']
        if 'name' in info:      self.name   = info['name']
        self.gdkhandle = None

    def __str__(self):
#    __str__ method for testing
        temp = 'TableWindow object\n'
        temp = temp + "    name = %s\n    site = %s\n    number = %s\n    title = %s\n" % (self.name, self.site, self.number, self.title)
#        temp = temp + "    game = %s\n    structure = %s\n    max = %s\n" % (self.game, self.structure, self.max)
        temp = temp + "    width = %d\n    height = %d\n    x = %d\n    y = %d\n" % (self.width, self.height, self.x, self.y)
        if getattr(self, 'tournament', 0):
            temp = temp + "    tournament = %d\n    table = %d" % (self.tournament, self.table)
        return temp

############################################################################
#    Top-level discovery routines--these are the modules interface
def discover(c):
    """Dispatch routine for finding all potential poker client windows."""
    if os.name == 'posix':
        tables = discover_posix(c)
    elif os.name == 'nt':
        tables = discover_nt(c)
    elif os.name == 'mac':
        tables = discover_mac(c)
    else:
        tables = {}
    return tables

def discover_table_by_name(c, tablename):
    """Dispatch routine for finding poker client windows with the given name."""
    if os.name == 'posix':
        info = discover_posix_by_name(c, tablename)
    elif os.name == 'nt':
        info = discover_nt_by_name(c, tablename)
    elif os.name == 'mac':
        info = discover_mac_by_name(c, tablename)
    else:
        return None
    if info is None:
        return None
    return Table_Window(info)

def discover_tournament_table(c, tour_number, tab_number):
    """Dispatch routine for finding poker clients with tour and table number."""
    if os.name == 'posix':
        info = discover_posix_tournament(c, tour_number, tab_number)
    elif os.name == 'nt':
        info = discover_nt_tournament(c, tour_number, tab_number)
    elif os.name == 'mac':
        info = discover_mac_tournament(c, tour_number, tab_number)
    else:
        return None
    if info:
        return Table_Window(info)
    return None

#############################################################################
# Posix (= XWindows) specific routines
def discover_posix(c):
    """Poker client table window finder for posix/Linux = XWindows."""
    tables = {}
    for listing in os.popen('xwininfo -root -tree').readlines():
#    xwininfo -root -tree -id 0xnnnnn    gets the info on a single window
        for s in c.get_supported_sites():
            params = c.get_site_parameters(s)
            
# TODO: We need to make a list of phrases, shared between the WIndows and Unix code!!!!!!       
            if re.search(params['table_finder'], listing):
                if 'Lobby' in listing:   continue
                if 'Instant Hand History' in listing: continue
#                if '\"Full Tilt Poker\"' in listing: continue
                if 'History for table:' in listing: continue
                if 'has no name' in listing: continue
                info = decode_xwininfo(c, listing)
                if info['site'] is None:                       continue
                if info['title'] == info['exe']:               continue
#    this appears to be a poker client, so make a table object for it
                tw = Table_Window(info)
                eval("%s(tw)" % params['decoder'])
                tables[tw.name] = tw
    return tables

def discover_posix_by_name(c, tablename):
    """Find an XWindows poker client of the given name."""
    for listing in os.popen('xwininfo -root -tree').readlines():
        if tablename in listing:
            if 'History for table:' in listing: continue
            info = decode_xwininfo(c, listing)
            if not info['name'] == tablename:            continue
            return info
    return None

def discover_posix_tournament(c, t_number, s_number):
    """Finds the X window for a client, given tournament and table nos."""
    search_string = "%s.+Table.+%s" % (t_number, s_number)
    for listing in os.popen('xwininfo -root -tree').readlines():
        if re.search(search_string, listing):
            return decode_xwininfo(c, listing)
    return None

def decode_xwininfo(c, info_string):
    """Gets window parameters from xwinifo string--XWindows."""
    info = {}
    mo = re.match('\s+([\dxabcdef]+) (.+):\s\(\"([a-zA-Z.]+)\".+  (\d+)x(\d+)\+\d+\+\d+  \+(\d+)\+(\d+)', info_string)
    if not mo:
        return None
    else:
        info['number'] = int( mo.group(1), 0)
        info['exe']    = mo.group(3)
        info['width']  = int( mo.group(4) )
        info['height'] = int( mo.group(5) )
        info['x']      = int( mo.group(6) )
        info['y']      = int( mo.group(7) )
        info['site']   = get_site_from_exe(c, info['exe'])
        info['title']  = re.sub('\"', '', mo.group(2))
        title_bits     = re.split(' - ', info['title'])
        info['name']   = clean_title(title_bits[0])
    return info

##############################################################################
#    NT (= Windows) specific routines
def discover_nt(c):
    """    Poker client table window finder for Windows."""
#
#    I cannot figure out how to get the inside dimensions of the poker table
#    windows.  So I just assume all borders are 3 thick and all title bars
#    are 29 high.  No doubt this will be off when used with certain themes.
#
    b_width = 3
    tb_height = 29
    titles = {}
    tables = {}
    win32gui.EnumWindows(win_enum_handler, titles)
    for hwnd in titles:
        if 'Logged In as' in titles[hwnd] and not 'Lobby' in titles[hwnd]:
            if 'Full Tilt Poker' in titles[hwnd]:
                continue
            tw = Table_Window()
            tw.number = hwnd
            (x, y, width, height) = win32gui.GetWindowRect(hwnd)
            tw.title  = titles[hwnd]
            tw.width  = int( width ) - 2*b_width
            tw.height = int( height ) - b_width - tb_height
            tw.x      = int( x ) + b_width
            tw.y      = int( y ) + tb_height
            
# TODO: Isn't the site being determined by the EXE name it belongs to? is this section of code even useful? cleaning it anyway
            if 'Logged In as' in titles[hwnd]:
                tw.site = "PokerStars"
            elif 'Logged In As' in titles[hwnd]:
                tw.site = "Full Tilt"
            else:
                tw.site = "Unknown"
                sys.stderr.write(_("Found unknown table = %s") % tw.title)
            if tw.site != "Unknown":
                eval("%s(tw)" % c.supported_sites[tw.site].decoder)
            else:
                tw.name = "Unknown"
            tables[len(tables)] = tw
    return tables

def discover_nt_by_name(c, tablename):
    """Finds poker client window with the given table name."""
    titles = {}
    win32gui.EnumWindows(win_enum_handler, titles)
        
    for hwnd in titles:
        #print "Tables.py: tablename =", tablename, "title =", titles[hwnd]
        try:
            # maybe it's better to make global titles[hwnd] decoding?
            # this can blow up in XP on some windows, eg firefox displaying http://docs.python.org/tutorial/classes.html
            if not tablename.lower() in titles[hwnd].decode(Configuration.LOCALE_ENCODING).lower():
                continue
        except:
            continue
        if 'History for table:' in titles[hwnd]: continue # Everleaf Network HH viewer window
        if 'HUD:' in titles[hwnd]: continue # FPDB HUD window
        if 'Chat:' in titles[hwnd]: continue # Some sites (FTP? PS? Others?) have seperable or seperately constructed chat windows
        if ' - Table ' in titles[hwnd]: continue # Absolute table Chat window.. sigh. TODO: Can we tell what site we're trying to discover for somehow in here, so i can limit this check just to AP searches?
        temp = decode_windows(c, titles[hwnd], hwnd)
        print _("attach to window"), temp
        return temp
    return None

def discover_nt_tournament(c, tour_number, tab_number):
    """Finds the Windows window handle for the given tournament/table."""
    search_string = "%s.+%s" % (tour_number, tab_number)

    titles ={}
    win32gui.EnumWindows(win_enum_handler, titles)
    for hwnd in titles:
        # Some sites (FTP? PS? Others?) have seperable or seperately constructed chat windows
        if 'Chat:' in titles[hwnd]: continue
        # Everleaf Network HH viewer window
        if 'History for table:' in titles[hwnd]: continue
        # FPDB HUD window
        if 'HUD:' in titles[hwnd]: continue

        if re.search(search_string, titles[hwnd]):
            return decode_windows(c, titles[hwnd], hwnd)
    return None

def get_nt_exe(hwnd):
    """Finds the name of the executable that the given window handle belongs to."""
    
    # Request privileges to enable "debug process", so we can later use
    # PROCESS_VM_READ, retardedly required to GetModuleFileNameEx()
    priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
    hToken = win32security.OpenProcessToken (win32api.GetCurrentProcess(),
                                             priv_flags)
    # enable "debug process"
    privilege_id = win32security.LookupPrivilegeValue(None,
                                                      win32security.SE_DEBUG_NAME)
    old_privs = win32security.AdjustTokenPrivileges(hToken, 0,
                                                    [(privilege_id,
                                                      win32security.SE_PRIVILEGE_ENABLED)])
    
    # Open the process, and query it's filename
    processid = win32process.GetWindowThreadProcessId(hwnd)
    pshandle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION |
                                    win32con.PROCESS_VM_READ, False,
                                    processid[1])
    try:
        exename = win32process.GetModuleFileNameEx(pshandle, 0)
    except pywintypes.error:
        # insert code to call GetProcessImageName if we can find it..
        # returning None from here will hopefully break all following code
        exename = None 
    finally:
        # clean up
        win32api.CloseHandle(pshandle)
        win32api.CloseHandle(hToken)
        
    return exename

def decode_windows(c, title, hwnd):
    """Gets window parameters from the window title and handle--Windows."""

#    I cannot figure out how to get the inside dimensions of the poker table
#    windows.  So I just assume all borders are 3 thick and all title bars
#    are 29 high.  No doubt this will be off when used with certain themes.
    b_width = 3
    tb_height = 29

    info = {}
    info['number'] = hwnd
    info['title'] = re.sub('\"', '', title)
    (x, y, width, height) = win32gui.GetWindowRect(hwnd)

    info['x']      = int(x)  + b_width
    info['y']      = int( y ) + tb_height
    info['width']  = int( width ) - 2*b_width
    info['height'] = int( height ) - b_width - tb_height
    info['exe']    = get_nt_exe(hwnd)
    print "get_nt_exe returned ", info['exe']
    # TODO: 'width' here is all sorts of screwed up.

    title_bits = re.split(' - ', info['title'])
    info['name'] = title_bits[0]
    info['site']   = get_site_from_exe(c, info['exe'])

    return info

def win_enum_handler(hwnd, titles):
    str = win32gui.GetWindowText(hwnd)
    if str != "":
        titles[hwnd] = win32gui.GetWindowText(hwnd)
  
###################################################################
#    Utility routines used by all the discoverers.
def get_site_from_exe(c, exe):
    """Look up the site from config, given the exe."""
    for s in c.get_supported_sites():
        params = c.get_site_parameters(s)
        if re.search(params['table_finder'], exe):
            return params['site_name']
    return None

def everleaf_decode_table(tw):
# 2 - Tournament ID: 573256 - NL Hold'em - 150/300 blinds - Good luck <username>! - [Connection is ...]    
    pass

def pokerstars_decode_table(tw):
#    Extract poker information from the window title.  This is not needed for
#    fpdb, since all that information is available in the db via new_hand_number.
#    This is needed only when using the HUD with a backend less integrated.
    title_bits = re.split(' - ', tw.title)
    name = title_bits[0]
    mo = re.search('Tournament (\d+) Table (\d+)', name)
    if mo:
        tw.tournament = int( mo.group(1) )
        tw.table      = int( mo.group(2) )
        tw.name       = name
    else:
        tw.tournament = None
        tw.name = clean_title(name)
    mo = re.search('(Razz|Stud H/L|Stud|Omaha H/L|Omaha|Hold\'em|5-Card Draw|Triple Draw 2-7 Lowball|Badugi)', tw.title)
    
    tw.game = mo.group(1).lower()
    tw.game = re.sub('\'', '', tw.game)
    tw.game = re.sub('h/l', 'hi/lo', tw.game)
    
    mo = re.search('(No Limit|Pot Limit)', tw.title)
    if mo:
        tw.structure = mo.group(1).lower()
    else:
        tw.structure = 'limit'
        
    tw.max = None
    if tw.game in ('razz', 'stud', 'stud hi/lo'):
        tw.max = 8
    elif tw.game in ('5-card draw', 'triple draw 2-7 lowball'):
        tw.max = 6
    elif tw.game == 'holdem':
        pass
    elif tw.game in ('omaha', 'omaha hi/lo'):
        pass

def fulltilt_decode_table(tw):
#    Extract poker information from the window title.  This is not needed for
#    fpdb, since all that information is available in the db via new_hand_number.
#    This is needed only when using the HUD with a backend less integrated.
    title_bits = re.split(' - ', tw.title)
    name = title_bits[0]
    tw.tournament = None
    tw.name = clean_title(name)

def clean_title(name):
    """Clean the little info strings from the table name."""
#    these strings could go in a config file
    for pattern in [' \(6 max\)', ' \(heads up\)', ' \(deep\)',
                ' \(deep hu\)', ' \(deep 6\)', '\(6 max, deep\)', ' \(2\)',
                ' \(edu\)', ' \(edu, 6 max\)', ' \(6\)',
                ' \(speed\)', 'special', 'newVPP', 
                ' no all-in', ' fast', ',', ' 50BB min', '50bb min', '\s+$']:
        name = re.sub(pattern, '', name)
    name = name.rstrip()
    return name

###########################################################################
#    Mac specific routines....all stubs for now
def discover_mac_tournament(c, tour_number, tab_number):
    """Mac users need help."""
    return None

def discover_mac(c):
    """Poker client table window finder for Macintosh."""
    tables = {}
    return tables

def discover_mac_by_name(c, tablename):
    """Oh, the humanity."""
    # again, i have no mac to test this on, sorry -eric
    return None

###########################################################################
#   Main function used for testing
if __name__=="__main__":
    c = Configuration.Config()

    print discover_table_by_name(c, "Torino")
#    print discover_tournament_table(c, "118942908", "3")

    tables = discover(c)
    for t in tables.keys():
        print tables[t]

    print _("press enter to continue")
    sys.stdin.readline()
