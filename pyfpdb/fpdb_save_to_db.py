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

import fpdb_simple

#stores a stud/razz hand into the database
def ring_stud(cursor, base, category, site_hand_no, gametype_id, hand_start_time, names, player_ids, start_cashes, antes, card_values, card_suits, winnings, rakes, action_types, allIns, action_amounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
	fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
	
	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names, tableName, maxSeats)
	
	#print "before calling store_hands_players_stud, antes:", antes
	hands_players_ids=fpdb_simple.store_hands_players_stud(cursor, hands_id, player_ids, 
				start_cashes, antes, card_values, card_suits, winnings, rakes, seatNos)
	
	fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
	return hands_id
#end def ring_stud

def ring_holdem_omaha(cursor, base, category, site_hand_no, gametype_id, hand_start_time, names, player_ids, start_cashes, positions, card_values, card_suits, board_values, board_suits, winnings, rakes, action_types, allIns, action_amounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
	"""stores a holdem/omaha hand into the database"""
	fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
	fpdb_simple.fill_board_cards(board_values, board_suits)

	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names, tableName, maxSeats)
	
	hands_players_ids=fpdb_simple.store_hands_players_holdem_omaha(cursor, category, hands_id, player_ids, start_cashes, positions, card_values, card_suits, winnings, rakes, seatNos)
				
	fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
	
	fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
	return hands_id
#end def ring_holdem_omaha

def tourney_holdem_omaha(cursor, base, category, siteTourneyNo, buyin, fee, knockout, entries, prizepool, tourney_start, payin_amounts, ranks, tourneyTypeId, siteId, #end of tourney specific params
			site_hand_no, gametype_id, hand_start_time, names, player_ids, start_cashes, positions, card_values, card_suits, board_values, board_suits, winnings, rakes, action_types, allIns, action_amounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
	"""stores a tourney holdem/omaha hand into the database"""
	fpdb_simple.fillCardArrays(len(names), base, category, card_values, card_suits)
	fpdb_simple.fill_board_cards(board_values, board_suits)
	
	tourney_id=fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourney_start)
	tourneys_players_ids=fpdb_simple.store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings)
	
	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names, tableName, maxSeats)
	
	hands_players_ids=fpdb_simple.store_hands_players_holdem_omaha_tourney(cursor, category, hands_id, player_ids, start_cashes, positions, card_values, card_suits, winnings, rakes, seatNos, tourneys_players_ids)
	
	fpdb_simple.storeHudCache(cursor, base, category, gametype_id, player_ids, hudImportData)
	
	fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, allIns, action_amounts, actionNos)
	return hands_id
#end def tourney_holdem_omaha

def tourney_stud(cursor, base, category, siteTourneyNo, buyin, fee, knockout, entries, prizepool, tourneyStartTime, payin_amounts, ranks, tourneyTypeId, siteId,
					siteHandNo, gametypeId, handStartTime, names, playerIds, startCashes, antes, cardValues, cardSuits, winnings, rakes, actionTypes, allIns, actionAmounts, actionNos, hudImportData, maxSeats, tableName, seatNos):
#stores a tourney stud/razz hand into the database
	fpdb_simple.fillCardArrays(len(names), base, category, cardValues, cardSuits)
	
	tourney_id=fpdb_simple.store_tourneys(cursor, tourneyTypeId, siteTourneyNo, entries, prizepool, tourneyStartTime)
	
	tourneys_players_ids=fpdb_simple.store_tourneys_players(cursor, tourney_id, playerIds, payin_amounts, ranks, winnings)
	
	hands_id=fpdb_simple.storeHands(cursor, siteHandNo, gametypeId, handStartTime, names, tableName, maxSeats)
	
	hands_players_ids=fpdb_simple.store_hands_players_stud_tourney(cursor, hands_id, playerIds, startCashes, antes, cardValues, cardSuits, winnings, rakes, seatNos, tourneys_players_ids)
	
	fpdb_simple.storeHudCache(cursor, base, category, gametypeId, playerIds, hudImportData)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, actionTypes, allIns, actionAmounts, actionNos)
	return hands_id
#end def tourney_stud
