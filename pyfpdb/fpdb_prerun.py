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
verbose = True

global_modules_to_test =   ["gobject",
                            "pygtk",
                            "gtk",
                            "pango",
                            "cairo",
                            "matplotlib",
                            "numpy",
                            "pylab",
                            "sqlite3"]

windows_modules_to_test =  ["win32gui",
                            "win32api",
                            "win32con",
                            "win32process",
                            "win32event",
                            "win32console",
                            "winpaths"]

linux_modules_to_test = []
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
        if modulename in ["cairo", "gobject", "pygtk"]:            
            failure(_("Unable to load PyGTK modules required for GUI. Please install PyCairo, PyGObject, and PyGTK from www.pygtk.org."))
        if modulename in ["win32console"]:
            failure (_("We appear to be running in Windows, but the Windows Python Extensions are not loading. Please install the PYWIN32 package from http://sourceforge.net/projects/pywin32/"))
        return False

    if modulename == "pygtk":
        try:
            module.require('2.0')
            success("pygtk 2.0")
            return True
        except:
            failure("pygtk 2.0 " + _('File not found'))
            return False

    if modulename == "matplotlib":
        try:
            module.use('GTK')
            success("matplotlib/gtk")
            return False
        except:
            failure("matplotlib/gtk")
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

#=====================================================================

#
# check for gross failures first, no translation on the first
#  two messages because L10n not guaranteed to be available
#

from Tkinter import *

try:
    try_import("sys")
except:
    failure("python failure - could not import sys module")
    win_output(failure_list)
    sys.exit(1)
    
try:
    try_import("Charset")
except:
    failure("fpdb must be installed in an American-English path")
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
    failure(_("\npython 2.6-2.7 not found, please install python 2.6 or 2.7 for fpdb\n"))

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

#
# finished, work out how to exit
#

if len(failure_list):
    win_output(failure_list)
        
if config.install_method == "exe":
    if len(failure_list):
        sys.exit(1)
    else:
        sys.exit(0)
        
if len(failure_list):
    if config.os_family in ("XP", "Win7"):
        sys.exit(1)
    else:
        sys.exit(failure_list)

import os
os.chdir(os.path.join(config.fpdb_program_path, u"pyfpdb"))

if config.os_family in ("XP", "Win7"):
    os.execvpe('pythonw.exe', list(('pythonw.exe', 'fpdb.pyw', '-r'))+sys.argv[1:], os.environ)
else:
    os.execvpe('python', list(('python', 'fpdb.pyw', '-r'))+sys.argv[1:], os.environ)
        
