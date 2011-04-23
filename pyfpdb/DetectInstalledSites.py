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

import Configuration
Config=Configuration.Config()

if Config.os_family in ['Win7', 'XP']:
    import winpaths
    PROGRAM_FILES = winpaths.get_program_files()
    LOCAL_APPDATA = winpaths.get_local_appdata()

class DetectInstalledSites():

    def __init__(self, sitename = "All"):
        #
        # objects returned
        #
        self.sitestatusdict = {}
        self.sitename = sitename
        self.heroname = ""
        self.hhpath = ""
        self.detected = ""
        #
        #since each site has to be hand-coded in this module, there
        #is little advantage in querying the sites table at the moment.
        #plus we can run from the command line as no dependencies
        #
        self.supportedSites = [ "Full Tilt Poker",
                                "PartyPoker",
                                "PokerStars"]#,
                                #"Everleaf",
                                #"Win2day",
                                #"OnGame",
                                #"UltimateBet",
                                #"Betfair",
                                #"Absolute",
                                #"PacificPoker",
                                #"Partouche",
                                #"Carbon",
                                #"PKR",
                                #"iPoker",
                                #"Winamax",
                                #"Everest" ]

        self.supportedPlatforms = ["Linux", "XP", "Win7"]

        if sitename == "All":
            for siteiter in self.supportedSites:
                self.sitestatusdict[siteiter]=self.Detect(siteiter)
        else:
            self.sitestatusdict[sitename]=self.Detect(sitename)
            self.heroname = self.sitestatusdict[sitename]['heroname']
            self.hhpath = self.sitestatusdict[sitename]['hhpath']
            self.detected = self.sitestatusdict[sitename]['detected']

        return

    def Detect(self, siteToDetect):

        self.pathfound = ""
        self.herofound = ""

        if siteToDetect == "Full Tilt Poker":
            self.DetectFullTilt()
        elif siteToDetect == "PartyPoker":
            self.DetectPartyPoker()
        elif siteToDetect == "PokerStars":
            self.DetectPokerStars()

        if (self.pathfound and self.herofound):
            self.pathfound = unicode(self.pathfound)
            self.herofound = unicode(self.herofound)
            return {"detected":True, "hhpath":self.pathfound, "heroname":self.herofound}
        else:
            return {"detected":False, "hhpath":"", "heroname":""}

    def DetectFullTilt(self):

        if Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/Full Tilt Poker/HandHistory/")
        elif Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\Full Tilt Poker\\HandHistory\\")
        elif Config.os_family == "Win7":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\Full Tilt Poker\\HandHistory\\")
        else:
            return

        if os.path.exists(hhp):
            self.pathfound = hhp
        else:
            return

        try:
            self.herofound = os.listdir(self.pathfound)[0]
            self.pathfound = self.pathfound + self.herofound
        except:
            pass

        return
        
    def DetectPokerStars(self):

        if Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/PokerStars/HandHistory/")
        elif Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\PokerStars\\HandHistory\\")
        elif Config.os_family == "Win7":
            hhp=os.path.expanduser(LOCAL_APPDATA+"\\PokerStars\\HandHistory\\")
        else:
            return

        if os.path.exists(hhp):
            self.pathfound = hhp
        else:
            return

        try:
            self.herofound = os.listdir(self.pathfound)[0]
            self.pathfound = self.pathfound + self.herofound
        except:
            pass

        return

    def DetectPartyPoker(self):

        if Config.os_family == "Linux":
            hhp=os.path.expanduser("~/.wine/drive_c/Program Files/PartyGaming/PartyPoker/HandHistory/")
        elif Config.os_family == "XP":
            hhp=os.path.expanduser(PROGRAM_FILES+"\\PartyGaming\\PartyPoker\\HandHistory\\")
        elif Config.os_family == "Win7":
            hhp=os.path.expanduser("c:\\Programs\\PartyGaming\\PartyPoker\\HandHistory\\")
        else:
            return

        if os.path.exists(hhp):
            self.pathfound = hhp
        else:
            return

        dirs = os.listdir(self.pathfound)
        if "XMLHandHistory" in dirs:
            dirs.remove("XMLHandHistory")

        try:
            self.herofound = dirs[0]
            self.pathfound = self.pathfound + self.herofound
        except:
            pass

        return
