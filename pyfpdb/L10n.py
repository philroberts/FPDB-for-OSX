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

#You may find http://boodebr.org/main/python/all-about-python-and-unicode helpful

def pass_through(to_translate): return to_translate

def set_translation(to_lang):

    import gettext

    try:
        trans = gettext.translation("fpdb", localedir="locale", languages=[to_lang])
        trans.install(unicode=True)
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

    # check if _ or pass_through has already been bound if it has,
    # return it now and do not bind again.
    # Otherwise startup will be very slow because L10n is called
    # multiple times during startup

    try:
        return _
    except:
        pass

    try:
        return pass_through
    except:
        pass
    
    #
    # shouldn't get this far, but just in case...
    #
    return init_translation()

def init_translation():
    #
    # set the system language
    # this function normally called once only per instance
    # Calling this function again will have no effect because
    # translations cannot be changed on-the-fly by this function
    #
    import Configuration
    conf=Configuration.Config()
    
    if conf.general['ui_language'] in ("system", ""):
        import locale
        try:
            (lang, charset) = locale.getdefaultlocale()
        except:
            lang = None
        if lang==None or lang[:2]=="en":
            return pass_through
        else:
            return set_translation(lang)
    elif conf.general['ui_language'] == "en":
        return pass_through
    else:
        return set_translation(conf.general['ui_language'])

def get_installed_translations():
    #
    # returns a list of translated installed languages, (de, es)...
    # and a list of lang/country combos for that language (de_DE, de_AT)...
    #
    import locale
    import gettext
    la_list = []
    la_co_list = []
    
    for (ident,la_co) in locale.windows_locale.iteritems():
        if gettext.find("fpdb", localedir="locale", languages=[la_co]):
            if "_" in la_co:
                la, co = la_co.split("_",1)
                la_list.append(la)
            else:
                la_list.append(la_co)
            la_co_list.append(la_co)
    #
    #eliminate dupes
    #
    la_set=set(la_list)
    la_list=list(la_set)
    
    la_dict = {}
    la_co_dict = {}
    try:
        from icu import Locale
        for code in la_list:
            la_dict[code] = Locale.getDisplayName(Locale(code))
        for code in la_co_list:
            la_co_dict[code] = Locale.getDisplayName(Locale(code))
    except:
        for code in la_list:
            la_dict[code] = code
        for code in la_co_list:
            la_co_dict[code] = code

    return la_dict, la_co_dict
