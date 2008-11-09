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

import Configuration
import sys
import traceback
import os
import os.path
import xml.dom.minidom
from xml.dom.minidom import Node

class HandHistoryConverter:
	def __init__(self, config, file, sitename):
		print "HandHistory init called"
		self.c         = config
		self.sitename  = sitename
		self.obs       = ""             # One big string
		self.filetype  = "text"
		self.doc       = None     # For XML based HH files
		self.file      = file
		self.hhbase    = self.c.get_import_parameters().get("hhArchiveBase")
		self.hhbase    = os.path.expanduser(self.hhbase)
		self.hhdir     = os.path.join(self.hhbase,sitename)
#		self.ofile     = os.path.join(self.hhdir,file)

	def __str__(self):
		tmp = "HandHistoryConverter: '%s'\n" % (self.sitename)
		tmp = tmp + "\thhbase:     '%s'\n" % (self.hhbase)
		tmp = tmp + "\thhdir:      '%s'\n" % (self.hhdir)
		tmp = tmp + "\tfiletype:   '%s'\n" % (self.filetype)
		tmp = tmp + "\tinfile:     '%s'\n" % (self.file)
#		tmp = tmp + "\toutfile:    '%s'\n" % (self.ofile)
		return tmp

	# Functions to be implemented in the inheriting class
	def readSupportedGames(self): abstract
	def determineGameType(self): abstract
	def readPlayerStacks(self): abstract
	def readBlinds(self): abstract
	def readAction(self): abstract

	def sanityCheck(self):
		sane = False
		base_w = False
		#Check if hhbase exists and is writable
		#Note: Will not try to create the base HH directory
		if not (os.access(self.hhbase, os.W_OK) and os.path.isdir(self.hhbase)):
			print "HH Sanity Check: Directory hhbase '" + self.hhbase + "' doesn't exist or is not writable"
		else:
			#Check if hhdir exists and is writable
			if not os.path.isdir(self.hhdir):
				# In first pass, dir may not exist. Attempt to create dir
				print "Creating directory: '%s'" % (self.hhdir)
				os.mkdir(self.hhdir)
				sane = True
			elif os.access(self.hhdir, os.W_OK):
				sane = True
			else:
				print "HH Sanity Check: Directory hhdir '" + self.hhdir + "' or its parent directory are not writable"

		return sane

	# Functions not necessary to implement in sub class
	def setFileType(self, filetype = "text"):
		self.filetype = filetype

	def processFile(self):
		if not self.sanityCheck():
			print "Cowardly refusing to continue after failed sanity check"
			return
		self.readFile(self.file)
		self.determineGameType()

	def readFile(self, filename):
		"""Read file"""
		print "Reading file: '%s'" %(filename)
		if(self.filetype == "text"):
			infile=open(filename, "rU")
			self.obs = infile.read()
			infile.close()
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

