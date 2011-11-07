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


from Hand import *
import Configuration
import Database
import SQL
import fpdb_import
import Filters
import pygtk
pygtk.require('2.0')
import gtk
import math
import gobject

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


class GuiHandViewer:
    def __init__(self, config, querylist, mainwin, options = None, debug=True):
        self.debug = debug
        self.config = config
        self.main_window = mainwin
        self.sql = querylist
        self.replayer = None

        # These are temporary variables until it becomes possible
        # to select() a Hand object from the database
        self.site="PokerStars"

        self.db = Database.Database(self.config, sql=self.sql)

        filters_display = { "Heroes"    : True,
                    "Sites"     : False,
                    "Games"     : False,
                    "Limits"    : False,
                    "LimitSep"  : False,
                    "LimitType" : False,
                    "Type"      : False,
                    "Seats"     : False,
                    "SeatSep"   : False,
                    "Dates"     : True,
                    "Cards"     : True,
                    "Groups"    : False,
                    "GroupsAll" : False,
                    "Button1"   : True,
                    "Button2"   : False
                  }


        self.states = [] # List with all table states.
        
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

        self.deck_image = "Cards01.png" #FIXME: read from config (requires deck to be defined somewhere appropriate
        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        #NOTE: There are two caches of card images as I haven't found a way to
        #      replicate the copy_area() function from Pixbuf in the Pixmap class
        #      cardImages is used for the tables display card_images is used for the
        #      table display. Sooner or later we should probably use one or the other.
        card_images = self.init_card_images(config)

    def init_card_images(self, config):
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
        pb = gtk.gdk.pixbuf_new_from_file(config.execution_path(self.deck_image))

        for j in range(0, 13):
            for i in range(0, 4):
                loc = Card.cardFromValueSuit(ranks[j], suits[i])
                card_images[loc] = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(), pb.get_bits_per_sample(), 30, 42)
                pb.copy_area(30*j, 42*i, 30, 42, card_images[loc], 0, 0)
        card_images[0] = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(), pb.get_bits_per_sample(), 30, 42)
        pb.copy_area(30*13, 0, 30, 42, card_images[0], 0, 0)
        return card_images

    def loadHands(self, button, userdata):
        result = self.handIdsFromDateRange(self.filters.getDates()[0], self.filters.getDates()[1])
        self.refreshHands(result)

    def handIdsFromDateRange(self, start, end):

        q = self.db.sql.query['handsInRange']
        q = q.replace('<datetest>', "between '" + start + "' and '" + end + "'")

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
        
        hand1 = self.hands[int(model.get_value(iter1, 7))]
        hand2 = self.hands[int(model.get_value(iter2, 7))]
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

    def sortnet(self, model, iter1, iter2):
        a = float(model.get_value(iter1, 6))
        b = float(model.get_value(iter2, 6))

        if a < b:
            return -1
        elif a > b:
            return 1
        
        return 0
    
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
                str,    # Won
                str,    # Bet
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
                  'Won'          : 5,
                  'Bet'          : 6,
                  'Net'          : 7,
                  'Game'         : 8,
                  'HID'          : 9,
                 }
        self.liststore = gtk.ListStore(*cols)
        self.view = gtk.TreeView()
        self.view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.handsWindow.add(self.view)

        self.viewfilter = self.liststore.filter_new()
        self.view.set_model(self.viewfilter)
        textcell = gtk.CellRendererText()
        pixbuf   = gtk.CellRendererPixbuf()

        self.view.insert_column_with_data_func(-1, 'Street 0', pixbuf, card_renderer_cell_func, self.colnum['Street0'])
        self.view.insert_column_with_data_func(-1, 'Street 1', pixbuf, card_renderer_cell_func, self.colnum['Street1'])
        self.view.insert_column_with_data_func(-1, 'Street 2', pixbuf, card_renderer_cell_func, self.colnum['Street2'])
        self.view.insert_column_with_data_func(-1, 'Street 3', pixbuf, card_renderer_cell_func, self.colnum['Street3'])
        self.view.insert_column_with_data_func(-1, 'Street 4', pixbuf, card_renderer_cell_func, self.colnum['Street4'])
        self.view.insert_column_with_data_func(-1, 'Won', textcell, cash_renderer_cell_func, self.colnum['Won'])
        self.view.insert_column_with_data_func(-1, 'Bet', textcell, cash_renderer_cell_func, self.colnum['Bet'])
        self.view.insert_column_with_data_func(-1, 'Net', textcell, cash_renderer_cell_func, self.colnum['Net'])
        self.view.insert_column_with_data_func(-1, 'Game', textcell, cash_renderer_cell_func, self.colnum['Game'])

        self.liststore.set_sort_func(self.colnum['Street0'], self.sorthand)
        self.liststore.set_sort_func(self.colnum['Net'], self.sortnet)
        self.view.get_column(self.colnum['Street0']).set_sort_column_id(self.colnum['Street0'])
        self.view.get_column(self.colnum['Net']).set_sort_column_id(self.colnum['Net'])

        #selection = self.view.get_selection()
        #selection.set_select_function(self.select_hand, None, True) #listen on selection (single click)
        print self.view.connect("row-activated", self.row_activated)      #listen to double klick

        for handid, hand in self.hands.items():
            hero = self.filters.getHeroes()[hand.sitename]
            won = 0
            if hero in hand.collectees.keys():
                won = hand.collectees[hero]
            bet = 0
            if hero in hand.pot.committed.keys():
                bet = hand.pot.committed[hero]
            net = won - bet
            gt =  hand.gametype['category']
            row = []
            if hand.gametype['base'] == 'hold':
                row = [hand.join_holecards(hero), hand.board["FLOP"], hand.board["TURN"], hand.board["RIVER"], None, str(won), str(bet), str(net), gt, handid]
            elif hand.gametype['base'] == 'stud':
                third = " ".join(hand.holecards['THIRD'][hero][0]) + " " + " ".join(hand.holecards['THIRD'][hero][1]) 
                #ugh - fix the stud join_holecards function so we can retrieve sanely
                fourth  = " ".join(hand.holecards['FOURTH'] [hero][0])
                fifth   = " ".join(hand.holecards['FIFTH']  [hero][0])
                sixth   = " ".join(hand.holecards['SIXTH']  [hero][0])
                seventh = " ".join(hand.holecards['SEVENTH'][hero][0])
                row = [third, fourth, fifth, sixth, seventh, str(won), str(bet), str(net), gt, handid]
            elif hand.gametype['base'] == 'draw':
                row = [hand.join_holecards(hero,street='DEAL'), None, None, None, None, str(won), str(bet), str(net), gt, handid]
            #print "DEBUG: row: %s" % row
            self.liststore.append(row)
        self.viewfilter.set_visible_func(self.viewfilter_visible_cb)
        self.handsWindow.show_all()

    def filter_cards_cb(self, card):
        self.viewfilter.refilter()

    def viewfilter_visible_cb(self, model, iter_):
        card_filter = self.filters.getCards()
        hcs = model.get_value(iter_, self.colnum['Street0']).split(' ')
        gt = model.get_value(iter_, self.colnum['Game'])

        if gt not in ('holdem', 'omaha', 'omahahilo'): return True
        # Holdem: Compare the real start cards to the selected filter (ie. AhKh = AKs)
        value1 = Card.card_map[hcs[0][0]]
        value2 = Card.card_map[hcs[1][0]]
        idx = Card.twoStartCards(value1, hcs[0][1], value2, hcs[1][1])
        abbr = Card.twoStartCardString(idx)
        return False if card_filter[abbr] == False else True

    #def select_hand(self, selection, model, path, is_selected, userdata):    #function head for single click event
    def row_activated(self, view, path, column):
        self.states = [] # List with all table states.
        #if is_selected:
        #    return True
        model = view.get_model()
        hand = self.hands[int(model.get_value(model.get_iter(path), self.colnum['HID']))]
        if hand.gametype['currency']=="USD":    #TODO: check if there are others ..
            currency="$"
        elif hand.gametype['currency']=="EUR":
            currency="�"
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

        ####### Shift this section in Database.py for all to use ######
        q = self.sql.query['get_gameinfo_from_hid']
        q = q.replace('%s', self.sql.query['placeholder'])

        c = self.db.get_cursor()

        c.execute(q, (handid,))
        res = c.fetchone()
        gametype = {'category':res[1],'base':res[2],'type':res[3],'limitType':res[4],'hilo':res[5],'sb':res[6],'bb':res[7], 'currency':res[10]}
        #FIXME: smallbet and bigbet are res[8] and res[9] respectively
        ###### End section ########
        if gametype['base'] == 'hold':
            h = HoldemOmahaHand(config = self.config, hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
        elif gametype['base'] == 'stud':
            h = StudHand(config = self.config, hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
        elif gametype['base'] == 'draw':
            h = DrawHand(config = self.config, hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
        h.select(self.db, handid)
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
        self.liststore.set_sort_func(self.colnum['+/-'], self.sortnet)
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
