#!/usr/bin/env python

"""setup.py

Py2exe script for fpdb.
"""
#    Copyright 2009,  Ray E. Barker
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################

#TODO:   change GuiAutoImport so that it knows to start HUD_main.exe, when appropriate
#        include the lib needed to handle png files in mucked
#        get rid of all the uneeded libraries (e.g., pyQT)
#        think about an installer

from distutils.core import setup
import py2exe

setup(
    name        = 'fpdb',
    description = 'Free Poker DataBase',
    version     = '0.12',

    console = [   {'script': 'fpdb.py', },
                  {'script': 'HUD_main.py', }
              ],

    options = {'py2exe': {
                      'packages'    :'encodings',
                      'includes'    : 'cairo, pango, pangocairo, atk, gobject, PokerStarsToFpdb',
		              'excludes'    : '_tkagg, _agg2, cocoaagg, fltkagg',
                      'dll_excludes': 'libglade-2.0-0.dll',
                  }
              },

    data_files = ['HUD_config.xml',
                  'Cards01.png'
                 ]
)

