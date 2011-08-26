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

        self.replayBox.pack_start(self.area)

        gobject.timeout_add(1000,self.draw_action)

        self.MyHand = self.importhand()
        self.table = Table(self.area, self.MyHand).table

        if self.MyHand.gametype['currency']=="USD":    #TODO: check if there are others ..
            self.currency="$"
        elif self.MyHand.gametype['currency']=="EUR":
            self.currency="€"

        self.actions=[]     #create list with all actions

        if isinstance(self.MyHand, HoldemOmahaHand):
            if self.MyHand.gametype['category'] == 'holdem':
                self.play_holdem()

        self.action_number=0
        self.action_level=0
        self.pot=0
        self.tableImage = None
        self.cardImages = None


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

        playerid='999'  #makes sure we have an error if player is not recognised
        for i in range(0,len(self.table)):  #surely there must be a better way to find the player id in the table...
            if self.table[i]['name']==self.actions[self.action_number][1]:
                playerid=i

        if self.actions[self.action_number][2]=="folds":
            self.table[playerid]["status"]="folded"

        if self.actions[self.action_number][3]:
            self.table[playerid]["stack"] -= Decimal(self.actions[self.action_number][3])  #decreases stack if player bets
            self.pot += Decimal(self.actions[self.action_number][3]) #increase pot
            self.table[playerid]["chips"] += Decimal(self.actions[self.action_number][3]) #increase player's chips on table


        padding = 5
        communityLeft = int(self.tableImage.get_width() / 2 - 2.5 * self.cardwidth - 2 * padding)
        communityTop = int(self.tableImage.get_height() / 2 - 1.5 * self.cardheight)

        cm = self.gc.get_colormap() #create colormap toi be able to play with colours

        color = cm.alloc_color("black") #defaults to black
        self.gc.set_foreground(color)

        convertx = lambda x: int(x * self.tableImage.get_width() * 0.85) + self.cardwidth
        converty = lambda y: int(y * self.tableImage.get_height() * 0.6) + self.cardheight * 2

        for i in self.table:
            if self.table[i]["status"]=="folded":
                color = cm.alloc_color("grey") #player has folded => greyed out
                self.gc.set_foreground(color)
            else:
                color = cm.alloc_color("black") #player is live
                self.gc.set_foreground(color)

            playerx = convertx(self.table[i]["x"])
            playery = converty(self.table[i]["y"])
            self.pangolayout.set_text(self.table[i]["name"]+self.table[i]["holecards"])     #player names + holecards
            self.area.window.draw_layout(self.gc, playerx, playery, self.pangolayout)
            cardIndex = Card.encodeCard(self.table[i]["holecards"][0:2])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx, playery - self.cardheight, -1, -1)
            cardIndex = Card.encodeCard(self.table[i]["holecards"][3:5])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, playerx + self.cardwidth + padding, playery - self.cardheight, -1, -1)
            self.pangolayout.set_text('$'+str(self.table[i]["stack"]))     #player stacks
            self.area.window.draw_layout(self.gc, playerx + 10, playery + 20, self.pangolayout)

        color = cm.alloc_color("black")
        self.gc.set_foreground(color)

        self.pangolayout.set_text(self.currency+str(self.pot)) #displays pot
        self.area.window.draw_layout(self.gc,self.tableImage.get_width() / 2,270, self.pangolayout)

        if self.actions[self.action_number][0]>1:   #displays flop
            self.pangolayout.set_text(self.MyHand.board['FLOP'][0]+" "+self.MyHand.board['FLOP'][1]+" "+self.MyHand.board['FLOP'][2])
            self.area.window.draw_layout(self.gc,communityLeft,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(self.MyHand.board['FLOP'][0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft, communityTop, -1, -1)
            cardIndex = Card.encodeCard(self.MyHand.board['FLOP'][1])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + self.cardwidth + padding, communityTop, -1, -1)
            cardIndex = Card.encodeCard(self.MyHand.board['FLOP'][2])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 2 * (self.cardwidth + padding), communityTop, -1, -1)
        if self.actions[self.action_number][0]>2:   #displays turn
            self.pangolayout.set_text(self.MyHand.board['TURN'][0])
            self.area.window.draw_layout(self.gc,communityLeft + 60,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(self.MyHand.board['TURN'][0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 3 * (self.cardwidth + padding), communityTop, -1, -1)
        if self.actions[self.action_number][0]>3:   #displays river
            self.pangolayout.set_text(self.MyHand.board['RIVER'][0])
            self.area.window.draw_layout(self.gc,communityLeft + 80,communityTop + self.cardheight, self.pangolayout)
            cardIndex = Card.encodeCard(self.MyHand.board['RIVER'][0])
            self.area.window.draw_drawable(self.gc, self.cardImages[cardIndex], 0, 0, communityLeft + 4 * (self.cardwidth + padding), communityTop, -1, -1)

        color = cm.alloc_color("red")   #highlights the action
        self.gc.set_foreground(color)

        playerx = convertx(self.table[playerid]["x"])
        playery = converty(self.table[playerid]["y"])

        self.pangolayout.set_text(self.actions[self.action_number][2]) #displays action
        self.area.window.draw_layout(self.gc, playerx + 10, playery + 35, self.pangolayout)
        if self.actions[self.action_number][3]:  #displays amount
            self.pangolayout.set_text(self.currency+self.actions[self.action_number][3])
            self.area.window.draw_layout(self.gc, playerx + 10, playery + 55, self.pangolayout)

        color = cm.alloc_color("black")      #we don't want to draw the filters and others in red
        self.gc.set_foreground(color)

    def play_holdem(self):
        actions=('BLINDSANTES','PREFLOP','FLOP','TURN','RIVER')
        for action in actions:
            for i in range(0,len(self.MyHand.actions[action])):
                player=self.MyHand.actions[action][i][0]
                act=self.MyHand.actions[action][i][1]
                try:
                    amount=str(self.MyHand.actions[action][i][2])
                except:
                    amount=''   #no amount
                self.actions.append([actions.index(action),player,act,amount])  #create table with all actions


    def draw_action(self):
        if self.action_number==len(self.actions)-1:     #no more actions, we exit the loop
            return False

        alloc = self.area.get_allocation()
        rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
        self.area.window.invalidate_rect(rect, True)    #make sure we refresh the whole screen
        
        if self.actions[self.action_number][0]!=self.action_level:  #have we changed street ?
            self.action_level=self.actions[self.action_number][0] #record the new street

        self.action_number+=1
        if self.area.window:
            self.area.window.process_updates(True)
        return True


    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox

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

    def temp(self):
        pass

class Table:
    def __init__(self, darea, hand):
        self.darea = darea
        self.hand = hand
        self.players = []
        #self.pixmap = gtk.gdk.Pixmap(darea, width, height, depth=-1)

        # tmp var while refactoring
        self.table = {}
        i = 0
        for seat, name, chips, dummy, dummy in hand.players:
            self.players.append(Player(hand, name, chips, seat))
            self.table[i] = self.players[i].get_hash()
            i += 1

    def draw(self):
        draw_players()
        draw_pot()
        draw_community_cards()

class Player:
    def __init__(self, hand, name, stack, seat):
        self.status    = 'live'
        self.stack     = Decimal(stack)
        self.chips     = 0
        self.seat      = seat
        self.name      = name
        self.holecards = hand.join_holecards(name)
        self.x         = 0.5 + 0.5 * math.cos(2 * self.seat * math.pi / hand.maxseats)
        self.y         = 0.5 + 0.5 * math.sin(2 * self.seat * math.pi / hand.maxseats)

    def get_hash(self):
        return { 'chips': 0,
                 'holecards': self.holecards,
                 'name': self.name,
                 'stack': self.stack,
                 'status': self.status,
                 'x': self.x,
                 'y': self.y,
                }

    def draw(self):
        draw_name()
        draw_stack()
        draw_cards()

class Pot:
    def __init__(self, hand):
        self.total = 0.0

    def draw(self):
        pass

class CommunityCards:
    def __init__(self, hand):
        self.pixbuf = self.gen_pixbuf_from_file(PATH_TO_THE_FILE)

    def draw(self):
        pass


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
