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

#    Standard Library modules
import Configuration
import traceback
import sys
import xml.dom.minidom
from xml.dom.minidom import Node
from HandHistoryConverter import HandHistoryConverter

# Carbon format looks like:

# 1) <description type="Holdem" stakes="No Limit ($0.25/$0.50)"/>
# 2) <game id="14902583-5578" starttime="20081006145401" numholecards="2" gametype="2" realmoney="true" data="20081006|Niagara Falls (14902583)|14902583|14902583-5578|false">
# 3)  <players dealer="8">
#                <player seat="3" nickname="PlayerInSeat3" balance="$43.29" dealtin="true" />
#                ...
# 4) <round id="BLINDS" sequence="1">
#                <event sequence="1" type="SMALL_BLIND" player="0" amount="0.25"/>
#                <event sequence="2" type="BIG_BLIND" player="1" amount="0.50"/>
# 5) <round id="PREFLOP" sequence="2">
#                <event sequence="3" type="CALL" player="2" amount="0.50"/>
# 6) <round id="POSTFLOP" sequence="3">
#           <event sequence="16" type="BET" player="3" amount="1.00"/>
#           ....
#	    <cards type="COMMUNITY" cards="7d,Jd,Jh"/>

# The full sequence for a NHLE cash game is:
# BLINDS, PREFLOP, POSTFLOP, POSTTURN, POSTRIVER, SHOWDOWN, END_OF_GAME
# This sequence can be terminated after BLINDS at any time by END_OF_FOLDED_GAME


class CarbonPoker(HandHistoryConverter): 
	def __init__(self, config, filename):
		print "Initialising Carbon Poker converter class"
		HandHistoryConverter.__init__(self, config, filename, "Carbon") # Call super class init
		self.setFileType("xml")

	def readSupportedGames(self): 
		pass
	def determineGameType(self): 
		desc_node = doc.getElementsByTagName("description")
		type = desc_node.getAttribute("type")
		stakes = desc_node.getAttribute("stakes")
		
	def readPlayerStacks(self):
		pass
	def readBlinds(self):
		pass
	def readAction(self):
		pass

	# Override read function as xml.minidom barfs on the Carbon layout
        # This is pretty dodgy
	def readFile(self, filename):
		print "Carbon: Reading file: '%s'" %(filename)
		infile=open(filename, "rU")
		self.obs = infile.read()
		infile.close()
		self.obs = "<CarbonHHFile>\n" + self.obs + "</CarbonHHFile>"
		try:
			doc = xml.dom.minidom.parseString(self.obs)
			self.doc = doc
		except:
			traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
	c = Configuration.Config()
	e = CarbonPoker(c, "regression-test-files/carbon-poker/Niagara Falls (15245216).xml") 
	e.processFile()
	print str(e)

