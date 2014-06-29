# -*- coding: UTF-8 -*-
#    Copyright 2012, Chaz Littlejohn
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

import os, sys
import re
from time import time, sleep
import codecs
import shutil
import subprocess

from IdentifySite import *

class FPDBArchive:
    def __init__(self, hand):
        self.hid = hand.dbid_hands
        self.handText = hand.handText
        
class Archive():
    def __init__(self, config=None, path = None, ftype="hh"):
        self.config = config
        self.archivePath = None
        if config:
            self.archivePath = config.imp.archivePath
        self.path   = path
        self.ftype  = ftype
        self.handList = {}
        self.sessionsArchive = {}
        self.startCardsArchive = {}
        self.positionsArchive = {}
        
    def quickImport(self, userid, filtertype, game, filter, settings, tz): pass
    """Sets up import in 'quick' mode to import the HandsPlayers, HandsActions, and HandsStove records"""
        
    def getSiteSplit(self): pass
    """Returns split string for each site so it can be added back into the handText when writing to archive"""
    
    def fileInfo(self, path, site, filter, filter_name, obj=None, summary=None): pass
    """Sets file site and header info if applicable"""
        
    def addHand(self, hand, write=False): pass
    """Creates a FPDBArchive object for the hand and adds it to the handList dictionary"""
    
    def createSession(self, sid): pass
    """Creates a session directory for a given sessionId"""
    
    def mergeFiles(self, path1, path2): pass
    """Merges two files together in cases where cash sessions need to be combined within a session"""
    
    def mergeSessions(self, oldsid, newsid): pass
    """Merges two session directories together"""
    
    def mergeSubSessions(self, type, sid, oldId, newId, hids): pass
    """Merges two cash session files together"""
    
    def addSessionHands(self, type, sid, id, hids): pass
    """Adds the handText records for a session to the sessionsArchive dictionary and sets the path"""
    
    def addStartCardsHands(self, category, type, startCards, wid, siteId, hids): pass
    """Adds the handText records for startCards to the startCardsArchive dictionary and sets the path"""
    
    def addPositionsHands(self, type, activeSeats, position, wid, siteId, hids): pass
    """Adds the handText records for Positions to the positionsArchive dictionary and sets the path"""
    
    def getFile(self, path): pass
    """Method for creating, appending and or unzipping a file"""
    
    def fileOrZip(self, path): pass
    """Checks to see if the file exists or if the zip file exists. Unzips if necessary"""
    
    def writeHands(self, doinsert): pass
    """Take the hands stored in the sessionsArchive, startCardsArchive, and positionsArchive dictionaries
       and write or append those hands to files organized in the archive directory"""
       
    def zipFile(self, path): pass
    """Zip a file for archiving"""
    
    def unzipFile(self, path): pass
    """Unzip a file for import"""
    
    def zipAll(self): pass
    """Recursively zip all the files in the archive directory"""
    
    def unzipAll(self): pass
    """Recursively unzip all the files in the archive directory"""
    
     