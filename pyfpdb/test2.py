#!/usr/bin/env python
"""test2.py

Test if gtk is working.
"""
#    Copyright 2008, Ray E. Barker
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

import sys

try:
    import pygtk
    pygtk.require('2.0')
    import gtk


    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_title("Test GTK")
    win.set_border_width(1)
    win.set_default_size(600, 500)
    win.set_resizable(True)
    #win.show()

    dia = gtk.Dialog("Test GTK",
                     win,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
    dia.set_default_size(500, 300)

    l = gtk.Label("GTK is working!")
    dia.vbox.add(l)
    l.show()

    response = dia.run()
    if response == gtk.RESPONSE_ACCEPT:
        pass
    dia.destroy()

except:
    print "\nError:", sys.exc_info()
    print "\npress return to finish"
    sys.stdin.readline()
