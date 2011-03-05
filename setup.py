#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Created by Mika Bostrom, released into the public domain as far as legally possible.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# Python packaging for fpdb

from distutils.core import setup
from distutils.command.install_data import install_data as INST

import glob, string, os


class inst_translations(INST):

    # Return triples for installations
    def __locales(self, rootdir):
        _globstr = '%s/*/*/*.mo' % rootdir
        paths = glob.glob(_globstr)
        _locales = []
        for p in paths:
            rp = string.split(p, '/', 2)
            (lang, loc, mo) = string.split(rp[2], '/')
            _locales.append( (lang, loc, mo) )
        return _locales

    def run(self):
        locales = self.__locales('pyfpdb/locale')
        for (lang, loc, mo_file) in locales:
            lang_dir = os.path.join('share', 'locale', lang, loc)
            lang_file = os.path.join('pyfpdb/locale', lang, loc, mo_file)
            self.data_files.append( (lang_dir, [lang_file]) )
        INST.run(self)


commands = {
    'install_data': inst_translations
}

setup(name = 'fpdb',
    description = 'Free Poker Database',
    version = '0.20',
    author = 'FPDB team',
    author_email = 'fpdb-main@lists.sourceforge.net',
    packages = ['fpdb'],
    package_dir = { 'fpdb' : 'pyfpdb' },
    cmdclass = commands,
    data_files = [
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
