#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""setup.py

Py2exe script for fpdb.
"""
#    Copyright 2009-2010,  Ray E. Barker
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

#TODO:   
#        get rid of all the uneeded libraries (e.g., pyQT)
#        think about an installer

# done:  change GuiAutoImport so that it knows to start HUD_main.exe, when appropriate
#        include the lib needed to handle png files in mucked

#HOW TO USE this script:
#
#- cd to the folder where this script is stored, usually ...packaging/windows
#- Run the script with python "py2exe_setup.py py2exe"
#- You will frequently get messages about missing .dll files.just assume other
#  person will have them? we have copyright issues including some dll's
#- If it works, you'll have a new dir  fpdb-YYYYMMDD-exe  which should
#  contain 2 dirs; gfx and pyfpdb and run_fpdb.bat
#- [ This bit is now automated:
#    Last, you must copy the etc/, lib/ and share/ folders from your
#    gtk/bin/ (just /gtk/?) folder to the pyfpdb folder. (the whole folders, 
#    not just the contents) ]
#- You can (should) then prune the etc/, lib/ and share/ folders to 
#  remove components we don't need. (see output at end of program run)

#  See walkthrough in packaging directory for versions used

# steffeN: Doesnt seem necessary to gettext-ify this, but feel free to if you disagree
# Gimick: restructure to allow script to run from packaging/windows directory, and not to write to source pyfpdb


import os
import sys

# get out now if parameter not passed
try: 
    sys.argv[1] <> ""
except: 
    print "A parameter is required, quitting now"
    quit()

from distutils.core import setup
import py2exe
import glob
import matplotlib
import shutil
#from datetime import date


def isSystemDLL(pathname):
        #dwmapi appears to be vista-specific file, not XP 
        if os.path.basename(pathname).lower() in ("dwmapi.dll"):
                return 0
        return origIsSystemDLL(pathname)

def test_and_remove(top):
    if os.path.exists(top):
        if os.path.isdir(top):
            remove_tree(top)
        else:
            print "Unexpected file '"+top+"' found. Exiting."
            exit()
        
def remove_tree(top):
    # Delete everything reachable from the directory named in 'top',
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    # sc: Nicked this from somewhere, added the if statement to try 
    #     make it a bit safer
    if top in ('build','dist',distdir) and os.path.basename(os.getcwd()) == 'windows':
        #print "removing directory '"+top+"' ..."
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(top)

def copy_tree(source,destination):
    source = source.replace('\\', '\\\\')
    destination = destination.replace('\\', '\\\\')
    print "*** Copying " + source + " to " + destination + " ***"
    shutil.copytree( source, destination )

def copy_file(source,destination):
    source = source.replace('\\', '\\\\')
    destination = destination.replace('\\', '\\\\')
    print "*** Copying " + source + " to " + destination + " ***"
    shutil.copy( source, destination )


fpdbver = '0.20.906'

distdir = r'fpdb-' + fpdbver
rootdir = r'../../' #cwd is normally /packaging/windows
pydir = rootdir+'pyfpdb/'
gfxdir = rootdir+'gfx/'
sys.path.append( pydir )  # allows fpdb modules to be found by options/includes below

print "\n" + r"Output will be created in "+distdir

print "*** Cleaning working folders ***"
test_and_remove('dist')
test_and_remove('build')
test_and_remove(distdir)

print "*** Building now in dist folder ***"

origIsSystemDLL = py2exe.build_exe.isSystemDLL
py2exe.build_exe.isSystemDLL = isSystemDLL

setup(
    name        = 'fpdb',
    description = 'Free Poker DataBase',
    version     = fpdbver,

    windows = [   {'script': pydir+'fpdb.pyw', "icon_resources": [(1, gfxdir+"fpdb_large_icon.ico")]},
                  {'script': pydir+'HUD_main.pyw', },
                  {'script': pydir+'Configuration.py', }
              ],

    options = {'py2exe': {
                      'packages'    : ['encodings', 'matplotlib'],
                      'includes'    : ['gio', 'cairo', 'pango', 'pangocairo', 'atk', 'gobject'    
                                      ,'matplotlib.numerix.random_array'
                                      ,'AbsoluteToFpdb',      'BetfairToFpdb'
                                      ,'CarbonToFpdb',        'EverleafToFpdb'
                                      ,'FulltiltToFpdb',      'OnGameToFpdb'
                                      ,'PartyPokerToFpdb',    'PokerStarsToFpdb'
                                      ,'UltimateBetToFpdb',   'Win2dayToFpdb'
                                      ],
                      'excludes'    : ['_tkagg', '_agg2', 'cocoaagg', 'fltkagg'],
                      'dll_excludes': ['libglade-2.0-0.dll', 'libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll'
                                      , 'msvcr90.dll', 'MSVCP90.dll', 'MSVCR90.dll','msvcr90.dll'],  # these are vis c / c++ runtimes, and must not be redistributed
                  }
              },

    # files in 2nd value in tuple are moved to dir named in 1st value
    # this code will not walk a tree
    # Note: cwd for 1st value is packaging/windows/dist (this is confusing BTW)
    # Note: only include files here which are to be put into the package pyfpdb folder or subfolders

    data_files = [('', glob.glob(rootdir+'*.txt'))
                 ,('', [pydir+'HUD_config.xml.example',pydir+'Cards01.png', pydir+'logging.conf'])
                 ] + matplotlib.get_py2exe_datafiles()
)

#                 ,(distdir, [rootdir+'run_fpdb.bat'])
#                 ,(distdir+r'\gfx', glob.glob(gfxdir+'*.*'))
#                 ] + 
print "*** py2exe build phase complete ***"

# copy zone info and fpdb translation folders
copy_tree (r'c:\python26\Lib\site-packages\pytz\zoneinfo', os.path.join(r'dist', 'zoneinfo'))
copy_tree (pydir+r'locale', os.path.join(r'dist', 'locale'))

# create distribution folder and populate with gfx + bat
copy_tree (gfxdir, os.path.join(distdir, 'gfx'))
copy_file (rootdir+'run_fpdb.bat', distdir)

print "*** Renaming dist folder as distribution pyfpdb folder ***"
dest = os.path.join(distdir, 'pyfpdb')
os.rename( 'dist', dest )

print "*** copying GTK runtime ***"
gtk_dir = ""
while not os.path.exists(gtk_dir):
    print "Enter directory name for GTK (e.g. c:/gtk) : ",     # the comma means no newline
    gtk_dir = sys.stdin.readline().rstrip()

print "*** copying GTK runtime ***"
dest = os.path.join(distdir, 'pyfpdb')
copy_file(os.path.join(gtk_dir, 'bin', 'libgdk-win32-2.0-0.dll'), dest )
copy_file(os.path.join(gtk_dir, 'bin', 'libgobject-2.0-0.dll'), dest)
copy_tree(os.path.join(gtk_dir, 'etc'), os.path.join(dest, 'etc'))
copy_tree(os.path.join(gtk_dir, 'lib'), os.path.join(dest, 'lib'))
copy_tree(os.path.join(gtk_dir, 'share'), os.path.join(dest, 'share'))

print "*** All done! ***"
test_and_remove('build')
print distdir+" is in the pyfpdb dir"
print """
The following dirs can probably removed to make the final package smaller:

pyfpdb/lib/glib-2.0
pyfpdb/lib/gtk-2.0/include
pyfpdb/lib/pkgconfig
pyfpdb/share/aclocal
pyfpdb/share/doc
pyfpdb/share/glib-2.0
pyfpdb/share/gtk-2.0
pyfpdb/share/gtk-doc
pyfpdb/share/locale
pyfpdb/share/man
pyfpdb/share/themes/Default

Use 7-zip to zip up the distribution and create a self extracting archive and that's it!
"""
