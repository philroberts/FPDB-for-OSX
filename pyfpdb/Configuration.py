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
import os
import sys
import string
import traceback
import shutil
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
        
        return temp + "\n"

class Site:
    def __init__(self, node):
        self.site_name    = node.getAttribute("site_name")
        self.table_finder = node.getAttribute("table_finder")
        self.screen_name  = node.getAttribute("screen_name")
        self.site_path    = node.getAttribute("site_path")
        self.HH_path      = node.getAttribute("HH_path")
        self.decoder      = node.getAttribute("decoder")
        self.hudopacity   = node.getAttribute("hudopacity")
        self.hudbgcolor   = node.getAttribute("bgcolor")
        self.hudfgcolor   = node.getAttribute("fgcolor")
        self.converter    = node.getAttribute("converter")
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
            temp = temp + '    ' + key + " = " + str(value) + "\n"
            
        for layout in self.layout:
            temp = temp + "%s" % self.layout[layout]
            
        return temp
        
class Stat:
    def __init__(self):
        pass
    
    def __str__(self):
        temp = "        stat_name = %s, row = %d, col = %d, tip = %s, click = %s, popup = %s\n" % (self.stat_name, self.row, self.col, self.tip, self.click, self.popup)
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
            stat.popup     = stat_node.getAttribute("popup")
            stat.hudprefix = stat_node.getAttribute("hudprefix")
            stat.hudsuffix = stat_node.getAttribute("hudsuffix")
            
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

class Popup:
    def __init__(self, node):
        self.name  = node.getAttribute("pu_name")
        self.pu_stats     = []
        for stat_node in node.getElementsByTagName('pu_stat'):
            self.pu_stats.append(stat_node.getAttribute("pu_stat_name"))
        
    def __str__(self):
        temp = "Popup = " + self.name + "\n"
        for stat in self.pu_stats:
            temp = temp + " " + stat
        return temp + "\n"

class Import:
    def __init__(self, node):
        self.interval    = node.getAttribute("interval")
        self.callFpdbHud = node.getAttribute("callFpdbHud")

    def __str__(self):
        return "    interval = %s\n    callFpdbHud = %s\n" % (self.interval, self.callFpdbHud)

class Tv:
    def __init__(self, node):
        self.combinedStealFold = node.getAttribute("combinedStealFold")
        self.combined2B3B      = node.getAttribute("combined2B3B")
        self.combinedPostflop  = node.getAttribute("combinedPostflop")

    def __str__(self):
        return ("    combinedStealFold = %s\n    combined2B3B = %s\n    combinedPostflop = %s\n" % 
                (self.combinedStealFold, self.combined2B3B, self.combinedPostflop) )

class Config:
    def __init__(self, file = None):

#    "file" is a path to an xml file with the fpdb/HUD configuration
#    we check the existence of "file" and try to recover if it doesn't exist

        self.default_config_path = self.get_default_config_path()
        if not file == None: # configuration file path has been passed
            if not os.path.exists(file):
                print "Configuration file %s not found.  Using defaults." % (file)
                sys.stderr.write("Configuration file %s not found.  Using defaults." % (file))
                file = None

        if file == None: # configuration file path not passed or invalid
            file = self.find_config() #Look for a config file in the normal places

        if file == None: # no config file in the normal places
            file = self.find_example_config() #Look for an example file to edit
            if not file == None:
                pass
            
        if file == None: # that didn't work either, just die
            print "No HUD_config_xml found.  Exiting"
            sys.stderr.write("No HUD_config_xml found.  Exiting")
            sys.exit()

#    Parse even if there was no real config file found and we are using the example
#    If using the example, we'll edit it later
        try:
            print "Reading configuration file %s\n" % (file)
            doc = xml.dom.minidom.parse(file)
        except:
            print "Error parsing %s.  See error log file." % (file)
            traceback.print_exc(file=sys.stderr)
            print "press enter to continue"
            sys.stdin.readline()
            sys.exit()

        self.doc = doc
        self.file = file
        self.supported_sites = {}
        self.supported_games = {}
        self.supported_databases = {}
        self.mucked_windows = {}
        self.popup_windows = {}

#        s_sites = doc.getElementsByTagName("supported_sites")
        for site_node in doc.getElementsByTagName("site"):
            site = Site(node = site_node)
            self.supported_sites[site.site_name] = site

#        s_games = doc.getElementsByTagName("supported_games")
        for game_node in doc.getElementsByTagName("game"):
            game = Game(node = game_node)
            self.supported_games[game.game_name] = game
            
#        s_dbs = doc.getElementsByTagName("supported_databases")
        for db_node in doc.getElementsByTagName("database"):
            db = Database(node = db_node)
            self.supported_databases[db.db_name] = db

#       s_dbs = doc.getElementsByTagName("mucked_windows")
        for mw_node in doc.getElementsByTagName("mw"):
            mw = Mucked(node = mw_node)
            self.mucked_windows[mw.name] = mw

#        s_dbs = doc.getElementsByTagName("popup_windows")
        for pu_node in doc.getElementsByTagName("pu"):
            pu = Popup(node = pu_node)
            self.popup_windows[pu.name] = pu

        for imp_node in doc.getElementsByTagName("import"):
            imp = Import(node = imp_node)
            self.imp = imp

        for tv_node in doc.getElementsByTagName("tv"):
            tv = Tv(node = tv_node)
            self.tv = tv

        db = self.get_db_parameters('fpdb')
        if db['db-password'] == 'YOUR MYSQL PASSWORD':
            df_file = self.find_default_conf()
            if df_file == None: # this is bad
                pass
            else:
                df_parms = self.read_default_conf(df_file)
                self.set_db_parameters(db_name = 'fpdb', db_ip = df_parms['db-host'],
                                       db_user = df_parms['db-user'],
                                       db_pass = df_parms['db-password'])
                self.save(file=os.path.join(self.default_config_path, "HUD_config.xml"))

                
    def find_config(self):
        """Looks in cwd and in self.default_config_path for a config file."""
        if os.path.exists('HUD_config.xml'):    # there is a HUD_config in the cwd
            file = 'HUD_config.xml'             # so we use it
        else: # no HUD_config in the cwd, look where it should be in the first place
            config_path = os.path.join(self.default_config_path, 'HUD_config.xml')
            if os.path.exists(config_path):
                file = config_path
            else:
                file = None
        return file

    def get_default_config_path(self):
        """Returns the path where the fpdb config file _should_ be stored."""
        if os.name == 'posix':
            config_path = os.path.join(os.path.expanduser("~"), '.fpdb')
        elif os.name == 'nt':
            config_path = os.path.join(os.environ["APPDATA"], 'fpdb')
        else: config_path = None
        return config_path


    def find_default_conf(self):
        if os.name == 'posix':
            config_path = os.path.join(os.path.expanduser("~"), '.fpdb', 'default.conf')
        elif os.name == 'nt':
            config_path = os.path.join(os.environ["APPDATA"], 'fpdb', 'default.conf')
        else: config_path = False

        if config_path and os.path.exists(config_path):
            file = config_path
        else:
            file = None
        return file

    def read_default_conf(self, file):
        parms = {}
        fh = open(file, "r")
        for line in fh:
            line = string.strip(line)
            (key, value) = line.split('=')
            parms[key] = value
        fh.close
        return parms
                
    def find_example_config(self):
        if os.path.exists('HUD_config.xml.example'):    # there is a HUD_config in the cwd
            file = 'HUD_config.xml.example'             # so we use it
            print "No HUD_config.xml found, using HUD_config.xml.example.\n", \
                "A HUD_config.xml will be written.  You will probably have to edit it."
            sys.stderr.write("No HUD_config.xml found, using HUD_config.xml.example.\n" + \
                "A HUD_config.xml will be written.  You will probably have to edit it.")
        else:
            file = None
        return file

    def get_site_node(self, site):
        for site_node in self.doc.getElementsByTagName("site"):
            if site_node.getAttribute("site_name") == site:
                return site_node

    def get_db_node(self, db_name):
        for db_node in self.doc.getElementsByTagName("database"):
            if db_node.getAttribute("db_name") == db_name:
                return db_node
        return None

    def get_layout_node(self, site_node, layout):
        for layout_node in site_node.getElementsByTagName("layout"):
            if layout_node.getAttribute("max") == None: 
                return None
            if int( layout_node.getAttribute("max") ) == int( layout ):
                return layout_node

    def get_location_node(self, layout_node, seat):
        for location_node in layout_node.getElementsByTagName("location"):
            if int( location_node.getAttribute("seat") ) == int( seat ):
                return location_node

    def save(self, file = None):
        if not file == None:
            f = open(file, 'w')
            self.doc.writexml(f)
            f.close()
        else:
            shutil.move(self.file, self.file+".backup")
            f = open(self.file, 'w')
            self.doc.writexml(f)
            f.close

    def edit_layout(self, site_name, max, width = None, height = None,
                    fav_seat = None, locations = None):
        print "max = ", max
        site_node   = self.get_site_node(site_name)
        layout_node = self.get_layout_node(site_node, max)
        if layout_node == None: return
        for i in range(1, max + 1):
            location_node = self.get_location_node(layout_node, i)
            location_node.setAttribute("x", str( locations[i-1][0] ))
            location_node.setAttribute("y", str( locations[i-1][1] ))
            self.supported_sites[site_name].layout[max].location[i] = ( locations[i-1][0], locations[i-1][1] )

    def get_db_parameters(self, name = None):
        if name == None: name = 'fpdb'
        db = {}
        try:
            db['db-databaseName'] = name
            db['db-host'] = self.supported_databases[name].db_ip
            db['db-user'] = self.supported_databases[name].db_user
            db['db-password'] = self.supported_databases[name].db_pass
            db['db-server'] = self.supported_databases[name].db_server
            if   string.lower(self.supported_databases[name].db_server) == 'mysql':
                db['db-backend'] = 2
            elif string.lower(self.supported_databases[name].db_server) == 'postgresql':
                db['db-backend'] = 3
            else: db['db-backend'] = None # this is big trouble
        except:
            pass
        return db

    def set_db_parameters(self, db_name = 'fpdb', db_ip = None, db_user = None,
                          db_pass = None, db_server = None, db_type = None):
        db_node = self.get_db_node(db_name)
        if not db_node == None:
            if not db_ip     == None: db_node.setAttribute("db_ip", db_ip)
            if not db_user   == None: db_node.setAttribute("db_user", db_user)
            if not db_pass   == None: db_node.setAttribute("db_pass", db_pass)
            if not db_server == None: db_node.setAttribute("db_server", db_server)
            if not db_type   == None: db_node.setAttribute("db_type", db_type)
        if self.supported_databases.has_key(db_name):
            if not db_ip     == None: self.supported_databases[db_name].dp_ip     = db_ip
            if not db_user   == None: self.supported_databases[db_name].dp_user   = db_user
            if not db_pass   == None: self.supported_databases[db_name].dp_pass   = db_pass
            if not db_server == None: self.supported_databases[db_name].dp_server = db_server
            if not db_type   == None: self.supported_databases[db_name].dp_type   = db_type
        return

    def get_tv_parameters(self):
        tv = {}
        try:
            tv['combinedStealFold'] = self.tv.combinedStealFold
            tv['combined2B3B']      = self.tv.combined2B3B
            tv['combinedPostflop']  = self.tv.combinedPostflop
        except: # Default tv parameters
            tv['combinedStealFold'] = True
            tv['combined2B3B']      = True
            tv['combinedPostflop']  = True
        return tv
    
    def get_import_parameters(self):
        imp = {}
        try:
            imp['imp-callFpdbHud'] = self.imp.callFpdbHud
            imp['hud-defaultInterval']    = int(self.imp.interval)
        except: # Default import parameters
            imp['imp-callFpdbHud'] = True
            imp['hud-defaultInterval']    = 10
        return imp

    def get_default_paths(self, site = "PokerStars"):
        paths = {}
        try:
            paths['hud-defaultPath']        = os.path.expanduser(self.supported_sites[site].HH_path)
            paths['bulkImport-defaultPath'] = os.path.expanduser(self.supported_sites[site].HH_path)
        except:
            paths['hud-defaultPath']        = "default"
            paths['bulkImport-defaultPath'] = "default"
        return paths

    def get_default_colors(self, site = "PokerStars"):
        colors = {}
        if self.supported_sites[site].hudopacity == "":
            colors['hudopacity'] = 0.90
        else:
            colors['hudopacity'] = float(self.supported_sites[site].hudopacity)
        if self.supported_sites[site].hudbgcolor == "":
            colors['hudbgcolor'] = "#FFFFFF"
        else:
            colors['hudbgcolor'] = self.supported_sites[site].hudbgcolor
        if self.supported_sites[site].hudfgcolor == "":
            colors['hudfgcolor'] = "#000000"
        else:
            colors['hudfgcolor'] = self.supported_sites[site].hudfgcolor
        return colors

    def get_locations(self, site = "PokerStars", max = "8"):
        
        try:
            locations = self.supported_sites[site].layout[max].location
        except:
            locations = ( (  0,   0), (684,  61), (689, 239), (692, 346), 
                          (586, 393), (421, 440), (267, 440), (  0, 361),
                          (  0, 280), (121, 280), ( 46,  30) )
        return locations


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
    
    print "\n----------- POPUP WINDOW FORMATS -----------"
    for w in c.popup_windows.keys():
        print c.popup_windows[w]
    print "----------- END MUCKED WINDOW FORMATS -----------"

    print "\n----------- IMPORT -----------"
#    print c.imp
    print "----------- END IMPORT -----------"

    print "\n----------- TABLE VIEW -----------"
#    print c.tv
    print "----------- END TABLE VIEW -----------"

    c.edit_layout("PokerStars", 6, locations=( (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6) ))
    c.save(file="testout.xml")
    
    print "db     = ", c.get_db_parameters()
#    print "tv     = ", c.get_tv_parameters()
#    print "imp    = ", c.get_import_parameters()
    print "paths  = ", c.get_default_paths("PokerStars")
    print "colors = ", c.get_default_colors("PokerStars")
    print "locs   = ", c.get_locations("PokerStars", 8)
