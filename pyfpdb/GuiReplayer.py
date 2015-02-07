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

# Note that this now contains the replayer only! The list of hands has been moved to GuiHandViewer by zarturo.

import L10n
_ = L10n.get_translation()

from functools import partial

import Hand
import Card
import Configuration
import Database
import SQL
import Deck

from PyQt5.QtCore import (QPoint, QRect, Qt, QTimer)
from PyQt5.QtGui import (QColor, QImage, QPainter)
from PyQt5.QtWidgets import (QHBoxLayout, QPushButton, QSlider, QVBoxLayout,
                             QWidget)

import math
from decimal_wrapper import Decimal

import copy
import os

CARD_HEIGHT = 42
CARD_WIDTH = 30

class GuiReplayer(QWidget):
    """A Replayer to replay hands."""
    def __init__(self, config, querylist, mainwin, handlist):
        QWidget.__init__(self, None)
        self.setFixedSize(800, 680)
        self.conf = config
        self.main_window = mainwin
        self.sql = querylist

        self.db = Database.Database(self.conf, sql=self.sql)
        self.states = [] # List with all table states.
        self.handlist = handlist
        self.handidx = 0

        self.setWindowTitle("FPDB Hand Replayer")
        
        self.replayBox = QVBoxLayout()
        self.setLayout(self.replayBox)

        self.replayBox.addStretch()

        self.buttonBox = QHBoxLayout()
        self.prevButton = QPushButton("Prev")
        self.prevButton.clicked.connect(self.prev_clicked)
        self.prevButton.setFocusPolicy(Qt.NoFocus)
        self.startButton = QPushButton("Start")
        self.startButton.clicked.connect(self.start_clicked)
        self.startButton.setFocusPolicy(Qt.NoFocus)
        self.endButton = QPushButton("End")
        self.endButton.clicked.connect(self.end_clicked)
        self.endButton.setFocusPolicy(Qt.NoFocus)
        self.playPauseButton = QPushButton("Play")
        self.playPauseButton.clicked.connect(self.play_clicked)
        self.playPauseButton.setFocusPolicy(Qt.NoFocus)
        self.nextButton = QPushButton("Next")
        self.nextButton.clicked.connect(self.next_clicked)
        self.nextButton.setFocusPolicy(Qt.NoFocus)

        self.replayBox.addLayout(self.buttonBox)

        self.stateSlider = QSlider(Qt.Horizontal)
        self.stateSlider.valueChanged.connect(self.slider_changed)
        self.stateSlider.setFocusPolicy(Qt.NoFocus)

        self.replayBox.addWidget(self.stateSlider, False)

        self.playing = False

        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        self.deck_inst = Deck.Deck(self.conf, height=CARD_HEIGHT, width=CARD_WIDTH)
        self.show()

    def renderCards(self, painter, cards, x, y):
        for card in cards:
            cardIndex = Card.encodeCard(card)
            painter.drawPixmap(QPoint(x, y), self.cardImages[cardIndex])
            x += self.cardwidth

    def paintEvent(self, event):
        if self.tableImage is None or self.playerBackdrop is None:
            try:
                self.playerBackdrop = QImage(os.path.join(self.conf.graphics_path, u"playerbackdrop.png"))
                self.tableImage = QImage(os.path.join(self.conf.graphics_path, u"Table.png"))
            except:
                return
        if self.cardImages is None:
            self.cardwidth = CARD_WIDTH
            self.cardheight = CARD_HEIGHT
            self.cardImages = [None] * 53
            suits = ('s', 'h', 'd', 'c')
            ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
            for j in range(0, 13):
                for i in range(0, 4):
                    index = Card.cardFromValueSuit(ranks[j], suits[i])
                    self.cardImages[index] = self.deck_inst.card(suits[i], ranks[j])
            self.cardImages[0] = self.deck_inst.back()

        if not event.rect().intersects(QRect(0, 0, self.tableImage.width(), self.tableImage.height())):
            return

        painter = QPainter(self)
        painter.drawImage(QPoint(0,0), self.tableImage)

        if len(self.states) == 0:
            return

        state = self.states[self.stateSlider.value()]

        communityLeft = int(self.tableImage.width() / 2 - 2.5 * self.cardwidth)
        communityTop = int(self.tableImage.height() / 2 - 1.75 * self.cardheight)

        convertx = lambda x: int(x * self.tableImage.width() * 0.8) + self.tableImage.width() / 2
        converty = lambda y: int(y * self.tableImage.height() * 0.6) + self.tableImage.height() / 2

        for player in state.players.values():
            playerx = convertx(player.x)
            playery = converty(player.y)
            painter.drawImage(QPoint(playerx - self.playerBackdrop.width() / 2, playery - 3), self.playerBackdrop)
            if player.action=="folds":
                painter.setPen(QColor("grey"))
            else:
                painter.setPen(QColor("white"))
                x = playerx - self.cardwidth * len(player.holecards) / 2
                self.renderCards(painter, player.holecards,
                                 x, playery - self.cardheight)

            painter.drawText(QRect(playerx - 100, playery, 200, 20),
                             Qt.AlignCenter,
                             '%s %s%.2f' % (player.name,
                                            self.currency,
                                            player.stack))

            if player.justacted:
                painter.setPen(QColor("yellow"))
                painter.drawText(QRect(playerx - 50, playery + 15, 100, 20), Qt.AlignCenter, player.action)
            else:
                painter.setPen(QColor("white"))
            if player.chips != 0:
                painter.drawText(QRect(convertx(player.x * .65) - 100,
                                       converty(player.y * 0.65),
                                       200,
                                       20),
                                 Qt.AlignCenter,
                                 '%s%.2f' % (self.currency, player.chips))

        painter.setPen(QColor("white"))

        if state.pot > 0:
            painter.drawText(QRect(self.tableImage.width() / 2 - 100,
                                   self.tableImage.height() / 2 - 20,
                                   200,
                                   40),
                             Qt.AlignCenter,
                             '%s%.2f' % (self.currency, state.pot))

        for street in state.renderBoard:
            x = communityLeft
            if street.startswith('TURN'):
                x += 3 * self.cardwidth
            elif street.startswith('RIVER'):
                x += 4 * self.cardwidth
            y = communityTop
            if street.endswith('1'): # Run it twice streets
                y -= 0.5 * self.cardheight
            elif street.endswith('2'):
                y += 0.5 * self.cardheight
            self.renderCards(painter, state.board[street], x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.stateSlider.setValue(max(0, self.stateSlider.value() - 1))
        elif event.key() == Qt.Key_Right:
            self.stateSlider.setValue(min(self.stateSlider.maximum(), self.stateSlider.value() + 1))
        elif event.key() == Qt.Key_Up:
            if self.handidx < len(self.handlist) - 1:
                self.play_hand(self.handidx + 1)
        elif event.key() == Qt.Key_Down:
            if self.handidx > 0:
                self.play_hand(self.handidx - 1)
        else:
            QWidget.keyPressEvent(self, event)

    def play_hand(self, handidx):
        self.handidx = handidx
        hand = Hand.hand_factory(self.handlist[handidx], self.conf, self.db)
        # hand.writeHand()  # Print handhistory to stdout -> should be an option in the GUI
        self.currency = hand.sym

        self.states = []
        state = TableState(hand)
        seenStreets = []
        for street in hand.allStreets:
            if state.called > 0:
                for player in state.players.values():
                    if player.stack == 0:
                        state.allin = True
                        break
            if not hand.actions[street] and not state.allin:
                break
            seenStreets.append(street)
            state = copy.deepcopy(state)
            state.startPhase(street)
            self.states.append(state)
            for action in hand.actions[street]:
                state = copy.deepcopy(state)
                state.updateForAction(action)
                self.states.append(state)
        state = copy.deepcopy(state)
        state.endHand(hand.collectees, hand.pot.returned)
        self.states.append(state)

        # Clear and repopulate the row of buttons
        for idx in reversed(range(self.buttonBox.count())):
            self.buttonBox.takeAt(idx).widget().setParent(None)
        self.buttonBox.addWidget(self.prevButton)
        self.prevButton.setEnabled(self.handidx > 0)
        self.buttonBox.addWidget(self.startButton)
        for street in hand.allStreets[1:]:
            btn = QPushButton(street.capitalize())
            self.buttonBox.addWidget(btn)
            btn.clicked.connect(partial(self.street_clicked, street=street))
            btn.setEnabled(street in seenStreets)
            btn.setFocusPolicy(Qt.NoFocus)
        self.buttonBox.addWidget(self.endButton)
        self.buttonBox.addWidget(self.playPauseButton)
        self.buttonBox.addWidget(self.nextButton)
        self.nextButton.setEnabled(self.handidx < len(self.handlist) - 1)

        self.stateSlider.setMaximum(len(self.states) - 1)
        self.stateSlider.setValue(0)
        self.update()

    def increment_state(self):
        if self.stateSlider.value() == self.stateSlider.maximum():
            self.playing = False
            self.playPauseButton.setText("Play")

        if self.playing:
            self.stateSlider.setValue(self.stateSlider.value() + 1)
    
    def slider_changed(self, value):
        self.update()

    def importhand(self, handid=1):

        h = Hand.hand_factory(handid, self.conf, self.db)
        
        return h

    def play_clicked(self, checkState):
        self.playing = not self.playing
        if self.playing:
            self.playPauseButton.setText("Pause")
            self.playTimer = QTimer()
            self.playTimer.timeout.connect(self.increment_state)
            self.playTimer.start(1000)
        else:
            self.playPauseButton.setText("Play")
            self.playTimer = None

    def start_clicked(self, checkState):
        self.stateSlider.setValue(0)

    def end_clicked(self, checkState):
        self.stateSlider.setValue(self.stateSlider.maximum())

    def prev_clicked(self, checkState):
        self.play_hand(self.handidx - 1)

    def next_clicked(self, checkState):
        self.play_hand(self.handidx + 1)

    def street_clicked(self, checkState, street):
        for i, state in enumerate(self.states):
            if state.street == street:
                self.stateSlider.setValue(i)
                break

# ICM code originally grabbed from http://svn.gna.org/svn/pokersource/trunk/icm-calculator/icm-webservice.py
# Copyright (c) 2008 Thomas Johnson <tomfmason@gmail.com>

class ICM:
    def __init__(self, stacks, payouts):
        self.stacks = stacks
        self.payouts = payouts
        self.equities = []
        self.prepare()
    def prepare(self):
        total = sum(self.stacks)
        for k in self.stacks:
            self.equities.append(round(Decimal(str(self.getEquities(total, k, 0))), 4))
    def getEquities(self, total, player, depth):
        D = Decimal
        eq = D(self.stacks[player]) / total * D(str(self.payouts[depth]))
        if(depth + 1 < len(self.payouts)):
            i=0
            for stack in self.stacks:
                if i != player and stack > 0.0:
                    self.stacks[i] = 0.0
                    eq += self.getEquities((total - stack), player, (depth + 1)) * (stack / D(total))
                    self.stacks[i] = stack
                i += 1
        return eq

class TableState:
    def __init__(self, hand):
        self.pot = Decimal(0)
        self.street = None
        self.board = hand.board
        self.renderBoard = set()
        self.bet = Decimal(0)
        self.called = Decimal(0)
        self.gametype = hand.gametype['category']
        self.gamebase = hand.gametype['base']
        self.allin = False
        self.allinThisStreet = False
        # NOTE: Need a useful way to grab payouts
        #self.icm = ICM(stacks,payouts)
        #print icm.equities

        self.players = {}

        for seat, name, chips, pos in hand.players:
            self.players[name] = Player(hand, name, chips, seat)

    def startPhase(self, phase):
        self.street = phase
        if phase in ("BLINDSANTES", "PREFLOP", "DEAL"):
            return

        self.renderBoard.add(phase)

        for player in self.players.values():
            player.justacted = False
            if player.chips > self.called:
                player.stack += player.chips - self.called
                player.chips = self.called
            self.pot += player.chips
            player.chips = Decimal(0)
            if phase in ("THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH"):
                player.holecards = player.streetcards[self.street]
        self.bet = Decimal(0)
        self.called = Decimal(0)
        self.allinThisStreet = False

    def updateForAction(self, action):
        for player in self.players.values():
            player.justacted = False

        player = self.players[action[0]]
        player.action = action[1]
        player.justacted = True
        if action[1] == "folds" or action[1] == "checks":
            pass
        elif action[1] == "raises" or action[1] == "bets":
            if self.allinThisStreet:
                self.called = Decimal(self.bet)
            else:
                self.called = Decimal(0)
            diff = self.bet - player.chips
            self.bet += action[2]
            player.chips += action[2] + diff
            player.stack -= action[2] + diff
        elif action[1] == "big blind":
            self.bet = action[2]
            player.chips += action[2]
            player.stack -= action[2]
        elif action[1] == "calls" or action[1] == "small blind" or action[1] == "secondsb":
            player.chips += action[2]
            player.stack -= action[2]
            self.called = max(self.called, player.chips)
        elif action[1] == "both":
            player.chips += action[2]
            player.stack -= action[2]
        elif action[1] == "ante":
            self.pot += action[2]
            player.stack -= action[2]
        elif action[1] == "discards":
            player.action += " " + str(action[2])
            if len(action) > 3:
                # Must be hero as we have discard information.  Update holecards now.
                player.holecards = player.streetcards[self.street]
        elif action[1] == "stands pat":
            pass
        elif action[1] == "bringin":
            player.chips += action[2]
            player.stack -= action[2]
        else:
            print "unhandled action: " + str(action)

        if player.stack == 0:
            self.allinThisStreet = True

    def endHand(self, collectees, returned):
        self.pot = Decimal(0)
        for player in self.players.values():
            player.justacted = False
            player.chips = Decimal(0)
            if self.gamebase == 'draw':
                player.holecards = player.streetcards[self.street]
        for name,amount in collectees.items():
            player = self.players[name]
            player.chips += amount
            player.action = "collected"
            player.justacted = True
        for name, amount in returned.items():
            self.players[name].stack += amount

class Player:
    def __init__(self, hand, name, stack, seat):
        self.stack     = Decimal(stack)
        self.chips     = Decimal(0)
        self.seat      = seat
        self.name      = name
        self.action    = None
        self.justacted = False
        self.holecards = hand.join_holecards(name, asList=True)
        self.streetcards = {}
        if hand.gametype['base'] == 'draw':
            for street in hand.actionStreets[1:]:
                self.streetcards[street] = hand.join_holecards(name, asList=True, street=street)
            self.holecards = self.streetcards[hand.actionStreets[1]]
        elif hand.gametype['base'] == 'stud':
            for i, street in enumerate(hand.actionStreets[1:]):
                self.streetcards[street] = self.holecards[:i + 3]
            self.holecards = self.streetcards[hand.actionStreets[1]]
        self.x         = 0.5 * math.cos(2 * self.seat * math.pi / hand.maxseats)
        self.y         = 0.5 * math.sin(2 * self.seat * math.pi / hand.maxseats)

if __name__ == '__main__':
    config = Configuration.Config()
    db = Database.Database(config)
    sql = SQL.Sql(db_server = config.get_db_parameters()['db-server'])

    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    handlist = [10, 39, 40, 72, 369, 390]
    replayer = GuiReplayer(config, sql, None, handlist)
    replayer.play_hand(0)

    app.exec_()
