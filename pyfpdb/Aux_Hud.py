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
    """Create a default table hud menu label"""
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

        lab.show(), eb.show()
        #self.show()
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
        self.set_deletable(False)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.move(self.parentwin.hud.table.x + self.parentwin.aw.xshift,
                  self.parentwin.hud.table.y + self.parentwin.aw.yshift)
        self.set_title(self.parentwin.menu_label)
        self.connect("delete_event", self.delete_event)
        self.connect("destroy", self.delete_event)

#combobox statrange
        stat_range_combo_dict = {} #[position][screentext, field value]
        stat_range_combo_dict[0] = ((_('Since:')+" "+_('All Time')), "A")
        stat_range_combo_dict[1] = ((_('Since:')+" "+_('Session')), "S")
        stat_range_combo_dict[2] = ((_('Since:')+" "+_('n Days')+" - - >"), "T")
#combobox seatsstyle
        seats_style_combo_dict = {} #[position][screentext, field value]
        seats_style_combo_dict[0] = ((_('Number of Seats:')+" "+_('Any Number')), "A")
        seats_style_combo_dict[1] = ((_('Number of Seats:')+" "+_('Custom')), "C")
        seats_style_combo_dict[2] = ((_('Number of Seats:')+" "+_('Exact')), "E")
#combobox multiplier
        multiplier_combo_dict = {}
        multiplier_combo_dict[0] = (_('For This Blind Level Only'), 1)
        multiplier_combo_dict[1] = ((_('%s to %s * Current Blinds') % ("  0.5", "2")), 2)
        multiplier_combo_dict[2] = ((_('%s to %s * Current Blinds') % ("  0.33", "3")), 3)
        multiplier_combo_dict[3] = ((_('%s to %s * Current Blinds') % ("  0.1", "10")), 10)
        multiplier_combo_dict[4] = (_('All Levels'), 10000)
#ComboBox - set max seats
        cb_max_dict = {} #[position][screentext, field value]
        cb_max_dict[0] = (_('Force layout')+'...',None)
        pos = 1
        for i in (sorted(self.parentwin.hud.layout_set.layout)):
            cb_max_dict[pos]= (('%d-max' % i), i)
            pos+=1

        grid = gtk.Table(1,3)
        self.add(grid)
        vbox1=gtk.VBox(homogeneous=False, spacing=3)
        vbox2=gtk.VBox(homogeneous=False, spacing=3)
        vbox3=gtk.VBox(homogeneous=False, spacing=3)
        
        vbox1.pack_start(self.build_button(_('Restart This HUD'), gtk.STOCK_REFRESH, "kill"))
        vbox1.pack_start(self.build_button(_('Save HUD Layout'), gtk.STOCK_SAVE, "save"))
        vbox1.pack_start(self.build_button(_('Stop this HUD'), gtk.STOCK_STOP, "blacklist"))
        vbox1.pack_start(self.build_button(_('Close'), gtk.STOCK_CLOSE, "close"))
        vbox1.pack_start(self.build_label(''))
        vbox1.pack_start(self.build_combo_and_set_active('new_max_seats', cb_max_dict))
        
        vbox2.pack_start(self.build_label(_('Show Player Stats for')))
        vbox2.pack_start(self.build_combo_and_set_active('h_agg_bb_mult', multiplier_combo_dict))
        vbox2.pack_start(self.build_combo_and_set_active('h_seats_style', seats_style_combo_dict))
        hbox=gtk.HBox(homogeneous=False, spacing=3)
        hbox.pack_start(self.build_label(_('Custom')))
        self.h_nums_low_spinner = self.build_spinner('h_seats_cust_nums_low',1,9)
        hbox.pack_start(self.h_nums_low_spinner)
        hbox.pack_start(self.build_label(_('To')))
        self.h_nums_high_spinner = self.build_spinner('h_seats_cust_nums_high',2,10)
        hbox.pack_start(self.h_nums_high_spinner)
        vbox2.add(hbox), hbox.show()
        hbox=gtk.HBox(homogeneous=False, spacing=3)
        hbox.pack_start(self.build_combo_and_set_active('h_stat_range', stat_range_combo_dict))
        self.h_hud_days_spinner = self.build_spinner('h_hud_days',1,9999)
        hbox.pack_start(self.h_hud_days_spinner)
        vbox2.add(hbox), hbox.show()

        vbox3.pack_start(self.build_label(_('Show Opponent Stats for')))
        vbox3.pack_start(self.build_combo_and_set_active('agg_bb_mult', multiplier_combo_dict))
        vbox3.pack_start(self.build_combo_and_set_active('seats_style', seats_style_combo_dict))
        hbox=gtk.HBox(homogeneous=False, spacing=3)
        hbox.pack_start(self.build_label(_('Custom')))
        self.nums_low_spinner = self.build_spinner('seats_cust_nums_low',1,9)
        hbox.pack_start(self.nums_low_spinner)
        hbox.pack_start(self.build_label(_('To')))
        self.nums_high_spinner = self.build_spinner('seats_cust_nums_high',2,10)
        hbox.pack_start(self.nums_high_spinner)
        vbox3.add(hbox), hbox.show()
        hbox=gtk.HBox(homogeneous=False, spacing=3)
        hbox.pack_start(self.build_combo_and_set_active('stat_range', stat_range_combo_dict))
        self.hud_days_spinner = self.build_spinner('hud_days',1,9999)
        hbox.pack_start(self.hud_days_spinner)
        vbox3.add(hbox), hbox.show()

        self.set_spinners_active()

        grid.attach(vbox1, 0, 1, 0, 1)
        grid.attach(vbox2, 1, 2, 0, 1)
        grid.attach(vbox3, 2, 3, 0, 1)

        vbox1.show(), vbox2.show(), vbox3.show()
        grid.show()
        self.show()

    def delete_event(self, widget, data=None):
        self.parentwin.menu_is_popped = False
        self.destroy()
        
    def callback(self, widget, data=None):
        if data == "kill":
            self.parentwin.hud.parent.kill_hud("kill", self.parentwin.hud.table.key)
            return True
        if data == "blacklist":
            self.parentwin.hud.parent.blacklist_hud("kill", self.parentwin.hud.table.key)
            return True
        if data == "save":
            # This calls the save_layout method of the Hud object. The Hud object 
            # then calls the save_layout method in each installed AW.
            self.parentwin.hud.save_layout()
            self.delete_event(widget)
            return True
            
        if data == "close":
            self.delete_event(widget)
            return True

    def build_button(self, labeltext, buttonimage, cbkeyword):
        button = gtk.Button(labeltext)
        image = gtk.Image()
        image.set_from_stock(buttonimage, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.set_alignment(0, 0)   
        button.connect("clicked", self.callback, cbkeyword)
        button.show()
        return button

    def build_label(self, labeltext):
        eb = gtk.EventBox()
        lab = gtk.Label(labeltext)
        eb.add(lab)
        lab.show(), eb.show()
        return eb
        
    def build_spinner(self, field, low, high):
        adjustment = gtk.Adjustment(value=self.parentwin.hud.hud_params[field],lower=low, upper=high, step_incr=1)
        spinner = gtk.SpinButton(adjustment, climb_rate=1, digits=0)
        spinner.connect("value-changed", self.change_spin_field_value, field)
        spinner.show()
        return spinner

    def build_combo_and_set_active(self, field, combo_dict):
        widget = gtk.combo_box_new_text()
        for pos in combo_dict:
            widget.append_text(combo_dict[pos][0])
            if combo_dict[pos][1] == self.parentwin.hud.hud_params[field]:
                widget.set_active(pos)
        widget.connect("changed", self.change_combo_field_value, field, combo_dict)
        widget.show()
        return widget
                
    def change_combo_field_value(self, widget, field, combo_dict):
        sel = widget.get_active()
        self.parentwin.hud.hud_params[field] = combo_dict[sel][1]
        self.set_spinners_active()
                
    def change_spin_field_value(self, widget, field):
        self.parentwin.hud.hud_params[field] = widget.get_value()

    def set_spinners_active(self):
        if self.parentwin.hud.hud_params['h_stat_range'] == "T":
            self.h_hud_days_spinner.set_sensitive(True)
        else:
            self.h_hud_days_spinner.set_sensitive(False)
        if self.parentwin.hud.hud_params['stat_range'] == "T":
            self.hud_days_spinner.set_sensitive(True)
        else:
            self.hud_days_spinner.set_sensitive(False)
        if self.parentwin.hud.hud_params['h_seats_style'] == "C":
            self.h_nums_low_spinner.set_sensitive(True)
            self.h_nums_high_spinner.set_sensitive(True)
        else:
            self.h_nums_low_spinner.set_sensitive(False)
            self.h_nums_high_spinner.set_sensitive(False)
        if self.parentwin.hud.hud_params['seats_style'] == "C":
            self.nums_low_spinner.set_sensitive(True)
            self.nums_high_spinner.set_sensitive(True)
        else:
            self.nums_low_spinner.set_sensitive(False)
            self.nums_high_spinner.set_sensitive(False)
