#!/usr/bin/env python
"""Configuration.py

Handles HUD configuration files.
"""
#    Copyright 2008, 2009,  Ray E. Barker

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
import inspect
import string
import traceback
import shutil
import xml.dom.minidom
from xml.dom.minidom import Node

def fix_tf(x, default = True):
    if x == "1" or x == 1 or string.lower(x) == "true"  or string.lower(x) == "t":
        return True
    if x == "0" or x == 0 or string.lower(x) == "false" or string.lower(x) == "f":
        return False
    return default

class Layout:
    def __init__(self, node):

        self.max      = int( node.getAttribute('max') )
        if node.hasAttribute('fav_seat'): self.fav_seat = int( node.getAttribute('fav_seat') )
        self.width    = int( node.getAttribute('width') )
        self.height   = int( node.getAttribute('height') )
        
        self.location = []
        self.location = map(lambda x: None, range(self.max+1)) # there must be a better way to do this?

        for location_node in node.getElementsByTagName('location'):
            if location_node.getAttribute('seat') != "":
                self.location[int( location_node.getAttribute('seat') )] = (int( location_node.getAttribute('x') ), int( location_node.getAttribute('y')))
            elif location_node.getAttribute('common') != "":
                self.common = (int( location_node.getAttribute('x') ), int( location_node.getAttribute('y')))

    def __str__(self):
        temp = "    Layout = %d max, width= %d, height = %d" % (self.max, self.width, self.height)
        if hasattr(self, 'fav_seat'): temp = temp + ", fav_seat = %d\n" % self.fav_seat
        else: temp = temp + "\n"
        if hasattr(self, "common"):
            temp = temp + "        Common = (%d, %d)\n" % (self.common[0], self.common[1])
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
        self.enabled      = node.getAttribute("enabled")
        self.aux_window   = node.getAttribute("aux_window")
        self.font         = node.getAttribute("font")
        self.font_size    = node.getAttribute("font_size")
        self.use_frames    = node.getAttribute("use_frames")
        self.layout       = {}

        for layout_node in node.getElementsByTagName('layout'):
            lo = Layout(layout_node)
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

        aux_text = node.getAttribute("aux")
        aux_list = aux_text.split(',')
        for i in range(0, len(aux_list)):
            aux_list[i] = aux_list[i].strip()
        self.aux = aux_list

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
            stat.hudcolor  = stat_node.getAttribute("hudcolor")
            
            self.stats[stat.stat_name] = stat
            
    def __str__(self):
        temp = "Game = " + self.game_name + "\n"
        temp = temp + "    db = %s\n" % self.db
        temp = temp + "    rows = %d\n" % self.rows
        temp = temp + "    cols = %d\n" % self.cols
        temp = temp + "    aux = %s\n" % self.aux
        
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

class Aux_window:
    def __init__(self, node):
        for (name, value) in node.attributes.items():
            setattr(self, name, value)

        self.layout = {}
        for layout_node in node.getElementsByTagName('layout'):
            lo = Layout(layout_node)
            self.layout[lo.max] = lo

    def __str__(self):
        temp = 'Aux = ' + self.name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            if key == 'layout':  continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"

        for layout in self.layout:
            temp = temp + "%s" % self.layout[layout]
        return temp

class HHC:
    def __init__(self, node):
        self.site      = node.getAttribute("site")
        self.converter = node.getAttribute("converter")

    def __str__(self):
        return "%s:\t%s" % (self.site, self.converter)


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
        self.interval      = node.getAttribute("interval")
        self.callFpdbHud   = node.getAttribute("callFpdbHud")
        self.hhArchiveBase = node.getAttribute("hhArchiveBase")
        self.saveActions = fix_tf(node.getAttribute("saveActions"), True)
        self.fastStoreHudCache = fix_tf(node.getAttribute("fastStoreHudCache"), True)

    def __str__(self):
        return "    interval = %s\n    callFpdbHud = %s\n    hhArchiveBase = %s\n    saveActions = %s\n    fastStoreHudCache = %s\n" \
             % (self.interval, self.callFpdbHud, self.hhArchiveBase, self.saveActions, self.fastStoreHudCache)

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
        self.aux_windows = {}
        self.hhcs = {}
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
        for aw_node in doc.getElementsByTagName("aw"):
            aw = Aux_window(node = aw_node)
            self.aux_windows[aw.name] = aw

#       s_dbs = doc.getElementsByTagName("mucked_windows")
        for hhc_node in doc.getElementsByTagName("hhc"):
            hhc = HHC(node = hhc_node)
            self.hhcs[hhc.site] = hhc

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

    def get_aux_node(self, aux):
        for aux_node in self.doc.getElementsByTagName("aw"):
            if aux_node.getAttribute("name") == aux:
                return aux_node

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
        if seat == "common":
            for location_node in layout_node.getElementsByTagName("location"):
                if location_node.hasAttribute("common"):
                    return location_node
        else:
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
        site_node   = self.get_site_node(site_name)
        layout_node = self.get_layout_node(site_node, max)
        if layout_node == None: return
        for i in range(1, max + 1):
            location_node = self.get_location_node(layout_node, i)
            location_node.setAttribute("x", str( locations[i-1][0] ))
            location_node.setAttribute("y", str( locations[i-1][1] ))
            self.supported_sites[site_name].layout[max].location[i] = ( locations[i-1][0], locations[i-1][1] )

    def edit_aux_layout(self, aux_name, max, width = None, height = None, locations = None):
        aux_node   = self.get_aux_node(aux_name)
        layout_node = self.get_layout_node(aux_node, max)
        if layout_node == None:
            print "aux node not found"
            return
        print "editing locations =", locations
        for (i, pos) in locations.iteritems():
            location_node = self.get_location_node(layout_node, i)
            location_node.setAttribute("x", str( locations[i][0] ))
            location_node.setAttribute("y", str( locations[i][1] ))
            if i == "common":
                self.aux_windows[aux_name].layout[max].common = ( locations[i][0], locations[i][1] )
            else:
                self.aux_windows[aux_name].layout[max].location[i] = ( locations[i][0], locations[i][1] )

    def get_db_parameters(self, name = None):
        if name == None: name = 'fpdb'
        db = {}
        try:    db['db-databaseName'] = name
        except: pass

        try:    db['db-host'] = self.supported_databases[name].db_ip
        except: pass

        try:    db['db-user'] = self.supported_databases[name].db_user
        except: pass

        try:    db['db-password'] = self.supported_databases[name].db_pass
        except: pass

        try:    db['db-server'] = self.supported_databases[name].db_server
        except: pass

        if   string.lower(self.supported_databases[name].db_server) == 'mysql':
            db['db-backend'] = 2
        elif string.lower(self.supported_databases[name].db_server) == 'postgresql':
            db['db-backend'] = 3
        else: db['db-backend'] = None # this is big trouble
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
        try:    tv['combinedStealFold'] = self.tv.combinedStealFold
        except: tv['combinedStealFold'] = True

        try:    tv['combined2B3B']      = self.tv.combined2B3B
        except: tv['combined2B3B']      = True

        try:    tv['combinedPostflop']  = self.tv.combinedPostflop
        except: tv['combinedPostflop']  = True
        return tv
    
    def get_import_parameters(self):
        imp = {}
        try:     imp['callFpdbHud']       = self.imp.callFpdbHud
        except:  imp['callFpdbHud']       = True

        try:     imp['interval']          = self.imp.interval
        except:  imp['interval']          = 10

        try:     imp['hhArchiveBase']     = self.imp.hhArchiveBase
        except:  imp['hhArchiveBase']     = "~/.fpdb/HandHistories/"

        try:     imp['saveActions']       = self.imp.saveActions
        except:  imp['saveActions']       = True

        try:     imp['fastStoreHudCache'] = self.imp.fastStoreHudCache
        except:  imp['fastStoreHudCache'] = True
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
    
    def get_frames(self, site = "PokerStars"):
        return self.supported_sites[site].use_frames == "True"

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
    
    def get_default_font(self, site = 'PokerStars'):
        (font, font_size) = ("Sans", "8")
        if self.supported_sites[site].font == "":
            font = "Sans"
        else:
            font = self.supported_sites[site].font

        if self.supported_sites[site].font_size == "":
            font_size = "8"
        else:
            font_size = self.supported_sites[site].font_size
        return (font, font_size)

    def get_locations(self, site = "PokerStars", max = "8"):
        
        try:
            locations = self.supported_sites[site].layout[max].location
        except:
            locations = ( (  0,   0), (684,  61), (689, 239), (692, 346), 
                          (586, 393), (421, 440), (267, 440), (  0, 361),
                          (  0, 280), (121, 280), ( 46,  30) )
        return locations

    def get_aux_locations(self, aux = "mucked", max = "9"):
        
        try:
            locations = self.aux_windows[aux].layout[max].location
        except:
            locations = ( (  0,   0), (684,  61), (689, 239), (692, 346), 
                          (586, 393), (421, 440), (267, 440), (  0, 361),
                          (  0, 280), (121, 280), ( 46,  30) )
        return locations

    def get_supported_sites(self):
        """Returns the list of supported sites."""
        return self.supported_sites.keys()

    def get_site_parameters(self, site):
        """Returns a dict of the site parameters for the specified site"""
        if not self.supported_sites.has_key(site):
            return None
        parms = {}
        parms["converter"]    = self.supported_sites[site].converter
        parms["decoder"]      = self.supported_sites[site].decoder
        parms["hudbgcolor"]   = self.supported_sites[site].hudbgcolor
        parms["hudfgcolor"]   = self.supported_sites[site].hudfgcolor
        parms["hudopacity"]   = self.supported_sites[site].hudopacity
        parms["screen_name"]  = self.supported_sites[site].screen_name
        parms["site_path"]    = self.supported_sites[site].site_path
        parms["table_finder"] = self.supported_sites[site].table_finder
        parms["HH_path"]      = self.supported_sites[site].HH_path
        parms["site_name"]    = self.supported_sites[site].site_name
        parms["enabled"]      = self.supported_sites[site].enabled
        parms["aux_window"]   = self.supported_sites[site].aux_window
        parms["font"]         = self.supported_sites[site].font
        parms["font_size"]    = self.supported_sites[site].font_size
        return parms

    def set_site_parameters(self, site_name, converter = None, decoder = None,
                            hudbgcolor = None, hudfgcolor = None, 
                            hudopacity = None, screen_name = None,
                            site_path = None, table_finder = None,
                            HH_path = None, enabled = None,
                            font = None, font_size = None):
        """Sets the specified site parameters for the specified site."""
        site_node = self.get_site_node(site_name)
        if not db_node == None:
            if not converter      == None: site_node.setAttribute("converter", converter)
            if not decoder        == None: site_node.setAttribute("decoder", decoder)
            if not hudbgcolor     == None: site_node.setAttribute("hudbgcolor", hudbgcolor)
            if not hudfgcolor     == None: site_node.setAttribute("hudfgcolor", hudfgcolor)
            if not hudopacity     == None: site_node.setAttribute("hudopacity", hudopacity)
            if not screen_name    == None: site_node.setAttribute("screen_name", screen_name)
            if not site_path      == None: site_node.setAttribute("site_path", site_path)
            if not table_finder   == None: site_node.setAttribute("table_finder", table_finder)
            if not HH_path        == None: site_node.setAttribute("HH_path", HH_path)
            if not enabled        == None: site_node.setAttribute("enabled", enabled)
            if not font           == None: site_node.setAttribute("font", font)
            if not font_size      == None: site_node.setAttribute("font_size", font_size)
        return

    def get_aux_windows(self):
        """Gets the list of mucked window formats in the configuration."""
        mw = []
        for w in self.aux_windows.keys():
            mw.append(w)
        return mw

    def get_aux_parameters(self, name):
        """Gets a dict of mucked window parameters from the named mw."""
        param = {}
        if self.aux_windows.has_key(name):
            for key in dir(self.aux_windows[name]):
                if key.startswith('__'): continue
                value = getattr(self.aux_windows[name], key)
                if callable(value): continue
                param[key] = value

            return param
        return None
    
    def get_game_parameters(self, name):
        """Get the configuration parameters for the named game."""
        param = {}
        if self.supported_games.has_key(name):
            param['game_name'] = self.supported_games[name].game_name
            param['db']        = self.supported_games[name].db
            param['rows']      = self.supported_games[name].rows
            param['cols']      = self.supported_games[name].cols
            param['aux']       = self.supported_games[name].aux
        return param

    def get_supported_games(self):
        """Get the list of supported games."""
        sg = []
        for game in c.supported_games.keys():
            sg.append(c.supported_games[game].game_name)
        return sg

    def execution_path(self, filename):
        """Join the fpdb path to filename."""
        return os.path.join(os.path.dirname(inspect.getfile(sys._getframe(0))), filename)

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

    print "\n----------- AUX WINDOW FORMATS -----------"
    for w in c.aux_windows.keys():
        print c.aux_windows[w]
    print "----------- END AUX WINDOW FORMATS -----------"

    print "\n----------- HAND HISTORY CONVERTERS -----------"
    for w in c.hhcs.keys():
        print c.hhcs[w]
    print "----------- END HAND HISTORY CONVERTERS -----------"
    
    print "\n----------- POPUP WINDOW FORMATS -----------"
    for w in c.popup_windows.keys():
        print c.popup_windows[w]
    print "----------- END POPUP WINDOW FORMATS -----------"

    print "\n----------- IMPORT -----------"
    print c.imp
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
    for mw in c.get_aux_windows():
        print c.get_aux_parameters(mw)

    print "mucked locations =", c.get_aux_locations('mucked', 9)
#    c.edit_aux_layout('mucked', 9, locations = [(487, 113), (555, 469), (572, 276), (522, 345), 
#                                                (333, 354), (217, 341), (150, 273), (150, 169), (230, 115)])
#    print "mucked locations =", c.get_aux_locations('mucked', 9)

    for site in c.supported_sites.keys():
        print "site = ", site,
        print c.get_site_parameters(site)
        print c.get_default_font(site)

    for game in c.get_supported_games():
        print c.get_game_parameters(game)

    print "start up path = ", c.execution_path("")
