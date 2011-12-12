#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Chaz Littlejohn
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

import L10n
_ = L10n.get_translation()

import re
import sys
import os
from time import time
from optparse import OptionParser
import codecs
import Database
import Configuration
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("parser")

__ARCHIVE_PRE_HEADER_REGEX='^Hand #(\d+)\s*$|\*{20}\s#\s\d+\s\*{20,25}\s+'
re_SplitArchive = re.compile(__ARCHIVE_PRE_HEADER_REGEX, re.MULTILINE)

class FPDBFile:
    path = ""
    ftype = None # Valid: hh, summary, both
    site = None
    codepage = None
    archive = False
    gametype = False

    def __init__(self, path):
        self.path = path

class Site:
    def __init__(self, name, hhc_fname, filter_name, summary, mod, obj, smod, sobj):
        self.name = name
        # FIXME: rename filter to hhc_fname
        self.hhc_fname = hhc_fname
        # FIXME: rename filter_name to hhc_type
        self.filter_name = filter_name
        self.summary = summary
        self.mod = mod
        self.obj = obj
        self.smod = smod
        self.sobj = sobj

class IdentifySite:
    def __init__(self, config, in_path = '-', list = []):
        self.in_path = in_path
        self.config = config
        self.codepage = ("utf8", "utf-16", "cp1252")
        self.db = Database.Database(self.config)
        self.sitelist = {}
        self.filelist = {}
        self.re_identify = self.getSiteRegex()
        self.generateSiteList()
        self.list = list

    def scan(self):
        if self.list:
            for file, id in self.list:
                self.processFile(file)
        else:
            if os.path.isdir(self.in_path):
                self.walkDirectory(self.in_path, self.sitelist)
            else:
                self.processFile(self.in_path)

    def get_filelist(self):
        return self.filelist
    
    def getSiteRegex(self):
        re_identify = {}
        re_identify['Fulltilt']     = re.compile(u'FullTiltPoker|Full\sTilt\sPoker\sGame\s#\d+:')
        re_identify['PokerStars']   = re.compile(u'PokerStars\sGame\s#\d+:',)
        re_identify['Everleaf']     = re.compile(u'\*{5}\sHand\shistory\sfor\sgame\s#\d+\s|Partouche\sPoker\s')
        re_identify['Boss']         = re.compile(u'<HISTORY\sID="\d+"\sSESSION=')
        re_identify['OnGame']       = re.compile(u'\*{5}\sHistory\sfor\shand\s[A-Z0-9\-]+\s')
        re_identify['Betfair']      = re.compile(u'\*{5}\sBetfair\sPoker\sHand\sHistory\sfor\sGame\s\d+\s')
        re_identify['Absolute']     = re.compile(u'Stage\s#[A-Z0-9]+:')
        re_identify['PartyPoker']   = re.compile(u'\*{5}\sHand\sHistory\s[fF]or\sGame\s\d+\s')
        re_identify['PacificPoker'] = re.compile(u'\*{5}\sCassava\sHand\sHistory\sfor\sGame\s\d+\s')
        re_identify['Merge']        = re.compile(u'<description\stype=')
        re_identify['Pkr']          = re.compile(u'Starting\sHand\s\#\d+')
        re_identify['iPoker']       = re.compile(u'<session\ssessioncode="\d+">')
        re_identify['Winamax']      = re.compile(u'Winamax\sPoker\s\-\s(CashGame|Tournament)')
        re_identify['Everest']      = re.compile(u'<SESSION\stime="\d+"\stableName=".+"\sid=')
        re_identify['Cake']         = re.compile(u'Hand\#\d+\s\-\s')
        re_identify['Entraction']   = re.compile(u'Game\s\#\s\d+\s\-\s')
        re_identify['BetOnline']    = re.compile(u'BetOnline\sPoker\sGame\s\#\d+')
        re_identify['FullTiltPokerSummary'] = re.compile(u'Full\sTilt\sPoker\.fr\sTournament|Full\sTilt\sPoker\sTournament\sSummary')
        re_identify['PokerStarsSummary']    = re.compile(u'PokerStars\sTournament\s\#\d+')
        return re_identify

    def generateSiteList(self):
        """Generates a ordered dictionary of site, filter and filter name for each site in hhcs"""
        hhcs = self.config.hhcs
        for site, hhc in hhcs.iteritems():
            filter = hhc.converter
            filter_name = filter.replace("ToFpdb", "")
            summary = hhc.summaryImporter
            result = self.db.get_site_id(site)
            if len(result) == 1:
                smod, sobj = None, None
                mod = __import__(filter)
                obj = getattr(mod, filter_name, None)
                if summary:
                    smod = __import__(summary)
                    sobj = getattr(smod, summary, None)
                self.sitelist[result[0][0]] = Site(site, filter, filter_name, summary, mod, obj, smod, sobj)

    def walkDirectory(self, dir, sitelist):
        """Walks a directory, and executes a callback on each file"""
        dir = os.path.abspath(dir)
        for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
            nfile = os.path.join(dir,file)
            if os.path.isdir(nfile):
                self.walkDirectory(nfile, sitelist)
            else:
                self.processFile(nfile)

    def __listof(self, x):
        if isinstance(x, list) or isinstance(x, tuple):
            return x
        else:
            return [x]

    def processFile(self, path):
        if path.endswith('.txt') or path.endswith('.xml') or path.endswith('.log'):
            if path not in self.filelist:
                whole_file, kodec = self.read_file(path)
                if whole_file:
                    fobj = self.idSite(path, whole_file[:250], kodec)
                    if fobj == False: # Site id failed
                        log.debug(_("DEBUG:") + " " + _("siteId Failed for: %s") % path)
                    else:
                        self.filelist[path] = fobj

    def read_file(self, in_path):
        for kodec in self.codepage:
            try:
                infile = codecs.open(in_path, 'r', kodec)
                whole_file = infile.read()
                infile.close()
                return whole_file, kodec
            except:
                continue
        return None, None
    
    def idSite(self, file, whole_file, kodec):
        """Identifies the site the hh file originated from"""
        f = FPDBFile(file)
        f.codepage = kodec
        for id, site in self.sitelist.iteritems():
            filter_name = site.filter_name
            m = self.re_identify[filter_name].search(whole_file)
            if m and filter_name in ('Fulltilt', 'PokerStars'):
                if re_SplitArchive.search(whole_file):
                    f.archive = True
            if m:
                f.site = site
                f.ftype = "hh"
                return f

        for id, site in self.sitelist.iteritems():
            filter_name = site.filter_name
            summary = site.summary
            if summary in ('FullTiltPokerSummary', 'PokerStarsSummary'):
                m = self.re_identify[summary].search(whole_file)
                if m:
                    f.site = site
                    f.ftype = "summary"
                    return f
        return False

    def getFilesForSite(self, sitename, ftype):
        l = []
        for name, f in self.filelist.iteritems():
            if f.ftype != None and f.site.name == sitename and f.ftype == "hh":
                l.append(f)
        return l

    def fetchGameTypes(self):
        for name, f in self.filelist.iteritems():
            if f.ftype != None and f.ftype == "hh":
                try: #TODO: this is a dirty hack. Borrowed from fpdb_import
                    name = unicode(name, "utf8", "replace")
                except TypeError:
                    print TypeError
                hhc = f.site.obj(self.config, in_path = name, sitename = f.site.hhc_fname, autostart = False)
                if hhc.readFile():
                    f.gametype = hhc.determineGameType(hhc.whole_file)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    Configuration.set_logfile("fpdb-log.txt")
    config = Configuration.Config(file = "HUD_config.test.xml")
    in_path = os.path.abspath('regression-test-files')
    IdSite = IdentifySite(config, in_path)
    start = time()
    IdSite.scan()
    print 'duration', time() - start

    print "\n----------- SITE LIST -----------"
    for sid, site in IdSite.sitelist.iteritems():
        print "%2d: Name: %s HHC: %s Summary: %s" %(sid, site.name, site.filter_name, site.summary)
    print "----------- END SITE LIST -----------"

    print "\n----------- ID REGRESSION FILES -----------"
    count = 0
    for f, ffile in IdSite.filelist.iteritems():
        tmp = ""
        tmp += ": Type: %s " % ffile.ftype
        count += 1
        if ffile.ftype == "hh":
            tmp += "Conv: %s" % ffile.site.hhc_fname
        elif ffile.ftype == "summary":
            tmp += "Conv: %s" % ffile.site.summary
        print f, tmp
    print count, 'files identified'
    print "----------- END ID REGRESSION FILES -----------"

    print "----------- RETRIEVE FOR SINGLE SITE -----------"
    IdSite.getFilesForSite("PokerStars", "hh")
    print "----------- END RETRIEVE FOR SINGLE SITE -----------"

if __name__ == '__main__':
    sys.exit(main())
