#!/usr/bin/env python
"""Discover_Tables.py

Inspects the currently open windows and finds those of interest to us--that is
poker table windows from supported sites.  Returns a list
of Table_Window objects representing the windows found.
"""
#    Copyright 2008, Ray E. Barker

#    
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
import re

#    FreePokerTools modules
import Configuration

class Table_Window:
    def __str__(self):
#    __str__ method for testing
        temp = 'TableWindow object\n'
        temp = temp + "    name = %s\n    site = %s\n    number = %s\n    title = %s\n" % (self.name, self.site, self.number, self.title)
        temp = temp + "    game = %s\n    structure = %s\n    max = %s\n" % (self.game, self.structure, self.max)
        temp = temp + "    width = %d\n    height = %d\n    x = %d\n    y = %d\n" % (self.width, self.height, self.x, self.y)
        if getattr(self, 'tournament', 0):
            temp = temp + "    tournament = %d\n    table = %d" % (self.tournament, self.table)
        return temp

    def get_details(table):
        table.game = 'razz'
        table.max = 8
        table.struture = 'limit'
        table.tournament = 0

def discover(c):
    tables = {}
    for listing in os.popen('xwininfo -root -tree').readlines():
        if re.search('Lobby', listing): continue
        if re.search('Instant Hand History', listing): continue
        if not re.search('Logged In as ', listing): continue
        for s in c.supported_sites.keys():
            if re.search(c.supported_sites[s].table_finder, listing):
                mo = re.match('\s+([\dxabcdef]+) (.+):.+  (\d+)x(\d+)\+\d+\+\d+  \+(\d+)\+(\d+)', listing)
                if mo.group(2) == '(has no name)': continue
                if re.match('[\(\)\d\s]+', mo.group(2)): continue  # this is a popup
                tw = Table_Window()
                tw.site = c.supported_sites[s].site_name
                tw.number = mo.group(1)
                tw.title  = mo.group(2)
                tw.width  = int( mo.group(3) )
                tw.height = int( mo.group(4) )
                tw.x      = int (mo.group(5) )
                tw.y      = int (mo.group(6) )
                tw.title  = re.sub('\"', '', tw.title)
#    this rather ugly hack makes my fake table used for debugging work
                if tw.title == "PokerStars.py": continue

#    use this eval thingie to call the title bar decoder specified in the config file
                eval("%s(tw)" % c.supported_sites[s].decoder)
                tables[tw.name] = tw
    return tables

def pokerstars_decode_table(tw):
#    extract the table name OR the tournament number and table name from the title
#    other info in title is redundant with data in the database 
    title_bits = re.split(' - ', tw.title)
    name = title_bits[0]
    mo = re.search('Tournament (\d+) Table (\d+)', name)
    if mo:
        tw.tournament = int( mo.group(1) )
        tw.table      = int( mo.group(2) )
        tw.name       = name
    else:
        tw.tournament = None
        for pattern in [' no all-in', ' fast', ',']:
            name = re.sub(pattern, '', name)
        name = re.sub('\s+$', '', name)
        tw.name = name

    mo = re.search('(Razz|Stud H/L|Stud|Omaha H/L|Omaha|Hold\'em|5-Card Draw|Triple Draw 2-7 Lowball)', tw.title)
    
#Traceback (most recent call last):
#  File "/home/fatray/razz-poker-productio/HUD_main.py", line 41, in process_new_hand
#    table_windows = Tables.discover(config)
#  File "/home/fatray/razz-poker-productio/Tables.py", line 58, in discover
#    eval("%s(tw)" % c.supported_sites[s].decoder)
#  File "<string>", line 1, in <module>
#  File "/home/fatray/razz-poker-productio/Tables.py", line 80, in pokerstars_decode_table
#    tw.game = mo.group(1).lower()
#AttributeError: 'NoneType' object has no attribute 'group'
#
#This problem happens with observed windows!!

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

if __name__=="__main__":
    c = Configuration.Config()
    tables = discover(c)
    
    for t in tables.keys():
        print tables[t]