#!/usr/bin/python2
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Mika Bostrom
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

# Python packaging for fpdb

from distutils.core import setup

setup(name = 'fpdb',
    description = 'Free Poker Database',
    version = '0.12',
    author = 'FPDB team',
    author_email = 'fpdb-main@lists.sourceforge.net',
    packages = ['fpdb'],
    package_dir = { 'fpdb' : 'pyfpdb' },
    data_files = [
        ('/usr/share/doc/python-fpdb',
            ['docs/readme.txt', 'docs/release-notes.txt',
            'docs/tabledesign.html', 'THANKS.txt']),
        ('/usr/share/pixmaps',
            ['gfx/fpdb-icon.png', 'gfx/fpdb-icon2.png',
             'gfx/fpdb-cards.png'
             ]),
        ('/usr/share/applications',
            ['files/fpdb.desktop']),
        ('/usr/share/python-fpdb',
            ['pyfpdb/logging.conf', 'pyfpdb/Cards01.png',
             'pyfpdb/HUD_config.xml.example'
            ])
        ]
)
