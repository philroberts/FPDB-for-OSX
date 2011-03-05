#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
#In the "official" distribution you can find the license in agpl-3.0.txt

"""A script for adding new stats to the regression test library"""

import Options

import logging, os, sys
import re, urllib2
import codecs
import pprint
pp = pprint.PrettyPrinter(indent=4)

def write_file(filename, data):
    print data
    f = open(filename, 'w')
    f.write(data)
    f.close()
    print f

def update(leaf, stat, default):
    filename = leaf
    #print "DEBUG: fileanme: %s" % filename

    # Test if this is a hand history file
    if filename.endswith('.hp'):
        in_fh = codecs.open(filename, 'r', 'utf8')
        whole_file = in_fh.read()
        in_fh.close()

        hash = eval(whole_file)
        for player in hash:
            hash[player][stat] = default

        string = pp.pformat(hash)
        write_file(filename, string)

def walk_testfiles(dir, stat, default):
    """Walks a directory, and executes a callback on each file """
    dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
        nfile = os.path.join(dir,file)
        if os.path.isdir(nfile):
            walk_testfiles(nfile, stat, default)
        else:
            update(nfile, stat, default)

def usage():
    print "USAGE:"
    print "\t./ScriptAddStatToRegression.py"
    sys.exit(0)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        usage()

    print "WARNING:"
    print "This script will modify many files in the regression test suite"
    print "As a safety precaution, you need to edit the file manually to run it"
    #walk_testfiles('regression-test-files/', 'zzzzzzz', False)

if __name__ == '__main__':
    main()
