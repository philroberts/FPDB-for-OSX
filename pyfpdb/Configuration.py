#!/usr/bin/env python
"""Configuration.py

Handles HUD configuration files.
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
import xml.dom.minidom
from xml.dom.minidom import Node

class Layout:
    def __init__(self, max):
        self.max = int(max)
        self.location = []
        for i in range(self.max + 1): self.location.append(None)
        
    def __str__(self):
        temp = "    Layout = %d max, width= %d, height = %d, fav_seat = %d\n" % (self.max, self.width, self.height, self.fav_seat)
        temp = temp + "        Locations = "
        for i in range(1, len(self.location)):
            temp = temp + "(%d,%d)" % self.location[i]
        
        return temp

class Site:
    def __init__(self, node):
        self.site_name    = node.getAttribute("site_name")
        self.table_finder = node.getAttribute("table_finder")
        self.screen_name  = node.getAttribute("screen_name")
        self.site_path    = node.getAttribute("site_path")
        self.HH_path      = node.getAttribute("HH_path")
        self.decoder      = node.getAttribute("decoder")
        self.layout       = {}
        
        for layout_node in node.getElementsByTagName('layout'):
            max         = int( layout_node.getAttribute('max') )
            lo = Layout(max)
            lo.fav_seat = int( layout_node.getAttribute('fav_seat') )
            lo.width    = int( layout_node.getAttribute('width') )
            lo.height   = int( layout_node.getAttribute('height') )
            
            for location_node in layout_node.getElementsByTagName('location'):
                lo.location[int( location_node.getAttribute('seat') )] = (int( location_node.getAttribute('x') ), int( location_node.getAttribute('y')))
                
            self.layout[lo.max] = lo

    def __str__(self):
        temp = "Site = " + self.site_name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            if key == 'layout':  continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"
            
        for layout in self.layout:
            temp = temp + "%s" % self.layout[layout]
            
        return temp
        
class Stat:
    def __init__(self):
        pass
    
    def __str__(self):
        temp = "        stat_name = %s, row = %d, col = %d, tip = %s, click = %s\n" % (self.stat_name, self.row, self.col, self.tip, self.click)
        return temp
                
class Game:
    def __init__(self, node):
        self.game_name = node.getAttribute("game_name")
        self.db        = node.getAttribute("db")
        self.rows      = int( node.getAttribute("rows") )
        self.cols      = int( node.getAttribute("cols") )

        self.stats     = {}
        for stat_node in node.getElementsByTagName('stat'):
            stat = Stat()
            stat.stat_name = stat_node.getAttribute("stat_name")
            stat.row       = int( stat_node.getAttribute("row") )
            stat.col       = int( stat_node.getAttribute("col") )
            stat.tip       = stat_node.getAttribute("tip")
            stat.click     = stat_node.getAttribute("click")
            
            self.stats[stat.stat_name] = stat
            
    def __str__(self):
        temp = "Game = " + self.game_name + "\n"
        temp = temp + "    db = %s\n" % self.db
        temp = temp + "    rows = %d\n" % self.rows
        temp = temp + "    cols = %d\n" % self.cols
        
        for stat in self.stats.keys():
            temp = temp + "%s" % self.stats[stat]
            
        return temp
             
class Database:
    def __init__(self, node):
        self.db_name   = node.getAttribute("db_name")
        self.db_server = node.getAttribute("db_server")
        self.db_ip     = node.getAttribute("db_ip")
        self.db_user   = node.getAttribute("db_user")
        self.db_type   = node.getAttribute("db_type")
        self.db_pass   = node.getAttribute("db_pass")
        
    def __str__(self):
        temp = 'Database = ' + self.db_name + '\n'
        for key in dir(self):
            if key.startswith('__'): continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"
        return temp

class Mucked:
    def __init__(self, node):
        self.name    = node.getAttribute("mw_name")
        self.cards   = node.getAttribute("deck")
        self.card_wd = node.getAttribute("card_wd")
        self.card_ht = node.getAttribute("card_ht")
        self.rows    = node.getAttribute("rows")
        self.cols    = node.getAttribute("cols")
        self.format  = node.getAttribute("stud")

    def __str__(self):
        temp = 'Mucked = ' + self.name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"
        return temp

class Config:
    def __init__(self, file = 'HUD_config.xml'):

        doc = xml.dom.minidom.parse(file)

        self.supported_sites = {}
        self.supported_games = {}
        self.supported_databases = {}
        self.mucked_windows = {}

#        s_sites = doc.getElementsByTagName("supported_sites")
        for site_node in doc.getElementsByTagName("site"):
            site = Site(node = site_node)
            self.supported_sites[site.site_name] = site

        s_games = doc.getElementsByTagName("supported_games")
        for game_node in doc.getElementsByTagName("game"):
            game = Game(node = game_node)
            self.supported_games[game.game_name] = game
            
        s_dbs = doc.getElementsByTagName("supported_databases")
        for db_node in doc.getElementsByTagName("database"):
            db = Database(node = db_node)
            self.supported_databases[db.db_name] = db

        s_dbs = doc.getElementsByTagName("mucked_windows")
        for mw_node in doc.getElementsByTagName("mw"):
            mw = Mucked(node = mw_node)
            self.mucked_windows[mw.name] = mw

if __name__== "__main__":
    c = Config()
    
    print "\n----------- SUPPORTED SITES -----------"
    for s in c.supported_sites.keys():
        print c.supported_sites[s]

    print "----------- END SUPPORTED SITES -----------"


    print "\n----------- SUPPORTED GAMES -----------"
    for game in c.supported_games.keys():
        print c.supported_games[game]

    print "----------- END SUPPORTED GAMES -----------"


    print "\n----------- SUPPORTED DATABASES -----------"
    for db in c.supported_databases.keys():
        print c.supported_databases[db]

    print "----------- END SUPPORTED DATABASES -----------"

    print "\n----------- MUCKED WINDOW FORMATS -----------"
    for w in c.mucked_windows.keys():
        print c.mucked_windows[w]

    print "----------- END MUCKED WINDOW FORMATS -----------"
