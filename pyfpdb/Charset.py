#!/usr/bin/python

#Copyright 2010 Mika Bostrom
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

# Error logging
import sys

# String manipulation
import codecs

# Settings
import Configuration

encoder_to_utf = codecs.lookup('utf-8')
encoder_to_sys = codecs.lookup(Configuration.LOCALE_ENCODING)

# I'm saving a few cycles with this one
not_needed1, not_needed2, not_needed3 = False, False, False
if Configuration.LOCALE_ENCODING == 'UTF8':
    not_needed1, not_needed2, not_needed3 = True, True, True

def to_utf8(s):
    if not_needed1: return s

    try:
        #(_out, _len) = encoder_to_utf.encode(s)
        _out = unicode(s, Configuration.LOCALE_ENCODING).encode('utf-8')
        return _out
    except UnicodeDecodeError:
        sys.stderr.write('Could not convert: "%s"\n' % s)
        raise
    except TypeError: # TypeError is raised when we give unicode() an already encoded string
        return s

def to_db_utf8(s):
    if not_needed2: return s

    try:
        (_out, _len) = encoder_to_utf.encode(unicode(s))
        return _out
    except UnicodeDecodeError:
        sys.stderr.write('Could not convert: "%s"\n' % s)
        raise

def to_gui(s):
    if not_needed3: return s

    try:
        (_out, _len) = encoder_to_sys.encode(s)
        return _out
    except UnicodeDecodeError:
        sys.stderr.write('Could not convert: "%s"\n' % s)
        raise
