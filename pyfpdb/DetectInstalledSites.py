#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2011 Gimick bbtgaf@googlemail.com
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
#In the "official" distribution you can find the license in agpl-3.0.txt.

"""
Attempt to detect which poker sites are installed by the user, their
 heroname and the path to the HH files.

This is intended for new fpdb users to get them up and running quickly.

We assume that the majority of these users will install the poker client
into default locations so we will only check those places.

We just look for a hero HH folder, and don't really care if the
  application is installed

Situations not handled are:
    Multiple screennames using the computer
    TODO Unexpected dirs in HH dir (e.g. "archive" may become a heroname!)
    Non-standard installation locations
    TODO Mac installations

Typical Usage:
    See TestDetectInstalledSites.py

Todo:
    replace hardcoded site list with something more subtle

"""
import platform
import os
import sys

import Configuration

if platform.system() == 'Windows':
    import winpaths
    PROGRAM_FILES = winpaths.get_program_files()
    LOCAL_APPDATA = winpaths.get_local_appdata()

class DetectInstalledSites():

    def __init__(self, sitename = "All"):

        self.Config=Configuration.Config()
        #
        # objects returned
        #
        self.sitestatusdict = {}
        self.sitename = sitename
        self.heroname = ""
        self.hhpath = ""
        self.tspath = ""
        self.detected = ""
        #
        #since each site has to be hand-coded in this module, there
        #is little advantage in querying the sites table at the moment.
        #plus we can run from the command line as no dependencies
        #
        self.supportedSites = [ "Full Tilt Poker",
                                "PartyPoker",
                                "Merge",
                                "PokerStars"]#,
                                #"Everleaf",
                                #"Win2day",
                                #"OnGame",
                                #"UltimateBet",
                                #"Betfair",
                                #"Absolute",
                                #"PacificPoker",
                                #"Partouche",
                                #"PKR",
                                #"iPoker",
                                #"Winamax",
                                #"Everest" ]

        self.supportedPlatforms = ["Linux", "XP", "Win7"]

        if sitename == "All":
            for siteiter in self.supportedSites:
                self.sitestatusdict[siteiter]=self.detect(siteiter)
        else:
            self.sitestatusdict[sitename]=self.detect(sitename)
            self.heroname = self.sitestatusdict[sitename]['heroname']
            self.hhpath = self.sitestatusdict[sitename]['hhpath']
            self.tspath = self.sitestatusdict[sitename]['tspath']
            self.detected = self.sitestatusdict[sitename]['detected']

        return

    def detect(self, siteToDetect):

        self.hhpathfound = ""
        self.tspathfound = ""
        self.herofound = ""

        if siteToDetect == "Full Tilt Poker":
            self.detectFullTilt()
        elif siteToDetect == "PartyPoker":
            self.detectPartyPoker()
        elif siteToDetect == "PokerStars":
            self.detectPokerStars()
        elif siteToDetect == "Merge":
            self.detectMergeNetwork()

        if (self.hhpathfound and self.herofound):
            encoding = sys.getfilesystemencoding()
            if type(self.hhpathfound) is not unicode:
                self.hhpathfound = unicode(self.hhpathfound, encoding)
            if type(self.tspathfound) is not unicode:
                self.tspathfound = unicode(self.tspathfound, encoding)
            if type(self.herofound) is not unicode:
                self.herofound = unicode(self.herofound, encoding)
            return {"detected":True, "hhpath":self.hhpathfound, "heroname":self.herofound, "tspath":self.tspathfound}
        else:
            return {"detected":False, "hhpath":u"", "heroname":u"", "tspath":u""}

    def detectFullTilt(self):

        if self.Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/Full Tilt Poker/HandHistory/")
        elif self.Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\Full Tilt Poker\\HandHistory\\")
        elif self.Config.os_family == "Win7":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\Full Tilt Poker\\HandHistory\\")
        else:
            return

        if os.path.exists(hhp):
            self.hhpathfound = hhp
        else:
            return

        try:
            self.herofound = os.listdir(self.hhpathfound)[0]
            self.hhpathfound = self.hhpathfound + self.herofound
        except:
            pass

        return
        
    def detectPokerStars(self):

        if self.Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/PokerStars/HandHistory/")
            tsp=os.path.expanduser("~/.wine/drive_c/Program Files/PokerStars/TournSummary/")
        elif self.Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\PokerStars\\HandHistory\\")
            tsp=os.path.expanduser(PROGRAM_FILES+"\\PokerStars\\TournSummary\\")
        elif self.Config.os_family == "Win7":
            hhp=os.path.expanduser(LOCAL_APPDATA+"\\PokerStars\\HandHistory\\")
            tsp=os.path.expanduser(LOCAL_APPDATA+"\\PokerStars\\TournSummary\\")
        elif self.Config.os_family == "Mac":
            hhp=os.path.expanduser("~/Library/Application Support/PokerStars/HandHistory/")
            tsp=os.path.expanduser("~/Library/Application Support/PokerStars/TournSummary/")
        else:
            return

        if os.path.exists(hhp):
            self.hhpathfound = hhp
            if os.path.exists(tsp):
                self.tspathfound = tsp
        else:
            return

        try:
            self.herofound = os.listdir(self.hhpathfound)[0]
            self.hhpathfound = self.hhpathfound + self.herofound
            if self.tspathfound:
                self.tspathfound = self.tspathfound + self.herofound
        except:
            pass

        return

    def detectPartyPoker(self):

        if self.Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/PartyGaming/PartyPoker/HandHistory/")
        elif self.Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\PartyGaming\\PartyPoker\\HandHistory\\")
        elif self.Config.os_family == "Win7":
            hhp=os.path.expanduser("c:\\Programs\\PartyGaming\\PartyPoker\\HandHistory\\")
        else:
            return

        if os.path.exists(hhp):
            self.hhpathfound = hhp
        else:
            return

        dirs = os.listdir(self.hhpathfound)
        if "XMLHandHistory" in dirs:
            dirs.remove("XMLHandHistory")

        try:
            self.herofound = dirs[0]
            self.hhpathfound = self.hhpathfound + self.herofound
        except:
            pass

        return

    def detectMergeNetwork(self):

# Carbon is the principal room on the Merge network but there are many other skins.

# Normally, we understand that a player can only be valid at one
# room on the Merge network so we will exit once successful

# Many thanks to Ilithios for the PlayersOnly information

        merge_skin_names = ["CarbonPoker", "PlayersOnly", "BlackChipPoker", "RPMPoker", "HeroPoker",
                            "PDCPoker", ]
        
        for skin in merge_skin_names:
            if self.Config.os_family == "Linux":
                hhp=os.path.expanduser("~/.wine/drive_c/Program Files/"+skin+"/history/")
            elif self.Config.os_family == "XP":
                hhp=os.path.expanduser(PROGRAM_FILES+"\\"+skin+"\\history\\")            
            elif self.Config.os_family == "Win7":
                hhp=os.path.expanduser(PROGRAM_FILES+"\\"+skin+"\\history\\")
            else:
                return

            if os.path.exists(hhp):
                self.hhpathfound = hhp
                try:
                    self.herofound = os.listdir(self.hhpathfound)[0]
                    self.hhpathfound = self.hhpathfound + self.herofound
                    break
                except:
                    continue

        return
