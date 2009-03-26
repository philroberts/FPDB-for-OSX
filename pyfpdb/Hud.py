#!/usr/bin/env python
"""Hud.py

Create and manage the hud overlays.
"""
#    Copyright 2008, 2009  Ray E. Barker

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
#    Standard Library modules
import os
import sys

#    pyGTK modules
import pygtk
import gtk
import pango
import gobject

#    win32 modules -- only imported on windows systems
if os.name == 'nt':
    import win32gui
    import win32con
    import win32api

#    FreePokerTools modules
import Tables # needed for testing only
import Configuration
import Stats
import Mucked
import Database
import HUD_main

def importName(module_name, name):
    """Import a named object 'name' from module 'module_name'."""
#    Recipe 16.3 in the Python Cookbook, 2nd ed.  Thanks!!!!

    try:
        module = __import__(module_name, globals(), locals(), [name])
    except:
        return None
    return(getattr(module, name))

class Hud:
    
    def __init__(self, parent, table, max, poker_game, config, db_connection):
#    __init__ is (now) intended to be called from the stdin thread, so it
#    cannot touch the gui
        self.parent        = parent
        self.table         = table
        self.config        = config
        self.poker_game    = poker_game
        self.max           = max
        self.db_connection = db_connection
        self.deleted       = False
        self.stacked       = True
        self.site          = table.site
        self.mw_created    = False

        self.stat_windows  = {}
        self.popup_windows = {}
        self.aux_windows   = []
        
        (font, font_size) = config.get_default_font(self.table.site)
        self.colors        = config.get_default_colors(self.table.site)

        if font == None:
            font = "Sans"
        if font_size == None:
            font_size = "8"
        self.font = pango.FontDescription("%s %s" % (font, font_size))
        # do we need to add some sort of condition here for dealing with a request for a font that doesn't exist?

        game_params = config.get_game_parameters(self.poker_game)
        if not game_params['aux'] == [""]:
            for aux in game_params['aux']:
                aux_params = config.get_aux_parameters(aux)
                my_import = importName(aux_params['module'], aux_params['class'])
                if my_import == None:
                    continue
                self.aux_windows.append(my_import(self, config, aux_params))

    def create_mw(self):

#	Set up a main window for this this instance of the HUD
        self.main_window = gtk.Window()
        self.main_window.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.main_window.set_title("%s FPDBHUD" % (self.table.name))
        self.main_window.set_decorated(False)
        self.main_window.set_opacity(self.colors["hudopacity"])
        self.main_window.set_focus_on_map(False)

        self.ebox = gtk.EventBox()
        self.label = gtk.Label("FPDB Menu (Right Click)\nLeft-drag to move")
        
        self.backgroundcolor = gtk.gdk.color_parse(self.colors['hudbgcolor'])
        self.foregroundcolor = gtk.gdk.color_parse(self.colors['hudfgcolor'])
        
        self.label.modify_bg(gtk.STATE_NORMAL, self.backgroundcolor)
        self.label.modify_fg(gtk.STATE_NORMAL, self.foregroundcolor)
        
        self.main_window.add(self.ebox)
        self.ebox.add(self.label)
        
        self.ebox.modify_bg(gtk.STATE_NORMAL, self.backgroundcolor)
        self.ebox.modify_fg(gtk.STATE_NORMAL, self.foregroundcolor)

        self.main_window.move(self.table.x, self.table.y)

#    A popup menu for the main window
        self.menu = gtk.Menu()
        self.item1 = gtk.MenuItem('Kill this HUD')
        self.menu.append(self.item1)
        self.item1.connect("activate", self.parent.kill_hud, self.table.name)
        self.item1.show()
        
        self.item2 = gtk.MenuItem('Save Layout')
        self.menu.append(self.item2)
        self.item2.connect("activate", self.save_layout)
        self.item2.show()
        
        self.item3 = gtk.MenuItem('Reposition Stats')
        self.menu.append(self.item3)
        self.item3.connect("activate", self.reposition_windows)
        self.item3.show()
        
        self.item4 = gtk.MenuItem('Debug Stat Windows')
        self.menu.append(self.item4)
        self.item4.connect("activate", self.debug_stat_windows)
        self.item4.show()
        
        self.ebox.connect_object("button-press-event", self.on_button_press, self.menu)

        self.main_window.show_all()
        self.mw_created = True

# TODO: fold all uses of this type of 'topify' code into a single function, if the differences between the versions don't
# create adverse effects?

        if os.name == 'nt':
            self.topify_window(self.main_window)
        else:
            self.main_window.parentgdkhandle = gtk.gdk.window_foreign_new(int(self.table.number))  # gets a gdk handle for poker client
            self.main_window.gdkhandle = gtk.gdk.window_foreign_new(self.main_window.window.xid) # gets a gdk handle for the hud table window
            self.main_window.gdkhandle.set_transient_for(self.main_window.parentgdkhandle) #
            
        self.update_table_position()
               
    def update_table_position(self):
        if os.name == 'nt':
            if not win32gui.IsWindow(self.table.number):
                self.parent.kill_hud(self, self.table.name)
                return False
        # anyone know how to do this in unix, or better yet, trap the X11 error that is triggered when executing the get_origin() for a closed window?
        
        (x, y) = self.main_window.parentgdkhandle.get_origin()
        if self.table.x != x or self.table.y != y:
            self.table.x = x
            self.table.y = y
            self.main_window.move(x, y)
            adj = self.adj_seats(self.hand, self.config)
            loc = self.config.get_locations(self.table.site, self.max)
            # TODO: is stat_windows getting converted somewhere from a list to a dict, for no good reason?
            for i, w in enumerate(self.stat_windows):
#<<<<<<< HEAD:pyfpdb/Hud.py
                if not type(w) == int: # how do we get pure ints in this list??
                    (x, y) = loc[adj[i]]
                    w.relocate(x, y)
#=======
#                (x, y) = loc[adj[i]]
#                self.stat_windows[w].relocate(x, y)
#                
#>>>>>>> 7c0d2eb6c664cfd8122b975e58438cfd158ee398:pyfpdb/Hud.py
        return True

    def on_button_press(self, widget, event):
        if event.button == 1:
            self.main_window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        if event.button == 3:
            widget.popup(None, None, None, event.button, event.time)
            return True
        return False

    def kill(self, *args):
#    kill all stat_windows, popups and aux_windows in this HUD
#    heap dead, burnt bodies, blood 'n guts, veins between my teeth
        for s in self.stat_windows.itervalues():
            s.kill_popups()
            s.window.destroy()    
        self.stat_windows = {}
#    also kill any aux windows
        (aux.destroy() for aux in self.aux_windows)
        self.aux_windows = []

    def reposition_windows(self, *args):
        if self.stat_windows != {} and len(self.stat_windows) > 0:
            (x.window.move(x.x, x.y) for x in self.stat_windows.itervalues() if type(x) != int)
        return True

    def debug_stat_windows(self, *args):
        print self.table, "\n", self.main_window.window.get_transient_for()
        for w in self.stat_windows:
            print self.stat_windows[w].window.window.get_transient_for()
                
    def save_layout(self, *args):
        new_layout = [(0, 0)] * self.max
        for sw in self.stat_windows:
            loc = self.stat_windows[sw].window.get_position()
            new_loc = (loc[0] - self.table.x, loc[1] - self.table.y)
            new_layout[self.stat_windows[sw].adj - 1] = new_loc
        self.config.edit_layout(self.table.site, self.max, locations = new_layout)
#    ask each aux to save its layout back to the config object
        (aux.save_layout() for aux in self.aux_windows)
#    save the config object back to the file
        print "saving new xml file"
        self.config.save()

    def adj_seats(self, hand, config):

#        Need range here, not xrange -> need the actual list        
        adj = range(0, self.max + 1) # default seat adjustments = no adjustment
#    does the user have a fav_seat?
        if int(config.supported_sites[self.table.site].layout[self.max].fav_seat) > 0:
            try:
                sys.stderr.write("site = %s, max = %d, fav seat = %d\n" % (self.table.site, self.max, config.supported_sites[self.table.site].layout[self.max].fav_seat))
                fav_seat = config.supported_sites[self.table.site].layout[self.max].fav_seat
                sys.stderr.write("found fav seat = %d\n" % fav_seat)
#                actual_seat = self.db_connection.get_actual_seat(hand, config.supported_sites[self.table.site].screen_name)
                actual_seat = self.get_actual_seat(config.supported_sites[self.table.site].screen_name)
                sys.stderr.write("found actual seat = %d\n" % actual_seat)
                for i in xrange(0, self.max + 1):
                    j = actual_seat + i
                    if j > self.max:
                        j = j - self.max
                    adj[j] = fav_seat + i
                    if adj[j] > self.max:
                        adj[j] = adj[j] - self.max
            except Exception, inst:
                sys.stderr.write("exception in adj!!!\n\n")
                sys.stderr.write("error is %s" % inst)           # __str__ allows args to printed directly
        return adj

    def get_actual_seat(self, name):
        for key in self.stat_dict:
            if self.stat_dict[key]['screen_name'] == name:
                return self.stat_dict[key]['seat']
        sys.stderr.write("Error finding actual seat.\n")

    def create(self, hand, config, stat_dict, cards):
#    update this hud, to the stats and players as of "hand"
#    hand is the hand id of the most recent hand played at this table
#
#    this method also manages the creating and destruction of stat
#    windows via calls to the Stat_Window class
        self.hand = hand  
        if not self.mw_created:
            self.create_mw()
            
        self.stat_dict = stat_dict
        self.cards = cards
        sys.stderr.write("------------------------------------------------------------\nCreating hud from hand %s\n" % hand)
        adj = self.adj_seats(hand, config)
        sys.stderr.write("adj = %s\n" % adj)
        loc = self.config.get_locations(self.table.site, self.max)

#    create the stat windows
        for i in xrange(1, self.max + 1):           
            (x, y) = loc[adj[i]]
            if i in self.stat_windows:
                self.stat_windows[i].relocate(x, y)
            else:
                sys.stderr.write("actual seat = %d, x = %d, y= %d\n" % (i, x, y))
                self.stat_windows[i] = Stat_Window(game = config.supported_games[self.poker_game],
                                               parent = self,
                                               table = self.table, 
                                               x = x,
                                               y = y,
                                               seat = i,
                                               adj = adj[i], 
                                               player_id = 'fake',
                                               font = self.font)

        self.stats = []
        game = config.supported_games[self.poker_game]
        
        for i in xrange(0, game.rows + 1):
            row_list = [''] * game.cols
            self.stats.append(row_list)
        for stat in game.stats:
            self.stats[config.supported_games[self.poker_game].stats[stat].row] \
                      [config.supported_games[self.poker_game].stats[stat].col] = \
                      config.supported_games[self.poker_game].stats[stat].stat_name
        
        if os.name == "nt":
            gobject.timeout_add(500, self.update_table_position)
            
    def update(self, hand, config):
        self.hand = hand   # this is the last hand, so it is available later
        if os.name == 'nt':
            self.update_table_position()

        for s in self.stat_dict:
            statd = self.stat_dict[s]
            try:
                self.stat_windows[self.stat_dict[s]['seat']].player_id = self.stat_dict[s]['player_id']
            except: # omg, we have more seats than stat windows .. damn poker sites with incorrect max seating info .. let's force 10 here
                self.max = 10
                self.create(hand, config, self.stat_dict, self.cards)
                self.stat_windows[statd['seat']].player_id = statd['player_id']
                
            for r in xrange(0, config.supported_games[self.poker_game].rows):
                for c in xrange(0, config.supported_games[self.poker_game].cols):
                    this_stat = config.supported_games[self.poker_game].stats[self.stats[r][c]]
                    number = Stats.do_stat(self.stat_dict, player = statd['player_id'], stat = self.stats[r][c])
                    statstring = "%s%s%s" % (this_stat.hudprefix, str(number[1]), this_stat.hudsuffix)
                    window = self.stat_windows[statd['seat']]
                    
                    if this_stat.hudcolor != "":
                        self.label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.colors['hudfgcolor']))
                        window.label[r][c].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(this_stat.hudcolor))
                    
                    window.label[r][c].set_text(statstring)
                    if statstring != "xxx": # is there a way to tell if this particular stat window is visible already, or no?
                        window.window.show_all()
                    tip = "%s\n%s\n%s, %s" % (statd['screen_name'], number[5], number[3], number[4])
                    Stats.do_tip(window.e_box[r][c], tip)

    def topify_window(self, window):
        """Set the specified gtk window to stayontop in MS Windows."""

        def windowEnumerationHandler(hwnd, resultList):
            '''Callback for win32gui.EnumWindows() to generate list of window handles.'''
            resultList.append((hwnd, win32gui.GetWindowText(hwnd)))

        unique_name = 'unique name for finding this window'
        real_name = window.get_title()
        window.set_title(unique_name)
        tl_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, tl_windows)
        
        for w in tl_windows:
            if w[1] == unique_name:
                self.main_window.parentgdkhandle = gtk.gdk.window_foreign_new(long(self.table.number))
                self.main_window.gdkhandle = gtk.gdk.window_foreign_new(w[0])
                self.main_window.gdkhandle.set_transient_for(self.main_window.parentgdkhandle)
                
                style = win32gui.GetWindowLong(self.table.number, win32con.GWL_EXSTYLE)
                style |= win32con.WS_CLIPCHILDREN
                win32gui.SetWindowLong(self.table.number, win32con.GWL_EXSTYLE, style)
                break
            
        window.set_title(real_name)

class Stat_Window:

    def button_press_cb(self, widget, event, *args):
#    This handles all callbacks from button presses on the event boxes in 
#    the stat windows.  There is a bit of an ugly kludge to separate single-
#    and double-clicks.

        if event.button == 3:   # right button event
            self.popups.append(Popup_window(widget, self))

        if event.button == 2:   # middle button event
            self.window.hide()

        if event.button == 1:   # left button event
            # TODO: make position saving save sizes as well?
            if event.state & gtk.gdk.SHIFT_MASK:
                self.window.begin_resize_drag(gtk.gdk.WINDOW_EDGE_SOUTH_EAST, event.button, int(event.x_root), int(event.y_root), event.time)
            else:
                self.window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def kill_popup(self, popup):
        popup.window.destroy()
        self.popups.remove(popup)
        
    def kill_popups(self):
        map(lambda x: x.window.destroy(), self.popups)
        self.popups = { }

    def relocate(self, x, y):
        self.x = x + self.table.x
        self.y = y + self.table.y
        self.window.move(self.x, self.y)

    def __init__(self, parent, game, table, seat, adj, x, y, player_id, font):
        self.parent = parent        # Hud object that this stat window belongs to
        self.game = game            # Configuration object for the curren
        self.table = table          # Table object where this is going
        self.seat = seat            # seat number of his player
        self.adj = adj              # the adjusted seat number for this player
        self.x = x + table.x        # table.x and y are the location of the table
        self.y = y + table.y        # x and y are the location relative to table.x & y
        self.player_id = player_id  # looks like this isn't used ;)
        self.sb_click = 0           # used to figure out button clicks
        self.popups = []            # list of open popups for this stat window
        self.useframes = parent.config.get_frames(parent.site)

        self.window = gtk.Window()
        self.window.set_decorated(0)
        self.window.set_gravity(gtk.gdk.GRAVITY_STATIC)

        self.window.set_title("%s" % seat)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_transient_for(parent.main_window)
        self.window.set_focus_on_map(False)

        grid = gtk.Table(rows = game.rows, columns = game.cols, homogeneous = False)
        self.grid = grid    
        self.window.add(grid)
        self.window.modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
        
        self.e_box = []
        self.frame = []
        self.label = []
        usegtkframes = self.useframes
        e_box = self.e_box
        label = self.label
        for r in xrange(game.rows):
            if usegtkframes:
                self.frame.append([])
            e_box.append([])
            label.append([])
            for c in xrange(game.cols):
                if usegtkframes:
                    self.frame[r].append( gtk.Frame() )
                e_box[r].append( gtk.EventBox() )
                
                e_box[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                e_box[r][c].modify_fg(gtk.STATE_NORMAL, parent.foregroundcolor)
                
                Stats.do_tip(e_box[r][c], 'stuff')
                if usegtkframes:
                    grid.attach(self.frame[r][c], c, c+1, r, r+1, xpadding = 0, ypadding = 0)
                    self.frame[r][c].add(e_box[r][c])
                else:
                    grid.attach(e_box[r][c], c, c+1, r, r+1, xpadding = 0, ypadding = 0)
                label[r].append( gtk.Label('xxx') )
                
                if usegtkframes:
                    self.frame[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                label[r][c].modify_bg(gtk.STATE_NORMAL, parent.backgroundcolor)
                label[r][c].modify_fg(gtk.STATE_NORMAL, parent.foregroundcolor)

                e_box[r][c].add(self.label[r][c])
                e_box[r][c].connect("button_press_event", self.button_press_cb)
                label[r][c].modify_font(font)

        self.window.set_opacity(parent.colors['hudopacity'])
        
        self.window.move(self.x, self.y)
                   
        self.window.hide()

def destroy(*args):             # call back for terminating the main eventloop
    gtk.main_quit()

class Popup_window:
    def __init__(self, parent, stat_window):
        self.sb_click = 0
        self.stat_window = stat_window

#    create the popup window
        self.window = gtk.Window()
        self.window.set_decorated(0)
        self.window.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.window.set_title("popup")
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_transient_for(parent.get_toplevel())
        
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        
        self.ebox = gtk.EventBox()
        self.ebox.connect("button_press_event", self.button_press_cb)
        self.lab  = gtk.Label("stuff\nstuff\nstuff")

#    need an event box so we can respond to clicks
        self.window.add(self.ebox)
        self.ebox.add(self.lab)
        
        self.ebox.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.ebox.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)
        self.window.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.window.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)
        self.lab.modify_bg(gtk.STATE_NORMAL, stat_window.parent.backgroundcolor)
        self.lab.modify_fg(gtk.STATE_NORMAL, stat_window.parent.foregroundcolor)
        
#    figure out the row, col address of the click that activated the popup
        row = 0
        col = 0
        for r in xrange(0, stat_window.game.rows):
            for c in xrange(0, stat_window.game.cols):
                if stat_window.e_box[r][c] == parent:
                    row = r
                    col = c
                    break

#    figure out what popup format we're using
        popup_format = "default"
        for stat in stat_window.game.stats:
            if stat_window.game.stats[stat].row == row and stat_window.game.stats[stat].col == col:
                popup_format = stat_window.game.stats[stat].popup
                break

#    get the list of stats to be presented from the config
        stat_list = []
        for w in stat_window.parent.config.popup_windows:
            if w == popup_format:
                stat_list = stat_window.parent.config.popup_windows[w].pu_stats
                break

#    get a database connection
#        db_connection = Database.Database(stat_window.parent.config, stat_window.parent.db_name, 'temp')
    
#    calculate the stat_dict and then create the text for the pu
#        stat_dict = db_connection.get_stats_from_hand(stat_window.parent.hand, stat_window.player_id)
#        stat_dict = self.db_connection.get_stats_from_hand(stat_window.parent.hand)
#        db_connection.close_connection()
        stat_dict = stat_window.parent.stat_dict
        pu_text = ""
        for s in stat_list:
            number = Stats.do_stat(stat_dict, player = int(stat_window.player_id), stat = s)
            pu_text += number[3] + "\n"

        self.lab.set_text(pu_text)        
        self.window.show_all()
        
        self.window.set_transient_for(stat_window.window)

        if os.name == 'nt':
            self.topify_window(self.window)

    def button_press_cb(self, widget, event, *args):
#    This handles all callbacks from button presses on the event boxes in 
#    the popup windows.  There is a bit of an ugly kludge to separate single-
#    and double-clicks.  This is the same code as in the Stat_window class
        if event.button == 1:   # left button event
            pass

        if event.button == 2:   # middle button event
            pass

        if event.button == 3:   # right button event
            self.stat_window.kill_popup(self)
#            self.window.destroy()

    def toggle_decorated(self, widget):
        top = widget.get_toplevel()
        (x, y) = top.get_position()
                    
        if top.get_decorated():
            top.set_decorated(0)
            top.move(x, y)
        else:
            top.set_decorated(1)
            top.move(x, y)

    def topify_window(self, window):
        """Set the specified gtk window to stayontop in MS Windows."""

        def windowEnumerationHandler(hwnd, resultList):
            '''Callback for win32gui.EnumWindows() to generate list of window handles.'''
            resultList.append((hwnd, win32gui.GetWindowText(hwnd)))

        unique_name = 'unique name for finding this window'
        real_name = window.get_title()
        window.set_title(unique_name)
        tl_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, tl_windows)
        
        for w in tl_windows:
            if w[1] == unique_name:
                window.set_transient_for(self.parent.main_window)               
                style = win32gui.GetWindowLong(self.table.number, win32con.GWL_EXSTYLE)
                style |= win32con.WS_CLIPCHILDREN
                win32gui.SetWindowLong(self.table.number, win32con.GWL_EXSTYLE, style)
                break
                
        window.set_title(real_name)

if __name__== "__main__":
    main_window = gtk.Window()
    main_window.connect("destroy", destroy)
    label = gtk.Label('Fake main window, blah blah, blah\nblah, blah')
    main_window.add(label)
    main_window.show_all()
    
    c = Configuration.Config()
    #tables = Tables.discover(c)
    t = Tables.discover_table_by_name(c, "Motorway")
    if t is None:
        print "Table not found."
    db = Database.Database(c, 'fpdb', 'holdem')

#    for t in tables:
    win = Hud(t, 10, 'holdem', c, db)
    win.create(1, c)
#        t.get_details()
    win.update(8300, db, c)

    gtk.main()
