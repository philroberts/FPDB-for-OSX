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
from optparse import OptionParser
import codecs
import Database
import Configuration

__ARCHIVE_PRE_HEADER_REGEX='^Hand #(\d+)\s*$|\*{20}\s#\s\d+\s\*{20,25}\s+'
re_SplitArchive = re.compile(__ARCHIVE_PRE_HEADER_REGEX, re.MULTILINE)

class FPDBFile:
    path = ""
    ftype = None # Valid: hh, summary, both
    site = None
    codepage = None
    archive = False
    gameinfo = False

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
        self.codepage = ("utf8", "cp1252", "utf-16")
        self.db = Database.Database(self.config)
        self.sitelist = {}
        self.filelist = {}
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
                    fobj = self.idSite(path, whole_file, kodec)
                    if fobj == False: # Site id failed
                        pass
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
        whole_file = whole_file[:1000]
        f = FPDBFile(file)
        f.codepage = kodec

        for id, site in self.sitelist.iteritems():
            filter_name = site.filter_name
            summary = site.summary
            mod = site.mod
            obj = site.obj

            if filter_name in ('OnGame', 'Winamax'):
                m = obj.re_HandInfo.search(whole_file)
            elif filter_name in ('Win2day'):
                m = obj.re_GameInfo.search(whole_file)
            elif filter_name in ('PartyPoker'):
                m = obj.re_GameInfo.search(whole_file)
                if not m:
                    m = obj.re_GameInfoTrny.search(whole_file)
            else:
                m = obj.re_GameInfo.search(whole_file)
                if m and re_SplitArchive.search(whole_file):
                    f.archive = True
            if m:
                f.site = site
                f.ftype = "hh"
                return f

        for id, site in self.sitelist.iteritems():
            filter_name = site.filter_name
            summary = site.summary
            if summary:
                smod = site.smod
                sobj = site.sobj

                if filter_name in ('Winamax'):
                    m = sobj.re_Details.search(whole_file)
                else:
                    m = sobj.re_TourneyInfo.search(whole_file)
                if m:
                    f.site = site
                    f.ftype = "summary"
                    return f
        return False

    def getFilesForSite(self, sitename, ftype):
        l = []
        sid = self.db.get_site_id(sitename)
        site = self.sitelist[sid[0][0]]
        for name, f in self.filelist.iteritems():
            if f.ftype != None and f.site.name == sitename and f.ftype == "hh":
                print name
                hhc = site.obj(self.config, in_path = name, sitename = site.hhc_fname, autostart = False)
                hhc.readFile()
                f.gametype = hhc.determineGameType(hhc.whole_file)
                l.append(f)
        return l

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    Configuration.set_logfile("fpdb-log.txt")
    config = Configuration.Config(file = "HUD_config.test.xml")
    in_path = os.path.abspath('regression-test-files')
    IdSite = IdentifySite(config, in_path)
    IdSite.scan()

    print "\n----------- SITE LIST -----------"
    for sid, site in IdSite.sitelist.iteritems():
        print "%2d: Name: %s HHC: %s Summary: %s" %(sid, site.name, site.filter_name, site.summary)
    print "----------- END SITE LIST -----------"

    print "\n----------- ID REGRESSION FILES -----------"
    for f, ffile in IdSite.filelist.iteritems():
        print f
        tmp = ""
        tmp += ": Type: %s " % ffile.ftype
        if ffile.ftype == "hh":
            tmp += "Conv: %s" % ffile.site.hhc_fname
        elif ffile.ftype == "summary":
            tmp += "Conv: %s" % ffile.site.summary
        print tmp
    print "----------- END ID REGRESSION FILES -----------"

    print "----------- RETRIEVE FOR SINGLE SITE -----------"
    IdSite.getFilesForSite("PokerStars", "hh")
    print "----------- END RETRIEVE FOR SINGLE SITE -----------"

if __name__ == '__main__':
    sys.exit(main())
