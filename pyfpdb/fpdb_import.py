#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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

#see status.txt for site/games support info

import sys

try:
	import MySQLdb
	mysqlLibFound=True
except:
	pass
	
try:
	import psycopg2
	pgsqlLibFound=True
except:
	pass

import math
import os
import datetime
import fpdb_simple
import fpdb_parse_logic
from optparse import OptionParser
from time import time

class Importer:

	def __init__(self):
		"""Constructor"""
		self.settings={'imp-callFpdbHud':False}
		self.db = None
		self.cursor = None
		self.options = None
		self.callHud = False
		self.lines = None

	def dbConnect(self, options, settings):
		#connect to DB
		if settings['db-backend'] == 2:
			if not mysqlLibFound:
				raise fpdb_simple.FpdbError("interface library MySQLdb not found but MySQL selected as backend - please install the library or change the config file")
			self.db = MySQLdb.connect(host = options.server, user = options.user,
							passwd = options.password, db = options.database)
		elif settings['db-backend'] == 3:
			if not pgsqlLibFound:
				raise fpdb_simple.FpdbError("interface library psycopg2 not found but PostgreSQL selected as backend - please install the library or change the config file")
			self.db = psycopg2.connect(host = options.server, user = options.user,
								  password = options.password, database = options.database)
		elif settings['db-backend'] == 4:
			pass
		else:
			pass
		self.cursor = self.db.cursor()

	def setCallHud(self, value):
		self.callHud = value

	def import_file_dict(self, options, settings):
		starttime = time()
		last_read_hand=0
		if (options.inputFile=="stdin"):
			inputFile=sys.stdin
		else:
			inputFile=open(options.inputFile, "rU")

		self.dbConnect(options,settings)

		# Read input file into class and close file
		self.lines=fpdb_simple.removeTrailingEOL(inputFile.readlines())
		inputFile.close()

		firstline = self.lines[0]

		if firstline.find("Tournament Summary")!=-1:
			print "TODO: implement importing tournament summaries"
			self.cursor.close()
			self.db.close()
			return 0
		
		site=fpdb_simple.recogniseSite(firstline)
		category=fpdb_simple.recogniseCategory(firstline)

		startpos=0
		stored=0 #counter
		duplicates=0 #counter
		partial=0 #counter
		errors=0 #counter

		for i in range (len(self.lines)): #main loop, iterates through the lines of a file and calls the appropriate parser method
			if (len(self.lines[i])<2):
				endpos=i
				hand=self.lines[startpos:endpos]
		
				if (len(hand[0])<2):
					hand=hand[1:]
		
				cancelled=False
				damaged=False
				if (site=="ftp"):
					for i in range (len(hand)):
						if (hand[i].endswith(" has been canceled")): #this is their typo. this is a typo, right?
							cancelled=True
						
						seat1=hand[i].find("Seat ") #todo: make this recover by skipping this line
						if (seat1!=-1):
							if (hand[i].find("Seat ", seat1+3)!=-1):
								damaged=True
				
				if (len(hand)<3):
					pass
					#todo: the above 2 self.lines are kind of a dirty hack, the mentioned circumstances should be handled elsewhere but that doesnt work with DOS/Win EOL. actually this doesnt work.
				elif (hand[0].endswith(" (partial)")): #partial hand - do nothing
					partial+=1
				elif (hand[1].find("Seat")==-1 and hand[2].find("Seat")==-1 and hand[3].find("Seat")==-1):#todo: should this be or instead of and?
					partial+=1
				elif (cancelled or damaged):
					partial+=1
				else: #normal processing
					isTourney=fpdb_simple.isTourney(hand[0])
					if not isTourney:
						fpdb_simple.filterAnteBlindFold(site,hand)
					hand=fpdb_simple.filterCrap(site, hand, isTourney)
			
					try:
						handsId=fpdb_parse_logic.mainParser(self.db, self.cursor, site, category, hand)
						self.db.commit()
						
						stored+=1
						self.db.commit()
#						if settings['imp-callFpdbHud'] and self.callHud and os.sep=='/':
						if settings['imp-callFpdbHud'] and self.callHud:
							#print "call to HUD here. handsId:",handsId
							#pipe the Hands.id out to the HUD
#							options.pipe_to_hud.write("%s" % (handsId) + os.linesep)
							options.pipe_to_hud.stdin.write("%s" % (handsId) + os.linesep)
					except fpdb_simple.DuplicateError:
						duplicates+=1
					except (ValueError), fe:
						errors+=1
						print "Error No.",errors,", please send the hand causing this to steffen@sycamoretest.info so I can fix it."
						print "Filename:",options.inputFile
						print "Here is the first line so you can identify it. Please mention that the error was a ValueError:"
						print hand[0]
					
						if (options.failOnError):
							self.db.commit() #dont remove this, in case hand processing was cancelled this ties up any open ends.
							self.cursor.close()
							self.db.close()
							raise
					except (fpdb_simple.FpdbError), fe:
						errors+=1
						print "Error No.",errors,", please send the hand causing this to steffen@sycamoretest.info so I can fix it."
						print "Filename:",options.inputFile
						print "Here is the first line so you can identify it."
						print hand[0]
						#fe.printStackTrace() #todo: get stacktrace
						self.db.rollback()
						
						if (options.failOnError):
							self.db.commit() #dont remove this, in case hand processing was cancelled this ties up any open ends.
							self.cursor.close()
							self.db.close()
							raise
					if (options.minPrint!=0):
						if ((stored+duplicates+partial+errors)%options.minPrint==0):
							print "stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors
			
					if (options.handCount!=0):
						if ((stored+duplicates+partial+errors)>=options.handCount):
							if (not options.quiet):
								print "quitting due to reaching the amount of hands to be imported"
								print "Total stored:", stored, "duplicates:", duplicates, "partial/damaged:", partial, "errors:", errors, " time:", (time() - starttime)
							sys.exit(0)
				startpos=endpos
		print "Total stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors, " time:", (time() - starttime)
		
		if stored==0:
			if duplicates>0:
				for line_no in range(len(self.lines)):
					if self.lines[line_no].find("Game #")!=-1:
						final_game_line=self.lines[line_no]
				handsId=fpdb_simple.parseSiteHandNo(final_game_line)
			else:
				print "failed to read a single hand from file:", inputFile
				handsId=0
			#todo: this will cause return of an unstored hand number if the last hand was error or partial
		self.db.commit()
		self.cursor.close()
		self.db.close()
		return handsId
#end def import_file_dict


if __name__ == "__main__":
	print "CLI for fpdb_import is currently on vacation please check in later"
