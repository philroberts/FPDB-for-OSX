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
#In the "official" distribution you can find the license in agpl-3.0.txt.

import os
import sys

# sys.path[0] holds the directory run_fpdb.py is in
sys.path[0] = sys.path[0]+os.sep+"pyfpdb"
# cd to pyfpdb subdir
os.chdir(sys.path[0])
#print "sys.path[0] =", sys.path[0], "cwd =", os.getcwd()

if os.name=='nt':
    os.execvpe('pythonw.exe', list(('pythonw.exe', 'fpdb_prerun.py'))+sys.argv[1:], os.environ)
else:
    os.execvpe('python', list(('python', 'fpdb_prerun.py'))+sys.argv[1:], os.environ)
# first arg is ignored (name of program being run)
