#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Steffen Schaumburg
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

import L10n
_ = L10n.get_translation()

from imaplib import IMAP4, IMAP4_SSL
import sys
import codecs
import re

import Configuration
import Database
from Exceptions import FpdbParseError
import SQL
import Options
import PokerStarsSummary
import FullTiltPokerSummary


def splitPokerStarsSummaries(summaryText): #TODO: this needs to go to PSS.py
    re_SplitTourneys = PokerStarsSummary.PokerStarsSummary.re_SplitTourneys
    splitSummaries = re.split(re_SplitTourneys, summaryText)

    if len(splitSummaries) <= 1:
        print (_("DEBUG:") + " " + _("Could not split tourneys"))

    return splitSummaries

def splitFullTiltSummaries(summaryText):#TODO: this needs to go to FTPS.py
    re_SplitTourneys = FullTiltPokerSummary.FullTiltPokerSummary.re_SplitTourneys
    splitSummaries = re.split(re_SplitTourneys, summaryText)

    if len(splitSummaries) <= 1:
		print(_("DEBUG:") + " " + _("Could not split tourneys"))

    return splitSummaries

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
        #print(_("response to logging in: "), response)
        #print "server.list():",server.list() #prints list of folders

        response = server.select(config.folder)
        #print "response to selecting INBOX:",response
        if response[0]!="OK":
            raise error #TODO: show error message

        neededMessages=[]
        response, searchData = server.search(None, "SUBJECT", "PokerStars Tournament History Request")
        for messageNumber in searchData[0].split(" "):
            response, headerData = server.fetch(messageNumber, "(BODY[HEADER.FIELDS (SUBJECT)])")
            if response!="OK":
                raise error #TODO: show error message
            neededMessages.append(("PS", messageNumber))

        print _("Found %s eMails to fetch") %(len(neededMessages))

        if (len(neededMessages)==0):
            raise error #TODO: show error message

        email_bodies = []
        for i, messageData in enumerate(neededMessages, start=1):
            #print("Retrieving message %s" % i)
            response, bodyData = server.fetch(messageData[1], "(UID BODY[TEXT])")
            bodyData=bodyData[0][1]
            if response!="OK":
                raise error #TODO: show error message
            if messageData[0]=="PS":
                email_bodies.append(bodyData)
    #finally:
     #   try:
        server.close()
       # finally:
        #    pass
        server.logout()
        print _("Finished downloading emails.")

        errors = 0
        if len(email_bodies) > 0:
            errors = importSummaries(db, config, email_bodies, options = None)
        else:
            print _("No Tournament summaries found.")

        print(_("Errors:"), errors)

def readFile(filename, options):
    codepage = ["utf8"]
    whole_file = None
    if options.hhc == "PokerStars":
        codepage = PokerStarsSummary.PokerStarsSummary.codepage
    elif options.hhc == "Full Tilt Poker":
        codepage = FullTiltPokerSummary.FullTiltPokerSummary.codepage

    for kodec in codepage:
        #print "trying", kodec
        try:
            in_fh = codecs.open(filename, 'r', kodec)
            whole_file = in_fh.read()
            in_fh.close()
            break
        except:
           pass

    return whole_file

def runFake(db, config, options):
    summaryText = readFile(options.filename, options)
    importSummaries(db, config,[summaryText], options=options)

def importSummaries(db, config, summaries, options = None):
    # TODO: At this point we should have:
    # - list of strings to process
    # - The sitename OR specialised TourneySummary object
    # Using options is pretty ugly
    errors = 0
    for summaryText in summaries:
        # And we should def be using a 'Split' from the site object
        if options == None or options.hhc == "PokerStars":
            summaryTexts=(splitPokerStarsSummaries(summaryText))
        elif options.hhc == "Full Tilt Poker":
            summaryTexts=(splitFullTiltSummaries(summaryText))

        print "Found %s summaries in email" %(len(summaryTexts))
        for j, summaryText in enumerate(summaryTexts, start=1):
            try:
                if options == None or options.hhc == "PokerStars":
                    PokerStarsSummary.PokerStarsSummary(db=db, config=config, siteName=u"PokerStars", summaryText=summaryText, builtFrom = "IMAP")
                elif options.hhc == "Full Tilt Poker":
                    FullTiltPokerSummary.FullTiltPokerSummary(db=db, config=config, siteName=u"Fulltilt", summaryText=summaryText, builtFrom = "IMAP")
            except FpdbParseError, e:
                errors += 1
            print _("Finished importing %s/%s tournament summaries") %(j, len(summaryTexts))

    return errors


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        print _("USAGE:")
        sys.exit(0)

    if options.hhc == "PokerStarsToFpdb":
        print _("Need to define a converter")
        exit(0)

    Configuration.set_logfile("fpdb-log.txt")
    # These options should really come from the OptionsParser
    config = Configuration.Config()
    db = Database.Database(config)
    sql = SQL.Sql(db_server = 'sqlite')
    settings = {}
    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())
    db.recreate_tables()

    runFake(db, config, options)

if __name__ == '__main__':
    sys.exit(main())

