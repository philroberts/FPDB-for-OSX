#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright 2011,  "Gimick" of the FPDB project  fpdb.sourceforge.net
#
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

"""
Aux_Classic_Hud.py

FPDB classic hud, implemented using new-hud framework.

This module structure must be based upon simple HUD in the module Aux_Hud.

Aux_Hud is minimal frozen functionality and is not changed,so
HUD customisation is done in modules which extend/subclass/override aux_hud.

***HERE BE DRAGONS*** 
Please take extra care making changes to this code - there is 
multiple-level inheritence in much of this code, class heirarchies
are not immediately obvious, and there is very close linkage with most of 
the Hud modules.

Note about super() and MRO patching.
------------------------------------

The call to super() invokes that method in the Aux_Hud code - therefore 
local code can be placed before or after the Aux_Hud code runs.

To replace a method from Aux_Hud, simply do not include a super() call.

With the exception of class Classic_HUD, all other classes are instanted
in Aux_Hud, and therefore local code here is never recognised.
To overcome this, the Method Resolution Order (MRO) is patched in the code
here using a command "Aux_Hud.some_class = local_class"
This causes the class to be instanted in THIS CODE rather than in Aux_Hud

To debug mro problems, import inspect and inspect.getmro(some_class_name)
"""#    to do

#    Standard Library modules

#    pyGTK modules
import gtk
#import gobject
#import pango

#    FreePokerTools modules
#import Mucked
#import Stats
#import Popup
import Aux_Hud

class Classic_Stat_Window(Aux_Hud.Stat_Window):
    """Stat windows are the blocks shown continually, 1 for each player."""
    def update_contents(self, i):
        #print "SW UP con"
        #print self.set_focus
        #print type(self.aw.config)
        #print type(self.aw.hud)
        #print self.aw.params
        
        super(Classic_Stat_Window, self).update_contents(i)
Aux_Hud.Stat_Window=Classic_Stat_Window  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud
        
class Classic_HUD(Aux_Hud.Simple_HUD):
    """
        There is one instance of this class per poker table
        the MENU block and stat_windows for each player are controlled
        from this class.
    """

    def __init__(self, hud, config, params):
        #print "SH init"
        #print dir(hud)
        #print config
        #print params
        super(Classic_HUD, self).__init__(hud, config, params)

    def create_contents(self, container, i):
        #print "SH create contents"
        super(Classic_HUD, self).create_contents(container, i)
##No-need to patch MRO in Aux_Hud - this is instanced here, not in Aux_hud

class Classic_stat(Aux_Hud.Simple_stat):
    """A class to display each individual statistic on the Stat_Window"""
    def update(self, player_id, stat_dict):
        super(Classic_stat, self).update(player_id, stat_dict)
        #print str(type(self.stat_window))
        '''
#                    this_stat = config.supported_games[self.poker_game].stats[self.stats[r][c]]
#                    number = Stats.do_stat(self.stat_dict, player = statd['player_id'], stat = self.stats[r][c])
#                    statstring = "%s%s%s" % (this_stat.hudprefix, str(number[1]), this_stat.hudsuffix)
#                    window = self.stat_windows[statd['seat']]
#
#                    if this_stat.hudcolor != "":
#                        window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.hudcolor))
#                    else:
#                        window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.colors['hudfgcolor']))	
#                    
#                    if this_stat.stat_loth != "":
#                        if number[0] < (float(this_stat.stat_loth)/100):
#                            window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.stat_locolor))
#
#                    if this_stat.stat_hith != "":
#                        if number[0] > (float(this_stat.stat_hith)/100):
#                            window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.stat_hicolor))
#
#                    window.label[r][c].set_text(statstring)
        '''
        fg=gtk.gdk.Color("#FFFF00")
        bg=gtk.gdk.Color("#6F6F1E")
        self.set_color(fg,bg)
Aux_Hud.Simple_stat=Classic_stat  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud

class Classic_eb(Aux_Hud.Simple_eb): pass
Aux_Hud.Simple_eb=Classic_eb  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud

class Classic_label(Aux_Hud.Simple_label): pass
Aux_Hud.Simple_label=Classic_label  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud

#class Classic_table_mw(Aux_Hud.Simple_table_mw): pass
#Aux_Hud.Simple_table_mw=Classic_table_mw  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud
