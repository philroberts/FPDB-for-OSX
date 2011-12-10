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

To completely replace a method from Aux_Hud, do not call super().

With the exception of class Classic_HUD, all other classes are instanted
in Aux_Hud, and therefore local code here is never recognised.
To overcome this, the Method Resolution Order (MRO) is patched in the code
here using a command "Aux_Hud.some_class = local_class"
This causes the class to be instanted in THIS CODE rather than in Aux_Hud

To debug mro problems, import inspect and inspect.getmro(some_class_name)

General comments about overriding simple_hud
--------------------------------------------
Although there is some flexibility to augment the Aux_Hud, it is not possible
to supplement everything.  For example, when Aux_Hud reads a value from a 
method and then acts on that value, it is difficult to pre-process here to
set a different value.  In those cases, one simply block-copies the method here
but that wasn't the design philosophy of new-hud.

"""
#    to do

#    Standard Library modules

#    pyGTK modules
import gtk

#    FreePokerTools modules
import Aux_Hud
import Stats
import Popup



class Classic_Stat_Window(Aux_Hud.Stat_Window):
    """Stat windows are the blocks shown continually, 1 for each player."""


    def update_contents(self, i):
        super(Classic_Stat_Window, self).update_contents(i)

    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the stat box."""
        # standard Aux method has been overriden to activate hide() button

        if event.button == 2:   # middle button event -- hide the window
            self.hide()

        elif event.button == 3:   # right button event -- show pop up
            pu_to_run = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup].pu_class
            Popup.default(seat = widget.aw_seat,
                                      stat_dict = widget.stat_dict,
                                      win = widget.get_ancestor(gtk.Window),
                                      pop = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup])

        elif event.button == 1:   # left button event -- drag the window
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)      

Aux_Hud.Stat_Window=Classic_Stat_Window  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud
      
      
              
class Classic_HUD(Aux_Hud.Simple_HUD):
    """
        There is one instance of this class per poker table
        the MENU block and stat_windows for each player are controlled
        from this class.
    """

    def __init__(self, hud, config, params):
        super(Classic_HUD, self).__init__(hud, config, params)

    def create_contents(self, container, i):
        #print "SH create contents"
        super(Classic_HUD, self).create_contents(container, i)
##No-need to patch MRO in Aux_Hud - this is instanced here, not in Aux_hud



class Classic_stat(Aux_Hud.Simple_stat):
    """A class to display each individual statistic on the Stat_Window"""
    
    def __init__(self, stat, seat, popup, game_stat_config, aw):
        super(Classic_stat, self).__init__(stat, seat, popup, game_stat_config, aw)
        #game_stat_config is the instance of this stat in the supported games stat configuration
        #use this prefix to directly extract the attributes

        self.click = game_stat_config.click
        self.popup = game_stat_config.popup
        self.tip = game_stat_config.tip
        self.hudprefix = game_stat_config.hudprefix
        self.hudsuffix = game_stat_config.hudsuffix
                
        try: 
            self.stat_locolor = gtk.gdk.Color(game_stat_config.stat_locolor)
            self.stat_loth = game_stat_config.stat_loth
        except: self.stat_locolor=self.stat_loth=""
        try: 
            self.stat_hicolor = gtk.gdk.Color(game_stat_config.stat_hicolor)
            self.stat_hith = game_stat_config.stat_hith
        except: self.stat_hicolor=self.stat_hith=""   
        try: self.hudcolor = gtk.gdk.Color(game_stat_config.hudcolor)
        except: self.hudcolor = gtk.gdk.Color(aw.params['fgcolor']) 

    def update(self, player_id, stat_dict):
        super(Classic_stat, self).update(player_id, stat_dict)

        # Simple hud uses the colour from <aw>; colour from <site> is deprecated
        fg=self.hudcolor        
        if self.stat_loth != "":
            if self.number[0] < (float(self.stat_loth)/100):
                fg=self.stat_locolor
        if self.stat_hith != "":
            if self.number[0] > (float(self.stat_hith)/100):
                fg=self.stat_hicolor
        self.set_color(fg=fg,bg=None)
        
        statstring = "%s%s%s" % (self.hudprefix, str(self.number[1]), self.hudsuffix)
        self.lab.set_text(statstring)
        
        tip = "%s\n%s\n%s, %s" % (stat_dict[player_id]['screen_name'], self.number[5], self.number[3], self.number[4])
        Stats.do_tip(self.widget, tip)
        
Aux_Hud.Simple_stat=Classic_stat  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud



class Classic_eb(Aux_Hud.Simple_eb): pass
Aux_Hud.Simple_eb=Classic_eb  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud



class Classic_label(Aux_Hud.Simple_label): pass
Aux_Hud.Simple_label=Classic_label  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud



class Classic_table_mw(Aux_Hud.Simple_table_mw):
    """
    A class controlling the table menu and the statblocks for that table
    Normally a 1:1 relationship with the Classic_HUD class ???? 
    """
    def __init__(self, hud, aw = None):
        self.menu_label = hud.config.get_hud_ui_parameters()['label']
        super(Classic_table_mw, self).__init__(hud, aw)

    def create_menu_items(self):
        # A tuple of menu items
        return  (  ('Kill This HUD', self.kill),  #self.hud.parent.kill_hud),
                        ('Save HUD Layout', self.save_current_layouts), 
                        ('HUD options', None)
                     )

Aux_Hud.Simple_table_mw=Classic_table_mw  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud
                                          ##see FIXME note in Aux_Hud Simple_table_mw init method
