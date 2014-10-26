#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
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

import os
import sys

import Charset
import Stove

DEBUG = False

class GuiStove():

    def __init__(self, config, parent, debug=True):
        """Constructor for GuiStove"""
        self.stove = Stove.Stove()
        self.ev = None
        self.boardtext = ""
        self.herorange = ""
        self.villainrange = ""
        self.conf = config
        self.parent = parent

        self.mainHBox = gtk.HBox(False, 0)

        # hierarchy:  self.mainHBox / self.notebook

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)

        self.createFlopTab()
        self.createStudTab()
        self.createDrawTab()


        self.mainHBox.add(self.notebook)

        self.mainHBox.show_all()

        if DEBUG == False:
            warning_string = _("Stove is a GUI mockup of a EV calculation page, and completely non functional.") + "\n "
            warning_string += _("Unless you are interested in developing this feature, please ignore this page.") + "\n "
            warning_string += _("If you are interested in developing the code further see GuiStove.py and Stove.py.") + "\n "
            warning_string += _("Thank you")
            self.warning_box(warning_string)


    def warning_box(self, str, diatitle=_("FPDB WARNING")):
        diaWarning = gtk.Dialog(title=diatitle, parent=self.parent, flags=gtk.DIALOG_DESTROY_WITH_PARENT, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))

        label = gtk.Label(str)
        diaWarning.vbox.add(label)
        label.show()

        response = diaWarning.run()
        diaWarning.destroy()
        return response


    def get_active_text(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]

    def create_combo_box(self, strings):
        combobox = gtk.combo_box_new_text()
        for label in strings:
            combobox.append_text(label)
        combobox.set_active(0)
        return combobox

    def createDrawTab(self):
        tab_title = _("Draw")
        label = gtk.Label(tab_title)

        ddbox = gtk.VBox(False, 0)
        self.notebook.append_page(ddbox, label)

    def createStudTab(self):
        tab_title = _("Stud")
        label = gtk.Label(tab_title)

        ddbox = gtk.VBox(False, 0)
        self.notebook.append_page(ddbox, label)

    def createFlopTab(self):
        # hierarchy: hbox / ddbox     / ddhbox / Label + flop_games_cb | label + players_cb
        #                 / gamehbox / in_frame / table /
        #                            / out_frame

        tab_title = _("Flop")
        label = gtk.Label(tab_title)

        ddbox = gtk.VBox(False, 0)
        self.notebook.append_page(ddbox, label)

        ddhbox = gtk.HBox(False, 0)
        gamehbox = gtk.HBox(False, 0)

        ddbox.add(ddhbox)
        ddbox.add(gamehbox)

        # Combo boxes in the top row

        games =   [ "Holdem", "Omaha", "Omaha 8", ]
        players = [ "2", "3", "4", "5", "6", "7", "8", "9", "10" ]
        flop_games_cb = self.create_combo_box(games)
        players_cb = self.create_combo_box(players)

        label = gtk.Label(_("Gametype")+":")
        ddhbox.add(label)
        ddhbox.add(flop_games_cb)
        label = gtk.Label(_("Players")+":")
        ddhbox.add(label)
        ddhbox.add(players_cb)

        # Frames for Stove input and output

        in_frame = gtk.Frame(_("Input:"))
        out_frame = gtk.Frame(_("Output:"))

        gamehbox.add(in_frame)
        gamehbox.add(out_frame)

        self.outstring = """
No board given. Using Monte-Carlo simulation...
Enumerated 2053443 possible plays.
Your hand: (Ad Ac)
Against the range: {
                    AhAd, AhAs, AdAs, KhKd, KhKs, 
                    KhKc, KdKs, KdKc, KsKc, QhQd, 
                    QhQs, QhQc, QdQs, QdQc, QsQc, 
                    JhJd, JhJs, JhJc, JdJs, JdJc, 
                    JsJc
                   }

  Win       Lose       Tie
 69.91%    15.83%    14.26%

"""
        self.outputlabel = gtk.Label(self.outstring)
        out_frame.add(self.outputlabel)

        # Input Frame
        table = gtk.Table(4, 5, True)
        label = gtk.Label(_("Board:"))
        self.board = gtk.Entry()
        #self.board.connect("changed", self.set_board_flop, self.board)

        btn1 = gtk.Button()
        btn1.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        #btn.connect('clicked', self._some_function, arg)
        table.attach(label, 0, 1, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.board, 1, 2, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(btn1, 2, 3, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)


        label = gtk.Label(_("Player1:"))
        self.p1_board = gtk.Entry()
        #self.p1_board.connect("changed", self.set_hero_cards_flop, self.p1_board)
        btn2 = gtk.Button()
        btn2.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        #btn.connect('clicked', self._some_function, arg)
        btn3 = gtk.Button()
        btn3.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        #btn.connect('clicked', self._some_function, arg)
        table.attach(label, 0, 1, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.p1_board, 1, 2, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(btn2, 2, 3, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(btn3, 3, 4, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)


        label = gtk.Label(_("Player2:"))
        self.p2_board = gtk.Entry()
        #self.p2_board.connect("changed", self.set_villain_cards_flop, self.p2_board)
        btn4 = gtk.Button()
        btn4.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        #btn.connect('clicked', self._some_function, arg)
        btn5 = gtk.Button()
        btn5.set_image(gtk.image_new_from_stock(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON))
        #btn.connect('clicked', self._some_function, arg)
        table.attach(label, 0, 1, 2, 3, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(self.p2_board, 1, 2, 2, 3, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(btn4, 2, 3, 2, 3, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        table.attach(btn5, 3, 4, 2, 3, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        
        btn6 = gtk.Button(_("Results"))
        btn6.connect("pressed", self.update_flop_output_pane, btn6)
        table.attach(btn6, 0, 1, 3, 4, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        in_frame.add(table)

    def set_output_label(self, string):
        self.outputlabel.set_text(string)

    def set_board_flop(self, caller, widget):
        print (_("DEBUG:") + " " + _("called") + " set_board_flop: '%s' '%s'" % (caller ,widget))
        self.boardtext = widget.get_text()

    def set_hero_cards_flop(self, caller, widget):
        print (_("DEBUG:") + " " + _("called") + " set_hero_cards_flop")
        self.herorange = widget.get_text()

    def set_villain_cards_flop(self, caller, widget):
        print (_("DEBUG:") + " " + _("called") + " set_villain_cards_flop")
        self.villainrange = widget.get_text()

    def update_flop_output_pane(self, caller, widget):
        print (_("DEBUG:") + " " + _("called") + " update_flop_output_pane")
#         self.stove.set_board_string(self.boardtext)
#         self.stove.set_hero_cards_string(self.herorange)
#         self.stove.set_villain_range_string(self.villainrange)
        self.stove.set_board_string(self.board.get_text())
        self.stove.set_hero_cards_string(self.p1_board.get_text())
        self.stove.set_villain_range_string(self.p2_board.get_text())
        print (_("DEBUG:") + ("odds_for_range"))
        self.ev = Stove.odds_for_range(self.stove)
        print (_("DEBUG:") + " " + ("set_output_label"))
        self.set_output_label(self.ev.output)



    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainHBox
    #end def get_vbox
