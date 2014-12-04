#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hud.py

Create and manage the hud overlays.
"""
#    Copyright 2008-2012  Ray E. Barker

#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################
# todo
 
import L10n
_ = L10n.get_translation()

#    Standard Library modules
import string
import logging
import copy

# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    FreePokerTools modules
import Configuration
import Database
import Hand


def importName(module_name, name):
    """Import a named object 'name' from module 'module_name'."""
#    Recipe 16.3 in the Python Cookbook, 2nd ed.  Thanks!!!!

    try:
        module = __import__(module_name, globals(), locals(), [name])
    except Exception as e:
        log.error("Could not load hud module %s: %s" % (module_name, e))
        return None
    return(getattr(module, name))


class Hud:
    def __init__(self, parent, table, max, poker_game, game_type, config):
#    __init__ is (now) intended to be called from the stdin thread, so it
#    must not touch the gui
        #if parent is None:  # running from cli .. # fixme dont think this is working as expected
        #    self.parent = self
        #else:
        #    self.parent    = parent
        #print "parent", parent
        self.parent        = parent
        self.table         = table
        self.config        = config
        self.poker_game    = poker_game
        self.game_type     = game_type # (ring|tour)
        self.max           = max

                      
        self.site          = table.site
        self.hud_params    = dict.copy(parent.hud_params) # we must dict.copy a fresh hud_params dict
                                                          # because each aux hud can control local hud param 
                                                          # settings.  Simply assigning the dictionary does not
                                                          # create a local/discrete version of the dictionary,
                                                          # so the different hud-windows get cross-contaminated
        self.aux_windows   = []
        
        self.site_parameters = config.get_site_parameters(self.table.site)
        self.supported_games_parameters = config.get_supported_games_parameters(self.poker_game, self.game_type)
        self.layout_set = config.get_layout(self.table.site, self.game_type)

        # Just throw error and die if any serious config issues are discovered
        if self.supported_games_parameters == None:
            log.error(_("No <game_stat_set> found for %s games for type %s.\n") % (self.poker_game, self.game_type))
            return
            
        if self.layout_set == None:
            log.error(_("No layout found for %s games for site %s.\n") % (self.game_type, self.table.site))
            return
                       
        if self.max not in self.layout_set.layout:
            log.error(_("No layout found for %d-max %s games for site %s.\n") % (self.max, self.game_type, self.table.site))
            return
        else:
            self.layout = copy.deepcopy(self.layout_set.layout[self.max]) # deepcopy required here, because self.layout is used
                                                                        # to propagate block moves from hud to mucked display
                                                                        # (needed because there is only 1 layout for all aux)
                                                                        #
                                                                        # if we didn't deepcopy, self.layout would be shared
                                                                        # amongst all open huds - this is fine until one of the
                                                                        # huds does a resize, and then we have a total mess to 
                                                                        # understand how a single block move on a resized screen
                                                                        # should be propagated to other tables of different sizes
                                
        # if there are AUX windows configured, set them up
        if not self.supported_games_parameters['aux'] == [""]:
            for aux in self.supported_games_parameters['aux'].split(","):
                aux=string.strip(aux) # remove leading/trailing spaces
                aux_params = config.get_aux_parameters(aux)
                my_import = importName(aux_params['module'], aux_params['class'])
                if my_import == None:
                    continue
                #The main action happening below !!!
                # the module/class is instantiated and is fed the config
                # and aux_params.  Normally this is ultimately inherited
                # at Mucked.Aux_seats() for a hud aux
                #
                #The instatiated aux object is recorded in the
                # self.aux_windows list in this module
                #
                #Subsequent updates to the aux's are controlled by
                # hud_main.pyw
                #
                self.aux_windows.append(my_import(self, config, aux_params))


        self.creation_attrs = None
        

    def move_table_position(self): pass

    def kill(self, *args):
#    kill all stat_windows, popups and aux_windows in this HUD
#    heap dead, burnt bodies, blood 'n guts, veins between my teeth
#    kill all aux windows
        for aux in self.aux_windows:
            aux.destroy()
        self.aux_windows = []

    def resize_windows(self):
        # resize self.layout object; this will then be picked-up
        # by all attached aux's when called by hud_main.idle_update
        
        x_scale = 1.0 * self.table.width / self.layout.width
        y_scale = 1.0 * self.table.height / self.layout.height
        
        for i in (range(1, self.max + 1)):
            if self.layout.location[i]:
                self.layout.location[i] = (
                (int(self.layout.location[i][0] * x_scale)),
                (int(self.layout.location[i][1] * y_scale))      )

        self.layout.common = (
                int(self.layout.common[0] * x_scale),
                int(self.layout.common[1] * y_scale)       )
        
        self.layout.width = self.table.width
        self.layout.height = self.table.height
        
    def reposition_windows(self, *args): pass

    def save_layout(self, *args):
#    ask each aux to save its layout back to the config object
        [aux.save_layout() for aux in self.aux_windows]
#    write the layouts back to the HUD_config
        self.config.save()


    def create(self, hand, config, stat_dict):
        # update this hud, to the stats and players as of "hand"
        # hand is the hand id of the most recent hand played at this table

        self.stat_dict = stat_dict # stat_dict from HUD_main.read_stdin is mapped here
        # the db_connection created in HUD_Main is NOT available to the
        #  hud.py and aux handlers, so create a fresh connection in this class
        # if the db connection is made in __init__, then the sqlite db threading will fail
        #  so the db connection is made here instead.
        self.db_hud_connection = Database.Database(self.config)
        # Load a hand instance (factory will load correct type for this hand)
        self.hand_instance = Hand.hand_factory(hand, config, self.db_hud_connection)
        self.db_hud_connection.connection.rollback()
        log.info(_('Creating hud from hand ')+str(hand))


    def update(self, hand, config):
         # re-load a hand instance (factory will load correct type for this hand)
        self.hand_instance = Hand.hand_factory(hand, config, self.db_hud_connection)
        self.db_hud_connection.connection.rollback()
