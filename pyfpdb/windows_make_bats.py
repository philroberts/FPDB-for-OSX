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

# create .bat scripts in windows to try out different gtk dirs

import L10n
_ = L10n.get_translation()

try:

    import os
    import sys
    import re

    if os.name != 'nt':
        print _("This script is only for Windows.")
        exit()

    dirs = re.split(os.pathsep, os.environ['PATH'])
    # remove any trailing / or \ chars from dirs:
    dirs = [re.sub('[\\/]$','',p) for p in dirs]
    # remove any dirs containing 'python' apart from those ending in 'python25', 'python26' or 'python':
    dirs = [p for p in dirs if not re.search('python', p, re.I) or re.search('python25$', p, re.I) or re.search('python26$', p, re.I)]
    # find gtk dirs:
    gtkdirs = [p for p in dirs if re.search('gtk', p, re.I)]

    lines = [ '@echo off\n\n'
            , '<path goes here>'
            , 'python fpdb.py\n\n'
            , 'pause\n\n'
            ]
    if gtkdirs:
        i = 1
        for gpath in gtkdirs:   # enumerate converts the \\ into \
            tmpdirs = [p for p in dirs if not re.search('gtk', p, re.I) or p == gpath]
            tmppath = ";".join(tmpdirs)
            lines[1] = 'PATH=' + tmppath + '\n\n'
            bat = open('run_fpdb'+str(i)+'.bat', 'w')
            bat.writelines(lines)
            bat.close()
            i = i + 1
    else:
        print _("No gtk directories found in your path.") + " " + _("Install gtk or edit the path manually.")

except SystemExit:
    pass

except:
    print "Error:", str(sys.exc_info())
    pass

# sys.stdin.readline()
