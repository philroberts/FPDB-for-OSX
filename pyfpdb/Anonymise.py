#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Carl Gherardi
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

import os
import re
import codecs
import Options
import HandHistoryConverter
import Configuration
import sys

#   command line is:
#  ./Anonymise.py -f <valid path to HH file> -k <name of input filter>

(options, argv) = Options.fpdb_options()
if options.config:
    config = Configuration.Config(options.config)
else:
    config = Configuration.Config()

filter = options.hhc

filter_name = filter.replace("ToFpdb", "")

mod = __import__(filter)
obj = getattr(mod, filter_name, None)

hhc = obj(config, autostart=False)

for kodec in ("utf8", "cp1252", "utf-16"):
    if os.path.exists(options.filename):
        in_fh = codecs.open(options.filename, 'r', kodec)
        filecontents = in_fh.read()
        in_fh.close()
        break
    else:
        print(_("Could not find file %s") % options.filename)
        exit(1)

m = hhc.re_PlayerInfo.finditer(filecontents)

outfile = options.filename+".anon"
print(_("Output being written to %s") % outfile)

savestdout = sys.stdout
fsock = open(outfile,"w")
sys.stdout = fsock

players = []
for a in m:
    players = players + [a.group('PNAME')]

uniq = set(players)

for i, name in enumerate(uniq):
    filecontents = filecontents.replace(name, 'Player%d' %i)

print(filecontents.encode('utf-8'))

sys.stdout = savestdout
fsock.close()

