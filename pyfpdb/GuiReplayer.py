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

import pprint
pp = pprint.PrettyPrinter(indent=4)


class GuiReplayer:
    def __init__(self, config, querylist, mainwin, options = None, debug=True):
        self.debug = debug
        self.conf = config
        self.main_window = mainwin
        self.sql = querylist

        # These are temporary variables until it becomes possible
        # to select() a Hand object from the database
        self.filename="regression-test-files/cash/Stars/Flop/NLHE-FR-USD-0.01-0.02-201005.microgrind.txt"
        self.site="PokerStars"

#        if options.filename != None:
#            self.filename = options.filename
#        if options.sitename != None:
#            self.site = options.sitename

        self.db = Database.Database(self.conf, sql=self.sql)

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
                    "Groups"    : False,
                    "GroupsAll" : False,
                    "Button1"   : True,
                    "Button2"   : False
                  }


        self.states = [] # List with all table states.
        
        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        self.filters.registerButton1Name(_("Load Hands"))
        self.filters.registerButton1Callback(self.loadHands)
        #self.filters.registerButton2Name(_("temp"))
        #self.filters.registerButton2Callback(self.temp())

        # hierarchy:  self.mainHBox / self.hpane / self.replayBox / self.area

        self.mainHBox = gtk.HBox(False, 0)
        self.mainHBox.show()

        self.leftPanelBox = self.filters.get_vbox()

        self.hpane = gtk.HPaned()
        self.hpane.pack1(self.leftPanelBox)
        self.mainHBox.add(self.hpane)

        self.replayBox = gtk.VBox(False, 0)
        self.replayBox.show()

        self.hpane.pack2(self.replayBox)
        self.hpane.show()

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
        self.state.connect("value_changed", self.slider_changed)
        self.stateSlider.show()

        self.replayBox.pack_start(self.stateSlider, False)

        self.tableImage = None
        self.playerBackdrop = None
        self.cardImages = None
        self.playing = False

    def loadHands(self, button, userdata):
        result = self.handIdsFromDateRange(self.filters.getDates()[0], self.filters.getDates()[1])
        self.refreshHands(result)

    def handIdsFromDateRange(self, start, end):
        q = "SELECT id FROM Hands h WHERE datetime(h.startTime) between '" + start + "' and '" + end + "' order by startTime"

        c = self.db.get_cursor()

        c.execute(q)
        return [r[0] for r in c.fetchall()]

    def refreshHands(self, handids):
        self.handids = handids
        self.hands = []
        for handid in self.handids:
            self.hands.append(self.importhand(handid))

        try:
            self.handswin.destroy()
        except:
            pass
        self.handswin = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.handswin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.replayBox.pack_end(self.handswin)
        liststore = gtk.ListStore(*([str] * 5))
        view = gtk.TreeView(model=liststore)
        view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.handswin.add(view)

        textcell = gtk.CellRendererText()
        textcell50 = gtk.CellRendererText()
        textcell50.set_property('xalign', 0.5)
        numcell = gtk.CellRendererText()
        numcell.set_property('xalign', 1.0)

        
        col = gtk.TreeViewColumn("Hero")
        col.pack_start(textcell)
        col.add_attribute(textcell, 'text', 0)
        view.append_column(col)
        col = gtk.TreeViewColumn("Flop")
        col.pack_start(textcell)
        col.add_attribute(textcell, 'text', 1)
        view.append_column(col)
        col = gtk.TreeViewColumn("Turn")
        col.pack_start(textcell)
        col.add_attribute(textcell, 'text', 2)
        view.append_column(col)
        col = gtk.TreeViewColumn("River")
        col.pack_start(textcell)
        col.add_attribute(textcell, 'text', 3)
        view.append_column(col)
        col = gtk.TreeViewColumn("Won")
        col.pack_start(textcell)
        col.add_attribute(textcell, 'text', 4)
        view.append_column(col)
        selection = view.get_selection()
        selection.set_select_function(self.select_hand, None, True)

        for hand in self.hands:
            hero = self.filters.getHeroes()[hand.sitename]
            won = 0
            if hero in hand.collectees.keys():
                won = hand.collectees[hero]
            liststore.append([hand.join_holecards(hero), hand.board["FLOP"], hand.board["TURN"], hand.board["RIVER"], str(won)])
        self.handswin.show_all()

    def select_hand(self, selection, model, path, is_selected, userdata):
        self.states = [] # List with all table states.
        if is_selected:
            return True

        hand = self.hands[path[0]]
        if hand.gametype['currency']=="USD":    #TODO: check if there are others ..
            self.currency="$"
        elif hand.gametype['currency']=="EUR":
            self.currency="€"
        else:
            self.currency = hand.gametype['currency']

        if isinstance(hand, HoldemOmahaHand):
            if hand.gametype['category'] == 'holdem':
                self.play_holdem(hand)
            else:
                print "Unhandled game type " + hand.gametype['category']
                return False

        self.state.set_value(0)
        self.state.set_upper(len(self.states) - 1)
        self.state.value_changed()
        return True

    def area_expose(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        if self.tableImage is None or self.playerBackdrop is None:
            try:
                self.playerBackdrop = gtk.gdk.pixbuf_new_from_file("../gfx/playerbackdrop.png")
                self.tableImage = gtk.gdk.pixbuf_new_from_file("../gfx/Table.png")
                self.area.set_size_request(self.tableImage.get_width(), self.tableImage.get_height())
            except:
                return
        if self.cardImages is None:
            try:
                pb = gtk.gdk.pixbuf_new_from_file("Cards01.png")
            except:
                return
            self.cardwidth = pb.get_width() / 14
            self.cardheight = pb.get_height() / 6
            
            self.cardImages = [gtk.gdk.Pixmap(self.area.window, self.cardwidth, self.cardheight) for i in range(53)]
            suits = ('s', 'h', 'd', 'c')
            ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
            for j in range(0, 13):
                for i in range(0, 4):
                    index = Card.cardFromValueSuit(ranks[j], suits[i])
                    self.cardImages[index].draw_pixbuf(self.gc, pb, self.cardwidth * j, self.cardheight * i, 0, 0, self.cardwidth, self.cardheight)
            self.cardImages[0].draw_pixbuf(self.gc, pb, self.cardwidth*13, self.cardheight*2, 0, 0, self.cardwidth, self.cardheight)

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
                cardIndex = Card.encodeCard(player.holecards[0:2])
                self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx - self.cardwidth - padding / 2, playery - self.cardheight, -1, -1)
                cardIndex = Card.encodeCard(player.holecards[3:5])
                self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + padding / 2, playery - self.cardheight, -1, -1)

            self.pangolayout.set_text("%s %s%.2f" % (player.name, self.currency, player.stack))
            self.area.window.draw_layout(self.gc, playerx - self.pangolayout.get_pixel_size()[0] / 2, playery, self.pangolayout)

            if player.justacted:
                color = cm.alloc_color("red")   #highlights the action
                self.gc.set_foreground(color)

                self.pangolayout.set_text(player.action)
                self.area.window.draw_layout(self.gc, playerx - self.pangolayout.get_pixel_size()[0] / 2, playery + self.pangolayout.get_pixel_size()[1], self.pangolayout)
            if player.chips != 0:  #displays amount
                self.pangolayout.set_text("%s%.2f" % (self.currency, player.chips))
                self.area.window.draw_layout(self.gc, convertx(player.x * .65) - self.pangolayout.get_pixel_size()[0] / 2, converty(player.y * 0.65), self.pangolayout)

        color = cm.alloc_color("white")
        self.gc.set_foreground(color)

        self.pangolayout.set_text("%s%.2f" % (self.currency, state.pot)) #displays pot
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

    def play_holdem(self, hand):
        actions=('BLINDSANTES','PREFLOP','FLOP','TURN','RIVER')
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

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox

    def slider_changed(self, adjustment):
        alloc = self.area.get_allocation()
        rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
        self.area.window.invalidate_rect(rect, True)    #make sure we refresh the whole screen
        self.area.window.process_updates(True)

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
            h = HoldemOmahaHand(config = self.conf, hhc = None, sitename=res[0], gametype = gametype, handText=None, builtFrom = "DB", handid=handid)
            h.select(self.db, handid)
        elif gametype['base'] == 'stud':
            print "DEBUG: Create stud hand here"
        elif gametype['base'] == 'draw':
            print "DEBUG: Create draw hand here"
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

        self.players = {}

        for seat, name, chips, dummy, dummy in hand.players:
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
            self.pot += player.chips
            player.chips = Decimal(0)
        self.bet = Decimal(0)

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
