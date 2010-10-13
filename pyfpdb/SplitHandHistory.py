#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2010 Chaz Littlejohn
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
from optparse import OptionParser
import Configuration
from cStringIO import StringIO

__ARCHIVE_PRE_HEADER_REGEX='^Hand #(\d+)\s*$|\*{20}\s#\s\d+\s\*+\s+'
re_SplitArchive = re.compile(__ARCHIVE_PRE_HEADER_REGEX)
codepage = ["utf-16", "utf-8", "cp1252"]


class SplitHandHistory:
    def __init__(self, config, in_path = '-', out_path = None, hands = 100, site = "PokerStars", archive = False):
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
        filter = self.config.hhcs[site].converter
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
        if site == 'OnGame':
            self.line_addendum = '*'
        if site == 'Carbon':
            self.line_addendum = '<game'
            
        #Open the gargantuan file  
        try:
            infile = file(self.in_path, 'r')
        except:
            print 'File is sophisticated'
            for kodec in self.__listof(codepage):
                try:
                    infile = codecs.open(self.in_path, 'r', kodec)
                except IOError:
                    print 'File not found'
                    sys.exit(2)
        
        #Split with do_hands_per_file if archive and paragraphs if a regular hh
        if self.archive:
            nn = 0
            while True:
                nn += 1
                check = self.do_hands_per_file(infile, nn)
                if check is None:
                    print '%s processed' % self.in_path
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
            print 'Nope, won\'t work (fileno=%d)' % fileno
            sys.exit(2)
        basename = os.path.splitext(os.path.basename(self.in_path))[0]
        name = os.path.join(self.out_path, basename+'-%06d.txt' % fileno)
        print '-> %s' % name
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
            except:
                done = True
                break
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
                raise IOError
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

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", metavar="FILE", default=None,
                    help=_("Input file in quiet mode"))
    parser.add_option("-o", "--outpath", dest="outpath", metavar="FILE", default=None,
                    help=_("Input out path in quiet mode"))
    parser.add_option("-c", "--convert", dest="filtername", default="PokerStars", metavar="FILTER",
                    help=_("Conversion filter (*Full Tilt Poker, PokerStars, Everleaf, Absolute)"))
    parser.add_option("-a", "--archive", action="store_true", dest="archive", default=False,
                    help=_("File to be split is a PokerStars or Full Tilt Poker archive file"))
    parser.add_option("-d", "--hands", dest="hands", default="100", type="int",
                    help=_("How many hands do you want saved to each file. Default is 100"))
    (options, argv) = parser.parse_args(args = argv)
    
    config = Configuration.Config(file = "HUD_config.test.xml")

    if not options.filename:
        pass
    else:
        SplitHH = SplitHandHistory(config, options.filename, options.outpath, options.hands,
                                   options.filtername, options.archive)

if __name__ == '__main__':
    sys.exit(main())
