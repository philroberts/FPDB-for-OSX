#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Matthew Boss
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

import L10n
_ = L10n.get_translation()

# TODO:
#
# -- Assumes that the currency of ring games is USD
# -- Only accepts 'realmoney="true"'
# -- A hand's time-stamp does not record seconds past the minute (a limitation of the history format)
# -- hand.maxseats can only be guessed at
# -- Cannot parse tables that run it twice
# -- Cannot parse hands in which someone is all in in one of the blinds.

import sys
from HandHistoryConverter import *
from decimal_wrapper import Decimal


class Merge(HandHistoryConverter):
    sitename = "Merge"
    filetype = "text"
    codepage = ("cp1252", "utf8")
    siteId   = 12
    copyGameHeader = True

    limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Limit':'fl', 'Pot Limit':'pl', 'Pot Limit ':'pl', 'Half Pot Limit':'hp'}
    games = {              # base, category
                    'Holdem' : ('hold','holdem'),
                    'Omaha'  : ('hold','omahahi'),
               'Omaha H/L8'  : ('hold','omahahilo'),
              '2-7 Lowball'  : ('draw','27_3draw'),
              'A-5 Lowball'  : ('draw','a5_3draw'),
                   'Badugi'  : ('draw','badugi'),
           '5-Draw w/Joker'  : ('draw','fivedraw'),
                   '5-Draw'  : ('draw','fivedraw'),
                   '7-Stud'  : ('stud','studhi'),
              '7-Stud H/L8'  : ('stud','studhilo'),
                   '5-Stud'  : ('stud','5studhi'),
                     'Razz'  : ('stud','razz'),
            }
    
    mixes = {
                   'HA' : 'ha',
                 'RASH' : 'rash',
                   'HO' : 'ho',
                 'SHOE' : 'shoe',
                'HORSE' : 'horse',
                 'HOSE' : 'hose',
                  'HAR' : 'har'
        }
    
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),
                        '0.20': ('0.05', '0.10'),
                        '0.25': ('0.05', '0.10'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),       '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
                       '12.00': ('3.00', '6.00'),      '12': ('3.00', '6.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '50.00': ('10.00', '25.00'),    '50': ('10.00', '25.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                  }

    Multigametypes = {  '1': ('hold','holdem'),
                        '2': ('hold','holdem'),
                        '4': ('hold','omahahi'),
                        '9': ('hold', 'holdem'),
                        '23': ('hold', 'holdem'),
                        '34': ('hold','omahahilo'),
                        '35': ('hold','omahahilo'),
                        '37': ('hold','omahahilo'),
                        '38': ('stud','studhi'),
                        '39': ('stud','studhi'),
                        '41': ('stud','studhi'),
                        '42': ('stud','studhi'),
                        '43': ('stud','studhilo'),
                        '45': ('stud','studhilo'),
                        '46': ('stud','razz'),
                        '47': ('stud','razz'),
                        '49': ('stud','razz')
                  }    

    SnG_Structures = {  '$1 NL Holdem Double Up - 10 Handed'    : {'buyIn': 1,   'fee': 0.08, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2,2,2,2,2)},
                        '$1 PL Omaha Double Up - 10 Handed'     : {'buyIn': 1,   'fee': 0.08, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2,2,2,2,2)},
                        '$10 Bounty SnG - 6 Handed'             : {'buyIn': 5,   'fee': 1,    'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        '$10 Bounty SnG - 9 Handed'             : {'buyIn': 5,   'fee': 1,    'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22.5, 13.5, 9)},
                        '$10 Bounty SnG - 10 Handed'            : {'buyIn': 5,   'fee': 1,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        '$10 NL Holdem Double Up - 10 Handed'   : {'buyIn': 10,  'fee': 0.8,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,20,20,20,20)},
                        '$10 PL Omaha Double Up - 10 Handed'    : {'buyIn': 10,  'fee': 0.8,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,20,20,20,20)},
                        '$10 Winner Takes All - $60 Coupon'     : {'buyIn': 10,  'fee': 0.8,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        '$100 Bounty SnG - 6 Handed'            : {'buyIn': 100, 'fee': 9,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (315, 135)},
                        '$100 NL Holdem Double Up - 10 Handed'  : {'buyIn': 100, 'fee': 8,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,200,200,200,200)},
                        '$100 PL Omaha Double Up - 10 Handed'   : {'buyIn': 100, 'fee': 8,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,200,200,200,200)},
                        '$100,000 Guaranteed - Super Turbo Satellite' : {'buyIn': 38.8, 'fee': 0.8, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (109,109,11,3.8)},
                        '$10 Bounty SnG - 6 Handed'             : {'buyIn': 5, 'fee': 1,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        '$10 Satellite'                         : {'buyIn': 10,  'fee': 1,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        '$100 Bounty SnG - 6 Handed'            : {'buyIn': 100, 'fee': 9,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (315, 135)},
                        '$11 Coupon - Super Turbo Satellite'    : {'buyIn': 1.84,  'fee': 0.05,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (11,0.04)},
                        '$2 Bounty SnG - 10 Handed'             : {'buyIn': 2,   'fee': 0.2,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,6,4)},
                        '$2 Bounty SnG - 6 Handed'              : {'buyIn': 2,   'fee': 0.2,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (7, 3, 2)},
                        '$2 NL Holdem All-In or Fold 10 - Handed' : {'buyIn': 2,   'fee': 0.16, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,6,4)},
                        '$2 NL Holdem Double Up - 10 Handed'    : {'buyIn': 2,   'fee': 0.16, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4,4,4,4,4)},
                        '$2 PL Omaha Double Up - 10 Handed'     : {'buyIn': 2,   'fee': 0.16, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4,4,4,4,4)},
                        '$2 Satellite'                          : {'buyIn': 2,   'fee': 0.2,  'currency': 'USD', 'seats': 5,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (11,)},
                        '$20 Bounty SnG - 10 Handed'            : {'buyIn': 20,  'fee': 2,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (50, 30, 30)},
                        '$20 Bounty SnG - 9 Handed'             : {'buyIn': 20,  'fee': 2,    'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (45, 27, 18)},
                        '$20 Bounty SnG - 6 Handed'             : {'buyIn': 20,  'fee': 2,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        '$20 Daily Deep Stack Satellite'        : {'buyIn': 20,  'fee': 2,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (109, 11)},
                        '$20 NL Holdem Double Up - 10 Handed'   : {'buyIn': 20,  'fee': 1.6,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,40,40,40,40)},
                        '$20 NL Holdem Double Up - 10 Handed Turbo' : {'buyIn': 20,  'fee': 1.4,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,40,40,40,40)},
                        '$3 NL Holdem Double Up - 10 Handed'    : {'buyIn': 3,   'fee': 0.24, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (6,6,6,6,6)},
                        '$3 PL Omaha Double Up - 10 Handed'    : {'buyIn': 3,   'fee': 0.24, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (6,6,6,6,6)},
                        '$3.30 - 90 Man - Unlimited Rebuys and Addon SNG' : {'buyIn': 3,   'fee': 0.3, 'currency': 'USD', 'seats': 9, 'max': 90, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (81, 58.05, 40.5, 29.7, 20.25, 14.85, 10.8)},
                        '$30 Bounty SnG - 6 Handed'             : {'buyIn': 30,  'fee': 3,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        '$33 Coupon - Super Turbo Satellite'    : {'buyIn': 11,  'fee': 0.2,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (33, 33)},
                        '$33 Turbo - 6 Max'                     : {'buyIn': 30,  'fee': 3,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (126, 54)},
                        '$5 Bounty SnG - 10 Handed'             : {'buyIn': 5,   'fee': 0.5,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (12.50, 7.50, 5)},
                        '$5 Bounty SnG - 9 Handed'              : {'buyIn': 5,   'fee': 0.5,  'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (11.25, 6.75, 4.5)},
                        '$5 Bounty SnG - 6 Handed'              : {'buyIn': 5,   'fee': 0.5,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (14, 6)},
                        '$5 NL Holdem All-In or Fold - 10 Handed': {'buyIn': 5,   'fee': 0.4,  'currency': 'USD', 'seats': 10,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        '$5 NL Holdem Double Up - 6 Handed'     : {'buyIn': 5,   'fee': 0.4,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10)},
                        '$5 NL Holdem Double Up - 10 Handed'    : {'buyIn': 5,   'fee': 0.4,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10,10,10)},
                        '$5 NL Holdem Double Up - 10 Handed Turbo' : {'buyIn': 5,   'fee': 0.35,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10,10,10)},
                        '$5 PL Omaha Double Up - 10 Handed'     : {'buyIn': 5,   'fee': 0.4,  'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10,10,10)},
                        '$50 NL Holdem Double Up - 10 Handed'   : {'buyIn': 50,  'fee': 4,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10,10,10)},
                        '$50 PL Omaha Double Up - 10 Handed'    : {'buyIn': 50,  'fee': 4,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,10,10,10,10)},
                        '$55 Turbo - 6 Max'                     : {'buyIn': 50,  'fee': 4,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        '$60 Coupon - Super Turbo Satellite'    : {'buyIn': 10,  'fee': 0.19, 'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        '$60 Daily High Roller SnG Satellite'   : {'buyIn': 55,  'fee': 5,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (215, 115)},
                        '$75 Bounty SnG - 6 Handed'             : {'buyIn': 75,  'fee': 7.5,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        '$82 Turbo - 6 Max'                     : {'buyIn': 75,  'fee': 7,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (315, 135)},
                        '**NEW** Bumblebee Room - 3 Minute Levels'    : {'buyIn': 0.1, 'fee': 0.01, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (0.39, 0.21)},
                        '**NEW** Coyote Room - 3 Minute Levels'       : {'buyIn': 50, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (195, 105)},
                        '**NEW** Dragonfly Room - 3 Minute Levels'    : {'buyIn': 2, 'fee': 0.12, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (7.80, 4.20)},
                        '**NEW** Fruit Fly Room - 3 Minute Levels'    : {'buyIn': 1, 'fee': 0.06, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (3.90, 2.1)},
                        '**NEW** Gazelle Room - 3 Minute Levels'      : {'buyIn': 100, 'fee': 3.7, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (390, 210)},
                        '**NEW** Greyhound Room - 3 Minute Levels'    : {'buyIn': 35, 'fee': 1.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (136.5, 73.5)},
                        '**NEW** Hare Room - 3 Minute Levels'         : {'buyIn': 20, 'fee': 0.9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (78, 42)},
                        '**NEW** Hummingbird Room - 3 Minute Levels'  : {'buyIn': 5, 'fee': 0.3, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (19.50, 10.50)},
                        '**NEW** Killer Whale Room - 3 Minute Levels' : {'buyIn': 500, 'fee': 12, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1950, 1050)},
                        '**NEW** Marlin Room - 3 Minute Levels'       : {'buyIn': 350, 'fee': 10, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1365, 735)},
                        '**NEW** Sailfish Room - 3 Minute Levels'     : {'buyIn': 209, 'fee': 7, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (815.10, 438.90)},
                        '**NEW** Swift Room - 3 Minute Levels'        : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (39, 21)},
                        '100 Man Shootout Satellite - 4 x $109 tickets guaranteed!':  {'buyIn': 5,  'fee': 0.5,    'currency': 'USD', 'seats': 10, 'max': 100,  'multi': True, 'payoutCurrency': 'USD', 'payouts': (109, 109, 109, 109, 64)},
                        '100 VIP Point SnG'                     : {'buyIn': 1,   'fee': 0.05, 'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (0,0)},
                        '250 VIP Point SnG'                     : {'buyIn': 2.5, 'fee': 0.15, 'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (0,0)},
                        '500 VIP Point SnG'                     : {'buyIn': 5,   'fee': 0.25, 'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (0,0)},
                        'Aardvark Room'                         : {'buyIn': 10,  'fee': 1,    'currency': 'USD', 'seats': 9,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (45,27,18)},
                        'Alligator Room - Heads Up'             : {'buyIn': 100, 'fee': 4.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,)},
                        'Alligator Room - Turbo Heads Up'       : {'buyIn': 110, 'fee': 4.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (220,)},
                        'Alpaca Room - Turbo'                   : {'buyIn': 10,  'fee': 1,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Anaconda Room - Heads Up'              : {'buyIn': 100, 'fee': 4.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,)},
                        'Anaconda Room - Turbo Heads Up'        : {'buyIn': 110, 'fee': 4.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (220,)},
                        'Anchovy Room - Super Turbo HU'         : {'buyIn': 4, 'fee': 0.15,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (8,)},
                        'Anteater Room'                         : {'buyIn': 10,  'fee': 1,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Antelope Room'                         : {'buyIn': 5,   'fee': 0.5,  'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Arctic Fox Room - Heads Up'            : {'buyIn': 2,   'fee': 0.1, 'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (4,)},
                        'Armadillo Room'                        : {'buyIn': 20,  'fee': 2,    'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100, 60, 40)},
                        'Aussie Millions - Super Turbo Satelite': {'buyIn': 10,  'fee': 1,    'currency': 'USD', 'seats': 6,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        'Axolotyl Room - Heads Up'              : {'buyIn': 30,  'fee': 1.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        'Axolotyl Room - Turbo Heads Up'        : {'buyIn': 33,  'fee': 1.5,  'currency': 'USD', 'seats': 2,  'multi': False, 'payoutCurrency': 'USD', 'payouts': (66,)},
                        'Badger Room'                           : {'buyIn': 10,  'fee': 1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (50, 30, 20)},
                        'Bandicoot Room'                        : {'buyIn': 2,   'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Barramundi Room - Super Turbo'         : {'buyIn': 20,   'fee': 0.9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Bear Room'                             : {'buyIn': 50,  'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Bear Room - Heads Up'                  : {'buyIn': 200, 'fee': 9, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (400,)},
                        'Bear Room - Turbo Heads Up'            : {'buyIn': 220, 'fee': 9, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (440,)},
                        'Beaver Room'                           : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Beaver Room 12 min levels'             : {'buyIn': 5,   'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Beaver Room 12 min levels Short Handed' : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Bilby Room - Heads Up'                 : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Bilby Room - Turbo Heads Up'           : {'buyIn': 7, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (14,)},
                        'Bison Room - Heads Up'                 : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Bison Room - Turbo Heads Up'           : {'buyIn': 55, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Black Bear Room Turbo Heads Up (4 player)' : {'buyIn': 4, 'fee': 0.6, 'currency': 'USD', 'seats': 2, 'max': 4, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (48,)},
                        'Black Mamba Room - Super Turbo'        : {'buyIn': 12, 'fee': 52, 'currency': 'USD', 'seats': 6, 'max': 12, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (312, 187.2, 124.8)},
                        'Blackfish Room - Super Turbo'          : {'buyIn': 5, 'fee': 0.3, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21,9)},
                        'Blue Ringed Octopus Room - Super Turbo HU' : {'buyIn': 8, 'fee': 0.2, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (16,)},
                        'Blue Swimmer Crab - Super Turbo HU'    : {'buyIn': 15, 'fee': 0.3, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (30,)},
                        'Boar Room - Heads Up'                  : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Boar Room - Turbo Heads Up'            : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Bobcat Room'                           : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Botfly Room - Super Turbo HU'          : {'buyIn': 8, 'fee': 0.2, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (16,)},
                        'Bottlenose Dolphin Room - Super Turbo' : {'buyIn': 100, 'fee': 3.70, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (420, 180)},
                        'Buffalo Room'                          : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Buffalo Room - Heads Up'               : {'buyIn': 300, 'fee': 12, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (600,)},
                        'Buffalo Room - Turbo Heads Up'         : {'buyIn': 330, 'fee': 12, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (660,)},
                        'Bumblebee Room - Super Turbo'          : {'buyIn': 0.1, 'fee': 0.01, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (0.42, 0.18)},
                        'Bunyip Room - Heads Up'                : {'buyIn': 100, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,)},
                        'Bunyip Room - Turbo Heads Up'          : {'buyIn': 110, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (220,)},
                        'Bushmaster Room Super Turbo HU'        : {'buyIn': 250, 'fee': 4, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (500,)},
                        'Caiman Room'                           : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Camel Room'                            : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Cape Hunting Dog Room'                 : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 9, 'max': 45, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (27.90, 19.35, 14.85, 11.25, 8.10, 5.40, 3.15)},
                        'Capra room - Heads Up'                 : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Capybara Room'                         : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Cassowary Room'                        : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        'Cobra Room - Heads Up'                 : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Cobra Room - Turbo Heads Up'           : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Coconut Crab Room - Super Turbo'       : {'buyIn': 35, 'fee': 1.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (147, 63)},
                        'Condor Room - Heads Up'                : {'buyIn': 30, 'fee': 1.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        'Condor Room - Turbo Heads Up'          : {'buyIn': 33, 'fee': 1.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (66,)},
                        'Conga Eel Room - Super Turbo HU'       : {'buyIn': 120, 'fee': 2.3, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (240,)},
                        'Cougar Room - Heads Up'                : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Cougar Room - Turbo Heads Up'          : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Coyote Room - Super Turbo'             : {'buyIn': 50, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Cricket Room - Super Turbo 6 Max'      : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'max': 18, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (14.40, 10.8, 7.2, 3.6)},
                        'Crocodile Room'                        : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 9, 'max': 18, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (36, 27, 18, 9)},
                        'Daily High Roller - Super Turbo Satellite' : {'buyIn': 72, 'fee': 1.3, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (215, 215, 2)},
                        'Dingo Room - Heads Up'                 : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Dingo Room - Turbo Heads Up'           : {'buyIn': 55, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Dollar Dazzler Turbo'                  : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (5, 3, 2)},
                        'Dolphin Room'                          : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10, 6, 4)},
                        'Dragon Room'                           : {'buyIn': 100, 'fee': 9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (420, 180)},
                        'Dragonfly Room - Super Turbo'          : {'buyIn': 2, 'fee': 0.12, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Dugong Room'                           : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (225, 135, 90)},
                        'Eagle Room'                            : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Eagle Room 12 min levels'              : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (50, 30, 20)},
                        'Eagle Room 12 min levels Short Handed' : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Echidna Room'                          : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Elephant Room - Heads Up'              : {'buyIn': 100, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,)},
                        'Elephant Room - Turbo Heads Up'        : {'buyIn': 110, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (220,)},
                        'Elephant Shrew Room'                   : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (9, 5.40, 3.60)},
                        'Elk Room'                              : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Emperor Penguin Room'                  : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 90, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (0,) },
                        'Emperor Penguin Room Turbo'            : {'buyIn': 2.20, 'fee': 0.2, 'currency': 'USD', 'seats': 90, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (0,) },
                        'Emu Room - Heads Up'                   : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Emu Room - Turbo Heads Up'             : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Falcon Room'                           : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (250, 150, 100)},
                        'Falcon Room Turbo'                     : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (250, 150, 100)},
                        'Fast Fifty SnG'                        : {'buyIn': 0.5, 'fee': 0.1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2.50, 1.50, 1)},
                        'Fast Fifty Turbo'                      : {'buyIn': 0.5, 'fee': 0.1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2.50, 1.50, 1)},
                        'Ferret Room - Turbo'                   : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (50, 30, 20)},
                        'Fox Room - Heads Up'                   : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Fox Room - Turbo Heads Up'             : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Frigate Bird Room Super Turbo HU'      : {'buyIn': 2, 'fee': 0.1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4,)},
                        'Fruit Fly Room - Super Turbo'          : {'buyIn': 1, 'fee': 0.06, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4.20, 1.80)},
                        'Fusilier Room Turbo'                   : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 9, 'max': 45, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (13.96, 9.68, 7.42, 5.62, 4.05, 2.70, 1.57)},
                        'Fun Step 1'                            : {'buyIn': 0, 'fee': 0, 'currency': 'FREE', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (0, 0, 0)},
                        'Fun Step 2'                            : {'buyIn': 0, 'fee': 0, 'currency': 'FREE', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (0, 0, 0)},
                        'Fun Step 3'                            : {'buyIn': 0, 'fee': 0, 'currency': 'FREE', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1, 0, 0)},
                        'Galapagos Turtle - Super Turbo HU'     : {'buyIn': 120, 'fee': 2.30, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (240,)},
                        'Gazelle Room - Super Turbo'            : {'buyIn': 100, 'fee': 3.7, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (420, 180)},
                        'Gecko Room'                            : {'buyIn': 30, 'fee': 3, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (150, 90, 60)},
                        'Gecko Room Turbo'                      : {'buyIn': 30, 'fee': 3, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (150, 90, 60)},
                        'Gibbon Room'                           : {'buyIn': 200, 'fee': 15, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (840, 360)},
                        'Giraffe Room'                          : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Goldfish Room'                         : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Gopher Room - Turbo'                   : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Gorilla Room - Heads Up'               : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Gorilla Room - Turbo Heads Up'         : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Gnat Room - Super Turbo HU'            : {'buyIn': 4, 'fee': 0.15, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8,)},
                        'Goblin Shark Room'                     : {'buyIn': 150, 'fee': 2.75, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (300,)},
                        'Goblin Shark Room - Super Turbo HU'    : {'buyIn': 150, 'fee': 2.75, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (300,)},
                        'Golden Eagle Turbo HU'                 : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Goldfish Room'                         : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Great White Shark Room - Heads Up'     : {'buyIn': 2000, 'fee': 40, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4000,)},
                        'Great White Shark Room - Turbo Heads Up' : {'buyIn': 2200, 'fee': 40, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (4400,)},
                        'Grey Wolf Room Turbo HU (4 player)'    : {'buyIn': 18, 'fee': 0.9, 'currency': 'USD', 'seats': 2, 'max': 4, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (72,)},
                        'Greyhound Room - 2 Minute Levels'      : {'buyIn': 35, 'fee': 1.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (136.5, 73.5)},
                        'Greyhound Room - Super Turbo'          : {'buyIn': 35, 'fee': 1.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (147, 63)},
                        'Grizzly Room'                          : {'buyIn': 30, 'fee': 3, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (126, 54)},
                        'Guinea Pig Room - Super Turbo'         : {'buyIn': 5, 'fee': 0.3, 'currency': 'USD', 'seats': 6, 'max': 12, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (30, 18, 12)},
                        'Hairy Frog Room - Super Turbo HU'      : {'buyIn': 28, 'fee': 0.7, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (56,)},
                        'Hare Room - Super Turbo'               : {'buyIn': 20, 'fee': 0.9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Hedgehog Room'                         : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22.50, 13.50, 9)},
                        'Heron Room'                            : {'buyIn': 300, 'fee': 20, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1260, 540)},
                        'Hippo Room - Heads Up'                 : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Hippo Room - Turbo Heads Up'           : {'buyIn': 55, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Honey Badger Room'                     : {'buyIn': 5, 'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Howler Monkey Room - Super Turbo'      : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'max': 12, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (60, 36, 24)},
                        'Hummingbird Room - Super Turbo'        : {'buyIn': 5, 'fee': 0.3, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Hyena Room'                            : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10, 6, 4)},
                        'Ibex Room - Super Turbo HU'            : {'buyIn': 180, 'fee': 3.1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (360,)},
                        'Iguana Room - Heads Up'                : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Iguana Room - Turbo Heads Up'          : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Impala Room'                           : {'buyIn': 30, 'fee': 3, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (135, 81, 54)},
                        'Jaguar Room'                           : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Killer Whale Room - Super Turbo'       : {'buyIn': 500, 'fee': 12, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2100, 900)},
                        'King Cobra Room - Super Turbo HU'      : {'buyIn': 500, 'fee': 7.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1000,)},
                        'King Crab Room - Super Turbo HU'       : {'buyIn': 28, 'fee': 0.7, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (56,)},
                        'King Tuna Room - Super Turbo'          : {'buyIn': 50, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Komodo Room'                           : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (210, 90)},
                        'Kookaburra Room - Heads Up'            : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Kookaburra Room - Turbo Heads Up'      : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Lemming Room - Super Turbo HU'         : {'buyIn': 40, 'fee': 0.8, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (80,)},
                        'Lemur Room - Super Turbo HU'           : {'buyIn': 55, 'fee': 1.1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Leopard Room'                          : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Leopard Seal Room - Heads Up'          : {'buyIn': 30, 'fee': 1.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (60,)},
                        'Lion Room - Heads Up'                  : {'buyIn': 1000, 'fee': 30, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2000,)},
                        'Lion Room - Turbo Heads Up'            : {'buyIn': 1100, 'fee': 30, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2200,)},
                        'Lizard Room - Turbo'                   : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Lynx Room'                             : {'buyIn': 110, 'fee': 9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (462, 198)},
                        'Mako Room'                             : {'buyIn': 75, 'fee': 7, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (375, 225, 150)},
                        'Mako Room Turbo'                       : {'buyIn': 75, 'fee': 7, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (375, 225, 150)},
                        'Mallard Room'                          : {'buyIn': 100, 'fee': 9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (420, 180)},
                        'Mandrill Room'                         : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        'Marlin Room - Super Turbo'             : {'buyIn': 350, 'fee': 10, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1470, 630)},
                        'Meerkat Room - Turbo'                  : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Mink Room - Heads Up'                  : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Mink Room - Turbo Heads Up'            : {'buyIn': 7, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (14,)},
                        'Mountain Goat Room Turbo HU (4 player)' : {'buyIn': 6, 'fee': 0.3, 'currency': 'USD', 'seats': 2, 'max': 4, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (24,)},
                        'Mongoose Room'                         : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10, 6, 4)},
                        'Monkey Room'                           : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (90, 54, 36)},
                        'Mountain Lion Turbo HU'                : {'buyIn': 75, 'fee': 3.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (150,)},
                        'Mouse Room'                            : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10, 6, 4)},
                        'Musk Rat Room'                         : {'buyIn': 3, 'fee': 0.3, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (16.80, 7.20)},
                        'Ocelot Room'                           : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (56, 24)},
                        'Orangutan Room'                        : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Otter Room - Turbo'                    : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (21, 9)},
                        'Ox Room - Turbo'                       : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100, 60, 40)},
                        'Panda Room - Heads Up'                 : {'buyIn': 100, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (200,)},
                        'Panda Room - Turbo Heads Up'           : {'buyIn': 110, 'fee': 4.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (220,)},
                        'Panther Room - Heads Up'               : {'buyIn': 500, 'fee': 20, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1000,)},
                        'Panther Room - Turbo Heads Up'         : {'buyIn': 550, 'fee': 20, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1100,)},
                        'Peregrine Room'                        : {'buyIn': 330, 'fee': 20, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1386, 594)},
                        'Pilchard Room Turbo'                   : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 9, 'max': 18, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (7.20, 5.40, 3.60, 1.80)},
                        'Piranha Room - Heads Up'               : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Piranha Room - Turbo Heads Up'         : {'buyIn': 55, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Polar Bear Room - Super Turbo HU'      : {'buyIn': 500, 'fee': 7.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1000,)},
                        'Pond Skater Room - Super Turbo HU'     : {'buyIn': 15, 'fee': 0.3, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (30,)},
                        'Platypus Room'                         : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        'Pronghorn Antelope Room - Super Turbo HU' : {'buyIn': 1000, 'fee': 15, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2000,)},
                        'Puffin Room - Super Turbo HU'          : {'buyIn': 70, 'fee': 1.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (140,)},
                        'Puma Room - Heads Up'                  : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Puma Room - Turbo Heads Up'            : {'buyIn': 22, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (44,)},
                        'Rabbit Room - Turbo'                   : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10, 6, 4)},
                        'Racoon Room'                           : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        'Rattlesnake Room - Heads Up'           : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Rattlesnake Room - Turbo Heads Up'     : {'buyIn': 5.75, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (11.50,)},
                        'Raven Room'                            : {'buyIn': 180, 'fee': 14, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (756, 324)},
                        'Razorback Room'                        : {'buyIn': 100, 'fee': 9, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (420, 180)},
                        'Red Kangaroo Room - Heads Up'          : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (40,)},
                        'Rhino Room - Heads Up'                 : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Rhino Room - Turbo Heads Up'           : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Sailfish Room - Super Turbo'           : {'buyIn': 209, 'fee': 7, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (877.80, 376.20)},
                        'Salmon Room'                           : {'buyIn': 5, 'fee': 0.5, 'currency': 'USD', 'seats': 9, 'max': 45, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (69.76, 48.38, 37.12, 28.12, 20.25, 13.50, 7.87)},
                        'Sardine Room Turbo'                    : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 9, 'max': 27, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (10.27, 7.02, 4.59, 2.75, 2.37)},
                        'Sea Eagle Room Turbo HU (4 player)'    : {'buyIn': 24, 'fee': 1.2, 'currency': 'USD', 'seats': 2, 'max': 4, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (96,)},
                        'Silverfish Room - Super Turbo'         : {'buyIn': 10, 'fee': 5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Sea Kraits Room - Super Turbo HU'      : {'buyIn': 70, 'fee': 1.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (140,)},
                        'Secretary Bird Room - Super Turbo HU'  : {'buyIn': 90, 'fee': 1.8, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (180,)},
                        'Shrew Room - Heads Up'                 : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Shrew Room - Turbo Heads Up'           : {'buyIn': 7, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (14,)},
                        "Snakes'n'Ladders Step 1"               : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (3.30, 3.30, 1.10, 1.10, 1.10, 0.10)},
                        "Snakes'n'Ladders Step 2"               : {'buyIn': 3, 'fee': 0.3, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (11, 11, 3.30, 3.30, 1.10, 0.30)},
                        "Snakes'n'Ladders Step 3"               : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (32.50, 32.50, 11, 11, 3.30, 3.30, 3.30, 1.10, 1.10, 0.90)},
                        "Snakes'n'Ladders Step 4"               : {'buyIn': 30, 'fee': 2.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (80, 80, 80, 32.50, 11, 11, 3.30, 1.10, 1.10)},
                        "Snakes'n'Ladders Step 5"               : {'buyIn': 75, 'fee': 5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (265, 265, 80, 80, 32.50, 11, 11, 3.30, 1.10, 1.10)},
                        "Snakes'n'Ladders Step 6"               : {'buyIn': 255, 'fee': 10, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (530, 530, 530, 265, 265, 265, 80, 80, 3.30, 1.70)},
                        "Snakes'n'Ladders Step 7"               : {'buyIn': 510, 'fee': 20, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2000, 1250, 750, 499.50, 295, 220, 80, 3.30, 1.10, 1.10)},
                        'Snow Goose Room'                       : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 9, 'max': 45, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (139.50, 96.75, 74.25, 56.25, 40.50, 27, 15.75)},
                        'Southern Stingray Room - Super Turbo HU' : {'buyIn': 55, 'fee': 1.1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (110,)},
                        'Springbok Room - Super Turbo'          : {'buyIn': 20, 'fee': 0.9, 'currency': 'USD', 'seats': 6, 'max': 12, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (120, 72, 48)},
                        'Squirrel Room - Turbo'                 : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.40, 3.60)},
                        'Stag Room Turbo HU (4 player)'        : {'buyIn': 3, 'fee': 0.15, 'currency': 'USD', 'seats': 2, 'max': 4, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (12,)},
                        'Starling Room'                         : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 9, 'max': 180, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (108, 72, 36, 28.80, 21.60, 18, 14.40, 10.80, 8.10, 6.30, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60) },
                        'Starling Room TURBO'                   : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 9, 'max': 180, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (108, 72, 36, 28.80, 21.60, 18, 14.40, 10.80, 8.10, 6.30, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60, 3.60) },
                        'STEP 1 AIOF Sng'                       : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (5.50, 1.10, 1.10, 1.10, 0.20)},
                        'STEP 10 AIOF Final Sng'                : {'buyIn': 1170, 'fee': 10, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2250, 90)},
                        'STEP 2 AIOF Sng'                       : {'buyIn': 5.25, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10.50,)},
                        'STEP 3 AIOF Sng'                       : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'STEP 4 AIOF Sng'                       : {'buyIn': 19.5, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (39,)},
                        'STEP 5 AIOF Sng'                       : {'buyIn': 38.5, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (77,)},
                        'STEP 6 AIOF Sng'                       : {'buyIn': 76, 'fee': 1, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (152,)},
                        'STEP 7 AIOF Sng'                       : {'buyIn': 150, 'fee': 2, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (300,)},
                        'STEP 8 AIOF Sng'                       : {'buyIn': 297, 'fee': 3, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (594,)},
                        'STEP 9 AIOF Sng'                       : {'buyIn': 590, 'fee': 4, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1180,)},
                        'Sun Bear Room'                         : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (112, 48)},
                        'Swift Room - Super Turbo'              : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Swordfish Room'                        : {'buyIn': 220, 'fee': 15, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (924, 396)},
                        'T-Rex Room - Heads Up'                 : {'buyIn': 5000, 'fee': 80, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10000,)},
                        'T-Rex Room - Turbo Heads Up'           : {'buyIn': 5500, 'fee': 80, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (11000,)},
                        'Tapir Room'                            : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (112, 48)},
                        'Termite Room'                          : {'buyIn': 3, 'fee': 0.3, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (16.80, 7.20)},
                        'Tetra Room Turbo'                      : {'buyIn': 1, 'fee': 0.1, 'currency': 'USD', 'seats': 90, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (0,) },
                        'Tiger Fish Room'                       : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 8, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (56, 24,)},
                        'Tiger Room - Heads Up'                 : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Tiger Room - Turbo Heads Up'           : {'buyIn': 55, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Tiger Shark - Super Turbo'             : {'buyIn': 209, 'fee': 7, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (877.80, 376.20)},
                        'Timber Wolf Room'                      : {'buyIn': 400, 'fee': 22, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1680, 720)},
                        'Toucan Room - Heads Up'                : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Toucan Room - Heads Up'                : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Toucan Room - Turbo Heads Up'          : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Tsetse Fly Room'                       : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (8.4,3.6)},
                        'Turkey Room - Heads Up'                : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Turkey Room - Turbo Heads Up'          : {'buyIn': 11, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (22,)},
                        'Viper Room - Heads Up'                 : {'buyIn': 1000, 'fee': 40, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2000,)},
                        'Vulture Room'                          : {'buyIn': 20, 'fee': 2, 'currency': 'USD', 'seats': 9, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (90,54,36)},
                        'Wallaby Room'                          : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Walrus Room'                           : {'buyIn': 50, 'fee': 5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (250, 150, 100)},
                        'Warthog Room'                          : {'buyIn': 2, 'fee': 0.2, 'currency': 'USD', 'seats': 9, 'max': 18, 'multi': True, 'payoutCurrency': 'USD', 'payouts': (18, 10.80, 7.20)},
                        'Waterbuck room - Heads Up'             : {'buyIn': 10, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (20,)},
                        'Whale Room - Heads Up'                 : {'buyIn': 500, 'fee': 20, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (1000,)},
                        'Whale Shark Room - Super Turbo'        : {'buyIn': 500, 'fee': 12, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (2100,900)},
                        'White Whale Room Super Turbo HU'     : {'buyIn': 250, 'fee': 4, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (500,)},
                        'Wildebeest Room'                       : {'buyIn': 10, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42, 18)},
                        'Wolf Spider Room - Super Turbo HU'     : {'buyIn': 21, 'fee': 0.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (42,)},
                        'Wolverine Room'                        : {'buyIn': 50, 'fee': 0.5, 'currency': 'USD', 'seats': 10, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (25, 15, 10)},
                        'Wombat Room'                           : {'buyIn': 20, 'fee': 1, 'currency': 'USD', 'seats': 6, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (84, 36)},
                        'Yak Room - Heads Up'                   : {'buyIn': 50, 'fee': 2.5, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (100,)},
                        'Zebra Room - Heads Up'                 : {'buyIn': 5, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (10,)},
                        'Zebra Room - Turbo Heads Up'           : {'buyIn': 7, 'fee': 0.25, 'currency': 'USD', 'seats': 2, 'multi': False, 'payoutCurrency': 'USD', 'payouts': (14,)},
                     }

    # Static regexes
    re_Identify = re.compile(u'<game\sid=\"[0-9]+\-[0-9]+\"\sstarttime')
    re_SplitHands = re.compile(r'</game>\n+(?=<)')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r'<description type="(?P<GAME>Holdem|Omaha|Omaha|Omaha\sH/L8|2\-7\sLowball|A\-5\sLowball|Badugi|5\-Draw\sw/Joker|5\-Draw|7\-Stud|7\-Stud\sH/L8|5\-Stud|Razz|HORSE|RASH|HA|HO|SHOE|HOSE|HAR)(?P<TYPE>\sTournament)?" stakes="(?P<LIMIT>[a-zA-Z ]+)(\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?)?"(\sversion="\d+")?/>', re.MULTILINE)
    # <game id="46154255-645" starttime="20111230232051" numholecards="2" gametype="1" seats="9" realmoney="false" data="20111230|Play Money (46154255)|46154255|46154255-645|false">
    # <game id="46165919-1" starttime="20111230161824" numholecards="2" gametype="23" seats="10" realmoney="true" data="20111230|Fun Step 1|46165833-1|46165919-1|true">
    # <game id="46289039-1" starttime="20120101200100" numholecards="2" gametype="23" seats="9" realmoney="true" data="20120101|$200 Freeroll - NL Holdem - 20%3A00|46245544-1|46289039-1|true">
    re_HandInfo = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>.+?)" numholecards="[0-9]+" gametype="[0-9]+" (multigametype="(?P<MULTIGAMETYPE>\d+)" )?(seats="(?P<SEATS>[0-9]+)" )?realmoney="(?P<REALMONEY>(true|false))" data="[0-9]+[|:](?P<TABLENAME>[^|:]+)[|:](?P<TDATA>[^|:]+)[|:]?.*>', re.MULTILINE)
    re_Button = re.compile(r'<players dealer="(?P<BUTTON>[0-9]+)">')
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" nickname="(?P<PNAME>.+)" balance="\$(?P<CASH>[.0-9]+)" dealtin="(?P<DEALTIN>(true|false))" />', re.MULTILINE)
    re_Board = re.compile(r'<cards type="COMMUNITY" cards="(?P<CARDS>[^"]+)"', re.MULTILINE)
    re_Buyin = re.compile(r'\$(?P<BUYIN>[.,0-9]+)\s(?P<TYPE>Freeroll|Satellite|Guaranteed)?', re.MULTILINE)
    re_secondGame = re.compile(r'\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)', re.MULTILINE)
    
    # The following are also static regexes: there is no need to call
    # compilePlayerRegexes (which does nothing), since players are identified
    # not by name but by seat number
    re_PostSB = re.compile(r'<event sequence="[0-9]+" type="SMALL_BLIND" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBB = re.compile(r'<event sequence="[0-9]+" type="(BIG_BLIND|INITIAL_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BB>[.0-9]+)"/>', re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="RETURN_BLIND" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[.0-9]+)"/>', re.MULTILINE)
    re_Antes = re.compile(r'<event sequence="[0-9]+" type="ANTE" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<ANTE>[.0-9]+)"/>', re.MULTILINE)
    re_BringIn = re.compile(r'<event sequence="[0-9]+" type="BRING_IN" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BRINGIN>[.0-9]+)"/>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="(HOLE|DRAW_DRAWN_CARDS)" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT|DRAW|COMPLETE)"( timestamp="(?P<TIMESTAMP>[0-9]+)")? player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?( text="(?P<TXT>.+)")?/>', re.MULTILINE)
    re_AllActions = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT|DRAW|COMPLETE|BIG_BLIND|INITIAL_BLIND|SMALL_BLIND|RETURN_BLIND|BRING_IN|ANTE)"( timestamp="(?P<TIMESTAMP>[0-9]+)")? player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?( text="(?P<TXT>.+)")?/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<winner amount="(?P<POT>[.0-9]+)" uncalled="(?P<UNCALLED>false|true)" potnumber="[0-9]+" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_ShownCards     = re.compile(r'<cards type="(?P<SHOWED>SHOWN|MUCKED)" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_Connection  = re.compile(r'<event sequence="[0-9]+" type="(?P<TYPE>RECONNECTED|DISCONNECTED)" timestamp="[0-9]+" player="[0-9]"/>', re.MULTILINE)
    re_Cancelled   = re.compile(r'<event sequence="\d+" type="GAME_CANCELLED" timestamp="\d+"/>', re.MULTILINE)
    re_LeaveTable  = re.compile(r'<event sequence="\d+" type="LEAVE" timestamp="\d+" player="\d"/>', re.MULTILINE)
    re_PlayerOut   = re.compile(r'<event sequence="\d+" type="PLAYER_OUT" timestamp="\d+" player="(?P<PSEAT>[0-9])"/>', re.MULTILINE)
    re_EndOfHand   = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)
    re_DateTime    = re.compile(r'(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)', re.MULTILINE)
    re_PlayMoney   = re.compile(r'realmoney="false"')

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # This special function is required because Merge Poker records
        # actions by seat number (0 based), not by the player's name
        for p in hand.players:
            if p[0] == int(seatNo)+1:
                return p[1]

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "hold", "hp"],

                ["ring", "stud", "fl"],
                ["ring", "stud", "pl"],
                ["ring", "stud", "nl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],
                ["ring", "draw", "hp"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                ["tour", "stud", "fl"],
                ["tour", "stud", "pl"],
                ["tour", "stud", "nl"],
                
                ["tour", "draw", "fl"],
                ["tour", "draw", "pl"],
                ["tour", "draw", "nl"],
                ]

    def parseHeader(self, handText, whole_file):
        gametype = self.determineGameType(handText)
        if gametype is None:
            gametype = self.determineGameType(whole_file)
            if gametype is None:
                tmp = handText[0:200]
                log.error(_("MergeToFpdb.determineGameType: '%s'") % tmp)
                raise FpdbParseError
            else:
                if 'mix' in gametype and gametype['mix']!=None:
                    self.mergeMultigametypes(handText)
        return gametype        

    def determineGameType(self, handText):
        """return dict with keys/values:
    'type'       in ('ring', 'tour')
    'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl', 'hp')
    'base'       in ('hold', 'stud', 'draw')
    'category'   in ('holdem', 'omahahi', omahahilo', 'razz', 'studhi', 'studhilo', 'fivedraw', '27_1draw', '27_3draw', 'badugi')
    'hilo'       in ('h','l','s')
    'smallBlind' int?
    'bigBlind'   int?
    'smallBet'
    'bigBet'
    'currency'  in ('USD', 'EUR', 'T$', <countrycode>)
or None if we fail to get the info """

        m = self.re_GameInfo.search(handText)
        if not m: return None

        self.info = {}
        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg

        if 'LIMIT' in mg:
            self.info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            if mg['GAME'] in self.mixes:
                self.info['mix'] = self.mixes[mg['GAME']]
                self.mergeMultigametypes(handText)
            else:
                (self.info['base'], self.info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']
        self.info['secondGame'] = False
        if mg['blah'] is not None:
            if self.re_secondGame.search(mg['blah']):
                self.info['secondGame'] = True
        if ' Tournament' == mg['TYPE']:
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
        else:
            self.info['type'] = 'ring'
            if self.re_PlayMoney.search(handText):
                self.info['currency'] = 'play'
            else:
                self.info['currency'] = 'USD'

        if self.info['limitType'] == 'fl' and self.info['bb'] is not None and self.info['type'] == 'ring':
            try:
                self.info['sb'] = self.Lim_Blinds[mg['BB']][0]
                self.info['bb'] = self.Lim_Blinds[mg['BB']][1]
            except KeyError:
                tmp = handText[0:200]
                log.error(_("MergeToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                raise FpdbParseError

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("MergeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: mg: %s" % m.groupdict()
        self.determineErrorType(hand, None)

        hand.handid = m.group('HID1') + m.group('HID2')

        if hand.gametype['type'] == 'tour':
            tid_table = m.group('TDATA').split('-')
            tid = tid_table[0]
            if len(tid_table)>1:
                table = tid_table[1]
            else:
                table = '0'
            self.info['tablename'] = m.group('TABLENAME').replace('  - ', ' - ').strip()
            self.info['tourNo'] = hand.tourNo
            hand.tourNo = tid
            hand.tablename = table
            if self.info['tablename'] in self.SnG_Structures:
                hand.buyin = int(100*self.SnG_Structures[self.info['tablename']]['buyIn'])
                hand.fee   = int(100*self.SnG_Structures[self.info['tablename']]['fee'])
                hand.buyinCurrency=self.SnG_Structures[self.info['tablename']]['currency']
                hand.maxseats = self.SnG_Structures[self.info['tablename']]['seats']
                hand.isSng = True
                self.summaryInFile = True
            else:
                #print 'DEBUG', 'no match for tourney %s tourNo %s' % (self.info['tablename'], tid)
                hand.buyin = 0
                hand.fee = 0
                hand.buyinCurrency="NA"
                hand.maxseats = None
                if m.group('SEATS')!=None:
                    hand.maxseats = int(m.group('SEATS'))                    
        else:
            #log.debug("HID %s-%s, Table %s" % (m.group('HID1'), m.group('HID2'), m.group('TABLENAME')))
            hand.tablename = m.group('TABLENAME')
            hand.maxseats = None
            if m.group('SEATS')!=None:
                hand.maxseats = int(m.group('SEATS')) 
                
        m1 = self.re_DateTime.search(m.group('DATETIME'))
        if m1:
            mg = m1.groupdict()
            datetimestr = "%s/%s/%s %s:%s:%s" % (mg['Y'], mg['M'],mg['D'],mg['H'],mg['MIN'],mg['S'])
            #tz = a.group('TZ')  # just assume ET??
            hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        else:
            hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:14],'%Y%m%d%H%M%S')
            
        hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
        hand.newFormat = datetime.datetime.strptime('20100908000000','%Y%m%d%H%M%S')
        hand.newFormat = HandHistoryConverter.changeTimezone(hand.newFormat, "ET", "UTC")
        # Check that the hand is complete up to the awarding of the pot; if
        # not, the hand is unparseable
        if self.re_EndOfHand.search(hand.handText) is None:
            self.determineErrorType(hand, "readHandInfo")

    def readPlayerStacks(self, hand):
        acted = {}
        seated = {}
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatno = a.group('SEAT')
            seated[seatno] = [a.group('PNAME'), a.group('CASH')]

        if hand.gametype['type'] == "ring" :
            # We can't 100% trust the 'dealtin' field. So read the actions and see if the players acted
            m2 = self.re_AllActions.finditer(hand.handText)
            fulltable = False
            for action in m2:
                acted[action.group('PSEAT')] = True
                if acted.keys() == seated.keys(): # We've faound all players
                    fulltable = True
                    break
            if fulltable != True:
                for seatno in seated.keys():
                    if seatno not in acted:
                        del seated[seatno]

                for seatno in acted.keys():
                    if seatno not in seated:
                        log.error(_("MergeToFpdb.readPlayerStacks: '%s' Seat:%s acts but not listed") % (hand.handid, seatno))
                        raise FpdbParseError

        for seat in seated:
            name, stack = seated[seat]
            # Merge indexes seats from 0. Add 1 so we don't have to add corner cases everywhere else.
            hand.addPlayer(int(seat) + 1, name, stack)
            
        if hand.maxseats==None:
            if hand.gametype['type'] == 'tour' and self.maxseats==0:
                hand.maxseats = self.guessMaxSeats(hand)
                self.maxseats = hand.maxseats
            elif hand.gametype['type'] == 'tour':
                hand.maxseats = self.maxseats
            else:
                hand.maxseats = None

        # No players found at all.
        if not hand.players:
            self.determineErrorType(hand, "readPlayerStacks")

    def markStreets(self, hand):
        if hand.gametype['base'] == 'hold':
            m = re.search(r'<round id="PREFLOP" sequence="[0-9]+">(?P<PREFLOP>.+(?=<round id="POSTFLOP")|.+)'
                         r'(<round id="POSTFLOP" sequence="[0-9]+">(?P<FLOP>.+(?=<round id="POSTTURN")|.+))?'
                         r'(<round id="POSTTURN" sequence="[0-9]+">(?P<TURN>.+(?=<round id="POSTRIVER")|.+))?'
                         r'(<round id="POSTRIVER" sequence="[0-9]+">(?P<RIVER>.+))?', hand.handText, re.DOTALL)
        elif hand.gametype['base'] == 'draw':
            if hand.gametype['category'] in ('27_3draw','badugi','a5_3draw'):
                m =  re.search(r'(?P<PREDEAL>.+(?=<round id="PRE_FIRST_DRAW" sequence="[0-9]+">)|.+)'
                           r'(<round id="PRE_FIRST_DRAW" sequence="[0-9]+">(?P<DEAL>.+(?=<round id="FIRST_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="FIRST_DRAW" sequence="[0-9]+">(?P<DRAWONE>.+(?=<round id="SECOND_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="SECOND_DRAW" sequence="[0-9]+">(?P<DRAWTWO>.+(?=<round id="THIRD_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="THIRD_DRAW" sequence="[0-9]+">(?P<DRAWTHREE>.+))?', hand.handText,re.DOTALL)
            else:
                m =  re.search(r'(?P<PREDEAL>.+(?=<round id="PRE_FIRST_DRAW" sequence="[0-9]+">)|.+)'
                           r'(<round id="PRE_FIRST_DRAW" sequence="[0-9]+">(?P<DEAL>.+(?=<round id="FIRST_DRAW" sequence="[0-9]+">)|.+))?'
                           r'(<round id="FIRST_DRAW" sequence="[0-9]+">(?P<DRAWONE>.+(?=<round id="SECOND_DRAW" sequence="[0-9]+">)|.+))?', hand.handText,re.DOTALL)
        elif hand.gametype['base'] == 'stud':
            m =  re.search(r'(?P<ANTES>.+(?=<round id="BRING_IN" sequence="[0-9]+">)|.+)'
                       r'(<round id="BRING_IN" sequence="[0-9]+">(?P<THIRD>.+(?=<round id="FOURTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="FOURTH_STREET" sequence="[0-9]+">(?P<FOURTH>.+(?=<round id="FIFTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="FIFTH_STREET" sequence="[0-9]+">(?P<FIFTH>.+(?=<round id="SIXTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="SIXTH_STREET" sequence="[0-9]+">(?P<SIXTH>.+(?=<round id="SEVENTH_STREET" sequence="[0-9]+">)|.+))?'
                       r'(<round id="SEVENTH_STREET" sequence="[0-9]+">(?P<SEVENTH>.+))?', hand.handText,re.DOTALL)
        if m == None:
            self.determineErrorType(hand, "markStreets")
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        if m and street in ('FLOP','TURN','RIVER'):
            if street == 'FLOP':
                hand.setCommunityCards(street, m.group('CARDS').split(','))
            elif street in ('TURN','RIVER'):
                hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])
        else:
            self.determineErrorType(hand, "readCommunityCards")

    def readAntes(self, hand):
        for player in self.re_Antes.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(player.group('PSEAT'), hand)
            #print "DEBUG: hand.addAnte(%s,%s)" %(pname, player.group('ANTE'))
            self.adjustMergeTourneyStack(hand, pname, player.group('ANTE'))
            hand.addAnte(pname, player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText)
        if m:
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            #print "DEBUG: hand.addBringIn(%s,%s)" %(pname, m.group('BRINGIN'))
            self.adjustMergeTourneyStack(hand, pname, m.group('BRINGIN'))
            hand.addBringIn(pname, m.group('BRINGIN'))
            
        if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
            hand.gametype['sb'] = "1"
            hand.gametype['bb'] = "2"

    def readBlinds(self, hand):
        if (hand.gametype['category'], hand.gametype['limitType']) == ("badugi", "hp"):
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
        else:
            if hand.gametype['base'] == 'hold':
                street = 'PREFLOP'
            elif hand.gametype['base'] == 'draw':
                street = 'DEAL'
            allinBlinds = {}
            blindsantes = hand.handText.split(street)[0]
            bb, sb = None, None
            for a in self.re_PostSB.finditer(blindsantes):
                #print "DEBUG: found sb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('SB'))
                sb = a.group('SB')
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, sb)
                hand.addBlind(player,'small blind', sb)
                if not hand.gametype['sb'] or hand.gametype['secondGame']:
                    hand.gametype['sb'] = sb
            for a in self.re_PostBB.finditer(blindsantes):
                #print "DEBUG: found bb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('BB'))
                bb = a.group('BB')
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, bb)
                hand.addBlind(player, 'big blind', bb)
                if not hand.gametype['bb'] or hand.gametype['secondGame']:
                    hand.gametype['bb'] = bb
            for a in self.re_PostBoth.finditer(blindsantes):
                bb = Decimal(self.info['bb'])
                amount = Decimal(a.group('SBBB'))
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, a.group('SBBB'))
                if amount < bb:
                    hand.addBlind(player, 'small blind', a.group('SBBB'))
                elif amount == bb:
                    hand.addBlind(player, 'big blind', a.group('SBBB'))
                else:
                    hand.addBlind(player, 'both', a.group('SBBB'))
            if sb is None or bb is None:
                m = self.re_Action.finditer(blindsantes)
                for action in m:
                    player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
                    #print "DEBUG: found: '%s' '%s'" %(self.playerNameFromSeatNo(action.group('PSEAT'), hand), action.group('BET'))
                    if sb is None:
                        if action.group('BET') and action.group('BET')!= '0.00':
                            sb = action.group('BET')  
                            self.adjustMergeTourneyStack(hand, player, sb)
                            hand.addBlind(player, 'small blind', sb)
                            if not hand.gametype['sb'] or hand.gametype['secondGame']:
                                hand.gametype['sb'] = sb
                        elif action.group('BET') == '0.00':
                            allinBlinds[player] = 'small blind'
                            #log.error(_(_("MergeToFpdb.readBlinds: Cannot calcualte tourney all-in blind for hand '%s'")) % hand.handid)
                            #raise FpdbParseError
                    elif sb and bb is None:
                        if action.group('BET') and action.group('BET')!= '0.00':
                            bb = action.group('BET')
                            self.adjustMergeTourneyStack(hand, player, bb)
                            hand.addBlind(player, 'big blind', bb)
                            if not hand.gametype['bb'] or hand.gametype['secondGame']:
                                hand.gametype['bb'] = bb
                        elif action.group('BET') == '0.00':
                            allinBlinds[player] = 'big blind'
                            #log.error(_(_("MergeToFpdb.readBlinds: Cannot calcualte tourney all-in blind for hand '%s'")) % hand.handid)
                            #raise FpdbParseError
            self.fixTourBlinds(hand, allinBlinds)

    def fixTourBlinds(self, hand, allinBlinds):
        # FIXME
        # The following should only trigger when a small blind is missing in a tournament, or the sb/bb is ALL_IN
        # see http://sourceforge.net/apps/mantisbt/fpdb/view.php?id=115
        if hand.gametype['type'] == 'tour' or hand.gametype['secondGame']:
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
            elif hand.gametype['sb'] == None:
                hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            elif hand.gametype['bb'] == None:
                hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
            if int(Decimal(hand.gametype['bb']))/2 != int(Decimal(hand.gametype['sb'])):
                if int(Decimal(hand.gametype['bb']))/2 < int(Decimal(hand.gametype['sb'])):
                    hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
                else:
                    hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            hand.sb = hand.gametype['sb']
            hand.bb = hand.gametype['bb']
            for player, blindtype in allinBlinds.iteritems():
                if blindtype=='big blind':
                    self.adjustMergeTourneyStack(hand, player, hand.bb)
                    hand.addBlind(player, 'big blind', hand.bb)
                else:
                    self.adjustMergeTourneyStack(hand, player, hand.sb)
                    hand.addBlind(player, 'small blind', hand.sb)
                    
    def mergeMultigametypes(self, handText):
        m2 = self.re_HandInfo.search(handText)
        if m2 is None:
            tmp = handText[0:200]
            log.error(_("MergeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        if m2.group('MULTIGAMETYPE'):
            try:
                (self.info['base'], self.info['category']) = self.Multigametypes[m2.group('MULTIGAMETYPE')]
            except KeyError:
                tmp = handText[0:200]
                log.error(_("MergeToFpdb.determineGameType: Multigametypes has no lookup for '%s'") % m2.group('MULTIGAMETYPE'))
                raise FpdbParseError
                    
    def adjustMergeTourneyStack(self, hand, player, amount):
        amount = Decimal(amount)
        if hand.gametype['type'] == 'tour':
            for p in hand.players:
                if p[1]==player:
                    stack  = Decimal(p[2])
                    stack += amount
                    p[2]   = str(stack)
            hand.stacks[player] += amount

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))
                    
    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        herocards = []
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
                    hand.hero = self.playerNameFromSeatNo(found.group('PSEAT'), hand)
                    cards = found.group('CARDS').split(',')
                    hand.addHoleCards(street, hand.hero, closed=cards, shown=False, mucked=False, dealt=True)

        for street in hand.holeStreets:
            if hand.streets.has_key(street):
                if not hand.streets[street] or street in ('PREFLOP', 'DEAL') or hand.gametype['base'] == 'hold': continue  # already done these
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    player = self.playerNameFromSeatNo(found.group('PSEAT'), hand)
                    if player in hand.stacks:
                        if found.group('CARDS') is None:
                            cards    = []
                            newcards = []
                            oldcards = []
                        else:
                            if hand.gametype['base'] == 'stud':
                                cards = found.group('CARDS').replace('null', '').split(',')
                                cards = [c for c in cards if c!='']
                                oldcards = cards[:-1]
                                newcards = [cards[-1]]
                            else:
                                cards = found.group('CARDS').split(',')
                                oldcards = cards
                                newcards = []
                        if street == 'THIRD' and len(cards) == 3: # hero in stud game
                            hand.hero = player
                            herocards = cards
                            hand.dealt.add(hand.hero) # need this for stud??
                            hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                        elif (cards != herocards and hand.gametype['base'] == 'stud'):
                            if hand.hero == player:
                                herocards = cards
                                hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                            elif (len(cards)<5):
                                if street == 'SEVENTH':
                                    oldcards = []
                                    newcards = []
                                hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                            elif (len(cards)==7):
                                for street in hand.holeStreets:
                                    hand.holecards[street][player] = [[], []]
                                hand.addHoleCards(street, player, closed=cards, open=[], shown=False, mucked=False, dealt=False)
                        elif (hand.gametype['base'] == 'draw'):
                            hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)

    def readAction(self, hand, street):
        #log.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if player in hand.stacks:
                if action.group('ATYPE') in ('FOLD', 'SIT_OUT'):
                    hand.addFold(street, player)
                elif action.group('ATYPE') == 'CHECK':
                    hand.addCheck(street, player)
                elif action.group('ATYPE') == 'CALL':
                    hand.addCall(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'RAISE':
                    if hand.startTime < hand.newFormat:
                        hand.addCallandRaise(street, player, action.group('BET'))
                    else:
                        hand.addRaiseTo(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'BET':
                    hand.addBet(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'ALL_IN':
                    hand.addAllIn(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'DRAW':
                    hand.addDiscard(street, player, action.group('TXT'))
                elif action.group('ATYPE') == 'COMPLETE':
                    if hand.gametype['base'] != 'stud':
                        hand.addRaiseTo(street, player, action.group('BET'))
                    else:
                        hand.addComplete( street, player, action.group('BET') )
                else:
                    log.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PSEAT'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        pass

    def readCollectPot(self, hand):
        hand.setUncalledBets(True)
        for m in self.re_CollectPot.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            pot = m.group('POT')
            hand.addCollectPot(player=pname, pot=pot)

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = m.group('CARDS').split(',')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "SHOWN": shown = True
                elif m.group('SHOWED') == "MUCKED": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'),hand), shown=shown, mucked=mucked)

    def determineErrorType(self, hand, function):
        message = False
        m = self.re_Connection.search(hand.handText)
        if m:
            message = _("Found %s. Hand missing information." % m.group('TYPE'))
        m = self.re_LeaveTable.search(hand.handText)
        if m:
            message = _("Found LEAVE. Player left table before hand completed")
        m = self.re_Cancelled.search(hand.handText)
        if m:
            message = _("Found CANCELLED")
        if message == False and function == "markStreets":
            message = _("Failed to identify all streets")
        if message == False and function == "readHandInfo":
            message = _("END_OF_HAND not found. No obvious reason")
        if message:
            raise FpdbHandPartial("Partial hand history: %s '%s' %s" % (function, hand.handid, message))

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        regex = re.escape(str(table_name))
        if type=="tour":
            # Ignoring table number as it doesn't appear to be in the window title
            # "$200 Freeroll - NL Holdem - 20:00 (46302299) - Table 1" -- the table number doesn't matter, it seems to always be 1 in the HH.
            # "Fun Step 1 (4358174) - Table 1"
            regex = re.escape(str(tournament))
        log.info("Merge.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.info("Merge.getTableTitleRe: returns: '%s'" % (regex))
        return regex
