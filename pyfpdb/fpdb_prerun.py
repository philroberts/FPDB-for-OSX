#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2011, Gimick (bbtgaf@googlemail.com)
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

########################################################################

failure_list = []
success_list = []
verbose = False

global_modules_to_test =   ["PyQt5",
                            "matplotlib",
                            "numpy",
                            "pylab",
                            "sqlite3",
                            "pytz"]

windows_modules_to_test =  ["win32gui",
                            "win32api",
                            "win32con",
                            "win32process",
                            "win32event",
                            "win32console",
                            "winpaths"]

linux_modules_to_test = ["xcffib", "xcffib.xproto"]
mac_modules_to_test = []
posix_modules_to_test = []

def win_output(message):
    
    win = Tk()
    win.title("FPDB")
    win.geometry("600x400")
    listbox  = Listbox(win)
    for item in message:
        listbox.insert(END,item)
    listbox.pack(fill=BOTH, expand=YES)
    win.mainloop()

def try_import(modulename):

    try:
        module = __import__(modulename)
        success(module)
    except:
        failure( _('File not found')+ ": " +modulename)
        if modulename in ["win32console"]:
            failure (_("We appear to be running in Windows, but the Windows Python Extensions are not loading. Please install the PYWIN32 package from http://sourceforge.net/projects/pywin32/"))
        if modulename in ["pytz"]:
            failure (_("Unable to import PYTZ library. Please install PYTZ from http://pypi.python.org/pypi/pytz/"))
        return False

    if modulename == "matplotlib":
        try:
            module.use('qt5agg')
            success("matplotlib/qt5agg")
            return False
        except:
            failure("matplotlib/qt5agg")
            return False

    return True

def success(message):
    if verbose:
        print message
    success_list.append(message)

def failure(message):
    if verbose:
        print _("Error:"), message
    failure_list.append(message)


class ChooseLanguage:
     
    def __init__(self, win, language_dict):
        win.title("Choose a language for FPDB")
        win.geometry("350x350")
        self.listbox  = Listbox(win)
        
        self.listbox.insert(END,("Use the system language settings"))
        self.listbox.insert(END,("en -- Always use English for FPDB"))
        for key in sorted(language_dict.iterkeys()):
            self.listbox.insert(END,(key + " -- " + language_dict[key]))
        self.listbox.pack(fill=BOTH, expand=1)
        self.listbox.select_set(0)
        self.selected_language = ""
        
        self.listbox.bind('<Double-1>', self.callbackLanguage)
        win.mainloop()
        
    def callbackLanguage(self, event):
        index = self.listbox.curselection()[0]
        if index == "0":
            self.selected_language = ""
        else:
            self.selected_language = self.listbox.get(index)
        win.destroy()
        
    def getLanguage(self):
        import string
        return string.split(self.selected_language, " -- ", 1)[0]

#=====================================================================

#
# check for gross failures first, no translation on the first
#  two messages because L10n not guaranteed to be available
#

from Tkinter import *

try:
    module = __import__("sys")
except:
    failure("python failure - could not import sys module")
    win_output(failure_list)
    sys.exit(1)
 
try:
    module = __import__("L10n")
except:
    failure("fpdb modules cannot be loaded, check that fpdb is installed in an English path")
    win_output(failure_list)
    sys.exit(1)

import sys
try:
    if sys.argv[1] == "-v":
        verbose = True
except:
    pass

import L10n
_ = L10n.get_translation()
import Configuration
config = Configuration.Config()

if config.python_version not in("2.6", "2.7"):
    failure(_("Python 2.6-2.7 not found, please install python 2.6 or 2.7 for fpdb."))
    
#
# next, check for individual modules existing
#

for i in global_modules_to_test:
    try_import(i)
if config.os_family in ("XP", "Win7"):
    for i in windows_modules_to_test:
        try_import(i)
elif config.os_family == "Linux":
    for i in linux_modules_to_test:
        try_import(i)
elif config.os_family == "Mac":
    for i in mac_modules_to_test:
        try_import(i)
if config.posix:
    for i in posix_modules_to_test:
        try_import(i) 

if len(failure_list):
    win_output(failure_list)

#
# finished validation, work out how to exit
#
if config.install_method == "exe":
    if len(failure_list):
        sys.exit(1)
 
if len(failure_list):
    if config.os_family in ("XP", "Win7"):
        sys.exit(1)
    else:
        sys.exit(failure_list)

#
# If initial run (example_copy==True), prompt for language
#
if config.example_copy:
    #
    # Ask user for their preferred language, save their choice in the
    #  config
    #
    language_dict,null=L10n.get_installed_translations()
    win = Tk()
    chosen_lang = ChooseLanguage(win, language_dict).getLanguage()

    if chosen_lang:
        conf=Configuration.Config()
        conf.set_general(lang=chosen_lang)
        conf.save()

    # signal fpdb.pyw to trigger the config created dialog
    initial_run = "-i"
else:
    initial_run = ""

if config.install_method == "exe":
    if initial_run:
        sys.exit(2)
    else:
        sys.exit(0)

#
# finally, invoke fpdb
#
import os
os.chdir(os.path.join(config.fpdb_root_path, u"pyfpdb"))

if config.os_family in ("XP", "Win7"):
    os.execvpe('pythonw.exe', list(('pythonw.exe', 'fpdb.pyw', initial_run, '-r'))+sys.argv[1:], os.environ)
else:
    os.execvpe('python', list(('python', 'fpdb.pyw', initial_run, '-r'))+sys.argv[1:], os.environ)
###################
# DO NOT INSERT ANY LINES BELOW HERE
# os.execvpe above transfers control to fpdb.pyw immediately
