#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2008 Steffen Jobbagy-Felso
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
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

# Users should run fpdb.pyw now, this is included in case they still try to run fpdb.py

import os
import sys

#print "fpdb.py has now been renamed to fpdb.pyw - calling fpdb.pyw ...\n"
sys.stdout.write('fpdb.py has been renamed to fpdb.pyw - now calling fpdb.pyw ...\n\n')
sys.stdout.flush()

os.execvpe('pythonw.exe', ('pythonw.exe', 'fpdb.pyw', '-r'), os.environ) 
# first arg is ignored (name of program being run)
