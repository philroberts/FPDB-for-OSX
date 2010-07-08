#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Eric Blade
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

from distutils.core import setup
import py2exe
opts = {
	'py2exe': { 
			'includes': "pango,atk,gobject",
	          }
	}
	
setup(name='Free Poker Database', version='0.12', console=[{"script":"fpdb.py"}])

