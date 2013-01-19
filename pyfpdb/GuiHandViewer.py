#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Maxime Grandchamp
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
#


# This code once was in GuiReplayer.py and was split up in this and the former by zarturo.

import L10n
_ = L10n.get_translation()


import Hand
import Card
import Configuration
import Database
import SQL
import Filters
import Deck

import pygtk
pygtk.require('2.0')
import gtk
import math
import gobject

from cStringIO import StringIO

import copy

import GuiReplayer

import pprint
pp = pprint.PrettyPrinter(indent=4)

# The ListView renderer data function requires a function signature of
# renderer_cell_func(tree_column, cell, model, tree_iter, data)
# Placing the function into the Replayer object changes the call singature
# card_images has been made global to facilitate this.

global card_images
card_images = 53 * [0]

def card_renderer_cell_func(tree_column, cell, model, tree_iter, data):
    card_width  = 30
    card_height = 42
    col = data
    coldata = model.get_value(tree_iter, col)
    if coldata == None or coldata == '':
        coldata = "0x"
    coldata = coldata.replace("'","")
    coldata = coldata.replace("[","")
    coldata = coldata.replace("]","")
    coldata = coldata.replace("'","")
    coldata = coldata.replace(",","")
    #print "DEBUG: coldata: %s" % (coldata)
    cards = [Card.encodeCard(c) for c in coldata.split(' ')]
    n_cards = len(cards)

    #print "DEBUG: cards: %s" % cards
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, card_width * n_cards, card_height)
    if pixbuf:
        x = 0 # x coord where the next card starts in scratch
        for card in cards:
            if card == None or card ==0:
                card_images[0].copy_area(0, 0, card_width, card_height, pixbuf, x, 0)

            card_images[card].copy_area(0, 0, card_width, card_height, pixbuf, x, 0)
            x = x + card_width
    cell.set_property('pixbuf', pixbuf)


# This function is a duplicate of 'ledger_style_render_func' in GuiRingPlayerStats
# TODO: Pull generic cell formatting functions into something common.
def cash_renderer_cell_func(tree_column, cell, model, tree_iter, data):
    col = data
    coldata = model.get_value(tree_iter, col)
    if '-' in coldata:
        coldata = coldata.replace("-", "")
        coldata = "(%s)" %(coldata)
        cell.set_property('foreground', 'red')
    else:
        cell.set_property('foreground', 'darkgreen')
    cell.set_property('text', coldata)
    
def reset_style_render_func(tree_column, cell, model, iter, data):
    cell.set_property('foreground', None)
    cell.set_property('text', model.get_value(iter, data))


class GuiHandViewer:
    def __init__(self, config, querylist, mainwin, options = None, debug=True):
        self.debug = debug
        self.config = config
        self.main_window = mainwin
        self.sql = querylist
        self.replayer = None
        self.date_from = None
        self.date_to = None

        # These are temporary variables until it becomes possible
        # to select() a Hand object from the database
        self.site="PokerStars"

        self.db = Database.Database(self.config, sql=self.sql)

        
        filters_display = { "Heroes"    : True,
                    "Sites"     : True,
                    "Games"     : True,
                    "Currencies": False,
                    "Limits"    : True,
                    "LimitSep"  : True,
                    "LimitType" : True,
                    "Positions" : True,
                    "Type"      : True,
                    "Seats"     : False,
                    "SeatSep"   : False,
                    "Dates"     : True,
                    "Cards"     : True,
                    "Groups"    : False,
                    "GroupsAll" : False,
                    "Button1"   : True,
                    "Button2"   : False
                  }
        
        self.filters = Filters.Filters(self.db, self.config, self.sql, display = filters_display)
        self.filters.registerButton1Name(_("Load Hands"))
        self.filters.registerButton1Callback(self.loadHands)
        self.filters.registerCardsCallback(self.filter_cards_cb)
        #self.filters.registerButton2Name(_("temp"))
        #self.filters.registerButton2Callback(self.temp())

        # hierarchy:  self.mainHBox / self.hpane / self.handsVBox / self.area

        self.mainHBox = gtk.HBox(False, 0)
        self.mainHBox.show()

        self.leftPanelBox = self.filters.get_vbox()

        self.hpane = gtk.HPaned()
        self.hpane.pack1(self.leftPanelBox)
        self.mainHBox.add(self.hpane)

        self.handsVBox = gtk.VBox(False, 0)
        self.handsVBox.show()

        self.hpane.pack2(self.handsVBox)
        self.hpane.show()

        self.playing = False

        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        #NOTE: There are two caches of card images as I haven't found a way to
        #      replicate the copy_area() function from Pixbuf in the Pixmap class
        #      cardImages is used for the tables display card_images is used for the
        #      table display. Sooner or later we should probably use one or the other.
        self.deck_instance = Deck.Deck(self.config, height=42, width=30)
        card_images = self.init_card_images(self.config)
       
    def init_card_images(self, config):
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)

        for j in range(0, 13):
            for i in range(0, 4):
                loc = Card.cardFromValueSuit(ranks[j], suits[i])
                card_image = self.deck_instance.card(suits[i], ranks[j])
                #must use copy(), method_instance not usable in global variable
                card_images[loc] = card_image.copy()
        back_image = self.deck_instance.back()
        card_images[0] = back_image.copy()
        return card_images

    def loadHands(self, button, userdata):
        hand_ids = self.get_hand_ids_from_date_range(self.filters.getDates()[0], self.filters.getDates()[1])
        self.reload_hands(hand_ids)

    def get_hand_ids_from_date_range(self, start, end, save_date = False):
        """Returns the handids in the given date range and in the filters. 
            Set save_data to true if you want to keep the start and end date if no other date is specified through the filters by the user."""
            
        if save_date:
            self.date_from = start
            self.date_to = end
        else:
            if start != self.filters.MIN_DATE:  #if date is ever changed by the user previously saved dates are deleted
                self.date_from = None
            if end != self.filters.MAX_DATE:
                self.date_to = None
            
        if self.date_from != None and start == self.filters.MIN_DATE:
            start = self.date_from
            
        if self.date_to != None and end == self.filters.MAX_DATE:
            end = self.date_to

        q = self.db.sql.query['handsInRange']
        q = q.replace('<datetest>', "between '" + start + "' and '" + end + "'")
        q = self.filters.replace_placeholders_with_filter_values(q)

        c = self.db.get_cursor()

        c.execute(q)
        return [r[0] for r in c.fetchall()]

    def rankedhand(self, hand, game):
        ranks = {'0':0, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
        suits = {'x':0, 's':1, 'c':2, 'd':3, 'h':4}

        if game == 'holdem':
            card1 = ranks[hand[0]]
            card2 = ranks[hand[3]]
            suit1 = suits[hand[1]]
            suit2 = suits[hand[4]]
            if card1 < card2:
                (card1, card2) = (card2, card1)
                (suit1, suit2) = (suit2, suit1)
            if suit1 == suit2:
                suit1 += 4
            return card1 * 14 * 14 + card2 * 14 + suit1
        else:
            return 0

    def sorthand(self, model, iter1, iter2):
        hand1 = self.hands[int(model.get_value(iter1, self.colnum['HandId']))]         
        hand2 = self.hands[int(model.get_value(iter2, self.colnum['HandId']))]
        base1 = hand1.gametype['base']
        base2 = hand2.gametype['base']
        if base1 < base2:
            return -1
        elif base1 > base2:
            return 1

        cat1 = hand1.gametype['category']
        cat2 = hand2.gametype['category']
        if cat1 < cat2:
            return -1
        elif cat1 > cat2:
            return 1

        a = self.rankedhand(model.get_value(iter1, 0), hand1.gametype['category'])
        b = self.rankedhand(model.get_value(iter2, 0), hand2.gametype['category'])
        
        if a < b:
            return -1
        elif a > b:
            return 1

        return 0

    def sort_float(self, model, iter1, iter2, col):
        a = float(model.get_value(iter1, col))
        b = float(model.get_value(iter2, col))

        if a < b:
            return -1
        elif a > b:
            return 1
        
        return 0
    
    def sort_pos(self, model, iter1, iter2, col):
        a = self.__get_sortable_int_from_pos__(model.get_value(iter1, col))
        b = self.__get_sortable_int_from_pos__(model.get_value(iter2, col))
        
        if a < b:
            return -1
        elif a > b:
            return 1
        
        return 0
        
    def __get_sortable_int_from_pos__(self, pos):
        if pos == 'B':
            return 8
        if pos == 'S':
            return 9
        else:
            return int(pos)
    
    def reload_hands(self, handids):
        self.hands = {}
        for handid in handids:
            self.hands[handid] = self.importhand(handid)
        self.refreshHands()
    
    def copyHandToClipboard(self, view, event, hand):
        handText = StringIO()
        hand.writeHand(handText)
        clipboard = gtk.Clipboard(display=gtk.gdk.display_get_default(), selection="CLIPBOARD")
        clipboard.set_text(handText.getvalue(), len=-1)

    def contextMenu(self, view, event):
        if(event.button != 3):
            return False
        coords = event.get_coords()
        path = view.get_path_at_pos(int(coords[0]), int(coords[1]))
        model = view.get_model()
        hand = self.hands[int(model.get_value(model.get_iter(path[0]), self.colnum['HandId']))]
        m = gtk.Menu()
        i = gtk.MenuItem('Copy to clipboard')
        i.connect('button-press-event', self.copyHandToClipboard, hand)
        i.show()
        m.append(i)
        m.popup(None, None, None, event.button, event.time, None)
        return False

    def refreshHands(self):
        try:
            self.handsWindow.destroy()
        except:
            pass
        self.handsWindow = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.handsWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.handsVBox.pack_end(self.handsWindow)

        # Dict of colnames and their column idx in the model/ListStore
        self.colnum = {
                  'Stakes'       : 0,
                  'Pos'          : 1,
                  'Street0'      : 2,
                  'Action0'      : 3,
                  'Street1-4'    : 4,
                  'Action1-4'    : 5,
                  'Won'          : 6,
                  'Bet'          : 7,
                  'Net'          : 8,
                  'Game'         : 9,
                  'HandId'       : 10,
                 }
        self.liststore = gtk.ListStore(*([str] * len(self.colnum)))
        self.view = gtk.TreeView()
        self.view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.handsWindow.add(self.view)

        #self.viewfilter = self.liststore.filter_new()                  #if a filter is used, the sorting doesnt work anymore!! As GtkTreeModelFilter does NOT implement GtkTreeSortable
        #self.view.set_model(self.viewfilter)
        self.view.set_model(self.liststore)
        textcell = gtk.CellRendererText()
        numcell = gtk.CellRendererText()
        numcell.set_property('xalign', 1.0)
        pixbuf   = gtk.CellRendererPixbuf()
        pixbuf.set_property('xalign', 0.0)

        self.view.insert_column_with_data_func(-1, 'Stakes', textcell, reset_style_render_func ,self.colnum['Stakes'])
        self.view.insert_column_with_data_func(-1, 'Pos', textcell, reset_style_render_func ,self.colnum['Pos'])
        self.view.insert_column_with_data_func(-1, 'Street 0', pixbuf, card_renderer_cell_func, self.colnum['Street0'])
        self.view.insert_column_with_data_func(-1, 'Action 0', textcell, reset_style_render_func ,self.colnum['Action0'])
        self.view.insert_column_with_data_func(-1, 'Street 1-4', pixbuf, card_renderer_cell_func, self.colnum['Street1-4'])
        self.view.insert_column_with_data_func(-1, 'Action 1-4', textcell, reset_style_render_func ,self.colnum['Action1-4'])
        self.view.insert_column_with_data_func(-1, 'Won', numcell, reset_style_render_func, self.colnum['Won'])
        self.view.insert_column_with_data_func(-1, 'Bet', numcell, reset_style_render_func, self.colnum['Bet'])
        self.view.insert_column_with_data_func(-1, 'Net', numcell, cash_renderer_cell_func, self.colnum['Net'])
        self.view.insert_column_with_data_func(-1, 'Game', textcell, reset_style_render_func ,self.colnum['Game'])
        
        self.liststore.set_sort_func(self.colnum['Street0'], self.sorthand)
        self.liststore.set_sort_func(self.colnum['Pos'], self.sort_pos, self.colnum['Pos'])
        self.liststore.set_sort_func(self.colnum['Net'], self.sort_float, self.colnum['Net'])
        self.liststore.set_sort_func(self.colnum['Bet'], self.sort_float, self.colnum['Bet'])
        self.view.get_column(self.colnum['Street0']).set_sort_column_id(self.colnum['Street0'])
        self.view.get_column(self.colnum['Net']).set_sort_column_id(self.colnum['Net'])
        self.view.get_column(self.colnum['Bet']).set_sort_column_id(self.colnum['Bet'])
        self.view.get_column(self.colnum['Pos']).set_sort_column_id(self.colnum['Pos'])

        #selection = self.view.get_selection()
        #selection.set_select_function(self.select_hand, None, True)     #listen on selection (single click)
        self.view.connect('row-activated', self.row_activated)           #listen to double klick
        self.view.connect('button-press-event', self.contextMenu)

        for handid, hand in self.hands.items():
            hero = self.filters.getHeroes()[hand.sitename]
            won = 0
            if hero in hand.collectees.keys():
                won = hand.collectees[hero]
            bet = 0
            if hero in hand.pot.committed.keys():
                bet = hand.pot.committed[hero]
            net = won - bet
            pos = hand.get_player_position(hero)
            gt =  hand.gametype['category']
            row = []
            if hand.gametype['base'] == 'hold':
                board =  []
                board.extend(hand.board['FLOP'])
                board.extend(hand.board['TURN'])
                board.extend(hand.board['RIVER'])
                
                pre_actions = hand.get_actions_short(hero, 'PREFLOP')
                post_actions = ''
                if 'F' not in pre_actions:      #if player hasen't folded preflop
                    post_actions = hand.get_actions_short_streets(hero, 'FLOP', 'TURN', 'RIVER')
                
                row = [hand.getStakesAsString(), pos, hand.join_holecards(hero), pre_actions, ' '.join(board), post_actions, str(won), str(bet), 
                       str(net), gt, handid]
                
            elif hand.gametype['base'] == 'stud':
                third = " ".join(hand.holecards['THIRD'][hero][0]) + " " + " ".join(hand.holecards['THIRD'][hero][1]) 
                #ugh - fix the stud join_holecards function so we can retrieve sanely
                later_streets= []
                later_streets.extend(hand.holecards['FOURTH'] [hero][0])
                later_streets.extend(hand.holecards['FIFTH']  [hero][0])
                later_streets.extend(hand.holecards['SIXTH']  [hero][0])
                later_streets.extend(hand.holecards['SEVENTH'][hero][0])
                
                pre_actions = hand.get_actions_short(hero, 'THIRD')
                post_actions = ''
                if 'F' not in pre_actions:
                    post_actions = hand.get_actions_short_streets(hero, 'FOURTH', 'FIFTH', 'SIXTH', 'SEVENTH')
                    
                row = [hand.getStakesAsString(), pos, third, pre_actions, ' '.join(later_streets), post_actions, str(won), str(bet), str(net), 
                       gt, handid]
                
            elif hand.gametype['base'] == 'draw':
                row = [hand.getStakesAsString(), pos, hand.join_holecards(hero,street='DEAL'), hand.get_actions_short(hero, 'DEAL'), None, None, 
                       str(won), str(bet), str(net), gt, handid]
            
            if self.is_row_in_card_filter(row):
                self.liststore.append(row)
        #self.viewfilter.set_visible_func(self.viewfilter_visible_cb)
        self.handsWindow.show_all()

    def filter_cards_cb(self, card):
        if hasattr(self, 'hands'):     #Do not call refresh if only filters are refreshed and no hands have been loaded yet
            self.refreshHands()
        #self.viewfilter.refilter()    #As the sorting doesnt work if this is used, a refresh is needed.

    def is_row_in_card_filter(self, row):
        """ Returns true if the cards of the given row are in the card filter """
        #Does work but all cards that should NOT be displayed have to be clicked.
        card_filter = self.filters.getCards() 
        hcs = row[self.colnum['Street0']].split(' ')
        
        if '0x' in hcs:      #if cards are unknown return True
            return True
        
        gt = row[self.colnum['Game']]

        if gt not in ('holdem', 'omahahi', 'omahahilo'): return True
        # Holdem: Compare the real start cards to the selected filter (ie. AhKh = AKs)
        value1 = Card.card_map[hcs[0][0]]
        value2 = Card.card_map[hcs[1][0]]
        idx = Card.twoStartCards(value1, hcs[0][1], value2, hcs[1][1])
        abbr = Card.twoStartCardString(idx)
        return False if card_filter[abbr] == False else True

    #def select_hand(self, selection, model, path, is_selected, userdata):    #function head for single click event
    def row_activated(self, view, path, column):
        model = view.get_model()
        hand = self.hands[int(model.get_value(model.get_iter(path), self.colnum['HandId']))]
        if hand.gametype['currency']=="USD":    #TODO: check if there are others ..
            currency="$"
        elif hand.gametype['currency']=="EUR":
            currency="\xe2\x82\xac"
        elif hand.gametype['currency']=="GBP":
            currency="£"
        else:
            currency = hand.gametype['currency']
            
        replayer = GuiReplayer.GuiReplayer(self.config, self.sql, self.main_window)

        replayer.currency = currency
        replayer.play_hand(hand)
        return True


    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox


    def importhand(self, handid=1):
        # Fetch hand info
        # We need at least sitename, gametype, handid
        # for the Hand.__init__

        h = Hand.hand_factory(handid, self.config, self.db)

        # Set the hero for this hand using the filter for the sitename of this hand
        h.hero = self.filters.getHeroes()[h.sitename]
        return h

    '''
    #This code would use pango markup instead of pix for the cards and renderers
    
    def refreshHands(self, handids):
        self.hands = {}
        for handid in handids:
            self.hands[handid] = self.importhand(handid)

        try:
            self.handsWindow.destroy()
        except:
            pass
        self.handsWindow = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.handsWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.handsVBox.pack_end(self.handsWindow)
        cols = [
                str,    # Street0 cards
                str,    # Street1 cards
                str,    # Street2 cards
                str,    # Street3 cards
                str,    # Street4 cards
                str,    # Net
                str,    # Gametype
                str,    # Hand Id
                ]
        # Dict of colnames and their column idx in the model/ListStore
        self.colnum = {
                  'Street0'      : 0,
                  'Street1'      : 1,
                  'Street2'      : 2,
                  'Street3'      : 3,
                  'Street4'      : 4,
                  '+/-'          : 5,
                  'Game'         : 6,
                  'HID'          : 7,
                 }
        self.liststore = gtk.ListStore(*cols)
        self.view = gtk.TreeView()
        self.view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.handsWindow.add(self.view)

        self.viewfilter = self.liststore.filter_new()
        self.view.set_model(self.viewfilter)
        text = gtk.CellRendererText()

        self.view.insert_column_with_attributes(-1, 'Street 0', text, markup = self.colnum['Street0'])
        self.view.insert_column_with_attributes(-1, 'Street 1', text, markup = self.colnum['Street1'])
        self.view.insert_column_with_attributes(-1, 'Street 2', text, markup = self.colnum['Street2'])
        self.view.insert_column_with_attributes(-1, 'Street 3', text, markup = self.colnum['Street3'])
        self.view.insert_column_with_attributes(-1, 'Street 4', text, markup = self.colnum['Street4'])
        self.view.insert_column_with_attributes(-1, '+/-', text, markup = self.colnum['+/-'])
        self.view.insert_column_with_attributes(-1, 'Game', text, text = self.colnum['Game'])

        self.liststore.set_sort_func(self.colnum['Street0'], self.sorthand)
        self.liststore.set_sort_func(self.colnum['+/-'], self.sort_float)
        self.view.get_column(self.colnum['Street0']).set_sort_column_id(self.colnum['Street0'])
        self.view.get_column(self.colnum['+/-']).set_sort_column_id(self.colnum['+/-'])

        selection = self.view.get_selection()
        selection.set_select_function(self.select_hand, None, True)

        for handid, hand in self.hands.items():
            hero = self.filters.getHeroes()[hand.sitename]
            won = 0
            if hero in hand.collectees.keys():
                won = hand.collectees[hero]
            bet = 0
            if hero in hand.pot.committed.keys():
                bet = hand.pot.committed[hero]
            net = self.get_net_pango_markup(won - bet)
            
            gt =  hand.gametype['category']
            row = []
            if hand.gametype['base'] == 'hold':
                hole = hand.get_cards_pango_markup(hand.holecards['PREFLOP'][hero][1])
                flop = hand.get_cards_pango_markup(hand.board["FLOP"])
                turn = hand.get_cards_pango_markup(hand.board["TURN"])
                river = hand.get_cards_pango_markup(hand.board["RIVER"])
                row = [hole, flop, turn, river, None, net, gt, handid]
            elif hand.gametype['base'] == 'stud':
                third = hand.get_cards_pango_markup(hand.holecards['THIRD'][hero][0]) + " " + hand.get_cards_pango_markup(hand.holecards['THIRD'][hero][1]) 
                #ugh - fix the stud join_holecards function so we can retrieve sanely
                fourth  = hand.get_cards_pango_markup(hand.holecards['FOURTH'] [hero][0])
                fifth   = hand.get_cards_pango_markup(hand.holecards['FIFTH']  [hero][0])
                sixth   = hand.get_cards_pango_markup(hand.holecards['SIXTH']  [hero][0])
                seventh = hand.get_cards_pango_markup(hand.holecards['SEVENTH'][hero][0])
                row = [third, fourth, fifth, sixth, seventh, net, gt, handid]
            elif hand.gametype['base'] == 'draw':
                row = [hand.get_cards_pango_markup(hand.holecards['DEAL'][hero][0]), None, None, None, None, net, gt, handid]
            #print "DEBUG: row: %s" % row
            self.liststore.append(row)
        self.viewfilter.set_visible_func(self.viewfilter_visible_cb)
        self.handsWindow.show_all()

    def get_net_pango_markup(self, net):
        """Pango marks up the +/- value ... putting negative values in () and coloring them red.
            used instead of cash_renderer_cell_func because the render function renders the foreground of all columns and not just the one needed """
        if net < 0:
            ret = '<span foreground="red">(%s)</span>' %(net*-1)
        else:
            ret = str(net)
        return ret
    '''
