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
from time import time

class Importer:

	def __init__(self, caller, settings):
		"""Constructor"""
		self.settings=settings
		self.caller=caller
		self.db = None
		self.cursor = None
		self.filelist = []
		self.dirlist = []
		self.monitor = False
		self.updated = 0		#Time last import was run, used as mtime reference
		self.callHud = False
		self.lines = None
		self.pos_in_file = {} # dict to remember how far we have read in the file
		#Set defaults
		if not self.settings.has_key('imp-callFpdbHud'):
			self.settings['imp-callFpdbHud'] = False
		if not self.settings.has_key('minPrint'):
			self.settings['minPrint'] = 30
		self.dbConnect()

	def dbConnect(self):
		#connect to DB
		if self.settings['db-backend'] == 2:
			if not mysqlLibFound:
				raise fpdb_simple.FpdbError("interface library MySQLdb not found but MySQL selected as backend - please install the library or change the config file")
			self.db = MySQLdb.connect(self.settings['db-host'], self.settings['db-user'],
							self.settings['db-password'], self.settings['db-databaseName'])
		elif self.settings['db-backend'] == 3:
			if not pgsqlLibFound:
				raise fpdb_simple.FpdbError("interface library psycopg2 not found but PostgreSQL selected as backend - please install the library or change the config file")
			self.db = psycopg2.connect(self.settings['db-host'], self.settings['db-user'],
							self.settings['db-password'], self.settings['db-databaseName'])
		elif self.settings['db-backend'] == 4:
			pass
		else:
			pass
		self.cursor = self.db.cursor()

	#Set functions
	def setCallHud(self, value):
		self.callHud = value

	def setMinPrint(self, value):
		self.settings['minPrint'] = int(value)

	def setHandCount(self, value):
		self.settings['handCount'] = int(value)

	def setQuiet(self, value):
		self.settings['quiet'] = value

	def setFailOnError(self, value):
		self.settings['failOnError'] = value

	def setWatchTime(self):
		self.updated = time()

	def clearFileList(self):
		self.filelist = []

	#Add an individual file to filelist
	def addImportFile(self, filename):
		#todo: test it is a valid file
		self.filelist = self.filelist + [filename]
		#Remove duplicates
		self.filelist = list(set(self.filelist))

	#Add a directory of files to filelist
	def addImportDirectory(self,dir,monitor = False):
		#todo: test it is a valid directory
		if monitor == True:
			self.monitor = True
			self.dirlist = self.dirlist + [dir]

		for file in os.listdir(dir):
			if os.path.isdir(file):
				print "BulkImport is not recursive - please select the final directory in which the history files are"
			else:
				self.filelist = self.filelist + [os.path.join(dir, file)]
		#Remove duplicates
		self.filelist = list(set(self.filelist))

	#Run full import on filelist
	def runImport(self):
		for file in self.filelist:
			self.import_file_dict(file)

	#Run import on updated files, then store latest update time.
	def runUpdated(self):
		#Check for new files in directory
		#todo: make efficient - always checks for new file, should be able to use mtime of directory
		# ^^ May not work on windows
		for dir in self.dirlist:
			for file in os.listdir(dir):
				self.filelist = self.filelist + [dir+os.sep+file]

		self.filelist = list(set(self.filelist))

		for file in self.filelist:
			stat_info = os.stat(file)
			if stat_info.st_mtime > self.updated:
				self.import_file_dict(file)
		self.updated = time()

	# This is now an internal function that should not be called directly.
	def import_file_dict(self, file):
		starttime = time()
		last_read_hand=0
		loc = 0
		if (file=="stdin"):
			inputFile=sys.stdin
		else:
			inputFile=open(file, "rU")
			try: loc = self.pos_in_file[file]
			except: pass

		# Read input file into class and close file
		inputFile.seek(loc)
		self.lines=fpdb_simple.removeTrailingEOL(inputFile.readlines())
		self.pos_in_file[file] = inputFile.tell()
		inputFile.close()

		firstline = self.lines[0]

		if firstline.find("Tournament Summary")!=-1:
			print "TODO: implement importing tournament summaries"
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
					self.hand=hand
					
					try:
						handsId=fpdb_parse_logic.mainParser(self.db, self.cursor, site, category, hand)
						self.db.commit()
						
						stored+=1
						self.db.commit()
#						if settings['imp-callFpdbHud'] and self.callHud and os.sep=='/':
						if self.settings['imp-callFpdbHud'] and self.callHud:
							#print "call to HUD here. handsId:",handsId
							#pipe the Hands.id out to the HUD
							self.caller.pipe_to_hud.stdin.write("%s" % (handsId) + os.linesep)
					except fpdb_simple.DuplicateError:
						duplicates+=1
					except (ValueError), fe:
						errors+=1
						self.printEmailErrorMessage(errors, file, hand[0])
				
						if (self.settings['failOnError']):
							self.db.commit() #dont remove this, in case hand processing was cancelled.
							raise
					except (fpdb_simple.FpdbError), fe:
						errors+=1
						self.printEmailErrorMessage(errors, file, hand[0])

						#fe.printStackTrace() #todo: get stacktrace
						self.db.rollback()
						
						if (self.settings['failOnError']):
							self.db.commit() #dont remove this, in case hand processing was cancelled.
							raise
					if (self.settings['minPrint']!=0):
						if ((stored+duplicates+partial+errors)%self.settings['minPrint']==0):
							print "stored:", stored, "duplicates:", duplicates, "partial:", partial, "errors:", errors
			
					if (self.settings['handCount']!=0):
						if ((stored+duplicates+partial+errors)>=self.settings['handCount']):
							if (not self.settings['quiet']):
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
		return handsId
#end def import_file_dict

	def printEmailErrorMessage(self, errors, filename, line):
		print "Error No.",errors,", please send the hand causing this to steffen@sycamoretest.info so I can fix it."
		print "Filename:", filename
		print "Here is the first line so you can identify it. Please mention that the error was a ValueError:"
		print self.hand[0]
	

if __name__ == "__main__":
	print "CLI for fpdb_import is currently on vacation please check in later"
