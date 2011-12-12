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
import L10n
_ = L10n.get_translation()

# to do
#=======

# logging not activated yet
# Killed hud-blocks do not re-appear
# Save not working at all yet
# hud menu options for stat display currently being ignored
# move stat blocks menu item not implemnted (is this deprecated)
# debug hud option not implemented
# check that the parameters stored at AW level make sense for players
#    playing more than one site
# activate the set-max-seats logic (on the menu but not working)
# fix the existing bugs with move/resize table (fix in aux_hud, not here)

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
            #pu_to_run = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup].pu_class
            Classic_popup(seat = widget.aw_seat,
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
        self.hud_params = hud.config.get_hud_ui_parameters()
        self.menu_label = self.hud_params['label']

        super(Classic_table_mw, self).__init__(hud, aw)

    def create_menu_items(self, menu):

        killitem = gtk.MenuItem(_('Kill This HUD'))
        menu.append(killitem)
        killitem.connect("activate", self.kill)

        saveitem = gtk.MenuItem(_('Save HUD Layout'))
        menu.append(saveitem)
        saveitem.connect("activate", self.save_current_layouts)

        aggitem = gtk.MenuItem(_('Show Player Stats for'))
        menu.append(aggitem)
        aggMenu = gtk.Menu()
        aggitem.set_submenu(aggMenu)

        def build_aggmenu(legend, cb_params, attrname):
            item = gtk.CheckMenuItem(legend)
            aggMenu.append(item)
            if   "_agg" in attrname: item.connect("activate", self.set_aggregation, cb_params)
            elif "_seats" in attrname: item.connect("activate", self.set_seats_style, cb_params)
            elif "_hud" in attrname: item.connect("activate", self.set_hud_style, cb_params)
            setattr(self, attrname, item)
                    
        # set agg_bb_mult to 1 to stop aggregation
        build_aggmenu(_('For This Blind Level Only'),('P', 1), 'h_aggBBmultItem1')
        aggMenu.append(gtk.MenuItem(_('For Multiple Blind Levels:')))
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.5", "2.0")),('P',2), 'h_aggBBmultItem2')
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.33", "3.0")),('P',3), 'h_aggBBmultItem3')
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.1", "10.0")),('P',10), 'h_aggBBmultItem10')
        build_aggmenu(("  " + _('All Levels')),('P',10000), 'h_aggBBmultItem10000')
        
        aggMenu.append(gtk.MenuItem(_('Number of Seats:')))
        build_aggmenu(("  " + _('Any Number')),('P','A'), 'h_seatsStyleOptionA')
        build_aggmenu(("  " + _('Custom')),('P','C'), 'h_seatsStyleOptionC')
        build_aggmenu(("  " + _('Exact')),('P','E'), 'h_seatsStyleOptionE')

        aggMenu.append(gtk.MenuItem(_('Since:')))
        build_aggmenu(("  " + _('All Time')),('P','A'), 'h_hudStyleOptionA')
        build_aggmenu(("  " + _('Session')),('P','S'), 'h_hudStyleOptionS')
        build_aggmenu(("  " + _('%s Days') % (self.hud_params['h_hud_days'])),('P','T'), 'h_hudStyleOptionT')
 
        aggitem = gtk.MenuItem(_('Show Opponent Stats for'))
        menu.append(aggitem)
        aggMenu = gtk.Menu()
        aggitem.set_submenu(aggMenu)
        
        build_aggmenu(_('For This Blind Level Only'),('O', 1), 'aggBBmultItem1')
        aggMenu.append(gtk.MenuItem(_('For Multiple Blind Levels:')))
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.5", "2.0")),('O',2), 'aggBBmultItem2')
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.33", "3.0")),('O',3), 'aggBBmultItem3')
        build_aggmenu((_('%s to %s * Current Blinds') % ("  0.1", "10.0")),('O',10), 'aggBBmultItem10')
        build_aggmenu(("  " + _('All Levels')),('O',10000), 'aggBBmultItem10000')
        
        aggMenu.append(gtk.MenuItem(_('Number of Seats:')))
        build_aggmenu(("  " + _('Any Number')),('O','A'), 'seatsStyleOptionA')
        build_aggmenu(("  " + _('Custom')),('O','C'), 'seatsStyleOptionC')
        build_aggmenu(("  " + _('Exact')),('O','E'), 'seatsStyleOptionE')

        aggMenu.append(gtk.MenuItem(_('Since:')))
        build_aggmenu(("  " + _('All Time')),('O','A'), 'hudStyleOptionA')
        build_aggmenu(("  " + _('Session')),('O','S'), 'hudStyleOptionS')
        build_aggmenu(("  " + _('%s Days') % (self.hud_params['h_hud_days'])),('O','T'), 'hudStyleOptionT')

        # set active on current options:
        if self.hud_params['h_agg_bb_mult'] == 1:
            getattr(self, 'h_aggBBmultItem1').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 2:
            getattr(self, 'h_aggBBmultItem2').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 3:
            getattr(self, 'h_aggBBmultItem3').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] == 10:
            getattr(self, 'h_aggBBmultItem10').set_active(True)
        elif self.hud_params['h_agg_bb_mult'] > 9000:
            getattr(self, 'h_aggBBmultItem10000').set_active(True)
        
        if self.hud_params['agg_bb_mult'] == 1:
            getattr(self, 'aggBBmultItem1').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 2:
            getattr(self, 'aggBBmultItem2').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 3:
            getattr(self, 'aggBBmultItem3').set_active(True)
        elif self.hud_params['agg_bb_mult'] == 10:
            getattr(self, 'aggBBmultItem10').set_active(True)
        elif self.hud_params['agg_bb_mult'] > 9000:
            getattr(self, 'aggBBmultItem10000').set_active(True)
        
        if self.hud_params['h_seats_style'] == 'A':
            getattr(self, 'h_seatsStyleOptionA').set_active(True)
        elif self.hud_params['h_seats_style'] == 'C':
            getattr(self, 'h_seatsStyleOptionC').set_active(True)
        elif self.hud_params['h_seats_style'] == 'E':
            getattr(self, 'h_seatsStyleOptionE').set_active(True)
        
        if self.hud_params['seats_style'] == 'A':
            getattr(self, 'seatsStyleOptionA').set_active(True)
        elif self.hud_params['seats_style'] == 'C':
            getattr(self, 'seatsStyleOptionC').set_active(True)
        elif self.hud_params['seats_style'] == 'E':
            getattr(self, 'seatsStyleOptionE').set_active(True)
        
        if self.hud_params['h_hud_style'] == 'A':
            getattr(self, 'h_hudStyleOptionA').set_active(True)
        elif self.hud_params['h_hud_style'] == 'S':
            getattr(self, 'h_hudStyleOptionS').set_active(True)
        elif self.hud_params['h_hud_style'] == 'T':
            getattr(self, 'h_hudStyleOptionT').set_active(True)
        
        if self.hud_params['hud_style'] == 'A':
            getattr(self, 'hudStyleOptionA').set_active(True)
        elif self.hud_params['hud_style'] == 'S':
            getattr(self, 'hudStyleOptionS').set_active(True)
        elif self.hud_params['hud_style'] == 'T':
            getattr(self, 'hudStyleOptionT').set_active(True)

        item5 = gtk.MenuItem(_('Set max seats'))
        menu.append(item5)
        maxSeatsMenu = gtk.Menu()
        item5.set_submenu(maxSeatsMenu)
        for i in range(2, 11, 1):
            item = gtk.MenuItem('%d-max' % i)
            item.ms = i
            maxSeatsMenu.append(item)
            item.connect("activate", self.change_max_seats)
            setattr(self, 'maxSeatsMenuItem%d' % (i - 1), item)
            
        return menu


    def set_aggregation(self, widget, val):
        (player_opp, num) = val
        if player_opp == 'P':
            # set these true all the time, set the multiplier to 1 to turn agg off:
            self.hud_params['h_aggregate_ring'] = True
            self.hud_params['h_aggregate_tour'] = True

            if     self.hud_params['h_agg_bb_mult'] != num \
               and getattr(self, 'h_aggBBmultItem'+str(num)).get_active():
                self.hud_params['h_agg_bb_mult'] = num
                for mult in ('1', '2', '3', '10', '10000'):
                    if mult != str(num):
                        getattr(self, 'h_aggBBmultItem'+mult).set_active(False)
        else:
            self.hud_params['aggregate_ring'] = True
            self.hud_params['aggregate_tour'] = True

            if     self.hud_params['agg_bb_mult'] != num \
               and getattr(self, 'aggBBmultItem'+str(num)).get_active():
                self.hud_params['agg_bb_mult'] = num
                for mult in ('1', '2', '3', '10', '10000'):
                    if mult != str(num):
                        getattr(self, 'aggBBmultItem'+mult).set_active(False)


    def set_seats_style(self, widget, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_seats_style'
            prefix = 'h_'
        else:
            param = 'seats_style'
            prefix = ''

        if style == 'A' and getattr(self, prefix+'seatsStyleOptionA').get_active():
            self.hud_params[param] = 'A'
            getattr(self, prefix+'seatsStyleOptionC').set_active(False)
            getattr(self, prefix+'seatsStyleOptionE').set_active(False)
        elif style == 'C' and getattr(self, prefix+'seatsStyleOptionC').get_active():
            self.hud_params[param] = 'C'
            getattr(self, prefix+'seatsStyleOptionA').set_active(False)
            getattr(self, prefix+'seatsStyleOptionE').set_active(False)
        elif style == 'E' and getattr(self, prefix+'seatsStyleOptionE').get_active():
            self.hud_params[param] = 'E'
            getattr(self, prefix+'seatsStyleOptionA').set_active(False)
            getattr(self, prefix+'seatsStyleOptionC').set_active(False)


    def set_hud_style(self, widget, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_hud_style'
            prefix = 'h_'
        else:
            param = 'hud_style'
            prefix = ''

        if style == 'A' and getattr(self, prefix+'hudStyleOptionA').get_active():
            self.hud_params[param] = 'A'
            getattr(self, prefix+'hudStyleOptionS').set_active(False)
            getattr(self, prefix+'hudStyleOptionT').set_active(False)
        elif style == 'S' and getattr(self, prefix+'hudStyleOptionS').get_active():
            self.hud_params[param] = 'S'
            getattr(self, prefix+'hudStyleOptionA').set_active(False)
            getattr(self, prefix+'hudStyleOptionT').set_active(False)
        elif style == 'T' and getattr(self, prefix+'hudStyleOptionT').get_active():
            self.hud_params[param] = 'T'
            getattr(self, prefix+'hudStyleOptionA').set_active(False)
            getattr(self, prefix+'hudStyleOptionS').set_active(False)


    def change_max_seats(self, widget):
        print self.hud.max
        print widget.ms
        if self.hud.max != widget.ms:
            self.hud.max = widget.ms
            self.kill("whatever")

Aux_Hud.Simple_table_mw=Classic_table_mw  ##Aux_Hud instances this class, so must patch MRO in Aux_Hud
                                          ##see FIXME note in Aux_Hud Simple_table_mw init method
                                          
class Classic_popup(Popup.Popup):

    def create(self):
        player_id = None
        for id in self.stat_dict.keys():
            if self.seat == self.stat_dict[id]['seat']:
                player_id = id
        if player_id is None:
            self.destroy_pop()
        popup_text = tip_text = ""
        for stat in self.pop.pu_stats:
            number = Stats.do_stat(self.stat_dict, player = int(player_id), stat = stat)
            popup_text += number[3] + "\n"
            tip_text += number[5] + " " + number[4] + "\n"

        self.lab.set_text(popup_text)
        Stats.do_tip(self.lab, tip_text)
        self.lab.modify_bg(gtk.STATE_NORMAL, self.win.aw.bgcolor)
        self.lab.modify_fg(gtk.STATE_NORMAL, self.win.aw.fgcolor)
        self.show_all()    
