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
from HandHistoryConverter import HandHistoryConverter

class Everleaf(HandHistoryConverter):
	def __init__(self, config, file):
		print "Initialising Everleaf converter class"
		HandHistoryConverter.__init__(self, config, file, "Everleaf") # Call super class init.
		self.sitename = "Everleaf"
		self.setFileType("text")

        def readSupportedGames(self):
		pass

        def determineGameType(self):
		pass

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
	
