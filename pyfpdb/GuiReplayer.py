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


        self.filters = Filters.Filters(self.db, self.conf, self.sql, display = filters_display)
        #self.filters.registerButton1Name(_("Import Hand"))
        #self.filters.registerButton1Callback(self.importhand)
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

        self.state = gtk.Adjustment(0, 0, 10, 1)
        self.stateSlider = gtk.HScale(self.state)
        self.stateSlider.connect("format_value", lambda x,y: "")
        self.stateSlider.set_digits(0)
        self.state.connect("value_changed", self.slider_changed)
        self.stateSlider.show()

        self.replayBox.pack_start(self.stateSlider, False)

        self.MyHand = self.importhand()

        if self.MyHand.gametype['currency']=="USD":    #TODO: check if there are others ..
            self.currency="$"
        elif self.MyHand.gametype['currency']=="EUR":
            self.currency="€"

        self.states = [] # List with all table states.
        
        if isinstance(self.MyHand, HoldemOmahaHand):
            if self.MyHand.gametype['category'] == 'holdem':
                self.play_holdem()

        self.state.set_upper(len(self.states) - 1)
        for i in range(len(self.states)):
            self.stateSlider.add_mark(i, gtk.POS_BOTTOM, None)

        self.tableImage = None
        self.cardImages = None
        self.playing = False

    def area_expose(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        if self.tableImage is None:
            try:
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

        state = self.states[int(self.state.get_value())]

        padding = 5
        communityLeft = int(self.tableImage.get_width() / 2 - 2.5 * self.cardwidth - 2 * padding)
        communityTop = int(self.tableImage.get_height() / 2 - 1.5 * self.cardheight)

        cm = self.gc.get_colormap() #create colormap toi be able to play with colours

        color = cm.alloc_color("white") #defaults to black
        self.gc.set_foreground(color)

        convertx = lambda x: int(x * self.tableImage.get_width() * 0.85) + self.cardwidth
        converty = lambda y: int(y * self.tableImage.get_height() * 0.6) + self.cardheight * 2

        for player in state.players.values():
            if player.action=="folds":
                color = cm.alloc_color("grey") #player has folded => greyed out
                self.gc.set_foreground(color)
            else:
                color = cm.alloc_color("white") #player is live
                self.gc.set_foreground(color)

            playerx = convertx(player.x)
            playery = converty(player.y)
            self.pangolayout.set_text(player.name + player.holecards)     #player names + holecards
            self.area.window.draw_layout(self.gc, playerx, playery, self.pangolayout)
            cardIndex = Card.encodeCard(player.holecards[0:2])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx, playery - self.cardheight, -1, -1)
            cardIndex = Card.encodeCard(player.holecards[3:5])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + self.cardwidth + padding, playery - self.cardheight, -1, -1)
            self.pangolayout.set_text(self.currency + str(player.stack))     #player stacks
            self.area.window.draw_layout(self.gc, playerx + 10, playery + 20, self.pangolayout)

            if player.justacted:
                color = cm.alloc_color("red")   #highlights the action
                self.gc.set_foreground(color)

                self.pangolayout.set_text(player.action)
                self.area.window.draw_layout(self.gc, playerx + 10, playery + 35, self.pangolayout)
            if player.chips != 0:  #displays amount
                self.pangolayout.set_text(self.currency + str(player.chips))
                self.area.window.draw_layout(self.gc, playerx + 10, playery + 55, self.pangolayout)

        color = cm.alloc_color("white")
        self.gc.set_foreground(color)

        self.pangolayout.set_text(self.currency+str(state.pot)) #displays pot
        self.area.window.draw_layout(self.gc,self.tableImage.get_width() / 2,270, self.pangolayout)

        if state.showFlop:
            self.pangolayout.set_text(state.flop[0] + " " + state.flop[1] + " " + state.flop[2])
            self.area.window.draw_layout(self.gc,communityLeft,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(state.flop[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft, communityTop, -1, -1)
            cardIndex = Card.encodeCard(state.flop[1])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + self.cardwidth + padding, communityTop, -1, -1)
            cardIndex = Card.encodeCard(state.flop[2])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 2 * (self.cardwidth + padding), communityTop, -1, -1)
        if state.showTurn:
            self.pangolayout.set_text(state.turn[0])
            self.area.window.draw_layout(self.gc,communityLeft + 60,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(state.turn[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 3 * (self.cardwidth + padding), communityTop, -1, -1)
        if state.showRiver:
            self.pangolayout.set_text(state.river[0])
            self.area.window.draw_layout(self.gc,communityLeft + 80,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(state.river[0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 4 * (self.cardwidth + padding), communityTop, -1, -1)

        color = cm.alloc_color("black")      #we don't want to draw the filters and others in red
        self.gc.set_foreground(color)

    def play_holdem(self):
        actions=('BLINDSANTES','PREFLOP','FLOP','TURN','RIVER')
        state = TableState(self.MyHand)
        for action in actions:
            if action != 'PREFLOP':
                state = copy.deepcopy(state)
                state.startPhase(action)
                self.states.append(state)
            for i in range(0,len(self.MyHand.actions[action])):
                state = copy.deepcopy(state)
                state.updateForAction(self.MyHand.actions[action][i])
                self.states.append(state)
        state = copy.deepcopy(state)
        state.endHand(self.MyHand.collectees)
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

    def importhand(self, handnumber=1):
        """Temporary function that grabs a Hand object from a specified file. Obviously this will
        be replaced by a function to select a hand from the db in the not so distant future.
        This code has been shamelessly stolen from Carl
        """
        if False:
            settings = {}
            settings.update(self.conf.get_db_parameters())
            settings.update(self.conf.get_import_parameters())
            settings.update(self.conf.get_default_paths())

            importer = fpdb_import.Importer(False, settings, self.conf, None)
            importer.setDropIndexes("don't drop")
            importer.setFailOnError(True)
            importer.setThreads(-1)
            importer.setCallHud(False)
            importer.setFakeCacheHHC(True)

            importer.addBulkImportImportFileOrDir(self.filename, site=self.site)
            (stored, dups, partial, errs, ttime) = importer.runImport()

            hhc = importer.getCachedHHC()
            handlist = hhc.getProcessedHands()

            return handlist[0]
        else:
            # Fetch hand info
            # We need at least sitename, gametype, handid
            # for the Hand.__init__

            ####### Shift this section in Database.py for all to use ######
            handid = 1
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
        self.pot = 0
        self.flop = hand.board["FLOP"]
        self.turn = hand.board["TURN"]
        self.river = hand.board["RIVER"]
        self.showFlop = False
        self.showTurn = False
        self.showRiver = False

        self.players = {}

        for seat, name, chips, dummy, dummy in hand.players:
            self.players[name] = Player(hand, name, chips, seat)

    def startPhase(self, phase):
        if phase == "BLINDSANTES":
            return
        if phase == "PREFLOP":
            return
        
        for player in self.players.values():
            player.justacted = False
            self.pot += player.chips
            player.chips = 0

        if phase == "FLOP":
            self.showFlop = True
        elif phase == "TURN":
            self.showTurn = True
        elif phase == "RIVER":
            self.showRiver = True

    def updateForAction(self, action):
        for player in self.players.values():
            player.justacted = False

        player = self.players[action[0]]
        player.action = action[1]
        player.justacted = True
        if action[1] == "folds" or action[1] == "checks":
            pass
        elif action[1] == "raises" or action[1] == "bets" or action[1] == "calls" or action[1] == "small blind" or action[1] == "big blind":
            player.chips += action[2]
            player.stack -= action[2]
        else:
            print action

    def endHand(self, collectees):
        self.pot = 0
        for player in self.players.values():
            player.justacted = False
            player.chips = 0
        for name,amount in collectees.items():
            player = self.players[name]
            player.chips += amount
            player.action = "collected"
            player.justacted = True

class Player:
    def __init__(self, hand, name, stack, seat):
        self.stack     = Decimal(stack)
        self.chips     = 0
        self.seat      = seat
        self.name      = name
        self.action    = None
        self.justacted = False
        self.holecards = hand.join_holecards(name)
        self.x         = 0.5 + 0.5 * math.cos(2 * self.seat * math.pi / hand.maxseats)
        self.y         = 0.5 + 0.5 * math.sin(2 * self.seat * math.pi / hand.maxseats)

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
