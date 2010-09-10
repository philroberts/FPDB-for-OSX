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
from Exceptions import FpdbParseError
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
            if response!="OK":
                raise error #TODO: show error message
            neededMessages.append(("PS", messageNumber))

        print _("ImapFetcher: Found %s messages to fetch") %(len(neededMessages))

        if (len(neededMessages)==0):
            raise error #TODO: show error message

        email_bodies = []
        for i, messageData in enumerate(neededMessages, start=1):
            print "Retrieving message %s" % i
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
        print _("Completed retrieving IMAP messages, closing server connection")

        errors = 0
        if len(email_bodies) > 0:
            errors = importSummaries(db, config, email_bodies)
        else:
            print _("No Tournament summaries found.")

        print _("Errors: %s" % errors)

def readFile(filename):
    kodec = "utf8"
    in_fh = codecs.open(filename, 'r', kodec)
    whole_file = in_fh.read()
    in_fh.close()
    return whole_file



def runFake(db, config, infile):
    summaryText = readFile(infile)
    importSummaries(db, config,[summaryText])

def importSummaries(db, config, summaries):
    errors = 0
    for summaryText in summaries:
        summaryTexts=(splitPokerStarsSummaries(summaryText))
        print "Found %s summaries in email" %(len(summaryTexts))
        for j, summaryText in enumerate(summaryTexts, start=1):
            try:
                result=PokerStarsSummary.PokerStarsSummary(db=db, config=config, siteName=u"PokerStars", summaryText=summaryText, builtFrom = "IMAP")
            except FpdbParseError, e:
                errors += 1
            print _("Finished importing %s/%s PS summaries") %(j, len(summaryTexts))

    return errors


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        print _("USAGE:")
        sys.exit(0)

    # These options should really come from the OptionsParser
    config = Configuration.Config()
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

