#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010 Steffen Schaumburg
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

import locale
def pass_through(to_translate): return to_translate

(lang, charset) = locale.getdefaultlocale()
if lang==None or lang[:2]=="en":
    translation=pass_through
else:
    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[lang])
        trans.install()
        translation=_
    except IOError:
        translation=pass_through
    
#def translate(to_translate):
#        return _(to_translate)
        
def get_translation():
    return translation
