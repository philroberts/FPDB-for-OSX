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

import logging, os, sys, string
import re, urllib2, datetime, pytz
import codecs
import pprint
pp = pprint.PrettyPrinter(indent=4)

def write_file(filename, data):
    print data
    f = open(filename, 'w')
    f.write(data)
    f.close()
    print f

def update(leaf, file_type, stat, default):
    filename = leaf
    #print "DEBUG: fileanme: %s" % filename

    # Test if this is a hand history file
    if filename.endswith(file_type):
        in_fh = codecs.open(filename, 'r', 'utf8')
        whole_file = in_fh.read()
        in_fh.close()

        hash = eval(whole_file)
        if file_type==".hp":
            for player in hash:
                print "player:", player, "<end>"
                hash[player][stat] = default
        elif file_type==".hands":
            hash[stat] = default

        out_string = pp.pformat(hash)
        out_string = string.replace(out_string, "<UTC>", "pytz.utc")
        write_file(filename, out_string)

def walk_test_files(dir, file_type, stat, default):
    """Walks a directory, and executes a callback on each file 
    dir: directory of to search
    file_type: .hands or .hp
    stat: stat to add
    default: value to insert"""
    dir = os.path.abspath(dir)
    for file in [file for file in os.listdir(dir) if not file in [".",".."]]:
        nfile = os.path.join(dir,file)
        if os.path.isdir(nfile):
            walk_test_files(nfile, file_type, stat, default)
        else:
            update(nfile, file_type, stat, default)

def usage():
    print "USAGE:"
    print "Edit this script to activate walk_test_files in main(). Parameters explained in comment of walk_test_files."
    print "\t./ScriptAddStatToRegression.py"
    sys.exit(0)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = Options.fpdb_options()

    if options.usage == True: # or (len(argv) < 1):
        usage()

    print "WARNING:"
    print "This script will modify many files in the regression test suite"
    print "As a safety precaution, you need to edit the file manually to run it"
    #walk_test_files('regression-test-files/', '.hp', 'NEW_STAT', "DEFAULT_VALUE")

if __name__ == '__main__':
    main()
