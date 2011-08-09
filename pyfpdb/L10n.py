#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Steffen Schaumburg
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

def pass_through(to_translate): return to_translate

def get_special_translation():
    # this function call used from the Configuration process
    # Configuration.py cannot call get_translation() because
    # that is dependent on Configuration !!
    return pass_through

def set_translation(to_lang):

    import gettext
    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[to_lang])
        trans.install()
        translation=_
    except IOError:
        translation=pass_through
    return translation

#def translate(to_translate):
#        return _(to_translate)
#       
def get_translation():
    # This cannot be done in an in-line function
    # because importing Configuration in turn calls L10n
    # which goes wrong because the attribute translation has
    # yet been set !!!!
    # FIXME: This function slows down fpdb-startup, because there
    # are multiple invocations of L10n by each imported
    # module in fpdb.pyw, therefore config() gets called
    # multiple times
    
    import Configuration
    conf=Configuration.Config()
    
    if conf.general['ui_language'] == "system":
        import locale
        try:
            (lang, charset) = locale.getdefaultlocale()
        except:
            lang = None
        if lang==None or lang[:2]=="en":
            return pass_through
        else:
            return set_translation(lang)
    else:
        return set_translation(conf.general['ui_language'])
