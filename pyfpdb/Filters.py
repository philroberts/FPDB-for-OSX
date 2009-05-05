#!/usr/bin/python

#Copyright 2008 Steffen Jobbagy-Felso
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
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

import threading
import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
from optparse import OptionParser
from time import *
#import pokereval

import Configuration
import fpdb_db
import FpdbSQLQueries

class Filters(threading.Thread):
    def __init__(self, db, settings, config, qdict, display = {},debug=True):
        self.debug=debug
        #print "start of GraphViewer constructor"
        self.db=db
        self.cursor=db.cursor
        self.settings=settings
        self.sql=qdict
        self.conf = config

        self.sites  = {}
        self.games  = {}
        self.limits = {}
        self.siteid = {}
        self.heroes = {}

        # For use in date ranges.
        self.start_date = gtk.Entry(max=12)
        self.end_date = gtk.Entry(max=12)
        self.start_date.set_property('editable', False)
        self.end_date.set_property('editable', False)

        # Outer Packing box        
        self.mainVBox = gtk.VBox(False, 0)

        playerFrame = gtk.Frame("Hero:")
        playerFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillPlayerFrame(vbox)
        playerFrame.add(vbox)

        sitesFrame = gtk.Frame("Sites:")
        sitesFrame.set_label_align(0.0, 0.0)
        vbox = gtk.VBox(False, 0)

        self.fillSitesFrame(vbox)
        sitesFrame.add(vbox)

        # Game types
        gamesFrame = gtk.Frame("Games:")
        gamesFrame.set_label_align(0.0, 0.0)
        gamesFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillGamesFrame(vbox)
        gamesFrame.add(vbox)

        # Limits
        limitsFrame = gtk.Frame("Limits:")
        limitsFrame.set_label_align(0.0, 0.0)
        limitsFrame.show()
        vbox = gtk.VBox(False, 0)
        self.cbLimits = {}
        self.cbNoLimits = None
        self.cbAllLimits = None

        self.fillLimitsFrame(vbox, display)
        limitsFrame.add(vbox)

        dateFrame = gtk.Frame("Date:")
        dateFrame.set_label_align(0.0, 0.0)
        dateFrame.show()
        vbox = gtk.VBox(False, 0)

        self.fillDateFrame(vbox)
        dateFrame.add(vbox)

        self.Button1=gtk.Button("Unamed 1")

        self.Button2=gtk.Button("Unamed 2")
        #self.exportButton.connect("clicked", self.exportGraph, "show clicked")
        self.Button2.set_sensitive(False)

        self.mainVBox.add(playerFrame)
        self.mainVBox.add(sitesFrame)
        self.mainVBox.add(gamesFrame)
        self.mainVBox.add(limitsFrame)
        self.mainVBox.add(dateFrame)
        self.mainVBox.add(self.Button1)
        self.mainVBox.add(self.Button2)

        self.mainVBox.show_all()

        # Should do this cleaner
        if display["Heroes"] == False:
            playerFrame.hide()
        if display["Sites"] == False:
            sitesFrame.hide()
        if display["Games"] == False:
            gamesFrame.hide()
        if display["Limits"] == False:
            limitsFrame.hide()
        if display["Dates"] == False:
            dateFrame.hide()
        if display["Button1"] == False:
            self.Button1.hide()
        if display["Button2"] == False:
            self.Button2.hide()

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    def getSites(self):
        return self.sites

    def getSiteIds(self):
        return self.siteid

    def getHeroes(self):
        return self.heroes

    def getLimits(self):
        ltuple = []
        for l in self.limits:
            if self.limits[l] == True:
                ltuple.append(l)
        return ltuple

    def getDates(self):
        return self.__get_dates()

    def registerButton1Name(self, title):
        self.Button1.set_label(title)

    def registerButton1Callback(self, callback):
        self.Button1.connect("clicked", callback, "clicked")

    def registerButton2Name(self, title):
        self.Button2.set_label(title)

    def registerButton2Callback(self, callback):
        self.Button2.connect("clicked", callback, "clicked")

    def cardCallback(self, widget, data=None):
        print "DEBUG: %s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])

    def createPlayerLine(self, hbox, site, player):
        label = gtk.Label(site +" id:")
        hbox.pack_start(label, False, False, 0)

        pname = gtk.Entry()
        pname.set_text(player)
        pname.set_width_chars(20)
        hbox.pack_start(pname, False, True, 0)
        pname.connect("changed", self.__set_hero_name, site)
        #TODO: Look at GtkCompletion - to fill out usernames

        self.__set_hero_name(pname, site)

    def __set_hero_name(self, w, site):
        self.heroes[site] = w.get_text()
#        print "DEBUG: settings heroes[%s]: %s"%(site, self.heroes[site])

    def createSiteLine(self, hbox, site):
        cb = gtk.CheckButton(site)
        cb.connect('clicked', self.__set_site_select, site)
        cb.set_active(True)
        hbox.pack_start(cb, False, False, 0)

    def createGameLine(self, hbox, game):
        cb = gtk.CheckButton(game)
        cb.connect('clicked', self.__set_game_select, game)
        hbox.pack_start(cb, False, False, 0)

    def createLimitLine(self, hbox, limit):
        cb = gtk.CheckButton(str(limit))
        cb.connect('clicked', self.__set_limit_select, limit)
        hbox.pack_start(cb, False, False, 0)
        if limit != "None":
            cb.set_active(True)
        return(cb)

    def __set_site_select(self, w, site):
        #print w.get_active()
        self.sites[site] = w.get_active()
        print "self.sites[%s] set to %s" %(site, self.sites[site])

    def __set_game_select(self, w, game):
        #print w.get_active()
        self.games[game] = w.get_active()
        print "self.games[%s] set to %s" %(game, self.games[game])

    def __set_limit_select(self, w, limit):
        #print w.get_active()
        self.limits[limit] = w.get_active()
        print "self.limit[%s] set to %s" %(limit, self.limits[limit])
        if str(limit).isdigit():
            if self.limits[limit]:
                if self.cbNoLimits != None:
                    self.cbNoLimits.set_active(False)
            else:
                if self.cbAllLimits != None:
                    self.cbAllLimits.set_active(False)
        elif limit == "All":
            if self.limits[limit]:
                for cb in self.cbLimits.values():
                    cb.set_active(True)
        elif limit == "None":
            if self.limits[limit]:
                for cb in self.cbLimits.values():
                    cb.set_active(False)

    def fillPlayerFrame(self, vbox):
        for site in self.conf.get_supported_sites():
            pathHBox = gtk.HBox(False, 0)
            vbox.pack_start(pathHBox, False, True, 0)

            player = self.conf.supported_sites[site].screen_name
            self.createPlayerLine(pathHBox, site, player)

    def fillSitesFrame(self, vbox):
        for site in self.conf.get_supported_sites():
            hbox = gtk.HBox(False, 0)
            vbox.pack_start(hbox, False, True, 0)
            self.createSiteLine(hbox, site)
            #Get db site id for filtering later
            self.cursor.execute(self.sql.query['getSiteId'], (site,))
            result = self.db.cursor.fetchall()
            if len(result) == 1:
                self.siteid[site] = result[0][0]
            else:
                print "Either 0 or more than one site matched - EEK"

    def fillGamesFrame(self, vbox):
        self.cursor.execute(self.sql.query['getGames'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            for line in result:
                hbox = gtk.HBox(False, 0)
                vbox.pack_start(hbox, False, True, 0)
                self.createGameLine(hbox, line[0])
        else:
            print "INFO: No games returned from database"

    def fillLimitsFrame(self, vbox, display):
        self.cursor.execute(self.sql.query['getLimits'])
        result = self.db.cursor.fetchall()
        if len(result) >= 1:
            hbox = gtk.HBox(True, 0)
            vbox.pack_start(hbox, False, False, 0)
            vbox1 = gtk.VBox(False, 0)
            hbox.pack_start(vbox1, False, False, 0)
            vbox2 = gtk.VBox(False, 0)
            hbox.pack_start(vbox2, False, False, 0)
            for i, line in enumerate(result):
                hbox = gtk.HBox(False, 0)
                if i < len(result)/2:
                    vbox1.pack_start(hbox, False, False, 0)
                else:
                    vbox2.pack_start(hbox, False, False, 0)
                self.cbLimits[line[0]] = self.createLimitLine(hbox, line[0])
            if "LimitSep" in display and display["LimitSep"] == True and len(result) >= 2:
                hbox = gtk.HBox(False, 0)
                vbox.pack_start(hbox, False, True, 0)
                self.cbAllLimits = self.createLimitLine(hbox, "All")
                hbox = gtk.HBox(False, 0)
                vbox.pack_start(hbox, False, True, 0)
                self.cbNoLimits = self.createLimitLine(hbox, "None")
                hbox = gtk.HBox(False, 0)
                vbox.pack_start(hbox, False, True, 0)
                cb = self.createLimitLine(hbox, "Separate levels")
        else:
            print "INFO: No games returned from database"

    def fillCardsFrame(self, vbox):
        hbox1 = gtk.HBox(True,0)
        hbox1.show()
        vbox.pack_start(hbox1, True, True, 0)

        cards = [ "A", "K","Q","J","T","9","8","7","6","5","4","3","2" ]

        for j in range(0, len(cards)):
            hbox1 = gtk.HBox(True,0)
            hbox1.show()
            vbox.pack_start(hbox1, True, True, 0)
            for i in range(0, len(cards)):
                if i < (j + 1):
                    suit = "o"
                else:
                    suit = "s"
                button = gtk.ToggleButton("%s%s%s" %(cards[i], cards[j], suit))
                button.connect("toggled", self.cardCallback, "%s%s%s" %(cards[i], cards[j], suit))
                hbox1.pack_start(button, True, True, 0)
                button.show()

    def fillDateFrame(self, vbox):
        # Hat tip to Mika Bostrom - calendar code comes from PokerStats
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)

        lbl_start = gtk.Label('From:')

        btn_start = gtk.Button()
        btn_start.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_start.connect('clicked', self.__calendar_dialog, self.start_date)

        hbox.pack_start(lbl_start, expand=False, padding=3)
        hbox.pack_start(btn_start, expand=False, padding=3)
        hbox.pack_start(self.start_date, expand=False, padding=2)

        #New row for end date
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)

        lbl_end = gtk.Label('  To:')
        btn_end = gtk.Button()
        btn_end.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        btn_end.connect('clicked', self.__calendar_dialog, self.end_date)

        btn_clear = gtk.Button(label=' Clear Dates ')
        btn_clear.connect('clicked', self.__clear_dates)

        hbox.pack_start(lbl_end, expand=False, padding=3)
        hbox.pack_start(btn_end, expand=False, padding=3)
        hbox.pack_start(self.end_date, expand=False, padding=2)

        hbox.pack_start(btn_clear, expand=False, padding=15)

    def __calendar_dialog(self, widget, entry):
        d = gtk.Window(gtk.WINDOW_TOPLEVEL)
        d.set_title('Pick a date')

        vb = gtk.VBox()
        cal = gtk.Calendar()
        vb.pack_start(cal, expand=False, padding=0)

        btn = gtk.Button('Done')
        btn.connect('clicked', self.__get_date, cal, entry, d)

        vb.pack_start(btn, expand=False, padding=4)

        d.add(vb)
        d.set_position(gtk.WIN_POS_MOUSE)
        d.show_all()

    def __clear_dates(self, w):
        self.start_date.set_text('')
        self.end_date.set_text('')

    def __get_dates(self):
        t1 = self.start_date.get_text()
        t2 = self.end_date.get_text()

        if t1 == '':
            t1 = '1970-01-01'
        if t2 == '':
            t2 = '2020-12-12'

        return (t1, t2)

    def __get_date(self, widget, calendar, entry, win):
# year and day are correct, month is 0..11
        (year, month, day) = calendar.get_date()
        month += 1
        ds = '%04d-%02d-%02d' % (year, month, day)
        entry.set_text(ds)
        win.destroy()

def main(argv=None):
    """main can also be called in the python interpreter, by supplying the command line as the argument."""
    if argv is None:
        argv = sys.argv[1:]

    def destroy(*args):  # call back for terminating the main eventloop
        gtk.main_quit()

    parser = OptionParser()
    (options, sys.argv) = parser.parse_args(args = argv)

    config = Configuration.Config()
    db = None
    
    settings = {}

    settings.update(config.get_db_parameters())
    settings.update(config.get_tv_parameters())
    settings.update(config.get_import_parameters())
    settings.update(config.get_default_paths())

    db = fpdb_db.fpdb_db()
    db.connect(settings['db-backend'],
               settings['db-host'],
               settings['db-databaseName'],
               settings['db-user'],
               settings['db-password'])

    qdict = FpdbSQLQueries.FpdbSQLQueries(db.get_backend_name())

    i = Filters(db, settings, config, qdict)
    main_window = gtk.Window()
    main_window.connect('destroy', destroy)
    main_window.add(i.get_vbox())
    main_window.show()
    gtk.main()

if __name__ == '__main__':
   sys.exit(main())


