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

# Note that this now contains the replayer only! The list of hands has been moved to GuiHandViewer by zarturo.

import L10n
_ = L10n.get_translation()


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
import sys
import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

CARD_HEIGHT = 42
CARD_WIDTH = 30
global card_images
card_images = 53 * [0]


class GuiReplayer(QWidget):
    """A Replayer to replay hands."""
    def __init__(self, config, querylist, mainwin, options = None, debug=True):
        QWidget.__init__(self, None)
        self.setFixedSize(800, 680)
        self.debug = debug
        self.conf = config
        self.main_window = mainwin
        self.sql = querylist

        self.db = Database.Database(self.conf, sql=self.sql)
        self.states = [] # List with all table states.

        self.setWindowTitle("FPDB Hand Replayer")
        
        self.replayBox = QVBoxLayout()
        self.setLayout(self.replayBox)

        self.replayBox.addStretch()

        self.buttonBox = QHBoxLayout()
        self.startButton = QPushButton("Start")
        self.startButton.clicked.connect(self.start_clicked)
        self.flopButton = QPushButton("Flop")
        self.flopButton.clicked.connect(self.flop_clicked)
        self.turnButton = QPushButton("Turn")
        self.turnButton.clicked.connect(self.turn_clicked)
        self.riverButton = QPushButton("River")
        self.riverButton.clicked.connect(self.river_clicked)
        self.endButton = QPushButton("End")
        self.endButton.clicked.connect(self.end_clicked)
        self.playPauseButton = QPushButton("Play")
        self.playPauseButton.clicked.connect(self.play_clicked)
        self.buttonBox.addWidget(self.startButton)
        self.buttonBox.addWidget(self.flopButton)
        self.buttonBox.addWidget(self.turnButton)
        self.buttonBox.addWidget(self.riverButton)
        self.buttonBox.addWidget(self.endButton)
        self.buttonBox.addWidget(self.playPauseButton)
        
        self.replayBox.addLayout(self.buttonBox)

        self.stateSlider = QSlider(Qt.Horizontal)
        self.stateSlider.valueChanged.connect(self.slider_changed)

        self.replayBox.addWidget(self.stateSlider, False)
        
        self.playing = False

        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        self.deck_inst = Deck.Deck(self.conf, height=CARD_HEIGHT, width=CARD_WIDTH)
        self.show()

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

        padding = 6
        communityLeft = int(self.tableImage.width() / 2 - 2.5 * self.cardwidth - 2 * padding)
        communityTop = int(self.tableImage.height() / 2 - 1.5 * self.cardheight)

        convertx = lambda x: int(x * self.tableImage.width() * 0.8) + self.tableImage.width() / 2
        converty = lambda y: int(y * self.tableImage.height() * 0.6) + self.tableImage.height() / 2

        for player in state.players.values():
            playerx = convertx(player.x)
            playery = converty(player.y)
            painter.drawImage(QPoint(playerx - self.playerBackdrop.width() / 2, playery - padding / 2), self.playerBackdrop)
            if player.action=="folds":
                painter.setPen(QColor("grey"))
            else:
                painter.setPen(QColor("white"))
                if state.gametype == 'holdem':
                    cardIndex = Card.encodeCard(player.holecards[0:2])
                    painter.drawPixmap(QPoint(playerx - self.cardwidth - padding / 2, playery - self.cardheight), self.cardImages[cardIndex])
                    cardIndex = Card.encodeCard(player.holecards[3:5])
                    painter.drawPixmap(QPoint(playerx + padding / 2, playery - self.cardheight), self.cardImages[cardIndex])
                elif state.gametype in ('omahahi', 'omahahilo'):
                    cardIndex = Card.encodeCard(player.holecards[0:2])
                    painter.drawPixmap(QPoint(playerx - 2 * self.cardwidth - 3 * padding / 2, playery - self.cardheight), self.cardImages[cardIndex])
                    cardIndex = Card.encodeCard(player.holecards[3:5])
                    painter.drawPixmap(QPoint(playerx - self.cardwidth - padding / 2, playery - self.cardheight), self.cardImages[cardIndex])
                    cardIndex = Card.encodeCard(player.holecards[6:8])
                    painter.drawPixmap(QPoint(playerx + padding / 2, playery - self.cardheight), self.cardImages[cardIndex])
                    cardIndex = Card.encodeCard(player.holecards[9:11])
                    painter.drawPixmap(QPoint(playerx + self.cardwidth + 3 * padding / 2, playery - self.cardheight), self.cardImages[cardIndex])

            painter.drawText(QRect(playerx - 100, playery, 200, 20), Qt.AlignCenter, '%s %s%.2f' % (player.name, self.currency, player.stack))

            if player.justacted:
                painter.setPen(QColor("yellow"))
                painter.drawText(QRect(playerx - 50, playery + 15, 100, 20), Qt.AlignCenter, player.action)
            else:
                painter.setPen(QColor("white"))
            if player.chips != 0:  #displays amount
                painter.drawText(QRect(convertx(player.x * .65) - 100, converty(player.y * 0.65), 200, 20), Qt.AlignCenter, '%s%.2f' % (self.currency, player.chips))

        painter.setPen(QColor("white"))

        painter.drawText(QRect(self.tableImage.width() / 2 - 100, self.tableImage.height() / 2 - 20, 200, 40), Qt.AlignCenter, '%s%.2f' % (self.currency, state.pot))

        if state.showFlop:
            cardIndex = Card.encodeCard(state.flop[0])
            painter.drawPixmap(QPoint(communityLeft, communityTop), self.cardImages[cardIndex])
            cardIndex = Card.encodeCard(state.flop[1])
            painter.drawPixmap(QPoint(communityLeft + self.cardwidth + padding, communityTop), self.cardImages[cardIndex])
            cardIndex = Card.encodeCard(state.flop[2])
            painter.drawPixmap(QPoint(communityLeft + 2 * (self.cardwidth + padding), communityTop), self.cardImages[cardIndex])
        if state.showTurn:
            cardIndex = Card.encodeCard(state.turn[0])
            painter.drawPixmap(QPoint(communityLeft + 3 * (self.cardwidth + padding), communityTop), self.cardImages[cardIndex])
        if state.showRiver:
            cardIndex = Card.encodeCard(state.river[0])
            painter.drawPixmap(QPoint(communityLeft + 4 * (self.cardwidth + padding), communityTop), self.cardImages[cardIndex])

    def play_hand(self, hand):
        # hand.writeHand()  # Print handhistory to stdout -> should be an option in the GUI
        actions = hand.allStreets
        state = TableState(hand)
        for action in actions:
            state = copy.deepcopy(state)
            if state.startPhase(action):
                self.states.append(state)
            for i in range(0,len(hand.actions[action])):
                state = copy.deepcopy(state)
                state.updateForAction(hand.actions[action][i])
                self.states.append(state)
        state = copy.deepcopy(state)
        state.endHand(hand.collectees)
        self.states.append(state)
        
        self.stateSlider.setMaximum(len(self.states) - 1)
        self.stateSlider.setValue(0)

    def increment_state(self):
        if self.stateSlider.value() == self.stateSlider.maximum():
            self.playing = False
            self.playPauseButton.setText("Play")

        if not self.playing:
            return False

        self.stateSlider.setValue(self.stateSlider.value() + 1)
        return True
    
    def slider_changed(self, adjustment):
        self.update()

    def importhand(self, handid=1):

        h = Hand.hand_factory(handid, self.conf, self.db)
        
        return h

    def play_clicked(self, button):
        self.playing = not self.playing
        if self.playing:
            self.playPauseButton.setText("Pause")
            self.playTimer = QTimer()
            self.playTimer.timeout.connect(self.increment_state)
            self.playTimer.start(1000)
        else:
            self.playPauseButton.setText("Play")
            self.playTimer = None
    def start_clicked(self, button):
        self.stateSlider.setValue(0)
    def end_clicked(self, button):
        self.stateSlider.setValue(self.stateSlider.maximum())
    def flop_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showFlop:
                self.stateSlider.setValue(i)
                break
    def turn_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showTurn:
                self.stateSlider.setValue(i)
                break
    def river_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showRiver:
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
        for k,v in enumerate(stacks):
            self.equities.append(round(Decimal(str(self.getEquities(total, k,0))),4))
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
        self.flop = hand.board["FLOP"]
        self.turn = hand.board["TURN"]
        self.river = hand.board["RIVER"]
        self.showFlop = False
        self.showTurn = False
        self.showRiver = False
        self.bet = Decimal(0)
        self.called = Decimal(0)
        self.gametype = hand.gametype['category']
        # NOTE: Need a useful way to grab payouts
        #self.icm = ICM(stacks,payouts)
        #print icm.equities

        self.players = {}

        for seat, name, chips, pos in hand.players:
            self.players[name] = Player(hand, name, chips, seat)

    def startPhase(self, phase):
        if phase == "BLINDSANTES":
            return True
        if phase == "PREFLOP":
            return False
        if phase == "FLOP" and len(self.flop) == 0:
            return False
        if phase == "TURN" and len(self.turn) == 0:
            return False
        if phase == "RIVER" and len(self.river) == 0:
            return False
        
        for player in self.players.values():
            player.justacted = False
            if player.chips > self.called:
                player.stack += player.chips - self.called
                player.chips = self.called
            self.pot += player.chips
            player.chips = Decimal(0)
        self.bet = Decimal(0)
        self.called = Decimal(0)

        if phase == "FLOP":
            self.showFlop = True
        elif phase == "TURN":
            self.showTurn = True
        elif phase == "RIVER":
            self.showRiver = True

        return True

    def updateForAction(self, action):
        for player in self.players.values():
            player.justacted = False

        player = self.players[action[0]]
        player.action = action[1]
        player.justacted = True
        if action[1] == "folds" or action[1] == "checks":
            pass
        elif action[1] == "raises" or action[1] == "bets":
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
        else:
            print "unhandled action: " + str(action)

    def endHand(self, collectees):
        self.pot = Decimal(0)
        for player in self.players.values():
            player.justacted = False
            player.chips = Decimal(0)
        for name,amount in collectees.items():
            player = self.players[name]
            player.chips += amount
            player.action = "collected"
            player.justacted = True

class Player:
    def __init__(self, hand, name, stack, seat):
        self.stack     = Decimal(stack)
        self.chips     = Decimal(0)
        self.seat      = seat
        self.name      = name
        self.action    = None
        self.justacted = False
        self.holecards = hand.join_holecards(name)
        self.x         = 0.5 * math.cos(2 * self.seat * math.pi / hand.maxseats)
        self.y         = 0.5 * math.sin(2 * self.seat * math.pi / hand.maxseats)

if __name__ == '__main__':
    config = Configuration.Config()
    db = Database.Database(config)
    sql = SQL.Sql(db_server = config.get_db_parameters()['db-server'])

    from PyQt5.QtWidgets import QApplication, QMainWindow
    app = QApplication([])

    replayer = GuiReplayer(config, sql, None, debug=True)
    h = Hand.hand_factory(1, config, db)
    if h.gametype['currency']=="USD":    #TODO: check if there are others ..
        replayer.currency="$"
    elif hand.gametype['currency']=="EUR":
        replayer.currency="\xe2\x82\xac"
    elif hand.gametype['currency']=="GBP":
        replayer.currency="£"
    else:
        replayer.currency = hand.gametype['currency']

    replayer.play_hand(h)

    app.exec_()
