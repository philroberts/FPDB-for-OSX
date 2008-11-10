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

import Configuration
from HandHistoryConverter import *

# Everleaf HH format

#Everleaf Gaming Game #55198191
#***** Hand history for game #55198191 *****
#Blinds $0.50/$1 NL Hold'em - 2008/09/01 - 10:02:11
#Table Speed Kuala
#Seat 8 is the button
#Total number of players: 10
#Seat 1: spicybum (  $ 77.50 USD )
#Seat 2: harrydebeng ( new player )
#Seat 3: EricBlade ( new player )
#Seat 4: dollar_hecht (  $ 16.40 USD )
#Seat 5: Apolon76 (  $ 154.10 USD )
#Seat 6: dogge ( new player )
#Seat 7: RonKoro (  $ 25.53 USD )
#Seat 8: jay68w (  $ 48.50 USD )
#Seat 9: KillerQueen1 (  $ 51.28 USD )
#Seat 10: Cheburashka (  $ 49.61 USD )
#KillerQueen1: posts small blind [$ 0.50 USD]
#Cheburashka: posts big blind [$ 1 USD]
#** Dealing down cards **
#spicybum folds
#dollar_hecht calls [$ 1 USD]
#Apolon76 folds
#RonKoro folds
#jay68w raises [$ 4.50 USD]
#KillerQueen1 folds
#Cheburashka folds
#dollar_hecht folds
#jay68w does not show cards
#jay68w wins $ 3.50 USD from main pot



class Everleaf(HandHistoryConverter):
	def __init__(self, config, file):
		print "Initialising Everleaf converter class"
		HandHistoryConverter.__init__(self, config, file, "Everleaf") # Call super class init.
		self.sitename = "Everleaf"
		self.setFileType("text")
		self.rexx.setGameInfoRegex('.*Blinds \$?(?P<SB>[.0-9]+)/\$?(?P<BB>[.0-9]+)')
		self.rexx.setSplitHandRegex('\n\n\n')
		self.rexx.compileRegexes()

        def readSupportedGames(self):
		pass

        def determineGameType(self):
		# Cheating with this regex, only support nlhe at the moment
		gametype = ["ring", "hold", "nl"]

		m = self.rexx.game_info_re.search(self.obs)
		gametype = gametype + [self.float2int(m.group('SB'))]
		gametype = gametype + [self.float2int(m.group('BB'))]
		
		return gametype

        def readPlayerStacks(self):
		pass

        def readBlinds(self):
		pass

        def readAction(self):
		pass

if __name__ == "__main__":
	c = Configuration.Config()
	e = Everleaf(c, "regression-test-files/everleaf/Speed_Kuala.txt")
	e.processFile()
	print str(e)
	
