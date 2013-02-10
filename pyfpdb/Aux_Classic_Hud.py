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

#    pyGTK modules
import gtk

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
        self.aw_class_eb = Classic_eb
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
            self.set_opacity(float(self.aw.params['opacity'])*0.3)
        else:
            #player dealt-in, force display of stat block
            #need to call move() to re-establish window position
            self.move(self.aw.positions[i][0]+self.aw.hud.table.x,
                        self.aw.positions[i][1]+self.aw.hud.table.y)
            self.set_opacity(float(self.aw.params['opacity']))
            # show item, just in case it was hidden by the user
            self.show()
            
    def button_press_middle(self, widget, event, *args):
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
        
        statstring = "%s%s%s" % (self.hudprefix, str(self.number[1]), self.hudsuffix)
        self.lab.set_text(statstring)
        
        tip = "%s\n%s\n%s, %s" % (stat_dict[player_id]['screen_name'], self.number[5], self.number[3], self.number[4])
        Stats.do_tip(self.widget, tip)


class Classic_eb(Aux_Hud.Simple_eb): pass
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
    def __init__(self, hud, aw = None):
        self.hud = hud
        self.aw = aw
        self.hud_params = hud.hud_params
        self.menu_label = hud.hud_params['label']

        super(Classic_table_mw, self).__init__(hud, aw)

    def create_menu_items(self, menu):

        killitem = gtk.MenuItem(_('Restart This HUD'))
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
            if   "aggBB" in attrname: item.connect("activate", self.set_aggregation, cb_params)
            elif "seatsStyle" in attrname: item.connect("activate", self.set_seats_style, cb_params)
            elif "hudStyle" in attrname: item.connect("activate", self.set_hud_style, cb_params)
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
        build_aggmenu(("  " + _('%s Days') % (self.hud_params['hud_days'])),('O','T'), 'hudStyleOptionT')
        
        item5 = gtk.MenuItem(_('Set max seats'))
        menu.append(item5)
        maxSeatsMenu = gtk.Menu()
        item5.set_submenu(maxSeatsMenu)
        for i in (sorted(self.hud.layout_set.layout)):
            item = gtk.MenuItem('%d-max' % i)
            item.ms = i
            maxSeatsMenu.append(item)
            item.connect("activate", self.change_max_seats)
            setattr(self, 'maxSeatsMenuItem%d' % (i - 1), item)

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
            
        return menu


    def set_aggregation(self, widget, val):
        (player_opp, num) = val
        
        if player_opp == 'P':
            # set these true all the time, set the multiplier to 1 to turn agg off:
            self.hud_params['h_aggregate_ring'] = True
            self.hud_params['h_aggregate_tour'] = True

            if self.hud_params['h_agg_bb_mult'] != num:
                if getattr(self, 'h_aggBBmultItem'+str(num)).get_active():
                    self.hud_params['h_agg_bb_mult'] = num
                    for mult in ('1', '2', '3', '10', '10000'):
                        if mult != str(num):
                            getattr(self, 'h_aggBBmultItem'+mult).set_active(False)
                        else:
                            getattr(self, 'h_aggBBmultItem'+mult).set_active(True)
            else:
                # do not allow current item to be switched off
                getattr(self, 'h_aggBBmultItem'+str(num)).set_active(True)
        else:
            self.hud_params['aggregate_ring'] = True
            self.hud_params['aggregate_tour'] = True

            if self.hud_params['agg_bb_mult'] != num:
                if getattr(self, 'aggBBmultItem'+str(num)).get_active():
                    self.hud_params['agg_bb_mult'] = num
                    for mult in ('1', '2', '3', '10', '10000'):
                        if mult != str(num):
                            getattr(self, 'aggBBmultItem'+mult).set_active(False)
            else:
                # do not allow current item to be switched off
                getattr(self, 'aggBBmultItem'+str(num)).set_active(True)

    def set_seats_style(self, widget, val):
        (player_opp, style) = val
        if player_opp == 'P':
            param = 'h_seats_style'
            prefix = 'h_'
        else:
            param = 'seats_style'
            prefix = ''
            
        # do not allow current item to be switched off
        if style == self.hud_params[param]:
            if not getattr(self, prefix+'seatsStyleOption'+style).get_active():
                getattr(self, prefix+'seatsStyleOption'+style).set_active(True)
                return

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

        # do not allow current item to be switched off
        if style == self.hud_params[param]:
            if not getattr(self, prefix+'hudStyleOption'+style).get_active():
                getattr(self, prefix+'hudStyleOption'+style).set_active(True)
                return
                
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
        self.hud_params['new_max_seats'] = widget.ms
                                          
