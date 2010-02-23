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
#- [ If it works, you'll have 3 new folders, build and dist and gfx. Build is 
#    working space and should be deleted. Dist and gfx contain the files to be
#    distributed. ]
#  If it works, you'll have a new dir  fpdb-XXX-YYYYMMDD-exe  which should
#  contain 2 dirs; gfx and pyfpdb and run_fpdb.bat
#- Last, you must copy the etc/, lib/ and share/ folders from your
#  gtk/bin/ (just /gtk/?) folder to the pyfpdb folder. (the whole folders, 
#  not just the contents) 
#- You can (should) then prune the etc/, lib/ and share/ folders to 
#  remove components we don't need. 

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


import os
import sys
from distutils.core import setup
import py2exe
import glob
import matplotlib
from datetime import date


origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in ("msvcp71.dll", "dwmapi.dll"):
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
test_and_remove('gfx')


today = date.today().strftime('%Y%m%d')
print "\n" + r"Output will be created in \pyfpdb\ and \fpdb_XXX_"+today+'\\'
print "Enter value for XXX (any length): ",     # the comma means no newline
xxx = sys.stdin.readline().rstrip()
dist_dirname = r'fpdb-' + xxx + '-' + today + '-exe'
dist_dir = r'..\fpdb-' + xxx + '-' + today + '-exe'
print

test_and_remove(dist_dir)

setup(
    name        = 'fpdb',
    description = 'Free Poker DataBase',
    version     = '0.12',

    console = [   {'script': 'fpdb.py', "icon_resources": [(1, "../gfx/fpdb_large_icon.ico")]},
                  {'script': 'HUD_main.py', },
                  {'script': 'Configuration.py', }
              ],

    options = {'py2exe': {
                      'packages'    : ['encodings', 'matplotlib'],
                      'includes'    : ['cairo', 'pango', 'pangocairo', 'atk', 'gobject'
                                      ,'matplotlib.numerix.random_array'
                                      ,'AbsoluteToFpdb',      'BetfairToFpdb'
                                      ,'CarbonToFpdb',        'EverleafToFpdb'
                                      ,'FulltiltToFpdb',      'OnGameToFpdb'
                                      ,'PartyPokerToFpdb',    'PokerStarsToFpdb'
                                      ,'UltimateBetToFpdb',   'Win2dayToFpdb'
                                      ],
                      'excludes'    : ['_tkagg', '_agg2', 'cocoaagg', 'fltkagg'],   # surely we need this? '_gtkagg'
                      'dll_excludes': ['libglade-2.0-0.dll', 'libgdk-win32-2.0-0.dll'
                                      ,'libgobject-2.0-0.dll'],
                  }
              },

    # files in 2nd value in tuple are moved to dir named in 1st value
    data_files = [('', ['HUD_config.xml.example', 'Cards01.png', 'logging.conf'])
                 ,(dist_dir, [r'..\run_fpdb.bat'])
                 ,( dist_dir + r'\gfx', glob.glob(r'..\gfx\*.*') )
                 # line below has problem with fonts subdir ('not a regular file')
                 #,(r'matplotlibdata', glob.glob(r'c:\python25\Lib\site-packages\matplotlib\mpl-data\*'))
                 ] + matplotlib.get_py2exe_datafiles()
)


os.rename('dist', 'pyfpdb')

print '\n' + 'If py2exe was successful add the \\etc \\lib and \\share dirs '
print 'from your gtk dir to \\%s\\pyfpdb\\\n' % dist_dirname
print 'Also copy libgobject-2.0-0.dll and libgdk-win32-2.0-0.dll from <gtk_dir>\\bin'
print 'into there'

dest = os.path.join(dist_dirname, 'pyfpdb')
#print "try renaming pyfpdb to", dest
dest = dest.replace('\\', '\\\\')
#print "dest is now", dest
os.rename( 'pyfpdb', dest )


