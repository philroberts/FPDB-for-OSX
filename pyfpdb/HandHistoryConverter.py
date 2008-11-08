#!/usr/bin/python

#Copyright 2008 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

class HandHistoryConverter:
	def __init__(self, config, file):
		print "HandHistory init called"
		self.c         = config
		self.sitename  = ""
		self.obs       = ""             # One big string
		self.filetype  = "text"
		self.doc       = None     # For XML based HH files
		self.file      = file
		self.hhbase    = self.c.get_import_parameters().get("hhArchiveBase")

	def __str__(self):
		tmp = "HandHistoryConverter: '%s'\n" % (self.sitename)
		tmp = tmp + "\thhbase:     %s\n" % (self.hhbase)
		tmp = tmp + "\tfiletype:   %s\n" % (self.filetype)
		return tmp

	# Functions to be implemented in the inheriting class
	def readSupportedGames(self): abstract
	def determineGameType(self): abstract
	def readPlayerStacks(self): abstract
	def readBlinds(self): abstract
	def readAction(self): abstract


	# Functions not necessary to implement in sub class
	def setFileType(self, filetype = "text"):
		self.filetype = filetype

	def processFile(self):
		self.readFile()

	def readFile(self, filename):
		"""Read file"""
		if(self.filetype == "text"):
			infile=open(filename, "rU")
			self.obs = readfile(inputFile)
			inputFile.close()
		elif(self.filetype == "xml"):
			try:
				doc = xml.dom.minidom.parse(filename)
				self.doc = doc
			except:
				traceback.print_exc(file=sys.stderr)

	def writeStars(self):
		"""Write out parsed data"""
#		print sitename + " Game #" + handid + ":  " + gametype + " (" + sb + "/" + bb + " - " + starttime
#		print "Table '" + tablename + "' " + maxseats + "-max Seat #" + buttonpos + " is the button"
#
#		counter = 1
#		for player in seating:
#			print "Seat " + counter + ": " + playername + "($" + playermoney + " in chips"
#
#		print playername + ": posts small blind " + sb
#		print playername + ": posts big blind " + bb
#
#		print "*** HOLE CARDS ***"
#		print "Dealt to " + hero + " [" + holecards + "]"
#
##		ACTION STUFF
#
#		print "*** SUMMARY ***"
#		print "Total pot $" + totalpot + " | Rake $" + rake
#		print "Board [" + boardcards + "]"
#
##		SUMMARY STUFF

