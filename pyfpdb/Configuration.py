#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configuration.py

Handles fpdb/fpdb-hud configuration files.
"""
#    Copyright 2008-2012,  Ray E. Barker

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

#TODO fix / rethink edit stats - it is broken badly just now

#    Standard Library modules
from __future__ import with_statement

import L10n
_ = L10n.get_translation()

import codecs
import os
import sys
import inspect
import string
import shutil
import locale
import re
import xml.dom.minidom
from xml.dom.minidom import Node

import platform
if platform.system() == 'Windows':
    import winpaths
    winpaths_appdata = winpaths.get_appdata()
else:
    winpaths_appdata = False

import logging, logging.config
import ConfigParser

# config version is used to flag a warning at runtime if the users config is
#  out of date.
# The CONFIG_VERSION should be incremented __ONLY__ if the add_missing_elements()
#  method cannot update existing standard configurations
CONFIG_VERSION = 83

#
# Setup constants
# code is centralised here to ensure uniform handling of path names
# especially important when user directory includes non-ascii chars
#
# INSTALL_METHOD ("source" or "exe")
# FPDB_ROOT_PATH (path to the root fpdb installation dir root (normally ...../fpdb)
# APPDATA_PATH (root path for appdata eg /~ or appdata)
# CONFIG_PATH (path to the directory holding logs, sqlite db's and config)
# GRAPHICS_PATH (path to graphics assets (normally .gfx)
# PYFPDB_PATH (path to py's)
# OS_FAMILY (OS Family for installed system (Linux, Mac, XP, Win7)
# POSIX (True=Linux or Mac platform, False=Windows platform)
# PYTHON_VERSION (n.n)

if hasattr(sys, "frozen"):
    if platform.system() == 'Windows':
        INSTALL_METHOD = "exe"
    elif platform.system() == 'Darwin':
        INSTALL_METHOD = "app"
else:
    INSTALL_METHOD = "source"

if INSTALL_METHOD == "exe" or INSTALL_METHOD == "app":
    FPDB_ROOT_PATH = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding())) # should be exe path to \fpdbroot\pyfpdb
elif sys.path[0] == "": # we are probably running directly (>>>import Configuration)
    temp = os.getcwdu() # should be ./pyfpdb
    FPDB_ROOT_PATH = os.path.join(temp, os.pardir)   # go up one level (to fpdbroot)
else: # all other cases
    FPDB_ROOT_PATH = os.path.dirname(unicode(sys.path[0], sys.getfilesystemencoding()))  # should be source path to /fpdbroot

sysPlatform = platform.system()  #Linux, Windows, Darwin
if sysPlatform[0:5] == 'Linux':
    OS_FAMILY = 'Linux'
elif sysPlatform == 'Darwin':
    OS_FAMILY = 'Mac'
elif sysPlatform == 'Windows':
    if platform.release() <> 'XP':
        OS_FAMILY = 'Win7' #Vista and win7
    else:
        OS_FAMILY = 'XP'
else:
    OS_FAMILY = False

GRAPHICS_PATH = os.path.join(FPDB_ROOT_PATH, u"gfx")
PYFPDB_PATH = os.path.join(FPDB_ROOT_PATH, u"pyfpdb")

if OS_FAMILY in ['XP', 'Win7']:
    APPDATA_PATH = winpaths_appdata
    CONFIG_PATH = os.path.join(APPDATA_PATH, u"fpdb")
elif OS_FAMILY == 'Mac':
    APPDATA_PATH = os.getenv("HOME")
    CONFIG_PATH = os.path.join(APPDATA_PATH, u".fpdb")
elif OS_FAMILY == 'Linux':
    APPDATA_PATH = os.path.expanduser(u"~")
    CONFIG_PATH = os.path.join(APPDATA_PATH, u".fpdb")
else:
    APPDATA_PATH = False
    CONFIG_PATH = False

if os.name == 'posix':
    POSIX = True
else:
    POSIX = False
    
PYTHON_VERSION = sys.version[:3]
    
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("config")

LOGLEVEL = {'DEBUG'   : logging.DEBUG,
            'INFO'    : logging.INFO,
            'WARNING' : logging.WARNING,
            'ERROR'   : logging.ERROR,
            'CRITICAL': logging.CRITICAL}

def get_config(file_name, fallback = True):
    """Looks in cwd and in self.default_config_path for a config file."""
    
    #FIXME
    # This function has become difficult to understand, plus it no-longer
    # just looks for a config file, it actually does file copying 
    
    # look for example file even if not used here, path is returned to caller
    config_found,example_found,example_copy = False,False,False
    config_path, example_path = None,None

    config_path = os.path.join(FPDB_ROOT_PATH, 'pyfpdb', file_name)
    
    #print "config_path=", config_path
    if os.path.exists(config_path):    # there is a file in the cwd
        config_found = True            # so we use it
    else: # no file in the cwd, look where it should be in the first place
        config_path = os.path.join(CONFIG_PATH, file_name)
        #print "config path 2=", config_path
        if os.path.exists(config_path):
            config_found = True
    #TODO: clean up the example path loading to ensure it behaves the same on all OSs
    # Example configuration for debian package
    if POSIX:
        # If we're on linux, try to copy example from the place
        # debian package puts it; get_default_config_path() creates
        # the config directory for us so there's no need to check it
        # again
        example_path = '/usr/share/python-fpdb/' + file_name + '.example'
        if not os.path.exists(example_path):
            if os.path.exists(file_name + '.example'):
                example_path = file_name + '.example'
            else:
                example_path = os.path.join(PYFPDB_PATH, file_name + '.example')
        if not config_found and fallback:
            try:
                shutil.copyfile(example_path, config_path)
                example_copy = True
                msg = _("Config file has been created at %s.") % (config_path)
                log.info(msg)
            except IOError:
                try:
                    example_path = file_name + '.example'
                    shutil.copyfile(example_path, config_path)
                    example_copy = True
                    msg = _("Config file has been created at %s.") % (config_path)
                    log.info(msg)
                except IOError:
                    pass

#    OK, fall back to the .example file, should be in the start dir
    elif os.path.exists(os.path.join(PYFPDB_PATH, file_name + '.example')):
        try:
            #print ""
            example_path = os.path.join(PYFPDB_PATH, file_name + '.example')
            if not config_found and fallback:
                shutil.copyfile(example_path, config_path)
                example_copy = True
                log.info (_("No %r found in \"%r\" or \"%r\".") % (file_name, FPDB_ROOT_PATH, CONFIG_PATH) \
                     + " " + _("Config file has been created at %r.") % (config_path+"\n") )

        except:
            print(_("Error copying .example config file, cannot fall back. Exiting."), "\n")
            sys.stderr.write(_("Error copying .example config file, cannot fall back. Exiting.")+"\n")
            sys.stderr.write( str(sys.exc_info()) )
            sys.exit()
    elif fallback:
        sys.stderr.write((_("No %s found, cannot fall back. Exiting.") % file_name) + "\n")
        sys.exit()

    #print "get_config: returning "+str( (config_path,example_copy,example_path) )
    return (config_path,example_copy,example_path)

def set_logfile(file_name):
    (conf_file,copied,example_file) = get_config(u"logging.conf", fallback = False)

    log_dir = os.path.join(CONFIG_PATH, u'log')
    check_dir(log_dir)
    log_file = os.path.join(log_dir, file_name)

    if conf_file:
        try:
            log_file = log_file.replace('\\', '\\\\')  # replace each \ with \\
            logging.config.fileConfig(conf_file, {"logFile":log_file})
        except:
            sys.stderr.write(_("Could not setup log file %s") % file_name)

def check_dir(path, create = True):
    """Check if a dir exists, optionally creates if not."""
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            return False
    if create:
        msg = _("Creating directory: '%s'") % (path)
        print(msg)
        log.info(msg)
        os.mkdir(path)#, "utf-8"))
    else:
        return False

def normalizePath(path):
    "Normalized existing pathes"
    if os.path.exists(path):
        return os.path.abspath(path)
    return path
            
########################################################################
# application wide consts

APPLICATION_NAME_SHORT = 'fpdb'
APPLICATION_VERSION = 'xx.xx.xx'

DATABASE_TYPE_POSTGRESQL = 'postgresql'
DATABASE_TYPE_SQLITE = 'sqlite'
DATABASE_TYPE_MYSQL = 'mysql'
DATABASE_TYPES = (
        DATABASE_TYPE_POSTGRESQL,
        DATABASE_TYPE_SQLITE,
        DATABASE_TYPE_MYSQL,
        )

LOCALE_ENCODING = locale.getpreferredencoding()
if LOCALE_ENCODING in ("US-ASCII", "", None):
    LOCALE_ENCODING = "cp1252"
    if (os.uname()[0]!="Darwin"):
        print(_("Default encoding set to US-ASCII, defaulting to CP1252 instead."), _("Please report this problem."))
    
# needs LOCALE_ENCODING (above), imported for sqlite setup in Config class below
import Charset


        
########################################################################
def string_to_bool(string, default=True):
    """converts a string representation of a boolean value to boolean True or False
    @param string: (str) the string to convert
    @param default: value to return if the string can not be converted to a boolean value
    """
    string = string.lower()
    if string in ('1', 'true', 't'):
        return True
    elif string in ('0', 'false', 'f'):
        return False
    return default

class Layout:
    def __init__(self, node):

        self.max    = int( node.getAttribute('max') )
        self.width    = int( node.getAttribute('width') )
        self.height   = int( node.getAttribute('height') )

        self.location = []
        self.hh_seats = []
        self.location = map(lambda x: None, range(self.max+1)) # fill array with max seats+1 empty entries
        # hh_seats is used to map the seat numbers specified in hand history files (and stored in db) onto 
        #   the contiguous integerss, 1 to self.max, used to index hud stat_windows (and aw seat_windows) for display
        #   For most sites these numbers are the same, but some sites (e.g. iPoker) omit seat numbers in hand histories
        #   for tables smaller than 10-max.   
        self.hh_seats= map(lambda x: None, range(self.max+1)) # fill array with max seats+1 empty entries

        for location_node in node.getElementsByTagName('location'):
            hud_seat = location_node.getAttribute('seat')
            if hud_seat != "":
                
                # if hist_seat for this seat number is specified in the layout, then store it in the hh_seats list
                hist_seat = location_node.getAttribute('hist_seat') #XXX
                if hist_seat:
                    self.hh_seats[int( hud_seat )] = int( hist_seat )
                else:
                    # .. otherwise just store the original seat number in the hh_seats list 
                    self.hh_seats[int( hud_seat )] = int( hud_seat )
                self.location[int( hud_seat )] = (int( location_node.getAttribute('x') ), int( location_node.getAttribute('y')))
            elif location_node.getAttribute('common') != "":
                self.common = (int( location_node.getAttribute('x') ), int( location_node.getAttribute('y')))

    def __str__(self):
        if hasattr(self, 'name'):
            name = str(self.name)
        temp = "    Layout = %d max, width= %d, height = %d" % (self.max, self.width, self.height)
        if hasattr(self, 'fav_seat'): temp = temp + ", fav_seat = %d\n" % self.fav_seat
        else: temp = temp + "\n"
        if hasattr(self, "common"):
            temp = temp + "        Common = (%d, %d)\n" % (self.common[0], self.common[1])
        temp = temp + "        Locations = "
        for i in range(1, len(self.location)):
            temp = temp + "%s:(%d,%d) " % (self.hh_seats[i],self.location[i][0],self.location[i][1])
        return temp + "\n"

class Email:
    def __init__(self, node):
        self.node = node
        self.host= node.getAttribute("host")
        self.username = node.getAttribute("username")
        self.password = node.getAttribute("password")
        self.useSsl = node.getAttribute("useSsl")
        self.folder = node.getAttribute("folder")
        self.fetchType = node.getAttribute("fetchType")
        
    def __str__(self):
        return "    email\n        fetchType = %s  host = %s\n        username = %s password = %s\n        useSsl = %s folder = %s" \
            % (self.fetchType, self.host, self.username, self.password, self.useSsl, self.folder) 


class Site:
    def __init__(self, node):
        self.site_name    = node.getAttribute("site_name")
        self.screen_name  = node.getAttribute("screen_name")
        self.site_path    = normalizePath(node.getAttribute("site_path"))
        self.HH_path    = normalizePath(node.getAttribute("HH_path"))
        self.TS_path    = normalizePath(node.getAttribute("TS_path"))
        self.enabled    = string_to_bool(node.getAttribute("enabled"), default=True)
        self.aux_enabled  = string_to_bool(node.getAttribute("aux_enabled"), default=True)
        self.hud_menu_xshift = node.getAttribute("hud_menu_xshift")
        self.hud_menu_xshift = 1 if self.hud_menu_xshift == "" else int(self.hud_menu_xshift)
        self.hud_menu_yshift = node.getAttribute("hud_menu_yshift")
        self.hud_menu_yshift = 1 if self.hud_menu_yshift == "" else int(self.hud_menu_yshift)
        if node.hasAttribute("TS_path"):
            self.TS_path    = normalizePath(node.getAttribute("TS_path"))
        else:
            self.TS_path    = ''

        self.fav_seat = {}
        for fav_node in node.getElementsByTagName('fav'):
            max = int(fav_node.getAttribute("max"))
            fav = int(fav_node.getAttribute("fav_seat"))
            self.fav_seat[max] = fav

        self.layout_set = {}
        for site_layout_node in node.getElementsByTagName('layout_set'):
            gt = site_layout_node.getAttribute("game_type")
            ls = site_layout_node.getAttribute("ls")
            self.layout_set[gt]=ls
                        
        self.emails = {}
        for email_node in node.getElementsByTagName('email'):
            email = Email(email_node)
            self.emails[email.fetchType] = email


    def __str__(self):
        temp = "Site = " + self.site_name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            if key == 'layout_set':  continue
            if key == 'fav_seat':  continue
            if key == 'emails':  continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + str(value) + "\n"

        for fetchtype in self.emails:
            temp = temp + str(self.emails[fetchtype]) + "\n"

        for game_type in self.layout_set:
            temp = temp + "    game_type = %s, layout_set = %s\n" % (game_type, self.layout_set[game_type])

        for max in self.fav_seat:
            temp = temp + "    max = %s, fav_seat = %s\n" % (max, self.fav_seat[max])
            
        return temp


class Stat:
    def __init__(self, node):
        rowcol         = node.getAttribute("_rowcol")                      # human string "(r,c)" values >0)
        self.rowcol    = tuple(int(s)-1 for s in rowcol[1:-1].split(',')) # tuple (r-1,c-1)
        self.stat_name = node.getAttribute("_stat_name")
        self.tip     = node.getAttribute("tip")
        self.click    = node.getAttribute("click")
        self.popup    = node.getAttribute("popup")
        self.hudprefix = node.getAttribute("hudprefix")
        self.hudsuffix = node.getAttribute("hudsuffix")
        self.hudcolor  = node.getAttribute("hudcolor")
        self.stat_loth = node.getAttribute("stat_loth")
        self.stat_hith = node.getAttribute("stat_hith")
        self.stat_locolor = node.getAttribute("stat_locolor")
        self.stat_hicolor = node.getAttribute("stat_hicolor")

    def __str__(self):
        temp = "        _rowcol = %s, _stat_name = %s, \n" % (self.rowcol, self.stat_name)
        for key in dir(self):
            if key.startswith('__'): continue
            if key == '_stat_name':  continue
            if key == '_rowcol':  continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '            ' + key + " = " + str(value) + "\n"

        return temp


class Stat_sets:
    
    def __init__(self, node):
        self.name    = node.getAttribute("name")
        self.rows    = int( node.getAttribute("rows") )
        self.cols    = int( node.getAttribute("cols") )
        self.xpad    = node.getAttribute("xpad")
        self.xpad = 0 if self.xpad == "" else int(self.xpad)
        self.ypad    = node.getAttribute("ypad")
        self.ypad = 0 if self.ypad == "" else int(self.ypad)

        self.stats    = {}
        for stat_node in node.getElementsByTagName('stat'):
            stat = Stat(stat_node)
            self.stats[stat.rowcol] = stat # this is the key!

    def __str__(self):
        temp = "Name = " + self.name + "\n"
        temp = temp + "    rows = %d" % self.rows
        temp = temp + " cols = %d" % self.cols
        temp = temp + "    xpad = %d" % self.xpad
        temp = temp + " ypad = %d\n" % self.ypad

        for stat in self.stats.keys():
            temp = temp + "%s" % self.stats[stat]

        return temp


class Database:
    def __init__(self, node):
        self.db_name   = node.getAttribute("db_name")
        self.db_desc   = node.getAttribute("db_desc")
        self.db_server = node.getAttribute("db_server").lower()
        self.db_ip    = node.getAttribute("db_ip")
        self.db_user   = node.getAttribute("db_user")
        self.db_pass   = node.getAttribute("db_pass")
        self.db_selected = string_to_bool(node.getAttribute("default"), default=False)
        log.debug("Database db_name:'%(name)s'  db_server:'%(server)s'  db_ip:'%(ip)s'  db_user:'%(user)s'  db_pass (not logged)  selected:'%(sel)s'" \
                % { 'name':self.db_name, 'server':self.db_server, 'ip':self.db_ip, 'user':self.db_user, 'sel':self.db_selected} )

    def __str__(self):
        temp = 'Database = ' + self.db_name + '\n'
        for key in dir(self):
            if key.startswith('__'): continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + repr(value) + "\n"
        return temp


class Aux_window:
    def __init__(self, node):
        for (name, value) in node.attributes.items():
            setattr(self, name, value)

    def __str__(self):
        temp = 'Aux = ' + self.name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"

        return temp


class Supported_games:
    def __init__(self, node):
        for (name, value) in node.attributes.items():
            setattr(self, name, value)

        self.game_stat_set = {}
        for game_stat_set_node in node.getElementsByTagName('game_stat_set'):
            gss = Game_stat_set(game_stat_set_node)
            self.game_stat_set[gss.game_type] = gss

    def __str__(self):
        temp = 'Supported_games = ' + self.game_name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            if key == 'game_stat_set':  continue
            if key == 'game_name': continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"

        for gs in self.game_stat_set:
            temp = temp + "%s" % str(self.game_stat_set[gs])
        return temp


class Layout_set:
    def __init__(self, node):
        for (name, value) in node.attributes.items():
            setattr(self, name, value)

        self.layout = {}
        for layout_node in node.getElementsByTagName('layout'):
            lo = Layout(layout_node)
            self.layout[lo.max] = lo

    def __str__(self):
        temp = 'Layout set = ' + self.name + "\n"
        for key in dir(self):
            if key.startswith('__'): continue
            if key == 'layout':  continue
            if key == 'name':  continue
            value = getattr(self, key)
            if callable(value): continue
            temp = temp + '    ' + key + " = " + value + "\n"

        for layout in self.layout:
            temp = temp + "%s" % self.layout[layout]
        return temp


class Game_stat_set:
    def __init__(self, node):
        self.game_type       = node.getAttribute("game_type")
        self.stat_set        = node.getAttribute("stat_set")

    def __str__(self):
        return "      Game Type: '%s' Stat Set: '%s'\n" % (self.game_type, self.stat_set)

        
class HHC:
    def __init__(self, node):
        self.site            = node.getAttribute("site")
        self.converter       = node.getAttribute("converter")
        self.summaryImporter = node.getAttribute("summaryImporter")

    def __str__(self):
        return "%s:\tconverter: '%s' summaryImporter: '%s'" % (self.site, self.converter, self.summaryImporter)


class Popup:
    def __init__(self, node):
        self.name  = node.getAttribute("pu_name")
        self.pu_class = node.getAttribute("pu_class")
        self.pu_stats    = []
        self.pu_stats_submenu = []
        
        for stat_node in node.getElementsByTagName('pu_stat'):
            self.pu_stats.append(stat_node.getAttribute("pu_stat_name"))
            #if stat_node.getAttribute("pu_stat_submenu"):
            self.pu_stats_submenu.append(
                tuple(
                (stat_node.getAttribute("pu_stat_name"),
                stat_node.getAttribute("pu_stat_submenu"))))
            

    def __str__(self):
        temp = "Popup = " + self.name + "  Class = " + self.pu_class + "\n"
        for stat in self.pu_stats:
            temp = temp + " " + stat
        return temp + "\n"

class Import:
    def __init__(self, node):
        self.node               = node
        self.interval           = node.getAttribute("interval")
        self.sessionTimeout     = string_to_bool(node.getAttribute("sessionTimeout")    , default=30)
        self.ResultsDirectory   = node.getAttribute("ResultsDirectory")
        self.hhBulkPath         = node.getAttribute("hhBulkPath")
        self.saveActions        = string_to_bool(node.getAttribute("saveActions")      , default=False)
        self.cacheSessions      = string_to_bool(node.getAttribute("cacheSessions")    , default=False)
        self.publicDB           = string_to_bool(node.getAttribute("publicDB")         , default=False)
        self.callFpdbHud        = string_to_bool(node.getAttribute("callFpdbHud")      , default=False)
        self.fastStoreHudCache  = string_to_bool(node.getAttribute("fastStoreHudCache"), default=False)
        self.saveStarsHH        = string_to_bool(node.getAttribute("saveStarsHH")      , default=False)
        if node.getAttribute("importFilters"):
            self.importFilters = node.getAttribute("importFilters").split(",")
        else:
            self.importFilters = []
        if node.getAttribute("timezone"):
            self.timezone = node.getAttribute("timezone")
        else:
            self.timezone = "America/New_York"

    def __str__(self):
        return "    interval = %s\n    callFpdbHud = %s\n    saveActions = %s\n   cacheSessions = %s\n    publicDB = %s\n    sessionTimeout = %s\n    fastStoreHudCache = %s\n    ResultsDirectory = %s" \
            % (self.interval, self.callFpdbHud, self.saveActions, self.cacheSessions, self.publicDB, self.sessionTimeout, self.fastStoreHudCache, self.ResultsDirectory)

class HudUI:
    def __init__(self, node):
        self.node = node
        self.label  = node.getAttribute('label')
        if node.hasAttribute('card_ht'): self.card_ht = node.getAttribute('card_ht')
        if node.hasAttribute('card_wd'): self.card_wd = node.getAttribute('card_wd')
        if node.hasAttribute('deck_type'): self.deck_type = node.getAttribute('deck_type')
        if node.hasAttribute('card_back'): self.card_back = node.getAttribute('card_back')
        #
        if node.hasAttribute('stat_range'): self.stat_range = node.getAttribute('stat_range')
        if node.hasAttribute('stat_days'): self.hud_days = node.getAttribute('stat_days')
        if node.hasAttribute('aggregation_level_multiplier'): self.agg_bb_mult = node.getAttribute('aggregation_level_multiplier')
        if node.hasAttribute('seats_style'): self.seats_style = node.getAttribute('seats_style')
        if node.hasAttribute('seats_cust_nums_low'): self.seats_cust_nums_low = node.getAttribute('seats_cust_nums_low')
        if node.hasAttribute('seats_cust_nums_high'): self.seats_cust_nums_high = node.getAttribute('seats_cust_nums_high')
        #
        if node.hasAttribute('hero_stat_range'): self.h_stat_range = node.getAttribute('hero_stat_range')
        if node.hasAttribute('hero_stat_days'): self.h_hud_days = node.getAttribute('hero_stat_days')
        if node.hasAttribute('hero_aggregation_level_multiplier'): self.h_agg_bb_mult = node.getAttribute('hero_aggregation_level_multiplier')
        if node.hasAttribute('hero_seats_style'): self.h_seats_style = node.getAttribute('hero_seats_style')
        if node.hasAttribute('hero_seats_cust_nums_low'): self.h_seats_cust_nums_low = node.getAttribute('hero_seats_cust_nums_low')
        if node.hasAttribute('hero_seats_cust_nums_high'): self.h_seats_cust_nums_high = node.getAttribute('hero_seats_cust_nums_high')


    def __str__(self):
        return "    label = %s\n" % self.label


class General(dict):
    def __init__(self):
        super(General, self).__init__()

    def add_elements(self, node):
        # day_start    - number n where 0.0 <= n < 24.0 representing start of day for user
        #                e.g. user could set to 4.0 for day to start at 4am local time
        # [ HH_bulk_path was here - now moved to import section ]
        for (name, value) in node.attributes.items():
            log.debug(unicode(_("config.general: adding %s = %s"), "utf8") % (name,value))
            self[name] = value
        
        try:
            self["version"]=int(self["version"])
        except KeyError:
            self["version"]=0
            self["ui_language"]="system"
            self["config_difficulty"]="expert"
            
    def get_defaults(self):
        self["version"]=0
        self["ui_language"]="system"
        self["config_difficulty"]="expert"
        self["config_wrap_len"]="-1"
        self["day_start"]="5"

    def __str__(self):
        s = ""
        for k in self:
            s = s + "    %s = %s\n" % (k, self[k])
        return(s)

class GUICashStats(list):
    """<gui_cash_stats>
           <col col_name="game" col_title="Game" disp_all="True" disp_posn="True" field_format="%s" field_type="str" xalignment="0.0" />
           ...
       </gui_cash_stats>
       """
    def __init__(self):
        super(GUICashStats, self).__init__()

    def add_elements(self, node):
        # is this needed?
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                col_name, col_title, disp_all, disp_posn, field_format, field_type, xalignment=None, None, True, True, "%s", "str", 0.0
                
                if child.hasAttribute('col_name'):     col_name     = child.getAttribute('col_name')
                if child.hasAttribute('col_title'):    col_title    = child.getAttribute('col_title')
                if child.hasAttribute('disp_all'):     disp_all     = string_to_bool(child.getAttribute('disp_all'))
                if child.hasAttribute('disp_posn'):    disp_posn    = string_to_bool(child.getAttribute('disp_posn'))
                if child.hasAttribute('field_format'): field_format = child.getAttribute('field_format')
                if child.hasAttribute('field_type'):   field_type   = child.getAttribute('field_type')
                try:
                    if child.hasAttribute('xalignment'):   xalignment   = float(child.getAttribute('xalignment'))
                except ValueError:
                    print(_("bad number in xalignment was ignored"))
                    log.info(_("bad number in xalignment was ignored"))

                self.append( [col_name, col_title, disp_all, disp_posn, field_format, field_type, xalignment] )

    def get_defaults(self):
        """A list of defaults to be called, should there be no entry in config"""
        # SQL column name, display title, display all, display positional, format, type, alignment
        defaults = [   [u'game', u'Game', True, True, u'%s', u'str', 0.0],       
            [u'hand', u'Hand', False, False, u'%s', u'str', 0.0],
            [u'plposition', u'Posn', False, False, u'%s', u'str', 1.0],
            [u'pname', u'Name', False, False, u'%s', u'str', 0.0],
            [u'n', u'Hds', True, True, u'%1.0f', u'str', 1.0],
            [u'avgseats', u'Seats', False, False, u'%3.1f', u'str', 1.0],
            [u'vpip', u'VPIP', True, True, u'%3.1f', u'str', 1.0],
            [u'pfr', u'PFR', True, True, u'%3.1f', u'str', 1.0],
            [u'pf3', u'PF3', True, True, u'%3.1f', u'str', 1.0],
            [u'aggfac', u'AggFac', True, True, u'%2.2f', u'str', 1.0],
            [u'aggfrq', u'AggFreq', True, True, u'%3.1f', u'str', 1.0],
            [u'conbet', u'ContBet', True, True, u'%3.1f', u'str', 1.0],
            [u'rfi', u'RFI', True, True, u'%3.1f', u'str', 1.0],
            [u'steals', u'Steals', True, True, u'%3.1f', u'str', 1.0],
            [u'saw_f', u'Saw_F', True, True, u'%3.1f', u'str', 1.0],
            [u'sawsd', u'SawSD', True, True, u'%3.1f', u'str', 1.0],
            [u'wtsdwsf', u'WtSDwsF', True, True, u'%3.1f', u'str', 1.0],
            [u'wmsd', u'W$SD', True, True, u'%3.1f', u'str', 1.0],
            [u'flafq', u'FlAFq', True, True, u'%3.1f', u'str', 1.0],
            [u'tuafq', u'TuAFq', True, True, u'%3.1f', u'str', 1.0],
            [u'rvafq', u'RvAFq', True, True, u'%3.1f', u'str', 1.0],
            [u'pofafq', u'PoFAFq', False, False, u'%3.1f', u'str', 1.0],
            [u'net', u'Net($)', True, True, u'%6.2f', u'cash', 1.0],
            [u'bbper100', u'bb/100', True, True, u'%4.2f', u'str', 1.0],
            [u'rake', u'Rake($)', True, True, u'%6.2f', u'cash', 1.0],
            [u'bb100xr', u'bbxr/100', True, True, u'%4.2f', u'str', 1.0],
            [u'stddev', u'Standard Deviation', True, True, u'%5.2f', u'str', 1.0]
            ]
        for col in defaults:
            self.append (col)

#    def __str__(self):
#        s = ""
#        for l in self:
#            s = s + "    %s = %s\n" % (k, self[k])
#        return(s)

class RawHands:
    def __init__(self, node=None):
        if node==None:
            self.save="error"
            self.compression="none"
            #print _("missing config section raw_hands")
        else:
            save=node.getAttribute("save")
            if save in ("none", "error", "all"):
                self.save=save
            else:
                print (_("Invalid config value for %s, defaulting to %s") % (raw_hands.save, "\"error\""))
                self.save="error"
            
            compression=node.getAttribute("compression")
            if save in ("none", "gzip", "bzip2"):
                self.compression=compression
            else:
                print (_("Invalid config value for %s, defaulting to %s") % (raw_hands.compression, "\"none\""))
                self.compression="none"
    #end def __init__

    def __str__(self):
        return "        save= %s, compression= %s\n" % (self.save, self.compression)
#end class RawHands

class RawTourneys:
    def __init__(self, node=None):
        if node==None:
            self.save="error"
            self.compression="none"
            #print _("missing config section raw_tourneys")
        else:
            save=node.getAttribute("save")
            if save in ("none", "error", "all"):
                self.save=save
            else:
                print (_("Invalid config value for %s, defaulting to %s") % (raw_tourneys.save, "\"error\""))
                self.save="error"
            
            compression=node.getAttribute("compression")
            if save in ("none", "gzip", "bzip2"):
                self.compression=compression
            else:
                print (_("Invalid config value for %s, defaulting to %s") % (raw_tourneys.compression, "\"none\""))
                self.compression="none"
    #end def __init__

    def __str__(self):
        return "        save= %s, compression= %s\n" % (self.save, self.compression)
#end class RawTourneys

class Config:
    def __init__(self, file = None, dbname = '', custom_log_dir='', lvl='INFO'):
        
        self.install_method = INSTALL_METHOD
        self.fpdb_root_path = FPDB_ROOT_PATH
        self.appdata_path = APPDATA_PATH
        self.config_path = CONFIG_PATH
        self.pyfpdb_path = PYFPDB_PATH
        self.graphics_path = GRAPHICS_PATH
        self.os_family = OS_FAMILY
        self.posix = POSIX
        self.python_version = PYTHON_VERSION
        
        if not os.path.exists(CONFIG_PATH):
            os.mkdir(CONFIG_PATH)

        if custom_log_dir and os.path.exists(custom_log_dir):
            self.dir_log = unicode(custom_log_dir, "utf8")
        else:
            self.dir_log = os.path.join(CONFIG_PATH, u'log')
        self.log_file = os.path.join(self.dir_log, u'fpdb-log.txt')
        self.dir_database = os.path.join(CONFIG_PATH, u'database')
        log = logging.getLogger("config")

#    "file" is a path to an xml file with the fpdb/HUD configuration
#    we check the existence of "file" and try to recover if it doesn't exist

#        self.default_config_path = self.get_default_config_path()
        self.example_copy = False
        if file is not None: # config file path passed in
            file = os.path.expanduser(file)
            if not os.path.exists(file):
                print(_("Configuration file %s not found. Using defaults.") % (file))
                sys.stderr.write(_("Configuration file %s not found. Using defaults.") % (file))
                file = None

        self.example_copy,example_file = True,None
        if file is None: (file,self.example_copy,example_file) = get_config(u"HUD_config.xml", True)

        self.file = file
                    
        self.supported_sites = {}
        self.supported_games = {}
        self.supported_databases = {}        # databaseName --> Database instance
        self.aux_windows = {}
        self.layout_sets = {}
        self.stat_sets = {}
        self.hhcs = {}
        self.popup_windows = {}
        self.db_selected = None              # database the user would like to use
        self.general = General()
        self.emails = {}
        self.gui_cash_stats = GUICashStats()
        self.site_ids = {}                   # site ID list from the database


        added,n = 1,0  # use n to prevent infinite loop if add_missing_elements() fails somehow
        while added > 0 and n < 2:
            n = n + 1
            log.info(unicode(_("Reading configuration file %s"), "utf8") % file)
            #print (("\n"+_("Reading configuration file %s")+"\n") % file)
            try:
                doc = xml.dom.minidom.parse(file)
                self.doc = doc
                self.file_error = None
            except:
                import traceback
                log.error((_("Error parsing %s.") % (file)) + _("See error log file."))
                traceback.print_exc(file=sys.stderr)
                self.file_error = sys.exc_info()[1]
                # we could add a parameter to decide whether to return or read a line and exit?
                return
                #print "press enter to continue"
                #sys.stdin.readline()
                #sys.exit()

            if (not self.example_copy) and (example_file is not None):
                # reads example file and adds missing elements into current config
                added = self.add_missing_elements(doc, example_file)

        if doc.getElementsByTagName("general") == []:
            self.general.get_defaults()
        for gen_node in doc.getElementsByTagName("general"):
            self.general.add_elements(node=gen_node) # add/overwrite elements in self.general
            
        if int(self.general["version"]) == CONFIG_VERSION:
            self.wrongConfigVersion = False
        else:
            self.wrongConfigVersion = True
            
        if doc.getElementsByTagName("gui_cash_stats") == []:
            self.gui_cash_stats.get_defaults()
        for gcs_node in doc.getElementsByTagName("gui_cash_stats"):
            self.gui_cash_stats.add_elements(node=gcs_node) # add/overwrite elements in self.gui_cash_stats

#        s_sites = doc.getElementsByTagName("supported_sites")
        for site_node in doc.getElementsByTagName("site"):
            site = Site(node = site_node)
            self.supported_sites[site.site_name] = site

#        s_games = doc.getElementsByTagName("supported_games")
        for supported_game_node in doc.getElementsByTagName("game"):
            supported_game = Supported_games(supported_game_node)
            self.supported_games[supported_game.game_name] = supported_game

        # parse databases defined by user in the <supported_databases> section
        # the user may select the actual database to use via commandline or by setting the selected="bool"
        # attribute of the tag. if no database is explicitely selected, we use the first one we come across
#        s_dbs = doc.getElementsByTagName("supported_databases")
        #TODO: do we want to take all <database> tags or all <database> tags contained in <supported_databases>
        #         ..this may break stuff for some users. so leave it unchanged for now untill there is a decission
        for db_node in doc.getElementsByTagName("database"):
            db = Database(node=db_node)
            if db.db_name in self.supported_databases:
                raise ValueError("Database names must be unique")
            if self.db_selected is None or db.db_selected:
                self.db_selected = db.db_name
                db_node.setAttribute("default", "True")
            self.supported_databases[db.db_name] = db
        #TODO: if the user may passes '' (empty string) as database name via command line, his choice is ignored
        #           ..when we parse the xml we allow for ''. there has to be a decission if to allow '' or not
        if dbname and dbname in self.supported_databases:
            self.db_selected = dbname
        #NOTE: fpdb can not handle the case when no database is defined in xml, so we throw an exception for now
        if self.db_selected is None:
            raise ValueError('There must be at least one database defined')

#     s_dbs = doc.getElementsByTagName("mucked_windows")
        for aw_node in doc.getElementsByTagName("aw"):
            aw = Aux_window(node = aw_node)
            self.aux_windows[aw.name] = aw

        for ls_node in doc.getElementsByTagName("ls"):
            ls = Layout_set(node = ls_node)
            self.layout_sets[ls.name] = ls
            
        for ss_node in doc.getElementsByTagName("ss"):
            ss = Stat_sets(node = ss_node)
            self.stat_sets[ss.name] = ss
            
#     s_dbs = doc.getElementsByTagName("mucked_windows")
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

        for hui_node in doc.getElementsByTagName('hud_ui'):
            hui = HudUI(node = hui_node)
            self.ui = hui

        db = self.get_db_parameters()
        if db['db-password'] == 'YOUR MYSQL PASSWORD':
            df_file = self.find_default_conf()
            if df_file is None: # this is bad
                pass
            else:
                df_parms = self.read_default_conf(df_file)
                self.set_db_parameters(db_name = 'fpdb', db_ip = df_parms['db-host'],
                                     db_user = df_parms['db-user'],
                                     db_pass = df_parms['db-password'])
                self.save(file=os.path.join(CONFIG_PATH, u"HUD_config.xml"))
        
        if doc.getElementsByTagName("raw_hands") == []:
            self.raw_hands = RawHands()
        for raw_hands_node in doc.getElementsByTagName('raw_hands'):
            self.raw_hands = RawHands(raw_hands_node)
        
        if doc.getElementsByTagName("raw_tourneys") == []:
            self.raw_tourneys = RawTourneys()
        for raw_tourneys_node in doc.getElementsByTagName('raw_tourneys'):
            self.raw_tourneys = RawTourneys(raw_tourneys_node)
        
        #print ""
    #end def __init__

    def add_missing_elements(self, doc, example_file):
        """ Look through example config file and add any elements that are not in the config
            May need to add some 'enabled' attributes to turn things off - can't just delete a
            config section now because this will add it back in"""

        nodes_added = 0

        try:
            example_doc = xml.dom.minidom.parse(example_file)
        except:
            log.error((_("Error parsing example configuration file %s.") % (example_file)) + _("See error log file."))
            return nodes_added

        for cnode in doc.getElementsByTagName("FreePokerToolsConfig"):
            for example_cnode in example_doc.childNodes:
                if example_cnode.localName == "FreePokerToolsConfig":
                    for e in example_cnode.childNodes:
                        #print "nodetype", e.nodeType, "name", e.localName, "found", len(doc.getElementsByTagName(e.localName))
                        if e.nodeType == e.ELEMENT_NODE and doc.getElementsByTagName(e.localName) == []:
                            new = doc.importNode(e, True)  # True means do deep copy
                            t_node = self.doc.createTextNode("    ")
                            cnode.appendChild(t_node)
                            cnode.appendChild(new)
                            t_node = self.doc.createTextNode("\r\n\r\n")
                            cnode.appendChild(t_node)
                            print("... adding missing config section: " + e.localName)
                            nodes_added = nodes_added + 1

        if nodes_added > 0:
            print(("Added %d missing config sections" % nodes_added)+"\n")
            self.save()

        return nodes_added

    def find_default_conf(self):
        if CONFIG_PATH:
            config_file = os.path.join(CONFIG_PATH, u'default.conf')
        else: config_file = False

        if config_file and os.path.exists(config_file):
            file = config_file
        else:
            file = None
        return file

    def get_doc(self):
        return self.doc

    def get_site_node(self, site):
        for site_node in self.doc.getElementsByTagName("site"):
            if site_node.getAttribute("site_name") == site:
                return site_node

    def getEmailNode(self, siteName, fetchType):
        siteNode = self.get_site_node(siteName)
        for emailNode in siteNode.getElementsByTagName("email"):
            if emailNode.getAttribute("fetchType") == fetchType:
                return emailNode
                break
    #end def getEmailNode

    def getStatSetNode(self,statsetName):
        """returns DOM game node for a given game"""
        for statsetNode in self.doc.getElementsByTagName("ss"):
            #print "getStatSetNode statsetNode:",statsetNode
            if statsetNode.getAttribute("name") == statsetName:
                return statsetNode
    
    
    def getGameNode(self,gameName):
        """returns DOM game node for a given game"""
        for gameNode in self.doc.getElementsByTagName("game"):
            #print "getGameNode gameNode:",gameNode
            if gameNode.getAttribute("game_name") == gameName:
                return gameNode
    #end def getGameNode

    
    def get_aux_node(self, aux):
        for aux_node in self.doc.getElementsByTagName("aw"):
            if aux_node.getAttribute("name") == aux:
                return aux_node

    def get_layout_set_node(self, ls):
        for layout_set_node in self.doc.getElementsByTagName("ls"):
            if layout_set_node.getAttribute("name") == ls:
                return layout_set_node

    def get_layout_node(self, ls, max):
        for layout_node in ls.getElementsByTagName("layout"):
            if layout_node.getAttribute("max") == str(max):
                return layout_node
                                
    def get_stat_set_node(self, ss):
        for stat_set_node in self.doc.getElementsByTagName("ss"):
            if set_node.getAttribute("name") == ss:
                return stat_set_node

    def get_db_node(self, db_name):
        for db_node in self.doc.getElementsByTagName("database"):
            if db_node.getAttribute("db_name") == db_name:
                return db_node
        return None

#    def get_layout_node(self, site_node, layout):
#        for layout_node in site_node.getElementsByTagName("layout"):
#            if layout_node.getAttribute("max") is None:
#                return None
#            if int( layout_node.getAttribute("max") ) == int( layout ):
#                return layout_node

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
        if file is None:
            file = self.file
            try:
                shutil.move(file, file+".backup")
            except:
                pass
                
        with codecs.open(file, 'w', 'utf-8') as f:
            #self.doc.writexml(f)
            f.write( self.wrap_long_lines( self.doc.toxml() ) )

    def wrap_long_lines(self, s):
        lines = [ self.wrap_long_line(l) for l in s.splitlines() ]
        return('\n'.join(lines) + '\n')

    def wrap_long_line(self, l):
        if 'config_wrap_len' in self.general:
            wrap_len = int(self.general['config_wrap_len'])
        else:
            wrap_len = -1    # < 0 means no wrap

        if wrap_len >= 0 and len(l) > wrap_len:
            m = re.compile('\s+\S+\s+')
            mo = m.match(l)
            if mo:
                indent_len = mo.end()
                #print "indent = %s (%s)" % (indent_len, l[0:indent_len])
                indent = '\n' + ' ' * indent_len
                m = re.compile('(\S+="[^"]+"\s+)')
                parts = [x for x in m.split(l[indent_len:]) if x]
                if len(parts) > 1:
                    #print "parts =", parts
                    l = l[0:indent_len] + indent.join(parts)
            return(l)
        else:
            return(l)

    def editEmail(self, siteName, fetchType, newEmail):
        emailNode = self.getEmailNode(siteName, fetchType)
        emailNode.setAttribute("host", newEmail.host)
        emailNode.setAttribute("username", newEmail.username)
        emailNode.setAttribute("password", newEmail.password)
        emailNode.setAttribute("folder", newEmail.folder)
        emailNode.setAttribute("useSsl", newEmail.useSsl)
    #end def editEmail
    
    def edit_site(self, site_name, enabled, screen_name, history_path, summary_path):
        site_node = self.get_site_node(site_name)
        site_node.setAttribute("enabled", enabled)
        site_node.setAttribute("screen_name", screen_name)
        site_node.setAttribute("HH_path", history_path)
        if summary_path:
            site_node.setAttribute("TS_path", summary_path)
            
    def editStats(self, statsetName, statArray):
        """replaces stat selection for the given gameName with the given statArray"""
        statsetNode = self.getStatSetNode(statsetName)
        statNodes = statsetNode.getElementsByTagName("stat")
        
        for node in statNodes:
            statsetNode.removeChild(node)
        
        statsetNode.setAttribute("rows", str(len(statArray)))
        statsetNode.setAttribute("cols", str(len(statArray[0])))
        
        for rowNumber in range(len(statArray)):
            for columnNumber in range(len(statArray[rowNumber])):
                newStat=self.doc.createElement("stat")
                
                newAttrStatName=self.doc.createAttribute("_stat_name")
                newStat.setAttributeNode(newAttrStatName)
                newStat.setAttribute("_stat_name", statArray[rowNumber][columnNumber])
                
                newAttrStatName=self.doc.createAttribute("_rowcol")
                newStat.setAttributeNode(newAttrStatName)
                newStat.setAttribute("_rowcol", ("("+str(rowNumber+1)+","+str(columnNumber+1)+")"))
                
                newAttrStatName=self.doc.createAttribute("click")
                newStat.setAttributeNode(newAttrStatName)
                newStat.setAttribute("click", "")
                
                newAttrStatName=self.doc.createAttribute("popup")
                newStat.setAttributeNode(newAttrStatName)
                newStat.setAttribute("popup", "default")
                
                newAttrStatName=self.doc.createAttribute("tip")
                newStat.setAttributeNode(newAttrStatName)
                newStat.setAttribute("tip", "")
                
                statsetNode.appendChild(newStat)
        statNodes = statsetNode.getElementsByTagName("stat") #TODO remove this line?
    #end def editStats

    def editImportFilters(self, games):
        self.imp.importFilters = games
        imp_node = self.doc.getElementsByTagName("import")[-1]
        imp_node.setAttribute("importFilters", games)

    def save_layout_set(self, ls, max, locations, width=None, height=None):
        #wid/height normally not specified when saving common from the mucked display
        
        print "saving layout =", ls.name, " ", str(max), "Max ", str(locations), "size:", str(width), "x", str(height)
        ls_node = self.get_layout_set_node(ls.name)
        layout_node = self.get_layout_node(ls_node, max)
        if width: layout_node.setAttribute("width", str(width))
        if height: layout_node.setAttribute("height", str(height))
        
        for (i, pos) in locations.iteritems():
            location_node = self.get_location_node(layout_node, i)
            location_node.setAttribute("x", str( locations[i][0] ))
            location_node.setAttribute("y", str( locations[i][1] ))
            #now refresh the live instance of the layout set with the new locations
            # this is needed because any future windows created after a save layout
            # MUST pickup the new layout
            #fixme - this is horrid 
            if i == "common":
                self.layout_sets[ls.name].layout[max].common = ( locations[i][0], locations[i][1] )
            else:
                self.layout_sets[ls.name].layout[max].location[i] = ( locations[i][0], locations[i][1] )
        # more horridness below, fixme
        if height: self.layout_sets[ls.name].layout[max].height = height
        if width: self.layout_sets[ls.name].layout[max].width = width
        
                
    #NOTE: we got a nice Database class, so why map it again here?
    #            user input validation should be done when initializing the Database class. this allows to give appropriate feddback when something goes wrong
    #            try ..except is evil here. it swallows all kinds of errors. dont do this
    #            naming database types 2, 3, 4 on the fly is no good idea. i see this all over the code. better use some globally defined consts (see DATABASE_TYPE_*)
    #            i would like to drop this method entirely and replace it by get_selected_database() or better get_active_database(), returning one of our Database instances
    #            thus we can drop self.db_selected (holding database name) entirely and replace it with self._active_database = Database, avoiding to define the same
    #            thing multiple times
    def get_db_parameters(self):
        db = {}
        name = self.db_selected
        # TODO: What's up with all the exception handling here?!
        try:    db['db-databaseName'] = name
        except: pass

        try:    db['db-desc'] = self.supported_databases[name].db_desc
        except: pass

        try:    db['db-host'] = self.supported_databases[name].db_ip
        except: pass

        try:    db['db-user'] = self.supported_databases[name].db_user
        except: pass

        try:    db['db-password'] = self.supported_databases[name].db_pass
        except: pass

        try:    db['db-server'] = self.supported_databases[name].db_server
        except: pass

        db['db-backend'] = self.get_backend(self.supported_databases[name].db_server)

        return db

    def set_db_parameters(self, db_name = 'fpdb', db_ip = None, db_user = None,
                          db_pass = None, db_desc = None, db_server = None,
                          default = "False"):
        db_node = self.get_db_node(db_name)
        default = default.lower()
        defaultb = string_to_bool(default, False)
        if db_node != None:
            if db_desc   is not None: db_node.setAttribute("db_desc", db_desc)
            if db_ip     is not None: db_node.setAttribute("db_ip", db_ip)
            if db_user   is not None: db_node.setAttribute("db_user", db_user)
            if db_pass   is not None: db_node.setAttribute("db_pass", db_pass)
            if db_server is not None: db_node.setAttribute("db_server", db_server)
            if defaultb or self.db_selected == db_name:
                db_node.setAttribute("default", "True")
                for dbn in self.doc.getElementsByTagName("database"):
                    if dbn.getAttribute('db_name') != db_name and dbn.hasAttribute("default"):
                        dbn.removeAttribute("default")
            elif db_node.hasAttribute("default"): 
                db_node.removeAttribute("default")
        if self.supported_databases.has_key(db_name):
            if db_desc   is not None: self.supported_databases[db_name].dp_desc   = db_desc
            if db_ip     is not None: self.supported_databases[db_name].dp_ip     = db_ip
            if db_user   is not None: self.supported_databases[db_name].dp_user   = db_user
            if db_pass   is not None: self.supported_databases[db_name].dp_pass   = db_pass
            if db_server is not None: self.supported_databases[db_name].dp_server = db_server
            self.supported_databases[db_name].db_selected = defaultb
        if defaultb:
            self.db_selected = db_name
        return

    def add_db_parameters(self, db_name = 'fpdb', db_ip = None, db_user = None,
                          db_pass = None, db_desc = None, db_server = None,
                          default = "False"):
        default = default.lower()
        defaultb = string_to_bool(default, False)
        if db_name in self.supported_databases:
            raise ValueError("Database names must be unique")

        db_node = self.get_db_node(db_name)
        if db_node is None:
            for db_node in self.doc.getElementsByTagName("supported_databases"):
                # should only be one supported_databases element, use last one if there are several
                suppdb_node = db_node
            t_node = self.doc.createTextNode("    ")
            suppdb_node.appendChild(t_node)
            db_node = self.doc.createElement("database")
            suppdb_node.appendChild(db_node)
            t_node = self.doc.createTextNode("\r\n    ")
            suppdb_node.appendChild(t_node)
            db_node.setAttribute("db_name", db_name)
            if db_desc   is not None: db_node.setAttribute("db_desc", db_desc)
            if db_ip     is not None: db_node.setAttribute("db_ip", db_ip)
            if db_user   is not None: db_node.setAttribute("db_user", db_user)
            if db_pass   is not None: db_node.setAttribute("db_pass", db_pass)
            if db_server is not None: db_node.setAttribute("db_server", db_server)
            if defaultb:
                db_node.setAttribute("default", "True")
                for dbn in self.doc.getElementsByTagName("database"):
                    if dbn.getAttribute('db_name') != db_name and dbn.hasAttribute("default"):
                        dbn.removeAttribute("default")
            elif db_node.hasAttribute("default"): 
                db_node.removeAttribute("default")
        else:
            if db_desc   is not None: db_node.setAttribute("db_desc", db_desc)
            if db_ip     is not None: db_node.setAttribute("db_ip", db_ip)
            if db_user   is not None: db_node.setAttribute("db_user", db_user)
            if db_pass   is not None: db_node.setAttribute("db_pass", db_pass)
            if db_server is not None: db_node.setAttribute("db_server", db_server)
            if defaultb or self.db_selected == db_name:
                                      db_node.setAttribute("default", "True")
            elif db_node.hasAttribute("default"): 
                                      db_node.removeAttribute("default")

        if self.supported_databases.has_key(db_name):
            if db_desc   is not None: self.supported_databases[db_name].dp_desc   = db_desc
            if db_ip     is not None: self.supported_databases[db_name].dp_ip     = db_ip
            if db_user   is not None: self.supported_databases[db_name].dp_user   = db_user
            if db_pass   is not None: self.supported_databases[db_name].dp_pass   = db_pass
            if db_server is not None: self.supported_databases[db_name].dp_server = db_server
            self.supported_databases[db_name].db_selected = defaultb
        else:
            db = Database(node=db_node)
            self.supported_databases[db.db_name] = db

        if defaultb:
            self.db_selected = db_name
        return
    
    def get_backend(self, name):
        """Returns the number of the currently used backend"""
        if name == DATABASE_TYPE_MYSQL:
            ret = 2
        elif name == DATABASE_TYPE_POSTGRESQL:
            ret = 3
        elif name == DATABASE_TYPE_SQLITE:
            ret = 4
            # sqlcoder: this assignment fixes unicode problems for me with sqlite (windows, cp1252)
            #           feel free to remove or improve this if you understand the problems
            #           better than me (not hard!)
            Charset.not_needed1, Charset.not_needed2, Charset.not_needed3 = True, True, True
        else:
            raise ValueError('Unsupported database backend: %s' % self.supported_databases[name].db_server)

        return ret

    def getDefaultSite(self):
        "Returns first enabled site or None"
        for site_name,site in self.supported_sites.iteritems():
            if site.enabled:
                return site_name
        return None

    # Allow to change the menu appearance
    def get_hud_ui_parameters(self):
        hui = {}

        default_text = 'FPDB Menu - Right click\nLeft-Drag to Move'
        try:
            hui['label'] = self.ui.label
            if self.ui.label == '':    # Empty menu label is a big no-no
                hui['label'] = default_text
        except:
            hui['label'] = default_text

        try:    hui['card_ht']        = int(self.ui.card_ht)
        except: hui['card_ht']        = 42

        try:    hui['card_wd']        = int(self.ui.card_wd)
        except: hui['card_wd']        = 30
        
        try:    hui['deck_type']      = unicode(self.ui.deck_type)
        except: hui['deck_type']        = u'colour'
        
        try:    hui['card_back']      = unicode(self.ui.card_back)
        except: hui['card_back']        = u'back04'
                
        try:    hui['stat_range']        = self.ui.stat_range
        except: hui['stat_range']        = 'A'  # default is show stats for All-time, also S(session) and T(ime)

        try:    hui['hud_days']        = int(self.ui.hud_days)
        except: hui['hud_days']        = 90

        try:    hui['agg_bb_mult']    = int(self.ui.agg_bb_mult)
        except: hui['agg_bb_mult']    = 1

        try:    hui['seats_style']    = self.ui.seats_style
        except: hui['seats_style']    = 'A'  # A / C / E, use A(ll) / C(ustom) / E(xact) seat numbers

        try:    hui['seats_cust_nums_low']    = int(self.ui.seats_cust_nums_low)
        except: hui['seats_cust_nums_low']    = 1
        try:    hui['seats_cust_nums_high']    = int(self.ui.seats_cust_nums_high)
        except: hui['seats_cust_nums_high']    = 10
          
        # Hero specific

        try:    hui['h_stat_range']    = self.ui.h_stat_range
        except: hui['h_stat_range']    = 'S'

        try:    hui['h_hud_days']     = int(self.ui.h_hud_days)
        except: hui['h_hud_days']     = 30

        try:    hui['h_agg_bb_mult']    = int(self.ui.h_agg_bb_mult)
        except: hui['h_agg_bb_mult']    = 1

        try:    hui['h_seats_style']    = self.ui.h_seats_style
        except: hui['h_seats_style']    = 'A'  # A / C / E, use A(ll) / C(ustom) / E(xact) seat numbers

        try:    hui['h_seats_cust_nums_low']    = int(self.ui.h_seats_cust_nums_low)
        except: hui['h_seats_cust_nums_low']    = 1
        try:    hui['h_seats_cust_nums_high']    = int(self.ui.h_seats_cust_nums_high)
        except: hui['h_seats_cust_nums_high']    = 10
        return hui


    def get_import_parameters(self):
        imp = {}
        try:    imp['callFpdbHud']     = self.imp.callFpdbHud
        except:  imp['callFpdbHud']     = True

        try:    imp['interval']        = self.imp.interval
        except:  imp['interval']        = 10

        # ResultsDirectory is the local cache for downloaded results
        # NOTE: try: except: doesn'tseem to be triggering
        #       using if instead
        if self.imp.ResultsDirectory != '':
            imp['ResultsDirectory']    = self.imp.ResultsDirectory
        else:
            imp['ResultsDirectory']    = "~/.fpdb/Results/"

        # hhBulkPath is the default location for bulk imports (if set)
        try:    imp['hhBulkPath']    = self.imp.hhBulkPath
        except:  imp['hhBulkPath']    = ""

        try:    imp['saveActions']     = self.imp.saveActions
        except:  imp['saveActions']     = False
        
        try:    imp['cacheSessions']     = self.imp.cacheSessions
        except:  imp['cacheSessions']     = False
        
        try:    imp['publicDB']     = self.imp.publicDB
        except:  imp['publicDB']     = False
        
        try:    imp['sessionTimeout']     = self.imp.sessionTimeout
        except:  imp['sessionTimeout']     = 30

        try:    imp['saveStarsHH'] = self.imp.saveStarsHH
        except:  imp['saveStarsHH'] = False

        try:    imp['fastStoreHudCache'] = self.imp.fastStoreHudCache
        except:  imp['fastStoreHudCache'] = False

        try:    imp['importFilters'] = self.imp.importFilters
        except:  imp['importFilters'] = []

        try:    imp['timezone'] = self.imp.timezone
        except:  imp['timezone'] = "America/New_York"

        return imp
    
    def set_timezone(self, timezone):
        self.imp.timezone = timezone

    def get_default_paths(self, site = None):
        if site is None: site = self.getDefaultSite()
        paths = {}
        try:
            path = os.path.expanduser(self.supported_sites[site].HH_path)
            assert(os.path.isdir(path) or os.path.isfile(path)) # maybe it should try another site?
            paths['hud-defaultPath'] = paths['bulkImport-defaultPath'] = path
            if self.imp.hhBulkPath:
                paths['bulkImport-defaultPath'] = self.imp.hhBulkPath
            if self.supported_sites[site].TS_path != '':
                tspath = os.path.expanduser(self.supported_sites[site].TS_path)
                paths['hud-defaultTSPath'] = tspath
        except AssertionError:
            paths['hud-defaultPath'] = paths['bulkImport-defaultPath'] = "** ERROR DEFAULT PATH IN CONFIG DOES NOT EXIST **"
        return paths

#    def get_frames(self, site = "PokerStars"):
#        if site not in self.supported_sites: return False
#        return self.supported_sites[site].use_frames == True

#    def get_default_colors(self, site = "PokerStars"):
#        colors = {}
#        if site not in self.supported_sites or self.supported_sites[site].hudopacity == "":
#            colors['hudopacity'] = 0.90
#        else:
#            colors['hudopacity'] = float(self.supported_sites[site].hudopacity)
#        if site not in self.supported_sites or self.supported_sites[site].hudbgcolor == "":
#            colors['hudbgcolor'] = "#FFFFFF"
#        else:
#            colors['hudbgcolor'] = self.supported_sites[site].hudbgcolor
#        if site not in self.supported_sites or self.supported_sites[site].hudfgcolor == "":
#            colors['hudfgcolor'] = "#000000"
#        else:
#            colors['hudfgcolor'] = self.supported_sites[site].hudfgcolor
#        return colors

#    def get_default_font(self, site='PokerStars'):
#        font = "Sans"
#        font_size = "8"
#        site = self.supported_sites.get(site, None)
#        if site is not None:
#            if site.font:
#                font = site.font
#            if site.font_size:
#                font_size = site.font_size
#        return font, font_size

    def get_layout_set_locations(self, set = "mucked", max = "9"):

        try:
            locations = self.layout_sets[set].layout[max].location
        except:
            locations = ( (  0,   0), (684,  61), (689, 239), (692, 346),
                        (586, 393), (421, 440), (267, 440), (  0, 361),
                        (  0, 280), (121, 280), ( 46,  30) )
        return locations
             
    def get_supported_sites(self, all=False):
        """Returns the list of supported sites."""
        if all:
            return self.supported_sites.keys()
        else:
            return [site_name for (site_name, site) in self.supported_sites.items() if site.enabled]

    def get_site_parameters(self, site):
        """Returns a dict of the site parameters for the specified site"""
        parms = {}
        parms["converter"]    = self.hhcs[site].converter
        parms["summaryImporter"] = self.hhcs[site].summaryImporter
        parms["screen_name"]  = self.supported_sites[site].screen_name
        parms["site_path"]    = self.supported_sites[site].site_path
        parms["HH_path"]    = self.supported_sites[site].HH_path
        parms["TS_path"]    = self.supported_sites[site].TS_path
        parms["site_name"]    = self.supported_sites[site].site_name
        parms["enabled"]    = self.supported_sites[site].enabled
        parms["aux_enabled"]    = self.supported_sites[site].aux_enabled
        parms["hud_menu_xshift"] = self.supported_sites[site].hud_menu_xshift
        parms["hud_menu_yshift"] = self.supported_sites[site].hud_menu_yshift        
        parms["layout_set"] = self.supported_sites[site].layout_set
        parms["emails"] = self.supported_sites[site].emails
        parms["fav_seat"] = self.supported_sites[site].fav_seat
        
        return parms

    def get_layout(self, site, game_type):
        
        # find layouts used at site
        # locate the one used for this game_type
        # return that Layout-set() instance 
        
        site_layouts = self.get_site_parameters(site)["layout_set"]
        
        if site_layouts.has_key(game_type):
            return self.layout_sets[site_layouts[game_type]]
        elif site_layouts.has_key("all"):
            return self.layout_sets[site_layouts["all"]]
        else:
            return None

#    def set_site_parameters(self, site_name, converter = None, decoder = None,
#                            hudbgcolor = None, hudfgcolor = None,
#                            hudopacity = None, screen_name = None,
#                            site_path = None, table_finder = None,
#                            HH_path = None, enabled = None,
#                            font = None, font_size = None):
#        """Sets the specified site parameters for the specified site."""
#        site_node = self.get_site_node(site_name)
#        if db_node is not None:
#            if converter      is not None: site_node.setAttribute("converter", converter)
#            if decoder        is not None: site_node.setAttribute("decoder", decoder)
#            if hudbgcolor     is not None: site_node.setAttribute("hudbgcolor", hudbgcolor)
#            if hudfgcolor     is not None: site_node.setAttribute("hudfgcolor", hudfgcolor)
#            if hudopacity     is not None: site_node.setAttribute("hudopacity", hudopacity)
#            if screen_name    is not None: site_node.setAttribute("screen_name", screen_name)
#            if site_path      is not None: site_node.setAttribute("site_path", site_path)
#            if table_finder   is not None: site_node.setAttribute("table_finder", table_finder)
#            if HH_path        is not None: site_node.setAttribute("HH_path", HH_path)
#            if enabled        is not None: site_node.setAttribute("enabled", enabled)
#            if font           is not None: site_node.setAttribute("font", font)
#            if font_size      is not None: site_node.setAttribute("font_size", font_size)
#        return

    def set_general(self,lang=None):

       for general_node in self.doc.getElementsByTagName('general'):
            if lang: general_node.setAttribute("ui_language", lang)

    def set_site_ids(self, sites):
        self.site_ids = dict(sites)

    def get_site_id(self, site):
        return( self.site_ids[site] )
        
    def get_aux_windows(self):
        """Gets the list of mucked window formats in the configuration."""
        return self.aux_windows.keys()

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

    def get_stat_sets(self):
        """Gets the list of stat block contents in the configuration."""
        return self.stat_sets.keys()
        
    def get_layout_sets(self):
        """Gets the list of block layouts in the configuration."""
        return self.layout_sets.keys()
        
    def get_layout_set_parameters(self, name):
        """Gets a dict of parameters from the named ls."""
        param = {}
        if self.layout_sets.has_key(name):
            for key in dir(self.layout_sets[name]):
                if key.startswith('__'): continue
                value = getattr(self.layout_sets[name], key)
                if callable(value): continue
                param[key] = value

            return param
        return None

    def get_supported_games(self):
        """Get the list of supported games."""
        sg = []
        for game in self.supported_games.keys():
            sg.append(self.supported_games[game].game_name)
        return sg

    def get_supported_games_parameters(self, name, game_type):
        """Gets a dict of parameters from the named gametype."""
        param = {}
        if self.supported_games.has_key(name):
            for key in dir(self.supported_games[name]):
                if key.startswith('__'): continue
                if key == ('game_stat_set'): continue
                value = getattr(self.supported_games[name], key)
                if callable(value): continue
                param[key] = value
                
            #some gymnastics now to load the correct Stats_sets instance
            # into the game_stat_set key
            
            game_stat_set = getattr(self.supported_games[name], 'game_stat_set')
                
            if game_stat_set.has_key(game_type):
                param['game_stat_set'] = self.stat_sets[game_stat_set[game_type].stat_set]
            elif game_stat_set.has_key("all"):
                param['game_stat_set'] = self.stat_sets[game_stat_set["all"].stat_set]
            else:
                return None

            return param
            
        return None
        
    def execution_path(self, filename):
        """Join the fpdb path to filename."""
        return os.path.join(os.path.dirname(inspect.getfile(sys._getframe(0))), filename)

    def get_general_params(self):
        return( self.general )

    def get_gui_cash_stat_params(self):
        return( self.gui_cash_stats )

if __name__== "__main__":
    set_logfile(u"fpdb-log.txt")
    c = Config()
    
    print "\n----------- GENERAL -----------"
    print c.general

    print "\n----------- SUPPORTED SITES -----------"
    for s in c.supported_sites.keys():
        print c.supported_sites[s]

    print "\n----------- SUPPORTED GAMES -----------"
    for game in c.supported_games.keys():
        print c.supported_games[game]

    print "\n----------- SUPPORTED DATABASES -----------"
    for db in c.supported_databases.keys():
        print c.supported_databases[db]

    print "\n----------- AUX WINDOW FORMATS -----------"
    for w in c.aux_windows.keys():
        print c.aux_windows[w]
    
    print "\n----------- LAYOUT SETS FORMATS -----------"
    for w in c.layout_sets.keys():
        print c.layout_sets[w]
    
    print "\n----------- STAT SETS FORMATS -----------"
    for w in c.stat_sets.keys():
        print c.stat_sets[w]

    print "\n----------- HAND HISTORY CONVERTERS -----------"
    for w in c.hhcs.keys():
        print c.hhcs[w]

    print "\n----------- POPUP WINDOW FORMATS -----------"
    for w in c.popup_windows.keys():
        print c.popup_windows[w]
        
    print "\n-----------  DATABASE PARAMS -----------"
    print "db    = ", c.get_db_parameters()
    
    print "\n-----------  HUD PARAMS -----------"
    print "hud params ="
    for hud_param, value in c.get_hud_ui_parameters().iteritems():
        print " %s = %s" % (hud_param, value)
        
    print "\n-----------  STARTUP PATH -----------"
    print "start up path = ", c.execution_path("")
    
    print "\n-----------  GUI CASH STATS -----------"
    print "gui_cash_stats =", c.gui_cash_stats

    print "\n----------- ENVIRONMENT CONSTANTS -----------"
    print "Configuration.install_method {source,exe,app} =", INSTALL_METHOD
    print "Configuration.fpdb_root_path =", FPDB_ROOT_PATH, type(FPDB_ROOT_PATH)
    print "Configuration.graphics_path =", GRAPHICS_PATH, type(GRAPHICS_PATH)
    print "Configuration.appdata_path =", APPDATA_PATH, type(APPDATA_PATH)
    print "Configuration.config_path =", CONFIG_PATH, type(CONFIG_PATH)
    print "Configuration.pyfpdb_path =", PYFPDB_PATH, type(PYFPDB_PATH)
    print "Configuration.os_family {Linux,Mac,XP,Win7} =", OS_FAMILY
    print "Configuration.posix {True/False} =", POSIX
    print "Configuration.python_version =", PYTHON_VERSION
    print "\n\n----------- END OF CONFIG REPORT -----------"

    print "press enter to end"
    sys.stdin.readline()

