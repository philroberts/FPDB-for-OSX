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

import pygtk
pygtk.require('2.0')
import gtk
import math
import gobject
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


class GuiReplayer:
    """A Replayer to replay hands."""
    def __init__(self, config, querylist, mainwin, options = None, debug=True):
        self.debug = debug
        self.conf = config
        self.main_window = mainwin
        self.sql = querylist

        self.db = Database.Database(self.conf, sql=self.sql)
        self.states = [] # List with all table states.

        self.window = gtk.Window()
        self.window.set_title("FPDB Hand Replayer")
        
        self.replayBox = gtk.VBox(False, 0)
        self.replayBox.show()
        
        self.window.add(self.replayBox)


        self.area=gtk.DrawingArea()
        self.pangolayout = self.area.create_pango_layout("")
        self.area.connect("expose-event", self.area_expose)
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        self.area.show()

        self.replayBox.pack_start(self.area, False)

        self.buttonBox = gtk.HButtonBox()
        self.buttonBox.set_layout(gtk.BUTTONBOX_SPREAD)
        self.startButton = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PREVIOUS, gtk.ICON_SIZE_BUTTON)
        self.startButton.set_image(image)
        self.startButton.connect("clicked", self.start_clicked)
        self.flopButton = gtk.Button("Flop")
        self.flopButton.connect("clicked", self.flop_clicked)
        self.turnButton = gtk.Button("Turn")
        self.turnButton.connect("clicked", self.turn_clicked)
        self.riverButton = gtk.Button("River")
        self.riverButton.connect("clicked", self.river_clicked)
        self.endButton = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_NEXT, gtk.ICON_SIZE_BUTTON)
        self.endButton.set_image(image)
        self.endButton.connect("clicked", self.end_clicked)
        self.playPauseButton = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.playPauseButton.set_image(image)
        self.playPauseButton.connect("clicked", self.play_clicked)
        self.buttonBox.add(self.startButton)
        self.buttonBox.add(self.flopButton)
        self.buttonBox.add(self.turnButton)
        self.buttonBox.add(self.riverButton)
        self.buttonBox.add(self.endButton)
        self.buttonBox.add(self.playPauseButton)
        self.buttonBox.show_all()
        
        self.replayBox.pack_start(self.buttonBox, False)

        self.state = gtk.Adjustment(0, 0, 0, 1)
        self.stateSlider = gtk.HScale(self.state)
        self.stateSlider.connect("format_value", lambda x,y: "")
        self.stateSlider.set_digits(0)
        self.handler_id = self.state.connect("value_changed", self.slider_changed)
        self.stateSlider.show()

        self.replayBox.pack_start(self.stateSlider, False)
        
        self.window.show_all()
        
        self.window.connect('destroy', self.on_destroy)

        self.playing = False

        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        #NOTE: There are two caches of card images as I haven't found a way to
        #      replicate the copy_area() function from Pixbuf in the Pixmap class
        #      cardImages is used for the tables display card_images is used for the
        #      table display. Sooner or later we should probably use one or the other.
        self.deck_inst = Deck.Deck(self.conf, height=CARD_HEIGHT, width=CARD_WIDTH)
        card_images = self.init_card_images(self.conf)

    def init_card_images(self, config):
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)

        for j in range(0, 13):
            for i in range(0, 4):
                loc = Card.cardFromValueSuit(ranks[j], suits[i])
                card_im = self.deck_inst.card(suits[i], ranks[j])
                #must use copy(), method_instance not usable in global variable
                card_images[loc] = card_im.copy()
        back_im = self.deck_inst.back()
        card_images[0] = back_im.copy()
        return card_images


    def area_expose(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        if self.tableImage is None or self.playerBackdrop is None:
            try:
                self.playerBackdrop = gtk.gdk.pixbuf_new_from_file(os.path.join(self.conf.graphics_path, u"playerbackdrop.png"))
                self.tableImage = gtk.gdk.pixbuf_new_from_file(os.path.join(self.conf.graphics_path, u"Table.png"))
                self.area.set_size_request(self.tableImage.get_width(), self.tableImage.get_height())
            except:
                return
        if self.cardImages is None:
            self.cardwidth = CARD_WIDTH
            self.cardheight = CARD_HEIGHT
            self.cardImages = [gtk.gdk.Pixmap(self.area.window, self.cardwidth, self.cardheight) for i in range(53)]
            suits = ('s', 'h', 'd', 'c')
            ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
            for j in range(0, 13):
                for i in range(0, 4):
                    index = Card.cardFromValueSuit(ranks[j], suits[i])
                    image = self.deck_inst.card(suits[i], ranks[j])
                    self.cardImages[index].draw_pixbuf(self.gc, image, 0, 0, 0, 0, -1, -1)
            back_im = self.deck_inst.back()
            self.cardImages[0].draw_pixbuf(self.gc, back_im, 0, 0, 0, 0, -1,-1)

        self.area.window.draw_pixbuf(self.gc, self.tableImage, 0, 0, 0, 0)

        if len(self.states) == 0:
            return

        state = self.states[int(self.state.get_value())]

        padding = 6
        communityLeft = int(self.tableImage.get_width() / 2 - 2.5 * self.cardwidth - 2 * padding)
        communityTop = int(self.tableImage.get_height() / 2 - 1.5 * self.cardheight)

        cm = self.gc.get_colormap() #create colormap toi be able to play with colours

        color = cm.alloc_color("white") #defaults to black
        self.gc.set_foreground(color)

        convertx = lambda x: int(x * self.tableImage.get_width() * 0.8) + self.tableImage.get_width() / 2
        converty = lambda y: int(y * self.tableImage.get_height() * 0.6) + self.tableImage.get_height() / 2

        for player in state.players.values():
            playerx = convertx(player.x)
            playery = converty(player.y)
            self.area.window.draw_pixbuf(self.gc, self.playerBackdrop, 0, 0, playerx - self.playerBackdrop.get_width() / 2, playery - padding / 2)
            if player.action=="folds":
                color = cm.alloc_color("grey") #player has folded => greyed out
                self.gc.set_foreground(color)
            else:
                color = cm.alloc_color("white") #player is live
                self.gc.set_foreground(color)
                if state.gametype == 'holdem':
                    cardIndex = Card.encodeCard(player.holecards[0:2])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx - self.cardwidth - padding / 2, playery - self.cardheight, -1, -1)
                    cardIndex = Card.encodeCard(player.holecards[3:5])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + padding / 2, playery - self.cardheight, -1, -1)
                elif state.gametype in ('omahahi', 'omahahilo'):
                    cardIndex = Card.encodeCard(player.holecards[0:2])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx - 2 * self.cardwidth - 3 * padding / 2, playery - self.cardheight, -1, -1)
                    cardIndex = Card.encodeCard(player.holecards[3:5])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx - self.cardwidth - padding / 2, playery - self.cardheight, -1, -1)
                    cardIndex = Card.encodeCard(player.holecards[6:8])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + padding / 2, playery - self.cardheight, -1, -1)
                    cardIndex = Card.encodeCard(player.holecards[9:11])
                    self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + self.cardwidth + 3 * padding / 2, playery - self.cardheight, -1, -1)

            color_string = '#FFFFFF'
            background_color = ''
            self.pangolayout.set_markup('<span foreground="%s" size="medium">%s %s%.2f</span>' % (color_string, player.name, self.currency, player.stack))
            self.area.window.draw_layout(self.gc, playerx - self.pangolayout.get_pixel_size()[0] / 2, playery, self.pangolayout)

            if player.justacted:
                color_string = '#FF0000'
                background_color = 'background="#000000" '
                self.pangolayout.set_markup('<span foreground="%s" size="medium">%s</span>' % (color_string, player.action))
                self.area.window.draw_layout(self.gc, playerx - self.pangolayout.get_pixel_size()[0] / 2, playery + self.pangolayout.get_pixel_size()[1], self.pangolayout)
            else:
                color_string = '#FFFF00'
                background_color = ''
            if player.chips != 0:  #displays amount
                self.pangolayout.set_markup('<span foreground="%s" %s weight="heavy" size="large">%s%.2f</span>' % (color_string, background_color, self.currency, player.chips))
                self.area.window.draw_layout(self.gc, convertx(player.x * .65) - self.pangolayout.get_pixel_size()[0] / 2, converty(player.y * 0.65), self.pangolayout)

        color_string = '#FFFFFF'

        self.pangolayout.set_markup('<span foreground="%s" size="large">%s%.2f</span>' % (color_string, self.currency, state.pot)) #displays pot
        self.area.window.draw_layout(self.gc,self.tableImage.get_width() / 2 - self.pangolayout.get_pixel_size()[0] / 2, self.tableImage.get_height() / 2, self.pangolayout)

        if state.showFlop:
            cardIndex = Card.encodeCard(state.flop[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft, communityTop, -1, -1)
            cardIndex = Card.encodeCard(state.flop[1])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + self.cardwidth + padding, communityTop, -1, -1)
            cardIndex = Card.encodeCard(state.flop[2])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 2 * (self.cardwidth + padding), communityTop, -1, -1)
        if state.showTurn:
            cardIndex = Card.encodeCard(state.turn[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 3 * (self.cardwidth + padding), communityTop, -1, -1)
        if state.showRiver:
            cardIndex = Card.encodeCard(state.river[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 4 * (self.cardwidth + padding), communityTop, -1, -1)

        color = cm.alloc_color("black")      #we don't want to draw the filters and others in red
        self.gc.set_foreground(color)

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
        
        self.state.set_value(0)
        self.state.set_upper(len(self.states) - 1)
        self.state.value_changed()

    def increment_state(self):
        if self.state.get_value() == self.state.get_upper():
            self.playing = False
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
            self.playPauseButton.set_image(image)

        if not self.playing:
            return False

        self.state.set_value(self.state.get_value() + 1)
        return True
    
    def on_destroy(self, window):
        """ Prevent replayer from continue playing after window is closed """
        self.state.disconnect(self.handler_id)

    def slider_changed(self, adjustment):
        alloc = self.area.get_allocation()
        rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
        self.area.window.invalidate_rect(rect, True)    #make sure we refresh the whole screen
        self.area.window.process_updates(True)

    def importhand(self, handid=1):

        h = Hand.hand_factory(handid, self.conf, self.db)
        
        return h

    def play_clicked(self, button):
        self.playing = not self.playing
        image = gtk.Image()
        if self.playing:
            image.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
            gobject.timeout_add(1000, self.increment_state)
        else:
            image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
        self.playPauseButton.set_image(image)
    def start_clicked(self, button):
        self.state.set_value(0)
    def end_clicked(self, button):
        self.state.set_value(self.state.get_upper())
    def flop_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showFlop:
                self.state.set_value(i)
                break
    def turn_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showTurn:
                self.state.set_value(i)
                break
    def river_clicked(self, button):
        for i in range(0, len(self.states)):
            if self.states[i].showRiver:
                self.state.set_value(i)
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

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    if argv is None:
        argv = sys.argv[1:]

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    Configuration.set_logfile("fpdb-log.txt")
    import Options

    (options, argv) = Options.fpdb_options()

    if options.usage == True:
        #Print usage examples and exit
        sys.exit(0)

    if options.sitename:
        options.sitename = Options.site_alias(options.sitename)
        if options.sitename == False:
            usage()

    config = Configuration.Config(file = "HUD_config.test.xml")
    db = Database.Database(config)
    sql = SQL.Sql(db_server = 'sqlite')

    main_window = gtk.Window()
    main_window.connect('destroy', destroy)

    replayer = GuiReplayer(config, sql, main_window, options=options, debug=True)

    main_window.add(replayer.get_vbox())
    main_window.set_default_size(800,800)
    main_window.show()
    gtk.main()

if __name__ == '__main__':
    sys.exit(main())
