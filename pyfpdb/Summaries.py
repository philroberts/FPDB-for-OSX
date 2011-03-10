#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

"""This file is to fetch summaries through IMAP and pass them on to the appropriate parser"""
#see http://docs.python.org/library/imaplib.html for the python interface
#see http://tools.ietf.org/html/rfc2060#section-6.4.4 for IMAP4 search criteria

import sys
from imaplib import IMAP4_SSL
from Summaries import Summaries
from PokerStarsSummaries import PokerStarsSummaries

#TODO: move all these into the config file. until then usage is: ./ImapSummaries.py YourImapHost YourImapUser YourImapPw 
configHost=sys.argv[1]
configUser=sys.argv[2]
configPw=sys.argv[3]

server = IMAP4_SSL(configHost) #TODO: optionally non-SSL
response = server.login(configUser, configPw) #TODO catch authentication error
#print "response to logging in:",response
#print "server.list():",server.list() #prints list of folders

response = server.select("INBOX")
#print "response to selecting INBOX:",response
if response[0]!="OK":
    raise error #TODO: show error message

neededMessages=[]
response, searchData = server.search(None, "SUBJECT", "PokerStars Tournament History Request")
for messageNumber in searchData[0].split(" "):
    response, headerData = server.fetch(messageNumber, "(BODY[HEADER.FIELDS (SUBJECT)])")
    #print "response to fetch subject:",response
    if response!="OK":
        raise error #TODO: show error message
    if headerData[1].find("Subject: PokerStars Tournament History Request - Last x")!=1:
        neededMessages.append(messageNumber, "PS")
        
tourneys=[]
if len(neededMessages)==0:
    raise error #TODO: show error message
for messageData in neededMessages:
    response, bodyData = server.fetch(messageData[0], "(UID BODY[TEXT])")
    if response!="OK":
        raise error #TODO: show error message
    if messageData[0]=="PS":
        tourneys.append(PokerStarsSummaries.PokerStarsSummaries(bodyData))

for tourney in tourneys:
    print "tourney:",tourney

server.close()
server.logout()
