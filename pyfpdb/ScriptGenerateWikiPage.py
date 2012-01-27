#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Carl Gherardi
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

import os
import copy

import Configuration
import IdentifySite
import pprint
pp = pprint.PrettyPrinter(indent=4)

def print_site(name, data, mask):
    print "! %s" % name
    for game, limits in gametypes:
        tmp = ""
        for lim in limits:
            style = "red"
            if mask[name][game][lim] == False: style = "lightgrey"
            if data[name][game][lim] == True: style = "lightgreen"
            tmp += "| style='background:%s' | %s |" %(style, lim.upper())
        print tmp[:-1]
    print "|-"


#########################################################################
# Masks - If a value is False, it means the site doesn't support the game
#########################################################################

defaultmask = {   'holdem'   : {   'nl': None,  'pl': None,  'fl': None},
                  'omahahi'  : {   'nl': False, 'pl': None,  'fl': None},
                  'omahahilo': {   'nl': False, 'pl': None,  'fl': None},
                  'fivedraw' : {   'nl': None,  'pl': None,  'fl': None},
                  '27_1draw' : {   'nl': None,  'pl': False, 'fl': False},
                  '27_3draw' : {   'nl': None,  'pl': False, 'fl': None},
                  'a5_3draw' : {   'nl': None,  'pl': None,  'fl': None},
                  'badugi'   : {   'nl': None,  'pl': False, 'fl': False},
                  'razz'     : {   'nl': None,  'pl': None,  'fl': None},
                  'studhi'   : {   'nl': None,  'pl': None,  'fl': None},
                  'studhilo' : {   'nl': None,  'pl': None,  'fl': None},
                  '5studhi'  : {   'nl': False, 'pl': False, 'fl': False},
               }

sitemasks = { "PokerStars": copy.deepcopy(defaultmask),
              "Full Tilt Poker": copy.deepcopy(defaultmask),
              "Everleaf": copy.deepcopy(defaultmask),
              "Boss": copy.deepcopy(defaultmask),
              "Absolute": copy.deepcopy(defaultmask),
              "PartyPoker": copy.deepcopy(defaultmask),
              "Betfair": copy.deepcopy(defaultmask),
              "Merge": copy.deepcopy(defaultmask),
              "OnGame": copy.deepcopy(defaultmask),
              "PKR": copy.deepcopy(defaultmask),
              "iPoker": copy.deepcopy(defaultmask),
              "Winamax": copy.deepcopy(defaultmask),
              "Everest": copy.deepcopy(defaultmask),
              "PacificPoker": copy.deepcopy(defaultmask),
              "Cake": copy.deepcopy(defaultmask),
              "Entraction": copy.deepcopy(defaultmask),
              "BetOnline": copy.deepcopy(defaultmask),
              "Microgaming": copy.deepcopy(defaultmask),
        }

# Site specific changes from the defaults
# Stars - no A-5 draw, does have PLBadugi
sitemasks['PokerStars']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PokerStars']['badugi']   = {   'nl': False,  'pl': None, 'fl' : None}
# PartyPoker - no draw games, no razz
sitemasks['PartyPoker']['fivedraw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PartyPoker']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PartyPoker']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PartyPoker']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PartyPoker']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['PartyPoker']['razz']     = {   'nl': False,  'pl': False, 'fl': False}
# Everleaf - no draw games
sitemasks['Everleaf']['fivedraw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everleaf']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everleaf']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everleaf']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everleaf']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}
# Everest - no draw games
sitemasks['Everest']['fivedraw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everest']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everest']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everest']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Everest']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}
# Cake - Only flop based games
sitemasks['Cake']['razz'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['studhi'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['studhilo'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['5studhi'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['fivedraw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Cake']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}
# Boss -Razz, +5CD, -other draw games
sitemasks['Boss']['razz']     = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Boss']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Boss']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Boss']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Boss']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}
# Winamax - Only Omaha and Holdem
sitemasks['Winamax']['omahahilo'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['razz'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['studhi'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['studhilo'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['5studhi'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['fivedraw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['27_1draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['27_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['a5_3draw'] = {   'nl': False,  'pl': False, 'fl': False}
sitemasks['Winamax']['badugi']   = {   'nl': False,  'pl': False, 'fl': False}



defaults = { 'nl':None, 'pl':None, 'fl':None, }

games = {"27_1draw"  : copy.deepcopy(defaults)
        ,"27_3draw"  : copy.deepcopy(defaults)
        ,"a5_3draw"  : copy.deepcopy(defaults)
        ,"5studhi"   : copy.deepcopy(defaults)
        ,"badugi"    : copy.deepcopy(defaults)
        ,"fivedraw"  : copy.deepcopy(defaults)
        ,"holdem"    : copy.deepcopy(defaults)
        ,"omahahi"   : copy.deepcopy(defaults)
        ,"omahahilo" : copy.deepcopy(defaults)
        ,"razz"      : copy.deepcopy(defaults)
        ,"studhi"    : copy.deepcopy(defaults)
        ,"studhilo"  : copy.deepcopy(defaults)
        }

Configuration.set_logfile("fpdb-log.txt")
config = Configuration.Config(file = "HUD_config.test.xml")
in_path = os.path.abspath('regression-test-files')
idsite = IdentifySite.IdentifySite(config, in_path)
idsite.scan()
idsite.fetchGameTypes()


sites = { "PokerStars": copy.deepcopy(games),
          "Full Tilt Poker": copy.deepcopy(games),
          "Everleaf": copy.deepcopy(games),
          "Boss": copy.deepcopy(games),
          "Absolute": copy.deepcopy(games),
          "PartyPoker": copy.deepcopy(games),
          "Betfair": copy.deepcopy(games),
          "Merge": copy.deepcopy(games),
          "OnGame": copy.deepcopy(games),
          "PKR": copy.deepcopy(games),
          "iPoker": copy.deepcopy(games),
          "Winamax": copy.deepcopy(games),
          "Everest": copy.deepcopy(games),
          "PacificPoker": copy.deepcopy(games),
          "Cake": copy.deepcopy(games),
          "Entraction": copy.deepcopy(games),
          "BetOnline": copy.deepcopy(games),
          "Microgaming": copy.deepcopy(games),
        }

ring = copy.deepcopy(sites)
tour = copy.deepcopy(sites)
summ = copy.deepcopy(sites)

for idx, f in idsite.filelist.iteritems():
    if f.gametype != False:
        a = f.gametype['category']
        b = f.gametype['limitType']
        c = f.site.name
        if f.gametype['type'] == 'ring':
            ring[c][a][b] = True
        if f.gametype['type'] == 'tour':
            if f.site.name == "Full Tilt Poker":
                print "DEBUG: Found FTP: %s" % f.path
            tour[c][a][b] = True
    else:
        print "Skipping: %s" % f.path


gametypes = [ ('holdem',    ['nl','pl','fl']),
              ('omahahi',   ['nl','pl','fl']),
              ('omahahilo', ['nl','pl','fl']),
              ('5studhi',   [     'pl','fl']),
              ('studhi',    [          'fl']),
              ('studhilo',  [          'fl']),
              ('razz',      [          'fl']),
              ('fivedraw',  ['nl','pl','fl']),
              ('27_1draw',  ['nl'          ]),
              ('27_3draw',  [     'pl','fl']),
              ('a5_3draw',  [     'pl','fl']),
              ('badugi',    [     'pl','fl']),
             ]

# The following needs to be written to 4 lines - its a lot easier to work with as laid out below
#print """{| border=0<br>
#|-
#| Site || colspan=3 style='background:%s' | Holdem |
#        | colspan=3 style='background:%s' | Omaha |
#        | colspan=3 style='background:%s' | O8 |
#        | colspan=2 style='background:%s' | 5CS |
#        |           style='background:%s' | 7CS |
#        |           style='background:%s' | 7CS H/L |
#        |           style='background:%s' | Razz |
#        | colspan=3 style='background:%s' | 5CD |
#        |           style='background:%s' | 27SD |
#        | colspan=2 style='background:%s' | 27TD |
#        | colspan=2 style='background:%s' | A5TD |
#        | colspan=2 style='background:%s' | Badugi
#|-""" % col_colours


hdcol1 = "grey"
hdcol2 = "lightgrey"

col_colours = (hdcol1,hdcol2,hdcol1,hdcol2,hdcol1,hdcol2,hdcol1,hdcol2,hdcol1,hdcol2,hdcol1,hdcol2)

###################### Cash Game Wiki Table ##############################

print """{| border=0<br>
|-
| Site || colspan=3 style='background:%s' | Holdem || colspan=3 style='background:%s' | Omaha || colspan=3 style='background:%s' | O8 || colspan=2 style='background:%s' | 5CS ||           style='background:%s' | 7CS ||           style='background:%s' | 7CS H/L ||           style='background:%s' | Razz || colspan=3 style='background:%s' | 5CD ||           style='background:%s' | 27SD || colspan=2 style='background:%s' | 27TD || colspan=2 style='background:%s' | A5TD || colspan=2 style='background:%s' | Badugi
|-""" % col_colours


print_site("PokerStars", ring, sitemasks)
print_site("Full Tilt Poker", ring, sitemasks)
print_site("PartyPoker", ring, sitemasks)
print_site("Everleaf", ring, sitemasks)
print_site("Boss", ring, sitemasks)
print_site("Merge", ring, sitemasks)
print_site("OnGame", ring, sitemasks)
print_site("iPoker", ring, sitemasks)
print_site("Winamax", ring, sitemasks)
print_site("Everest", ring, sitemasks)
print_site("Cake", ring, sitemasks)
print_site("Entraction", ring, sitemasks)
print_site("BetOnline", ring, sitemasks)
print_site("Absolute", ring, sitemasks)
print_site("Betfair", ring, sitemasks)
print_site("PKR", ring, sitemasks)
print_site("PacificPoker", ring, sitemasks)

print "|}"

print "###################### Tourney Wiki Table ##############################"

# Site specific changes for tourneys
# Stars: Preference for NLO8 to PLO8 in tourneys
sitemasks['PokerStars']['omahahilo'] = {   'nl': None,  'pl': None, 'fl': None}
print """{| border=0<br>
|-
| Site || colspan=3 style='background:%s' | Holdem || colspan=3 style='background:%s' | Omaha || colspan=3 style='background:%s' | O8 || colspan=2 style='background:%s' | 5CS ||           style='background:%s' | 7CS ||           style='background:%s' | 7CS H/L ||           style='background:%s' | Razz || colspan=3 style='background:%s' | 5CD ||           style='background:%s' | 27SD || colspan=2 style='background:%s' | 27TD || colspan=2 style='background:%s' | A5TD || colspan=2 style='background:%s' | Badugi 
|-""" % col_colours

print_site("PokerStars", tour, sitemasks)
print_site("Full Tilt Poker", tour, sitemasks)
print_site("PartyPoker", tour, sitemasks)
print_site("Everleaf", tour, sitemasks)
print_site("Boss", tour, sitemasks)
print_site("Merge", tour, sitemasks)
print_site("OnGame", tour, sitemasks)
print_site("iPoker", tour, sitemasks)
print_site("Winamax", tour, sitemasks)
print_site("Everest", tour, sitemasks)
print_site("Cake", tour, sitemasks)
print_site("Entraction", tour, sitemasks)
print_site("BetOnline", tour, sitemasks)
print_site("Absolute", tour, sitemasks)
print_site("Betfair", tour, sitemasks)
print_site("PKR", tour, sitemasks)
print_site("PacificPoker", tour, sitemasks)

print "|}"

