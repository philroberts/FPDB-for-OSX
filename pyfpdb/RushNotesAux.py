#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RushNotesAux.py

            EXPERIMENTAL - USE WITH CARE
            
Auxilliary process to push HUD data into the FullTilt player notes XML
This will allow a rudimentary "HUD" in rush games

The existing notes file will be altered by this function
"""
#    Copyright 2010,  "Gimick" of the FPDB project  fpdb.sourceforge.net
#
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

########################################################################

##########for each hand processed, attempts to update hero.xml player notes for FullTilt
##########based upon the AW howto notes written by Ray E. Barker (nutomatic) at fpdb.sourceforge.net

#to do
### think about seeding
### multiple huds firing at the same xml
### same player / two levels / only one xml
### http://www.faqs.org/docs/diveintopython/kgp_search.html

#debugmode will write logfiles for the __init__ and update_data methods
debugmode = False

#    Standard Library modules
import os
from xml.dom import minidom 
from datetime import datetime
from time import *

#    FreePokerDatabase modules
from Mucked import Aux_Window
from Mucked import Seat_Window
from Mucked import Aux_Seats
import Stats

class RushNotes(Aux_Window):

    def __init__(self, hud, config, params):

        self.hud = hud
        self.config = config
        
        #
        # following line makes all the site params magically available (thanks Ray!)        
        #
        site_params_dict = self.hud.config.get_site_parameters(self.hud.site)
        
        heroname = site_params_dict['screen_name']
        sitename = site_params_dict['site_name']
        notepath = site_params_dict['site_path']  # this is a temporary hijack of site-path
        notepath = r"/home/steve/.wine/drive_c/Program Files/Full Tilt Poker/"
        self.heroid = self.hud.db_connection.get_player_id(self.config, sitename, heroname)
        self.notefile = notepath + "/" + heroname + ".xml"

        #
        # read in existing notefile and backup with date/time in name
        # todo change to not use dom
        #
        now = datetime.now()
        notefilebackup = self.notefile + ".backup." + now.strftime("%Y%m%d%H%M%S")
        xmlnotefile = minidom.parse(self.notefile)        
        outputfile = open(notefilebackup, 'w')
        xmlnotefile.writexml(outputfile)
        outputfile.close()
        xmlnotefile.unlink

        # Create a fresh queue file with skeleton XML
        #        
        self.queuefile = self.notefile + ".queue"
        queuedom = minidom.Document()  
        # Create the minidom document

# Create the <wml> base element
        pld=queuedom.createElement("PLAYERDATA")
        queuedom.appendChild(pld)

        nts=queuedom.createElement("NOTES")
        pld.appendChild(nts)
        
        nte = queuedom.createElement("NOTE")
        nte = queuedom.createTextNode("\n")
        nts.insertBefore(nte,None)   
             
        outputfile = open(self.queuefile, 'w')
        queuedom.writexml(outputfile)
        outputfile.close()
        queuedom.unlink
        
        if (debugmode):
            #initialise logfiles
            debugfile=open("~Rushdebug.init", "w")
            debugfile.write("conf="+str(config)+"\n")
            debugfile.write("spdi="+str(site_params_dict)+"\n")
            debugfile.write("para="+str(params)+"\n")
            debugfile.write("hero="+heroname+" "+str(self.heroid)+"\n")
            debugfile.write("back="+notefilebackup+"\n")
            debugfile.write("queu="+self.queuefile+"\n")            
            debugfile.close()
            
            open("~Rushdebug.data", "w").close()
            

    def update_data(self, new_hand_id, db_connection):
        #this method called once for every hand processed
        # self.hud.stat_dict contains the stats information for this hand
        

        
        if (debugmode):
            debugfile=open("~Rushdebug.data", "a")
            debugfile.write(new_hand_id+"\n")
            now = datetime.now()
            debugfile.write(now.strftime("%Y%m%d%H%M%S")+ " update_data begins"+ "\n")
            debugfile.write("hero="+str(self.heroid)+"\n")
            #debugfile.write(str(self.hud.stat_dict)+"\n")
            debugfile.write(self.hud.table.name+"\n")
            debugfile.write(str(self.hud.stat_dict.keys())+"\n")     

        if self.hud.table.name not in ("Mach 10", "Lightning", "Celerity", "Flash", "Zoom"):
            return
        #
        # Grab a list of player id's
        #
        handplayers = self.hud.stat_dict.keys()  

        #
        # build a dictionary of stats text for each player in the hand (excluding the hero)
        # xmlqueuedict contains {playername : stats text}
        #
        xmlqueuedict = {}
        for playerid in handplayers:
            # ignore hero, no notes available for hero at Full Tilt
            if playerid == self.heroid: continue

            playername=unicode(str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'playername')[1]))
            # Use index[3] which is a short description
            n=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'n')[3] + " ")
            vpip=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'vpip')[3] + " ")
            pfr=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'pfr')[3] + " ")
            three_B=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'three_B')[3] + " ")
            cbet=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'cbet')[3] + " ")
            steal=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'steal')[3] + " ")
            ffreq1=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'ffreq1')[3] + " ")
            agg_freq=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'agg_freq')[3] + " ")
            BBper100=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'BBper100')[3] + " ")
        
            xmlqueuedict[playername] = "~fpdb~" + n + vpip + pfr + three_B + cbet + steal + ffreq1 + agg_freq + BBper100 + "~ends~"
        
        if (debugmode):
            now = datetime.now()
            debugfile.write(now.strftime("%Y%m%d%H%M%S")+" villain data has been processed" + "\n")
            debugfile.write(str(xmlqueuedict)+"\n")
        
        #
        # delaying processing of xml until now.  Grab current queuefile contents and
        # read each existing NOTE element in turn, if matched to a player in xmlqueuedict
        # update their text in the xml and delete the dictionary item
        # 
        xmlnotefile = minidom.parse(self.queuefile)
        notelist = xmlnotefile.getElementsByTagName('NOTE')
        
        for noteentry in notelist:                              #for each note in turn
            noteplayer = noteentry.getAttribute("PlayerId")     #extract the playername from xml
            if noteplayer in xmlqueuedict:                      # does that player exist in the queue?
                noteentry.setAttribute("Text",xmlqueuedict[noteplayer])
                del xmlqueuedict[noteplayer]                    #remove from list, does not need to be added later on

        #
        #create entries for new players (those remaining in the dictionary)
        #
        if len(xmlqueuedict) > 0:
            playerdata=xmlnotefile.lastChild #move to the PLAYERDATA node (assume last one in the list)
            notesnode=playerdata.childNodes[0] #Find NOTES node 
        
            for newplayer in xmlqueuedict:
                newentry = xmlnotefile.createElement("NOTE")
                newentry.setAttribute("PlayerId", newplayer)
                newentry.setAttribute("Text", xmlqueuedict[newplayer])              
                notesnode.insertBefore(newentry,None)
                newentry = xmlnotefile.createTextNode("\n")
                notesnode.insertBefore(newentry,None)
                                
        if (debugmode):
            now = datetime.now()
            debugfile.write(now.strftime("%Y%m%d%H%M%S")+" xml pre-processing complete"+ "\n")
            
        #
        # OverWrite existing xml file with updated DOM and cleanup
        #
        updatednotes = open(self.queuefile, 'w')
        xmlnotefile.writexml(updatednotes)
        updatednotes.close()
        
        xmlnotefile.unlink

        if (debugmode):
            now = datetime.now()
            debugfile.write(now.strftime("%Y%m%d%H%M%S")+" dom written, process finished"+ "\n")
            debugfile.close()
