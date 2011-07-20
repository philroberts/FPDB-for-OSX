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

class IdentifySite:
    def __init__(self, config, in_path = '-', list = []):
        self.in_path = in_path
        self.config = config
        self.db = Database.Database(self.config)
        self.sitelist = {}
        self.filelist = {}
        self.generateSiteList()
        if list:
            for file in list:
                self.idSite(file, self.sitelist)
        else:
            if os.path.isdir(self.in_path):
                self.walkDirectory(self.in_path, self.sitelist)
            else:
                self.idSite(self.in_path, self.sitelist)
            
    def get_filelist(self):
        return self.filelist
        
    def generateSiteList(self):
        """Generates a ordered dictionary of site, filter and filter name for each site in hhcs"""
        #print self.config.hhcs
        for site, hhc in self.config.hhcs.iteritems():
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
                self.sitelist[result[0][0]] = (site, filter, filter_name, summary, mod, obj, smod, sobj)
            else:
                pass

    def walkDirectory(self, dir, sitelist):
        """Walks a directory, and executes a callback on each file"""
        dir = os.path.abspath(dir)
        for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
            nfile = os.path.join(dir,file)
            if os.path.isdir(nfile):
                self.walkDirectory(nfile, sitelist)
            else:
                self.idSite(nfile, sitelist)
                
    def __listof(self, x):
        if isinstance(x, list) or isinstance(x, tuple):
            return x
        else:
            return [x]
    
    def idSite(self, file, sitelist):
        """Identifies the site the hh file originated from"""
        if file.endswith('.txt') or file.endswith('.xml'):
            self.filelist[file] = ''
            archive = False
            for id, info in sitelist.iteritems():
                site = info[0]
                filter = info[1]
                filter_name = info[2]
                summary = info[3]
                mod = info[4]
                obj = info[5]
                if summary:
                    smod = info[6]
                    sobj = info[7]
                
                for kodec in self.__listof(obj.codepage):
                    try:
                        in_fh = codecs.open(file, 'r', kodec)
                        whole_file = in_fh.read(250)
                        in_fh.close()
                        if filter_name in ('OnGame', 'Winamax'):
                            m = obj.re_HandInfo.search(whole_file)
                        elif filter_name in ('PartyPoker'):
                            m = obj.re_GameInfo.search(whole_file)
                            if not m:
                                m = obj.re_GameInfoTrny.search(whole_file)
                        else:
                            m = obj.re_GameInfo.search(whole_file)
                            if m and re_SplitArchive.search(whole_file):
                                archive = True
                            if not m and summary:
                                m = sobj.re_TourneyInfo.search(whole_file)
                                if m:
                                    filter = summary            
                        if m:
                            self.filelist[file] = [site] + [filter] + [kodec] + [archive]
                            if self.verbose: print 'found --', site, filter, kodec, archive
                            break

                    except:
                        pass
            
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        
    config = Configuration.Config(file = "HUD_config.test.xml")
    in_path = os.path.abspath('regression-test-files')
    IdSite = IdentifySite(config, in_path)

    print "\n----------- SITE LIST -----------"
    for site, info in IdSite.sitelist.iteritems():
        print site, info
    print "----------- END SITE LIST -----------"
    
    print "\n----------- ID REGRESSION FILES -----------"
    for file, site in IdSite.filelist.iteritems():
        print file, site
    print "----------- END ID REGRESSION FILES -----------"

if __name__ == '__main__':
    sys.exit(main())
