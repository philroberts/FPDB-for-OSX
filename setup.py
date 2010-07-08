#!/usr/bin/python
# -*- coding: utf-8 -*-

#Created by Mika Bostrom, released into the public domain as far as legally possible.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

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
            ['THANKS.txt']),
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
