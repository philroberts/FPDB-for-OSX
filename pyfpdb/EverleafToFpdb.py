#!/usr/bin/env python
#    Copyright 2008, Carl Gherardi
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

import sys
import Configuration
from HandHistoryConverter import *

# Everleaf HH format

# Everleaf Gaming Game #55208539
# ***** Hand history for game #55208539 *****
# Blinds $0.50/$1 NL Hold'em - 2008/09/01 - 13:35:01
# Table Speed Kuala
# Seat 1 is the button
# Total number of players: 9
# Seat 1: BadBeatBox (  $ 98.97 USD )
# Seat 3: EricBlade (  $ 73.96 USD )
# Seat 4: randy888 (  $ 196.50 USD )
# Seat 5: BaronSengir (  $ 182.80 USD )
# Seat 6: dogge (  $ 186.06 USD )
# Seat 7: wings ( $ 50 USD )
# Seat 8: schoffeltje (  $ 282.05 USD )
# Seat 9: harrydebeng (  $ 109.45 USD )
# Seat 10: smaragdar (  $ 96.50 USD )
# EricBlade: posts small blind [$ 0.50 USD]
# randy888: posts big blind [$ 1 USD]
# wings: posts big blind [$ 1 USD]
# ** Dealing down cards **
# Dealt to EricBlade [ qc, 3c ]
# BaronSengir folds
# dogge folds
# wings raises [$ 2.50 USD]
# schoffeltje folds
# harrydebeng calls [$ 3.50 USD]
# smaragdar raises [$ 15.50 USD]
# BadBeatBox folds
# EricBlade folds
# randy888 folds
# wings calls [$ 12 USD]
# harrydebeng folds
# ** Dealing Flop ** [ qs, 3d, 8h ]
# wings: bets [$ 34.50 USD]
# smaragdar calls [$ 34.50 USD]
# ** Dealing Turn ** [ 2d ]
# ** Dealing River ** [ 6c ]
# dogge shows [ 9h, 9c ]a pair of nines
# spicybum shows [ 5d, 6d ]a straight, eight high
# harrydebeng does not show cards
# smaragdar wins $ 102 USD from main pot with a pair of aces [ ad, ah, qs, 8h, 6c ]

class Everleaf(HandHistoryConverter):
	def __init__(self, config, file):
		print "Initialising Everleaf converter class"
		HandHistoryConverter.__init__(self, config, file, "Everleaf") # Call super class init.
		self.sitename = "Everleaf"
		self.setFileType("text")
		self.rexx.setGameInfoRegex('.*Blinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)')
		self.rexx.setSplitHandRegex('\n\n\n\n')
		self.rexx.setHandInfoRegex('.*#(?P<HID>[0-9]+)\n.*\nBlinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+) (?P<GAMETYPE>.*) - (?P<YEAR>[0-9]+)/(?P<MON>[0-9]+)/(?P<DAY>[0-9]+) - (?P<HR>[0-9]+):(?P<MIN>[0-9]+):(?P<SEC>[0-9]+)\nTable (?P<TABLE>[ a-zA-Z]+)\nSeat (?P<BUTTON>[0-9]+)')
		self.rexx.setPlayerInfoRegex('Seat (?P<SEAT>[0-9]+): (?P<PNAME>.*) \(  \$ (?P<CASH>[.0-9]+) USD \)')
		self.rexx.setPostSbRegex('.*\n(?P<PNAME>.*): posts small blind \[\$? (?P<SB>[.0-9]+)')
		self.rexx.setPostBbRegex('.*\n(?P<PNAME>.*): posts big blind \[\$? (?P<BB>[.0-9]+)')
		# mct : what about posting small & big blinds simultaneously?
		self.rexx.setHeroCardsRegex('.*\nDealt\sto\s(?P<PNAME>.*)\s\[ (?P<HOLE1>\S\S), (?P<HOLE2>\S\S) \]')
		self.rexx.setActionStepRegex('.*\n(?P<PNAME>.*) (?P<ATYPE>bets|checks|raises|calls|folds)(\s\[\$ (?P<BET>[.\d]+) USD\])?')
		self.rexx.compileRegexes()

	def readSupportedGames(self):
		pass

	def determineGameType(self):
		# Cheating with this regex, only support nlhe at the moment
		gametype = ["ring", "hold", "nl"]

		m = self.rexx.game_info_re.search(self.obs)
		gametype = gametype + [m.group('SB')]
		gametype = gametype + [m.group('BB')]
		
		return gametype

	def readHandInfo(self, hand):
		m =  self.rexx.hand_info_re.search(hand.string)
		hand.handid = m.group('HID')
		hand.tablename = m.group('TABLE')
# These work, but the info is already in the Hand class - should be used for tourneys though.
#		m.group('SB')
#		m.group('BB')
#		m.group('GAMETYPE')

# Believe Everleaf time is GMT/UTC, no transation necessary
# Stars format (Nov 10 2008): 2008/11/07 12:38:49 CET [2008/11/07 7:38:49 ET]
# or                        : 2008/11/07 12:38:49 ET
# Not getting it in my HH files yet, so using
# 2008/11/10 3:58:52 ET
#TODO: Do conversion from GMT to ET
#TODO: Need some date functions to convert to different timezones (Date::Manip for perl rocked for this)
		hand.starttime = "%d/%02d/%02d %d:%02d:%02d ET" %(int(m.group('YEAR')), int(m.group('MON')), int(m.group('DAY')),
							  int(m.group('HR')), int(m.group('MIN')), int(m.group('SEC')))
		hand.buttonpos = int(m.group('BUTTON'))

	def readPlayerStacks(self, hand):
		m = self.rexx.player_info_re.finditer(hand.string)
		players = []

		for a in m:
			hand.addPlayer(a.group('SEAT'), a.group('PNAME'), a.group('CASH'))


	def markStreets(self, hand):
		# PREFLOP = ** Dealing down cards **
		m = re.search('(\*\* Dealing down cards \*\*\n)(?P<PREFLOP>.*?\n\*\*)?( Dealing Flop \*\* \[ (?P<FLOP1>\S\S), (?P<FLOP2>\S\S), (?P<FLOP3>\S\S) \])?(?P<FLOP>.*?\*\*)?( Dealing Turn \*\* \[ (?P<TURN1>\S\S) \])?(?P<TURN>.*?\*\*)?( Dealing River \*\* \[ (?P<RIVER1>\S\S) \])?(?P<RIVER>.*)', hand.string,re.DOTALL)
#		for street in m.groupdict():
#			print "DEBUG: Street: %s\tspan: %s" %(street, str(m.span(street)))
		hand.streets = m

	def readBlinds(self, hand):
		try:
			m = self.rexx.small_blind_re.search(hand.string)
			hand.addBlind(m.group('PNAME'), m.group('SB'))
			#hand.posted = [m.group('PNAME')]
		except:
			hand.addBlind(None, 0)
			#hand.posted = ["FpdbNBP"]
		m = self.rexx.big_blind_re.finditer(hand.string)
		for a in m:
			hand.addBlind(a.group('PNAME'), a.group('BB'))
			#hand.posted = hand.posted + [a.group('PNAME')]

	def readHeroCards(self, hand):
		m = self.rexx.hero_cards_re.search(hand.string)
		if(m == None):
			#Not involved in hand
			hand.involved = False
		else:
			hand.hero = m.group('PNAME')
			hand.addHoleCards(m.group('HOLE1'), m.group('HOLE2'))

	def readAction(self, hand, street):
		m = self.rexx.action_re.finditer(hand.streets.group(street))
		hand.actions[street] = []
		for action in m:
			if action.group('ATYPE') == 'raises':
				hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
			elif action.group('ATYPE') == 'calls':
				hand.addCall( street, action.group('PNAME'), action.group('BET') )
			elif action.group('ATYPE') == 'bets':
				hand.addBet( street, action.group('PNAME'), action.group('BET') )
			else:
				print "DEBUG: unimplemented readAction: %s %s" %(action.group('PNAME'),action.group('ATYPE'),)
				hand.actions[street] += [[action.group('PNAME'), action.group('ATYPE')]]


	def getRake(self, hand):
		hand.rake = hand.totalpot * Decimal('0.05') # probably not quite right

if __name__ == "__main__":
	c = Configuration.Config()
	e = Everleaf(c, "Speed_Kuala.txt")
	e.processFile()
	print str(e)
	
