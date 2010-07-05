#!/usr/bin/env python

"""setup.py

Py2exe script for fpdb.
"""
#    Copyright 2009,  Ray E. Barker
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
#- cd to the folder where this script is stored, usually .../pyfpdb.
#  [If there are build and dist subfolders present , delete them to get
#   rid of earlier builds. Update: script now does this for you]
#- Run the script with "py2exe_setup.py py2exe"
#- You will frequently get messages about missing .dll files. E. g., 
#  MSVCP90.dll. These are somewhere in your windows install, so you 
#  can just copy them to your working folder. (or just assume other
#  person will have them? any copyright issues with including them?)
#- If it works, you'll have a new dir  fpdb-YYYYMMDD-exe  which should
#  contain 2 dirs; gfx and pyfpdb and run_fpdb.bat
#- [ This bit is now automated:
#    Last, you must copy the etc/, lib/ and share/ folders from your
#    gtk/bin/ (just /gtk/?) folder to the pyfpdb folder. (the whole folders, 
#    not just the contents) ]
#- You can (should) then prune the etc/, lib/ and share/ folders to 
#  remove components we don't need. (see output at end of program run)

# sqlcoder notes: this worked for me with the following notes:
#- I used the following versions:
#  python 2.5.4
#  gtk+ 2.14.7   (gtk_2.14.7-20090119)
#  pycairo 1.4.12-2
#  pygobject 2.14.2-2
#  pygtk 2.12.1-3
#  matplotlib 0.98.3
#  numpy 1.4.0
#  py2exe-0.6.9 for python 2.5
#  
#- I also copied these dlls manually from <gtk>/bin to /dist :
#  
#  libgobject-2.0-0.dll
#  libgdk-win32-2.0-0.dll
#
#  Now updated to work with python 2.6 + related dependencies
#  See walkthrough in packaging directory for versions used
#  Updates to this script have broken python 2.5 compatibility (gio module, msvcr71 references now msvcp90)


import os
import sys
from distutils.core import setup
import py2exe
import glob
import matplotlib
import shutil
from datetime import date


origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
        #VisC++ runtime msvcp71.dll removed; py2.6 needs msvcp90.dll which will not be distributed.
        #dwmapi appears to be vista-specific file, not XP 
        if os.path.basename(pathname).lower() in ("dwmapi.dll"):
                return 0
        return origIsSystemDLL(pathname)
py2exe.build_exe.isSystemDLL = isSystemDLL


def remove_tree(top):
    # Delete everything reachable from the directory named in 'top',
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    # sc: Nicked this from somewhere, added the if statement to try 
    #     make it a bit safer
    if top in ('build','dist','gfx') and os.path.basename(os.getcwd()) == 'pyfpdb':
        #print "removing directory '"+top+"' ..."
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(top)

def test_and_remove(top):
    if os.path.exists(top):
        if os.path.isdir(top):
            remove_tree(top)
        else:
            print "Unexpected file '"+top+"' found. Exiting."
            exit()

# remove build and dist dirs if they exist
test_and_remove('dist')
test_and_remove('build')
#test_and_remove('gfx')


today = date.today().strftime('%Y%m%d')
print "\n" + r"Output will be created in \pyfpdb\ and \fpdb_"+today+'\\'
#print "Enter value for XXX (any length): ",     # the comma means no newline
#xxx = sys.stdin.readline().rstrip()
dist_dirname = r'fpdb-' + today + '-exe'
dist_dir = r'..\fpdb-' + today + '-exe'
print

test_and_remove(dist_dir)

setup(
    name        = 'fpdb',
    description = 'Free Poker DataBase',
    version     = '0.20',

    windows = [   {'script': 'fpdb.pyw', "icon_resources": [(1, "../gfx/fpdb_large_icon.ico")]},
                  {'script': 'HUD_main.pyw', },
                  {'script': 'Configuration.py', }
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
                      'excludes'    : ['_tkagg', '_agg2', 'cocoaagg', 'fltkagg'],   # surely we need this? '_gtkagg'
                      'dll_excludes': ['libglade-2.0-0.dll', 'libgdk-win32-2.0-0.dll'
                                      ,'libgobject-2.0-0.dll', 'msvcr90.dll', 'MSVCP90.dll', 'MSVCR90.dll','msvcr90.dll'],
                  }
              },

    # files in 2nd value in tuple are moved to dir named in 1st value
    #data_files updated for new locations of licences + readme nolonger exists
    data_files = [('', ['HUD_config.xml.example', 'Cards01.png', 'logging.conf', '../agpl-3.0.txt', '../fdl-1.2.txt', '../THANKS.txt', '../readme.txt'])
                 ,(dist_dir, [r'..\run_fpdb.bat'])
                 ,( dist_dir + r'\gfx', glob.glob(r'..\gfx\*.*') )
                 # line below has problem with fonts subdir ('not a regular file')
                 #,(r'matplotlibdata', glob.glob(r'c:\python25\Lib\site-packages\matplotlib\mpl-data\*'))
                 ] + matplotlib.get_py2exe_datafiles()
)


os.rename('dist', 'pyfpdb')

#   these instructions no longer needed:
#print '\n' + 'If py2exe was successful add the \\etc \\lib and \\share dirs '
#print 'from your gtk dir to \\%s\\pyfpdb\\\n' % dist_dirname
#print 'Also copy libgobject-2.0-0.dll and libgdk-win32-2.0-0.dll from <gtk_dir>\\bin'
#print 'into there'

dest = os.path.join(dist_dirname, 'pyfpdb')
#print "try renaming pyfpdb to", dest
dest = dest.replace('\\', '\\\\')
#print "dest is now", dest
os.rename( 'pyfpdb', dest )


print "Enter directory name for GTK (e.g. c:\code\gtk_2.14.7-20090119)\n: ",     # the comma means no newline
gtk_dir = sys.stdin.readline().rstrip()


print "\ncopying files and dirs from ", gtk_dir, "to", dest.replace('\\\\', '\\'), "..."
src = os.path.join(gtk_dir, 'bin', 'libgdk-win32-2.0-0.dll')
src = src.replace('\\', '\\\\')
shutil.copy( src, dest )

src = os.path.join(gtk_dir, 'bin', 'libgobject-2.0-0.dll')
src = src.replace('\\', '\\\\')
shutil.copy( src, dest )


src_dir = os.path.join(gtk_dir, 'etc')
src_dir = src_dir.replace('\\', '\\\\')
dest_dir = os.path.join(dest, 'etc')
dest_dir = dest_dir.replace('\\', '\\\\')
shutil.copytree( src_dir, dest_dir )

src_dir = os.path.join(gtk_dir, 'lib')
src_dir = src_dir.replace('\\', '\\\\')
dest_dir = os.path.join(dest, 'lib')
dest_dir = dest_dir.replace('\\', '\\\\')
shutil.copytree( src_dir, dest_dir )

src_dir = os.path.join(gtk_dir, 'share')
src_dir = src_dir.replace('\\', '\\\\')
dest_dir = os.path.join(dest, 'share')
dest_dir = dest_dir.replace('\\', '\\\\')
shutil.copytree( src_dir, dest_dir )

print "\nIf py2exe was successful you should now have a new dir"
print dist_dirname+" in your pyfpdb dir"
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


