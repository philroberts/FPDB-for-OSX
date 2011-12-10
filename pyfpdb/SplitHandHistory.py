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

# This code is based heavily on stars-support-hh-split.py by Mika Boström

import os
import sys
import re
import codecs
import Options
import Configuration
from Exceptions import *
from cStringIO import StringIO

(options, argv) = Options.fpdb_options()

__ARCHIVE_PRE_HEADER_REGEX='^Hand #(\d+)\s*$|\*{20}\s#\s\d+\s\*+\s+'
re_SplitArchive = re.compile(__ARCHIVE_PRE_HEADER_REGEX)
codepage = ["utf-16", "utf-8", "cp1252"]


class SplitHandHistory:
    def __init__(self, config, in_path = '-', out_path = None, hands = 100, filter = "PokerStarsToFpdb", archive = False):
        self.config = config
        self.in_path = in_path
        self.out_path = out_path
        if not self.out_path:
            self.out_path = os.path.dirname(self.in_path)
        self.hands = hands
        self.archive = archive
        self.re_SplitHands = None
        self.line_delimiter = None
        self.line_addendum = None
        self.filedone = False
        
        #Acquire re_SplitHands for this hh
        filter_name = filter.replace("ToFpdb", "")
        mod = __import__(filter)
        obj = getattr(mod, filter_name, None)
        self.re_SplitHands = obj.re_SplitHands
        
        #Determine line delimiter type if any
        if self.re_SplitHands.match('\n\n'):
            self.line_delimiter = '\n\n'
        if self.re_SplitHands.match('\n\n\n'):
            self.line_delimiter = '\n\n\n'
            
        #Add new line addendum for sites which match SplitHand to next line as well
        if filter_name == 'OnGame':
            self.line_addendum = '*'
        if filter_name == 'Merge':
            self.line_addendum = '<game'
            
        #Open the gargantuan file
        for kodec in self.__listof(codepage):
            try:
                infile = codecs.open(self.in_path, 'r', kodec)
            except IOError:
                print (_('File not found'))
                sys.exit(2)
        
        #Split with do_hands_per_file if archive and paragraphs if a regular hh
        if self.archive:
            nn = 0
            while True:
                nn += 1
                check = self.do_hands_per_file(infile, nn)
                if check is None:
                    print (_('%s processed') % self.in_path)
                    break
        else:
            filenum = 0
            while not self.filedone:
                filenum += 1
                outfile = self.new_file(filenum)
                handnum = 0
                for hand in self.paragraphs(infile, None, self.line_addendum):
                    outfile.write(hand)
                    if self.line_delimiter:
                        outfile.write(self.line_delimiter)
                    handnum += 1
                    if handnum >= self.hands:
                        break
                outfile.close()
                    
    def new_file(self, fileno=-1):
        if fileno < 1:
            print (_('Invalid file number') + ': %d)' % fileno)
            sys.exit(2)
        basename = os.path.splitext(os.path.basename(self.in_path))[0]
        name = os.path.join(self.out_path, basename+'-%06d.txt' % fileno)
        print ('-> %s' % name)
        newfile = file(name, 'w')
        return newfile
        
    #Archive Hand Splitter
    def do_hands_per_file(self, infile, num=-1):
        done = False
        n = 0
        outfile = self.new_file(num)
        while n < self.hands:
            try:
                infile = self.next_hand(infile)
                infile = self.process_hand(infile, outfile)
            except FpdbEndOfFile:
                done = True
                break
            except:
                print _("Unexpected error processing file")
                sys.exit(2)
            n += 1
        outfile.close()
        if not done:
            return infile
        else:
            return None
    
    #Non-Archive Hand Splitter
    def paragraphs(self, file, separator=None, addendum=None):
        if not callable(separator) and self.line_delimiter:
            def separator(line): return line == '\n'
        else:
            def separator(line): return self.re_SplitHands.search(line)
        file_str = StringIO()
        print file_str.getvalue()
        for line in file:
            if separator(line+addendum):
                if file_str.getvalue():
                    if not self.line_delimiter:
                        file_str.write(line)
                    yield file_str.getvalue()
                    file_str = None
                    file_str = StringIO()
            else:
                file_str.write(line)
        if file_str.getvalue(): yield file_str.getvalue()
        self.filedone = True
        
    
    # Finds pre-hand header (Hand #<num>)
    def next_hand(self, infile):
        m = None
        while not m:
            l = infile.readline()
            #print l, len(l)
            # Catch EOF
            if len(l) == 0:
                raise FpdbEndOfFile(_("End of file reached"))
            m = re_SplitArchive.search(l)
        # There is an empty line after pre-hand header and actual HH entry
        l = infile.readline()
                
        return infile
    
    # Each individual hand is written separately
    def process_hand(self, infile=None, outfile=None):
        l = infile.readline()
        l = l.replace('\r\n', '\n')
        outfile.write(l)
        l = infile.readline()
    
        while len(l) < 3:
            l = infile.readline()
        
        while len(l) > 2:
            l = l.replace('\r\n', '\n')
            outfile.write(l)
            l = infile.readline()
        outfile.write(self.line_delimiter)
        return infile
        
    def __listof(self, x):
        if isinstance(x, list) or isinstance(x, tuple):
            return x
        else:
            return [x]

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    Configuration.set_logfile("fpdb-log.txt")
    if not options.config:
        options.config = Configuration.Config(file = "HUD_config.test.xml")

    if options.filename:
        SplitHH = SplitHandHistory(options.config, options.filename, options.outpath, options.hands,
                                   options.hhc, options.archive)

if __name__ == '__main__':
    sys.exit(main())
