#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Aux_Hud.py

Simple HUD display for FreePokerTools/fpdb HUD.
"""
import L10n
_ = L10n.get_translation()
#    Copyright 2011-2012,  Ray E. Barker
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

#    to do

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import gtk
import pango

#    FreePokerTools modules
import Aux_Base
import Stats
import Popup


class Simple_HUD(Aux_Base.Aux_Seats):
    """A simple HUD class based on the Aux_Window interface."""

    def __init__(self, hud, config, aux_params):
        super(Simple_HUD, self).__init__(hud, config, aux_params)
        
        #    Save everything you need to know about the hud as attrs.
        #    That way a subclass doesn't have to grab them.
        #    Also, the subclass can override any of these attributes

        self.poker_game  = self.hud.poker_game
        self.site_params = self.hud.site_parameters
        self.aux_params  = aux_params
        self.game_params = self.hud.supported_games_parameters["game_stat_set"]
        self.max         = self.hud.max
        self.nrows       = self.game_params.rows
        self.ncols       = self.game_params.cols
        self.xpad        = self.game_params.xpad
        self.ypad        = self.game_params.ypad
        self.xshift      = self.site_params['hud_menu_xshift']
        self.yshift      = self.site_params['hud_menu_yshift']
        self.fgcolor     = gtk.gdk.color_parse(self.aux_params["fgcolor"])
        self.bgcolor     = gtk.gdk.color_parse(self.aux_params["bgcolor"])
        self.opacity     = self.aux_params["opacity"]
        self.font        = pango.FontDescription("%s %s" % (self.aux_params["font"], self.aux_params["font_size"]))
        
        #store these class definitions for use elsewhere
        # this is needed to guarantee that the classes in _this_ module
        # are called, and that some other overriding class is not used.

        self.aw_class_window = Simple_Stat_Window
        self.aw_class_stat = Simple_stat
        self.aw_class_table_mw = Simple_table_mw
        self.aw_class_eb = Simple_eb
        self.aw_class_label = Simple_label

        #    layout is handled by superclass!
        #    retrieve the contents of the stats. popup and tips elements
        #    for future use do this here so that subclasses don't have to bother
        
        self.stats  = [ [None]*self.ncols for i in range(self.nrows) ]
        self.popups = [ [None]*self.ncols for i in range(self.nrows) ]
        self.tips   = [ [None]*self.ncols for i in range(self.nrows) ]

        for stat in self.game_params.stats:
            self.stats[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].stat_name
            self.popups[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].popup
            self.tips[self.game_params.stats[stat].rowcol[0]][self.game_params.stats[stat].rowcol[1]] \
                    = self.game_params.stats[stat].tip
                                        
    def create_contents(self, container, i):
        # this is a call to whatever is in self.aw_class_window but it isn't obvious
        container.create_contents(i)

    def update_contents(self, container, i):
        # this is a call to whatever is in self.aw_class_window but it isn't obvious
        container.update_contents(i)

    def create_common(self, x, y):
        # invokes the simple_table_mw class (or similar)
        self.table_mw = self.aw_class_table_mw(self.hud, aw = self)
        return self.table_mw
        
    def move_windows(self):
        super(Simple_HUD, self).move_windows()
        #
        #tell our mw that an update is needed (normally on table move)
        # custom code here, because we don't use the ['common'] element
        # to control menu position
        self.table_mw.move_windows()

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""

        new_locs = {}
        for (i, pos) in self.positions.iteritems():
            if i != 'common':
                new_locs[self.adj[int(i)]] = ((pos[0]), (pos[1]))
            else:
                #common position belongs to mucked display so, don't alter its location
                pass

        self.config.save_layout_set(self.hud.layout_set, self.hud.max,
                    new_locs ,self.hud.table.width, self.hud.table.height)

        
class Simple_Stat_Window(Aux_Base.Seat_Window):
    """Simple window class for stat windows."""
    
    def __init__(self, aw = None, seat = None):
        super(Simple_Stat_Window, self).__init__(aw, seat)
        self.popup_count = 0
        
    def button_press_left(self, widget, event, *args): #move window
        self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
        
    def button_press_middle(self, widget, event, *args): pass 

    def button_press_right(self, widget, event, *args):  #show pop up

        if widget.stat_dict and self.popup_count == 0: # do not popup on empty blocks or if one is already active
            Popup.popup_factory(
                seat = widget.aw_seat,
                stat_dict = widget.stat_dict,
                win = widget.get_ancestor(gtk.Window),
                pop = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup],
                hand_instance = widget.get_ancestor(gtk.Window).aw.hud.hand_instance,
                config = widget.get_ancestor(gtk.Window).aw.config)
                    
    def create_contents(self, i):
        self.grid = gtk.Table(rows = self.aw.nrows, columns = self.aw.ncols, homogeneous = False)
        self.add(self.grid)
        self.grid.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        self.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        self.stat_box = [ [None]*self.aw.ncols for i in range(self.aw.nrows) ]

        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c] = self.aw.aw_class_stat(self.aw.stats[r][c],
                    seat = self.seat,
                    popup = self.aw.popups[r][c],
                    game_stat_config = self.aw.hud.supported_games_parameters["game_stat_set"].stats[(r,c)],
                    aw = self.aw)
                self.grid.attach(self.stat_box[r][c].widget, c, c+1, r, r+1, xpadding = self.aw.xpad, ypadding = self.aw.ypad)
                self.stat_box[r][c].set_color(self.aw.fgcolor, self.aw.bgcolor)
                self.stat_box[r][c].set_font(self.aw.font)
                self.stat_box[r][c].widget.connect("button_press_event", self.button_press_cb) #setup callback on each stat

    def update_contents(self, i):
        if i == "common": return
        player_id = self.aw.get_id_from_seat(i)
        if player_id is None: return
        for r in xrange(self.aw.nrows):
            for c in xrange(self.aw.ncols):
                self.stat_box[r][c].update(player_id, self.aw.hud.stat_dict)


class Simple_stat(object):
    """A simple class for displaying a single stat."""
    def __init__(self, stat, seat, popup, game_stat_config=None, aw=None):
        self.stat = stat
        self.eb = aw.aw_class_eb()
        self.eb.aw_seat = seat
        self.eb.aw_popup = popup
        self.eb.stat_dict = None
        self.lab = aw.aw_class_label("xxx") # xxx is used as initial value because longer labels don't shrink
        self.eb.add(self.lab)
        self.widget = self.eb
        self.stat_dict = None
        self.hud = aw.hud

    def update(self, player_id, stat_dict):
        self.stat_dict = stat_dict     # So the Simple_stat obj always has a fresh stat_dict
        self.eb.stat_dict = stat_dict
        self.number = Stats.do_stat(stat_dict, player_id, self.stat, self.hud.hand_instance)
        if self.number:
            self.lab.set_text( str(self.number[1]))

    def set_color(self, fg=None, bg=None):
        if fg:
            self.eb.modify_fg(gtk.STATE_NORMAL, fg)
            self.lab.modify_fg(gtk.STATE_NORMAL, fg)
        if bg:
            self.eb.modify_bg(gtk.STATE_NORMAL, bg)
            self.lab.modify_bg(gtk.STATE_NORMAL, bg)

    def set_font(self, font):
        self.lab.modify_font(font)

#    Override thise methods to customize your eb or label
class Simple_eb(gtk.EventBox): pass
class Simple_label(gtk.Label): pass

class Simple_table_mw(Aux_Base.Seat_Window):
    """Create a default table hud main window with a menu."""
#    This is a recreation of the table main window from the default HUD
#    in the old Hud.py. This has the menu options from that hud. 

#    BTW: It might be better to do this with a different AW.

    def __init__(self, hud, aw = None):
        super(Simple_table_mw, self).__init__(aw)
        self.hud = hud
        self.aw = aw
        self.menu_is_popped = False

        #self.connect("configure_event", self.configure_event_cb, "auxmenu") base class will deal with this

        eb = gtk.EventBox()
        try:
            self.menu_label = hud.hud_params['label']
        except:
            self.menu_label = ("fpdb menu")

        lab=gtk.Label(self.menu_label)
        
        eb.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        eb.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)
        lab.modify_bg(gtk.STATE_NORMAL, self.aw.bgcolor)
        lab.modify_fg(gtk.STATE_NORMAL, self.aw.fgcolor)

        self.add(eb)
        eb.add(lab)
        eb.connect_object("button-press-event", self.button_press_cb, self)

        self.move(self.hud.table.x + self.aw.xshift, self.hud.table.y + self.aw.yshift)
                
        eb.show_all()
        #self.menu.show_all() do not attempt to show self.menu !! show its' eb container instead
        #self.show_all() do not do this, it creates oversize eventbox in windows pygtk2.24
        #self.hud.table.topify(self) does not serve any useful purpose, it seems


                     
    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the FPDB main menu event box."""

        if event.button == 3: # right button 
            if not self.menu_is_popped:
                self.menu_is_popped = True
                Simple_table_popup_menu(self)
 
#    button 2 is not handled here because it is the pupup window

        elif event.button == 1:   # left button event -- drag the window
            try:
                self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            except AttributeError:  # in case get_ancestor returns None
                pass
            return True
        return False
    
    def move_windows(self, *args):
        # force menu to the offset position from table origin (do not use common setting)
        self.move(self.hud.table.x + self.aw.xshift, self.hud.table.y + self.aw.yshift)


class Simple_table_popup_menu(gtk.Window):

    def __init__(self, parentwin):
        
        super(Simple_table_popup_menu, self).__init__()
        self.parentwin = parentwin
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_transient_for(parentwin)
        self.set_destroy_with_parent(True)
        self.set_resizable(False)
        self.set_title(self.parentwin.menu_label)
        self.connect("delete_event", self.delete_event)
        self.connect("destroy", self.delete_event)
        vbox=gtk.VBox(homogeneous=False, spacing=3)
        self.add(vbox)

        kill_button = gtk.Button(_('Restart This HUD'))
        kill_button.connect("clicked", self.callback, "kill")
        vbox.pack_start(kill_button)
        kill_button.show()
        
        save_button = gtk.Button(_('Save HUD Layout'))
        save_button.connect("clicked", self.callback, "save")
        vbox.pack_start(save_button)
        save_button.show()        

#    ComboBox - set max seats
        cb_max_combo = gtk.combo_box_new_text()
        vbox.pack_start(cb_max_combo)
        cb_max_dict = {} #[position][screentext, field value]
        cb_max_dict[0] = (_('Set max seats'),None)
        pos = 1
        for i in (sorted(self.parentwin.hud.layout_set.layout)):
            cb_max_dict[pos]= (('%d-max' % i), i)
            pos+=1
        self.build_combo_and_set_active(cb_max_combo, 'new_max_seats', cb_max_dict)
        cb_max_combo.show()

#label
        eb2 = gtk.EventBox()
        lab = gtk.Label(_('Show Player Stats for'))
        eb2.add(lab)
        vbox.pack_start(eb2)
        lab.show(), eb2.show()

#combobox statrange
        stat_range_combo_dict = {} #[position][screentext, field value]
        stat_range_combo_dict[0] = ((_('Since:')+" "+_('All Time')), "A")
        stat_range_combo_dict[1] = ((_('Since:')+" "+_('Session')), "S")
        stat_range_combo_dict[2] = ((_('Since:')+" "+_('%s Days' % "n")), "T")

#combobox multiplier
        multiplier_combo_dict = {}
        multiplier_combo_dict[0] = (_('For This Blind Level Only'), 1)
        multiplier_combo_dict[1] = ((_('%s to %s * Current Blinds') % ("  0.5", "2")), 2)
        multiplier_combo_dict[2] = ((_('%s to %s * Current Blinds') % ("  0.33", "3")), 3)
        multiplier_combo_dict[3] = ((_('%s to %s * Current Blinds') % ("  0.1", "10")), 10)
        multiplier_combo_dict[4] = (_('All Levels'), 10000)
       

#hero_stat_range 
        hsr_combo = gtk.combo_box_new_text()
        vbox.pack_start(hsr_combo)
        self.build_combo_and_set_active(hsr_combo, 'h_hud_style', stat_range_combo_dict)
        hsr_combo.show()

#hero ndays spinbox
        adjustment = gtk.Adjustment(value=self.parentwin.hud.hud_params['h_hud_days'],lower=1, upper=9999, step_incr=1)
        hero_ndays_spin = gtk.SpinButton(adjustment, climb_rate=1, digits=0)
        vbox.pack_start(hero_ndays_spin)
        hero_ndays_spin.show()

#hero multiplier combo
        hmu_combo = gtk.combo_box_new_text()
        vbox.pack_start(hmu_combo)
        self.build_combo_and_set_active(hmu_combo, 'h_agg_bb_mult', multiplier_combo_dict)
        hmu_combo.show()

#label
        eb3 = gtk.EventBox()
        lab = gtk.Label(_('Show Opponent Stats for'))
        eb3.add(lab)
        vbox.pack_start(eb3)
        lab.show(), eb3.show()

#villain_stat_range

        vsr_combo = gtk.combo_box_new_text()
        vbox.pack_start(vsr_combo)
        self.build_combo_and_set_active(vsr_combo, 'hud_style', stat_range_combo_dict)
        vsr_combo.show()

#villain ndays spinbox
        adjustment = gtk.Adjustment(value=self.parentwin.hud.hud_params['hud_days'],lower=1, upper=9999, step_incr=1)
        vndays_spin = gtk.SpinButton(adjustment, climb_rate=1, digits=0)
        vbox.pack_start(vndays_spin)
        vndays_spin.show()

#villain multiplier combo
        vmu_combo = gtk.combo_box_new_text()
        vbox.pack_start(vmu_combo)
        print "kjh ", self.parentwin.hud.hud_params['agg_bb_mult']
        self.build_combo_and_set_active(vmu_combo, 'agg_bb_mult', multiplier_combo_dict)
        vmu_combo.show()


        
        vbox.show()
        self.show()

    def delete_event(self, widget, data=None):
        self.parentwin.menu_is_popped = False
        self.destroy()

    def callback(self, widget, data=None):
        if data == "kill":
            self.parentwin.hud.parent.kill_hud("kill", self.parentwin.hud.table.key)
            
        if data == "save":
            # This calls the save_layout method of the Hud object. The Hud object 
            # then calls the save_layout method in each installed AW.
            self.parentwin.hud.save_layout()
            self.delete_event(widget)

    def build_combo_and_set_active(self, widget, field, combo_dict):
        for pos in combo_dict:
            widget.append_text(combo_dict[pos][0])
            if combo_dict[pos][1] == self.parentwin.hud.hud_params[field]:
                widget.set_active(pos)
        widget.connect("changed", self.change_combo_field_value, field, combo_dict)
                
    def change_combo_field_value(self, widget, field, combo_dict):
        sel = widget.get_active()
        self.parentwin.hud.hud_params[field] = combo_dict[sel][1]
