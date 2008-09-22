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


def import_file(server, database, user, password, inputFile):
	self.server=server
	self.database=database
	self.user=user
	self.password=password
	self.inputFile=inputFile
	self.settings={'imp-callFpdbHud':False}
	import_file_dict(self, settings)

def import_file_dict(options, settings, callHud=False):
		last_read_hand=0
		if (options.inputFile=="stdin"):
			inputFile=sys.stdin
		else:
			inputFile=open(options.inputFile, "rU")

		#connect to DB
		if options.settings['db-backend'] == 2:
			if not mysqlLibFound:
				raise fpdb_simple.FpdbError("interface library MySQLdb not found but MySQL selected as backend - please install the library or change the config file")
			db = MySQLdb.connect(host = options.server, user = options.user,
							passwd = options.password, db = options.database)
		elif options.settings['db-backend'] == 3:
			if not pgsqlLibFound:
				raise fpdb_simple.FpdbError("interface library psycopg2 not found but PostgreSQL selected as backend - please install the library or change the config file")
			db = psycopg2.connect(host = options.server, user = options.user,
								  password = options.password, database = options.database)
		elif options.settings['db-backend'] == 4:
			pass
		else:
			pass
		cursor = db.cursor()
		
		if (not options.quiet):
			print "Opened file", options.inputFile, "and connected to MySQL on", options.server

		line=inputFile.readline()
		
		if line.find("Tournament Summary")!=-1:
			print "TODO: implement importing tournament summaries"
			inputFile.close()
			cursor.close()
			db.close()
			return 0
		
		site=fpdb_simple.recogniseSite(line)
		category=fpdb_simple.recogniseCategory(line)
		inputFile.seek(0)
		lines=fpdb_simple.removeTrailingEOL(inputFile.readlines())

		startpos=0
		stored=0 #counter
		duplicates=0 #counter
		partial=0 #counter
		errors=0 #counter

		for i in range (len(lines)): #main loop, iterates through the lines of a file and calls the appropriate parser method
			if (len(lines[i])<2):
				endpos=i
				hand=lines[startpos:endpos]
		
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
					#todo: the above 2 lines are kind of a dirty hack, the mentioned circumstances should be handled elsewhere but that doesnt work with DOS/Win EOL. actually this doesnt work.
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
						handsId=fpdb_parse_logic.mainParser(db, cursor, site, category, hand)
						db.commit()
						
						stored+=1
						db.commit()
#						if settings['imp-callFpdbHud'] and callHud and os.sep=='/':
						if settings['imp-callFpdbHud'] and callHud:
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
							db.commit() #dont remove this, in case hand processing was cancelled this ties up any open ends.
							inputFile.close()
							cursor.close()
							db.close()
							raise
					except (fpdb_simple.FpdbError), fe:
						errors+=1
						print "Error No.",errors,", please send the hand causing this to steffen@sycamoretest.info so I can fix it."
						print "Filename:",options.inputFile
						print "Here is the first line so you can identify it."
						print hand[0]
						#fe.printStackTrace() #todo: get stacktrace
						db.rollback()
						
						if (options.failOnError):
							db.commit() #dont remove this, in case hand processing was cancelled this ties up any open ends.
							inputFile.close()
							cursor.close()
							db.close()
							raise
					if (options.minPrint!=0):
						if ((stored+duplicates+partial+errors)%options.minPrint==0):
							print "stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors
			
					if (options.handCount!=0):
						if ((stored+duplicates+partial+errors)>=options.handCount):
							if (not options.quiet):
								print "quitting due to reaching the amount of hands to be imported"
								print "Total stored:", stored, "duplicates:", duplicates, "partial/damaged:", partial, "errors:", errors
							sys.exit(0)
				startpos=endpos
		print "Total stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors
		
		if stored==0 and duplicates>0:
			for line_no in range(len(lines)):
				if lines[line_no].find("Game #")!=-1:
					final_game_line=lines[line_no]
			handsId=fpdb_simple.parseSiteHandNo(final_game_line)
			#todo: this will cause return of an unstored hand number if the last hadn was error or partial
		db.commit()
		inputFile.close()
		cursor.close()
		db.close()
		return handsId


if __name__ == "__main__":
	failOnError=False
	quiet=False

	#process CLI parameters
	parser = OptionParser()
	parser.add_option("-c", "--handCount", default="0", type="int",
					help="Number of hands to import (default 0 means unlimited)")
	parser.add_option("-d", "--database", default="fpdb", help="The MySQL database to use (default fpdb)")
	parser.add_option("-e", "--errorFile", default="failed.txt", 
					help="File to store failed hands into. (default: failed.txt) Not implemented.")
	parser.add_option("-f", "--inputFile", "--file", "--inputfile", default="stdin", 
					help="The file you want to import (remember to use quotes if necessary)")
	parser.add_option("-m", "--minPrint", "--status", default="50", type="int",
					help="How often to print a one-line status report (0 means never, default is 50)")
	parser.add_option("-p", "--password", help="The password for the MySQL user")
	parser.add_option("-q", "--quiet", action="store_true",
					help="If this is passed it doesn't print a total at the end nor the opening line. Note that this purposely does NOT change --minPrint")
	parser.add_option("-s", "--server", default="localhost",
					help="Hostname/IP of the MySQL server (default localhost)")
	parser.add_option("-u", "--user", default="fpdb", help="The MySQL username (default fpdb)")
	parser.add_option("-x", "--failOnError", action="store_true",
					help="If this option is passed it quits when it encounters any error")

	(options, sys.argv) = parser.parse_args()
	
	settings={'imp-callFpdbHud':False}
	import_file_dict(options, settings, False)
