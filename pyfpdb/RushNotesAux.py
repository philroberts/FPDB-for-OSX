#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RushNotesAux.py

            EXPERIMENTAL - USE WITH CARE
            
Auxilliary process to push HUD data into the FullTilt player notes XML
This will allow a rudimentary "HUD" in rush games

The existing notes file will be altered by this function
"""
#    Copyright 2010-2011,  "Gimick" of the FPDB project  fpdb.sourceforge.net
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

##########for each hand processed, attempts to create update for player notes in FullTilt
##########based upon the AW howto notes written by Ray E. Barker (nutomatic) at fpdb.sourceforge.net
##########Huge thanks to Ray for his guidance and encouragement to create this !!

#
#debugmode will write logfiles for the __init__ and update_data methods
# writes into ./pyfpdb/~Rushdebug.*
#
debugmode = False

#    Standard Library modules
import os
import sys
from xml.dom import minidom 
from datetime import datetime
from time import *

#    FreePokerDatabase modules
from Mucked import Aux_Window
from Mucked import Seat_Window
from Mucked import Aux_Seats
import Stats
import Card

#
# overload minidom methods to fix bug where \n is parsed as " ".
# described here: http://bugs.python.org/issue7139
#

def _write_data(writer, data, isAttrib=False):
    "Writes datachars to writer."
    if isAttrib:
        data = data.replace("\r", "&#xD;").replace("\n", "&#xA;")
        data = data.replace("\t", "&#x9;")
    writer.write(data)
minidom._write_data = _write_data

def writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        _write_data(writer, attrs[a_name].value, isAttrib=True)
        writer.write("\"")
    if self.childNodes:
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))
# For an introduction to overriding instance methods, see
#   http://irrepupavel.com/documents/python/instancemethod/
instancemethod = type(minidom.Element.writexml)
minidom.Element.writexml = instancemethod(
    writexml, None, minidom.Element)



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
        self.heroid = self.hud.db_connection.get_player_id(self.config, sitename, heroname)
        self.notefile = notepath + "/" + heroname + ".xml"
        self.rushtables = ("Mach 10", "Lightning", "Celerity", "Flash", "Zoom", "Apollo")

        if not (os.path.isfile(self.notefile)):
            self.active = False
            return
        else:
            self.active = True

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

        #
        # if queue file does not exist create a fresh queue file with skeleton XML
        # This is possibly not totally safe, if multiple threads arrive
        # here at the same time, but the consequences are not serious
        #

        self.queuefile = self.notefile + ".queue"
        if not (os.path.isfile(self.queuefile)):

            queuedom = minidom.Document()

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
            debugfile=open("~Rushdebug.init", "a")
            debugfile.write("conf="+str(config)+"\n")
            debugfile.write("spdi="+str(site_params_dict)+"\n")
            debugfile.write("para="+str(params)+"\n")
            debugfile.write("hero="+heroname+" "+str(self.heroid)+"\n")
            debugfile.write("back="+notefilebackup+"\n")
            debugfile.write("queu="+self.queuefile+"\n")
            debugfile.close()


    def update_data(self, new_hand_id, db_connection):
        #this method called once for every hand processed
        # self.hud.stat_dict contains the stats information for this hand

        if not self.active:
            return

        if (debugmode):
            debugfile=open("~Rushdebug.data", "a")
            debugfile.write(new_hand_id+"\n")
            now = datetime.now()
            debugfile.write(now.strftime("%Y%m%d%H%M%S")+ " update_data begins"+ "\n")
            debugfile.write("hero="+str(self.heroid)+"\n")
            #debugfile.write(str(self.hud.stat_dict)+"\n")
            debugfile.write("table="+self.hud.table.name+"\n")
            debugfile.write("players="+str(self.hud.stat_dict.keys())+"\n")
            debugfile.write("db="+str(db_connection)+"\n")

        if self.hud.table.name not in self.rushtables:
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
            four_B=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'four_B')[3] + " ")            
            cbet=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'cbet')[3] + " ")
            
            fbbsteal=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'f_BB_steal')[3] + " ")
            f_3bet=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'f_3bet')[3] + " ")
            f_4bet=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'f_4bet')[3] + " ")
                        
            steal=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'steal')[3] + " ")
            ffreq1=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'ffreq1')[3] + " ")
            agg_freq=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'agg_freq')[3] + " ")
            BBper100=str(Stats.do_stat(self.hud.stat_dict, player = playerid, stat = 'BBper100')[3])
            if BBper100[6] == "-": BBper100=BBper100[0:6] + "(" + BBper100[7:] + ")"

            #
            # grab villain known starting hands
            # only those where they VPIP'd, so limp in the BB will not be shown
            # sort by hand strength.  Output will show position too,
            #  so KK.1 is KK from late posn etc.
            # ignore non-rush hands (check against known rushtablenames)
            #  cards decoding is hard-coded for holdem, so that's tuff atm
            # three categories of known hands are shown:
            #    agression preflop hands
            #    non-aggression preflop hands
            #    bigblind called to defend hands
            #
            # This isn't perfect, but it isn't too bad a starting point
            #

            PFcall="PFcall"
            PFaggr="PFaggr"
            PFdefend="PFdefend"

            c = db_connection.get_cursor()
            c.execute(("SELECT handId, position, startCards, street0Aggr, tableName " +
                        "FROM Hands, HandsPlayers " +
                        "WHERE HandsPlayers.handId = Hands.id " +
                        "AND street0VPI " +
                        "AND startCards > 0 " +
                        "AND playerId = %d " +
                        "ORDER BY startCards DESC " +
                        ";")
                         % int(playerid))

            for (qid, qposition, qstartcards, qstreet0Aggr, qtablename) in c.fetchall():
                if (debugmode):
                    debugfile.write("pid, hid, pos, cards, aggr, table player"+
                                    str(playerid)+"/"+str(qid)+"/"+str(qposition)+"/"+
                                    str(qstartcards)+"/"+str(qstreet0Aggr)+"/"+
                                    str(qtablename)+"/"+str(playername)+
                                    "\n")

                humancards = Card.decodeStartHandValue("holdem", qstartcards)
                
                if qtablename not in self.rushtables:
                    pass
                elif qposition == "B" and qstreet0Aggr == False:
                    PFdefend=PFdefend+"/"+humancards
                elif qstreet0Aggr == True:
                    PFaggr=PFaggr+"/"+humancards+"."+qposition
                else:
                    PFcall=PFcall+"/"+humancards+"."+qposition
            c.close

            #
            # build up final text package (top/tail with ~fpdb~ ~ends~
            # for later search/replace by Merge module
            #
            xmlqueuedict[playername] = ("~fpdb~" + "\n" +
                                        n + vpip + pfr + "\n" +
                                        steal + cbet + fbbsteal + ffreq1 + "\n" +
                                        three_B + four_B + f_3bet + f_4bet + "\n" +
                                        agg_freq + BBper100 + "\n" +
                                        PFcall+"\n"+
                                        PFaggr+"\n"+
                                        PFdefend +"\n"+
                                        "~ends~")

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





