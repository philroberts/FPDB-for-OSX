#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright 2011-2012,  "Gimick" of the FPDB project  fpdb.sourceforge.net
#                     -  bbtgaf@googlemail.com
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
"""
import L10n
_ = L10n.get_translation()

# to do
#=======
# check that the parameters stored at AW level make sense for players
#  - when playing more than one site
# sort out the wierd focus issues in flop-mucked.

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    FreePokerTools modules
import Aux_Hud
import Stats


class Classic_HUD(Aux_Hud.Simple_HUD):
    """
        There is one instance of this class per poker table
        the stat_windows for each player are controlled
        from this class.
    """

    def __init__(self, hud, config, params):
        super(Classic_HUD, self).__init__(hud, config, params)
        
        # the following attributes ensure that the correct
        # classes are invoked by the calling modules (aux_hud+mucked)
        
        self.aw_class_window = Classic_Stat_Window
        self.aw_class_stat = Classic_stat
        self.aw_class_table_mw = Classic_table_mw
        self.aw_class_label = Classic_label


class Classic_Stat_Window(Aux_Hud.Simple_Stat_Window):
    """Stat windows are the blocks shown continually, 1 for each player."""

    def update_contents(self, i):
        super(Classic_Stat_Window, self).update_contents(i)
        if i == "common": return
                
        # control kill/display of active/inactive player stat blocks
        if self.aw.get_id_from_seat(i) is None:
            #no player dealt in this seat for this hand
            # dim the display to indicate that this block
            # is currently inactive
            self.setWindowOpacity(float(self.aw.params['opacity'])*0.3)
        else:
            #player dealt-in, force display of stat block
            #need to call move() to re-establish window position
            self.move(self.aw.positions[i][0]+self.aw.hud.table.x,
                        self.aw.positions[i][1]+self.aw.hud.table.y)
            self.setWindowOpacity(float(self.aw.params['opacity']))
            # show item, just in case it was hidden by the user
            self.show()
            
    def button_press_middle(self, event):
        self.hide()


class Classic_stat(Aux_Hud.Simple_stat):
    """A class to display each individual statistic on the Stat_Window"""
    
    def __init__(self, stat, seat, popup, game_stat_config, aw):
    
        super(Classic_stat, self).__init__(stat, seat, popup, game_stat_config, aw)
        #game_stat_config is the instance of this stat in the supported games stat configuration
        #use this prefix to directly extract the attributes
        
        self.popup = game_stat_config.popup
        self.click = game_stat_config.click # not implemented yet
        self.tip = game_stat_config.tip     # not implemented yet
        self.hudprefix = game_stat_config.hudprefix
        self.hudsuffix = game_stat_config.hudsuffix
                
        try: 
            self.stat_locolor = game_stat_config.stat_locolor
            self.stat_loth = game_stat_config.stat_loth
        except: self.stat_locolor=self.stat_loth=""
        try: 
            self.stat_hicolor = game_stat_config.stat_hicolor
            self.stat_hith = game_stat_config.stat_hith
        except: self.stat_hicolor=self.stat_hith=""   
        try: self.hudcolor = game_stat_config.hudcolor
        except: self.hudcolor = aw.params['fgcolor']

    def update(self, player_id, stat_dict):
        super(Classic_stat, self).update(player_id, stat_dict)

        if not self.number: #stat did not create, so exit now
            return False
            
        fg=self.hudcolor        
        if self.stat_loth != "":
            try: # number[1] might not be a numeric (e.g. NA)
                if float(self.number[1]) < float(self.stat_loth):
                    fg=self.stat_locolor
            except: pass
        if self.stat_hith != "":
            try: # number[1] might not be a numeric (e.g. NA)
                if float(self.number[1]) > float(self.stat_hith):
                    fg=self.stat_hicolor
            except: pass
        self.set_color(fg=fg,bg=None)
        
        statstring = "%s%s%s" % (self.hudprefix, unicode(self.number[1]), self.hudsuffix)
        self.lab.setText(statstring)
        
        tip = "%s\n%s\n%s, %s" % (stat_dict[player_id]['screen_name'], self.number[5], self.number[3], self.number[4])
        Stats.do_tip(self.lab, tip)


class Classic_label(Aux_Hud.Simple_label): pass

class Classic_table_mw(Aux_Hud.Simple_table_mw):
    """
    A class normally controlling the table menu for that table
    Normally a 1:1 relationship with the Classic_HUD class
    
    This is invoked by the create_common method of the Classic/Simple_HUD class
    (although note that the positions of this block are controlled by shiftx/y
    and NOT by the common position in the layout)
    Movements of the menu block are handled through Classic_HUD/common methods
    """
    pass
