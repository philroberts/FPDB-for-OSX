#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010-2011 Maxime Grandchamp
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# In the "official" distribution you can find the license in agpl-3.0.txt.
#


# This code once was in GuiReplayer.py and was split up in this and the former by zarturo.

import L10n
_ = L10n.get_translation()

from functools import partial

import Hand
import Card
import Configuration
import Database
import SQL
import Filters
import Deck

from PyQt5.QtCore import QCoreApplication, QSortFilterProxyModel, Qt
from PyQt5.QtGui import (QPainter, QPixmap, QStandardItem, QStandardItemModel)
from PyQt5.QtWidgets import (QApplication, QFrame, QMenu,
                             QProgressDialog, QScrollArea, QSplitter,
                             QTableView, QVBoxLayout)

from StringIO import StringIO

import GuiReplayer

class GuiHandViewer(QSplitter):
    def __init__(self, config, querylist, mainwin):
        QSplitter.__init__(self, mainwin)
        self.config = config
        self.main_window = mainwin
        self.sql = querylist
        self.replayer = None

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
        
        self.filters = Filters.Filters(self.db, display = filters_display)
        self.filters.registerButton1Name(_("Load Hands"))
        self.filters.registerButton1Callback(self.loadHands)
        self.filters.registerCardsCallback(self.filter_cards_cb)

        scroll = QScrollArea()
        scroll.setWidget(self.filters)

        self.handsFrame = QFrame()
        self.handsVBox = QVBoxLayout()
        self.handsFrame.setLayout(self.handsVBox)

        self.addWidget(scroll)
        self.addWidget(self.handsFrame)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

        self.deck_instance = Deck.Deck(self.config, height=42, width=30)
        self.cardImages = self.init_card_images()

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
        self.view = QTableView()
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.handsVBox.addWidget(self.view)
        self.model = QStandardItemModel(0, len(self.colnum), self.view)
        self.filterModel = QSortFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.filterModel.setSortRole(Qt.UserRole)

        self.view.setModel(self.filterModel)
        self.view.verticalHeader().hide()
        self.model.setHorizontalHeaderLabels(
            ['Stakes', 'Pos', 'Street0', 'Action0', 'Street1-4', 'Action1-4',
             'Won', 'Bet', 'Net', 'Game', 'HandId'])

        self.view.doubleClicked.connect(self.row_activated)
        self.view.contextMenuEvent = self.contextMenu
        self.filterModel.rowsInserted.connect(lambda index, start, end: [self.view.resizeRowToContents(r) for r in xrange(start, end + 1)])
        self.filterModel.filterAcceptsRow = lambda row, sourceParent: self.is_row_in_card_filter(row)

        self.view.resizeColumnsToContents()
        self.view.setSortingEnabled(True)

       
    def init_card_images(self):
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)

        card_images = [0]*53
        for j in range(0, 13):
            for i in range(0, 4):
                loc = Card.cardFromValueSuit(ranks[j], suits[i])
                card_image = self.deck_instance.card(suits[i], ranks[j])
                card_images[loc] = card_image
        back_image = self.deck_instance.back()
        card_images[0] = back_image
        return card_images

    def loadHands(self, checkState):
        hand_ids = self.get_hand_ids_from_date_range(self.filters.getDates()[0], self.filters.getDates()[1])
        self.reload_hands(hand_ids)

    def get_hand_ids_from_date_range(self, start, end):
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

    def reload_hands(self, handids):
        self.hands = {}
        self.model.removeRows(0, self.model.rowCount())
        if len(handids) == 0:
            return
        progress = QProgressDialog("Loading hands", "Abort", 0, len(handids), self)
        progress.setValue(0)
        progress.show()
        for idx, handid in enumerate(handids):
            if progress.wasCanceled():
                break
            self.hands[handid] = self.importhand(handid)
            self.addHandRow(handid, self.hands[handid])
            progress.setValue(idx + 1)
            if idx % 10 == 0:
                QCoreApplication.processEvents()
                self.view.resizeColumnsToContents()
        self.view.resizeColumnsToContents()
    
    def addHandRow(self, handid, hand):
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
                   str(net), gt, str(handid)]
        elif hand.gametype['base'] == 'stud':
            third = " ".join(hand.holecards['THIRD'][hero][0]) + " " + " ".join(hand.holecards['THIRD'][hero][1]) 
            # ugh - fix the stud join_holecards function so we can retrieve sanely
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
                   gt, str(handid)]
        elif hand.gametype['base'] == 'draw':
            row = [hand.getStakesAsString(), pos, hand.join_holecards(hero,street='DEAL'), hand.get_actions_short(hero, 'DEAL'), None, None, 
                   str(won), str(bet), str(net), gt, str(handid)]

        modelrow = [QStandardItem(r) for r in row]
        for index, item in enumerate(modelrow):
            item.setEditable(False)
            if index in (self.colnum['Street0'], self.colnum['Street1-4']):
                cards = item.data(Qt.DisplayRole)
                item.setData(self.render_cards(cards), Qt.DecorationRole)
                item.setData("", Qt.DisplayRole)
                item.setData(cards, Qt.UserRole + 1)
            if index in (self.colnum['Bet'], self.colnum['Net'], self.colnum['Won']):
                item.setData(float(item.data(Qt.DisplayRole)), Qt.UserRole)
        self.model.appendRow(modelrow)

    def copyHandToClipboard(self, checkState, hand):
        handText = StringIO()
        hand.writeHand(handText)
        QApplication.clipboard().setText(handText.getvalue())

    def contextMenu(self, event):
        index = self.view.currentIndex()
        if index.row() < 0:
            return
        hand = self.hands[int(index.sibling(index.row(), self.colnum['HandId']).data())]
        m = QMenu()
        copyAction = m.addAction('Copy to clipboard')
        copyAction.triggered.connect(partial(self.copyHandToClipboard, hand=hand))
        m.move(event.globalPos())
        m.exec_()

    def filter_cards_cb(self, card):
        if hasattr(self, 'hands'):
            self.filterModel.invalidateFilter()

    def is_row_in_card_filter(self, rownum):
        """ Returns true if the cards of the given row are in the card filter """
        # Does work but all cards that should NOT be displayed have to be clicked.
        card_filter = self.filters.getCards() 
        hcs = self.model.data(self.model.index(rownum, self.colnum['Street0']), Qt.UserRole + 1).split(' ')
        
        if '0x' in hcs:      #if cards are unknown return True
            return True
        
        gt = self.model.data(self.model.index(rownum, self.colnum['Game']))

        if gt not in ('holdem', 'omahahi', 'omahahilo'): return True
        # Holdem: Compare the real start cards to the selected filter (ie. AhKh = AKs)
        value1 = Card.card_map[hcs[0][0]]
        value2 = Card.card_map[hcs[1][0]]
        idx = Card.twoStartCards(value1, hcs[0][1], value2, hcs[1][1])
        abbr = Card.twoStartCardString(idx)
        return card_filter[abbr]

    def row_activated(self, index):
        handlist = list(sorted(self.hands.keys()))
        self.replayer = GuiReplayer.GuiReplayer(self.config, self.sql, self.main_window, handlist)

        self.replayer.play_hand(handlist.index(int(index.sibling(index.row(), self.colnum['HandId']).data())))

    def importhand(self, handid=1):
        # Fetch hand info
        # We need at least sitename, gametype, handid
        # for the Hand.__init__

        h = Hand.hand_factory(handid, self.config, self.db)

        # Set the hero for this hand using the filter for the sitename of this hand
        h.hero = self.filters.getHeroes()[h.sitename]
        return h

    def render_cards(self, cardstring):
        card_width  = 30
        card_height = 42
        if cardstring is None or cardstring == '':
            cardstring = "0x"
        cardstring = cardstring.replace("'","")
        cardstring = cardstring.replace("[","")
        cardstring = cardstring.replace("]","")
        cardstring = cardstring.replace("'","")
        cardstring = cardstring.replace(",","")
        cards = [Card.encodeCard(c) for c in cardstring.split(' ')]
        n_cards = len(cards)
    
        pixbuf = QPixmap(card_width * n_cards, card_height)
        painter = QPainter(pixbuf)
        x = 0 # x coord where the next card starts in pixbuf
        for card in cards:
            painter.drawPixmap(x, 0, self.cardImages[card])
            x += card_width
        return pixbuf


if __name__ == "__main__":
    config = Configuration.Config()

    settings = {}

    settings.update(config.get_db_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    from PyQt5.QtWidgets import QMainWindow
    app = QApplication([])
    sql = SQL.Sql(db_server=settings['db-server'])
    main_window = QMainWindow()
    i = GuiHandViewer(config, sql, main_window)
    main_window.setCentralWidget(i)
    main_window.show()
    main_window.resize(1400, 800)
    app.exec_()
