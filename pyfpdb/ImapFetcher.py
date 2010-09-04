#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2010 Steffen Schaumburg
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

from imaplib import IMAP4, IMAP4_SSL
import sys
import codecs
import re

import Configuration
import Database
import SQL
import Options
import PokerStarsSummary


import locale
lang=locale.getdefaultlocale()[0][0:2]
if lang=="en":
    def _(string): return string
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
    except IOError:
        def _(string): return string

def splitPokerStarsSummaries(emailText):
    splitSummaries=emailText.split("\nPokerStars Tournament #")[1:]
    for i in range(len(splitSummaries)):
        splitSummaries[i]="PokerStars Tournament #"+splitSummaries[i]
    return splitSummaries
#end def emailText

def run(config, db):
        #print "start of IS.run"
        server=None
    #try:
        #print "useSSL",config.useSsl,"host",config.host
        if config.useSsl:
            server = IMAP4_SSL(config.host)
        else:
            server = IMAP4(config.host)
        response = server.login(config.username, config.password) #TODO catch authentication error
        print _("response to logging in:"),response
        #print "server.list():",server.list() #prints list of folders

        response = server.select(config.folder)
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
            neededMessages.append(("PS", messageNumber))
        
        if (len(neededMessages)==0):
            raise error #TODO: show error message
        for messageData in neededMessages:
            response, bodyData = server.fetch(messageData[1], "(UID BODY[TEXT])")
            bodyData=bodyData[0][1]
            if response!="OK":
                raise error #TODO: show error message
            if messageData[0]=="PS":
                summaryTexts=(splitPokerStarsSummaries(bodyData))
                for summaryText in summaryTexts:
                    result=PokerStarsSummary.PokerStarsSummary(db=db, config=config, siteName=u"PokerStars", summaryText=summaryText, builtFrom = "IMAP")
                    #print "finished importing a PS summary with result:",result
                    #TODO: count results and output to shell like hand importer does
            
        print _("completed running Imap import, closing server connection")
    #finally:
     #   try:
        server.close()
       # finally:
        #    pass
        server.logout()

def readFile(filename):
    kodec = "utf8"
    in_fh = codecs.open(filename, 'r', kodec)
    whole_file = in_fh.read()
    in_fh.close()
    return whole_file



def runFake(db, config, infile):
    summaryText = readFile(infile)
    # This regex should be part of PokerStarsSummary
    re_SplitGames = re.compile("PokerStars Tournament ")
    summaryList = re.split(re_SplitGames, summaryText)

    if len(summaryList) <= 1:
        print "DEBUG: re_SplitGames isn't matching"

    for summary in summaryList[1:]:
        result = PokerStarsSummary.PokerStarsSummary(db=db, config=config, siteName=u"PokerStars", summaryText=summary, builtFrom = "file")

def splitPokerStarsSummaries(emailText):
    splitSummaries=emailText.split("\nPokerStars Tournament #")[1:]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        print _("USAGE:")
        sys.exit(0)

    # These options should really come from the OptionsParser
    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)
    sql = SQL.Sql(db_server = 'sqlite')
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()

    runFake(db, config, options.infile)

if __name__ == '__main__':
    sys.exit(main())

