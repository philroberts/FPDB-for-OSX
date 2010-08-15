#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Carl Gherardi
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

import os
import re
import codecs
import Options
import HandHistoryConverter
import Configuration
import sys

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

(options, argv) = Options.fpdb_options()
config = Configuration.Config()

filter = options.hhc

filter_name = filter.replace("ToFpdb", "")

mod = __import__(filter)
obj = getattr(mod, filter_name, None)

hhc = obj(config, autostart=False)

if os.path.exists(options.infile):
    in_fh = codecs.open(options.infile, 'r', "utf8")
    filecontents = in_fh.read()
    in_fh.close()
else:
    print _("Could not find file %s") % options.infile
    exit(1)

m = hhc.re_PlayerInfo.finditer(filecontents)

outfile = options.infile+".anon"
print _("Output being written to"), outfile

savestdout = sys.stdout
fsock = open(outfile,"w")
sys.stdout = fsock

players = []
for a in m:
    players = players + [a.group('PNAME')]

uniq = set(players)

for i, name in enumerate(uniq):
    filecontents = filecontents.replace(name, 'Player%d' %i)

print filecontents

sys.stdout = savestdout
fsock.close()

