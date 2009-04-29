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

#This file contains methods to store hands into the db. decides to move this
#into a seperate file since its ugly, fairly long and just generally in the way.

from time import time

import fpdb_simple

MYSQL_INNODB    = 2
PGSQL           = 3
SQLITE          = 4

fastStoreHudCache = False   # set this to True to test the new storeHudCache routine

saveActions = True  # set this to False to avoid storing action data
                    # Pros: speeds up imports
                    # Cons: no action data is saved, so you need to keep the hand histories
                    #       variance not available on stats page
                    #       no graphs

#stores a stud/razz hand into the database
def ring_stud(config, backend, db, cursor, base, category, site_hand_no, gametype_id, hand_start_time
             ,names, player_ids, start_cashes, antes, card_values, card_suits, winnings, rakes
             ,action_types, allIns, action_amounts, actionNos, hudImportData, maxSeats, tableName
             ,seatNos):

    import_options = config.get_import_parameters()
    
    saveActions = False if import_options['saveActions'] == False else True
    fastStoreHudCache = True if import_options['fastStoreHudCache'] == True else False

    fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
    
    hands_id = fpdb_simple.storeHands(backend, db, cursor, site_hand_no, gametype_id
                                   ,hand_start_time, names, tableName, maxSeats)
    
    #print "before calling store_hands_players_stud, antes:", antes
    hands_players_ids = fpdb_simple.store_hands_players_stud(backend, db, cursor, hands_id, player_ids
                                                          ,start_cashes, antes, card_values
                                                          ,card_suits, winnings, rakes, seatNos)
    
    fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
    
    if saveActions:
        fpdb_simple.storeActions(cursor, hands_players_ids, action_types
                                ,allIns, action_amounts, actionNos)
    return hands_id
#end def ring_stud

def ring_holdem_omaha(config, backend, db, cursor, base, category, site_hand_no, gametype_id
                     ,hand_start_time, names, player_ids, start_cashes, positions, card_values
                     ,card_suits, board_values, board_suits, winnings, rakes, action_types, allIns
                     ,action_amounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
    """stores a holdem/omaha hand into the database"""

    import_options = config.get_import_parameters()
    saveActions = False if import_options['saveActions'] == False else True
    fastStoreHudCache = True if import_options['fastStoreHudCache'] == True else False

#   print "DEBUG: saveActions = '%s' fastStoreHudCache = '%s'"%(saveActions, fastStoreHudCache)
#   print "DEBUG: import_options = ", import_options

    t0 = time()
    fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
    t1 = time()
    fpdb_simple.fill_board_cards(board_values, board_suits)
    t2 = time()

    hands_id = fpdb_simple.storeHands(backend, db, cursor, site_hand_no, gametype_id
                                   ,hand_start_time, names, tableName, maxSeats)
    t3 = time()
    hands_players_ids = fpdb_simple.store_hands_players_holdem_omaha(
                               backend, db, cursor, category, hands_id, player_ids, start_cashes
                             , positions, card_values, card_suits, winnings, rakes, seatNos)
    t4 = time()            
    #print "ring holdem, backend=%d" % backend
    if fastStoreHudCache:
        fpdb_simple.storeHudCache2(backend, cursor, base, category, gametype_id, player_ids, hudImportData)
    else:
        fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
    t5 = time()
    fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
    t6 = time()
    if saveActions:
        fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
    t7 = time()
    #print "fills=(%4.3f) saves=(%4.3f,%4.3f,%4.3f,%4.3f)" % (t2-t0, t3-t2, t4-t3, t5-t4, t6-t5)
    return hands_id
#end def ring_holdem_omaha

def tourney_holdem_omaha(config, backend, db, cursor, base, category, siteTourneyNo, buyin, fee, knockout
                        ,entries, prizepool, tourney_start, payin_amounts, ranks, tourneyTypeId
                        ,siteId #end of tourney specific params
                        ,site_hand_no, gametype_id, hand_start_time, names, player_ids
                        ,start_cashes, positions, card_values, card_suits, board_values
                        ,board_suits, winnings, rakes, action_types, allIns, action_amounts
                        ,actionNos, hudImportData, maxSeats, tableName, seatNos):
    """stores a tourney holdem/omaha hand into the database"""

    import_options = config.get_import_parameters()
    saveActions = True if import_options['saveActions'] == True else False
    fastStoreHudCache = True if import_options['fastStoreHudCache'] == True else False

    fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
    fpdb_simple.fill_board_cards(board_values, board_suits)
    
    tourney_id = fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourney_start)
    tourneys_players_ids = fpdb_simple.store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings)
    
    hands_id = fpdb_simple.storeHands(backend, db, cursor, site_hand_no, gametype_id
                                   ,hand_start_time, names, tableName, maxSeats)
    
    hands_players_ids = fpdb_simple.store_hands_players_holdem_omaha_tourney(
                      backend, db, cursor, category, hands_id, player_ids, start_cashes, positions
                    , card_values, card_suits, winnings, rakes, seatNos, tourneys_players_ids)
    
    #print "tourney holdem, backend=%d" % backend
    if fastStoreHudCache:
        fpdb_simple.storeHudCache2(backend, cursor, base, category, gametype_id, player_ids, hudImportData)
    else:
        fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
    
    fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
    
    if saveActions:
        fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
    return hands_id
#end def tourney_holdem_omaha

def tourney_stud(config, backend, db, cursor, base, category, siteTourneyNo, buyin, fee, knockout, entries
                ,prizepool, tourneyStartTime, payin_amounts, ranks, tourneyTypeId, siteId
                ,siteHandNo, gametypeId, handStartTime, names, playerIds, startCashes, antes
                ,cardValues, cardSuits, winnings, rakes, actionTypes, allIns, actionAmounts
                ,actionNos, hudImportData, maxSeats, tableName, seatNos):
#stores a tourney stud/razz hand into the database

    import_options = config.get_import_parameters()
    saveActions = True if import_options['saveActions'] == True else False
    fastStoreHudCache = True if import_options['fastStoreHudCache'] == True else False
    
    fpdb_simple.fillCardArrays(len(names), base, category, cardValues, cardSuits)
    
    tourney_id = fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourneyStartTime)
    
    tourneys_players_ids = fpdb_simple.store_tourneys_players(cursor, tourney_id, playerIds, payin_amounts, ranks, winnings)
    
    hands_id = fpdb_simple.storeHands(backend, db, cursor, siteHandNo, gametypeId, handStartTime, names, tableName, maxSeats)
    
    hands_players_ids = fpdb_simple.store_hands_players_stud_tourney(backend, db, cursor, hands_id
                                             , playerIds, startCashes, antes, cardValues, cardSuits
                                             , winnings, rakes, seatNos, tourneys_players_ids)
    
    fpdb_simple.storeHudCache(cursor, base, category, gametypeId, playerIds, hudImportData)
    
    if saveActions:
        fpdb_simple.storeActions(cursor, hands_players_ids, actionTypes, allIns, actionAmounts, actionNos)
    return hands_id
#end def tourney_stud
