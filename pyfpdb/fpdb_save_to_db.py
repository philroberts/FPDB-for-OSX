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
def ring_stud(cursor, category, site_hand_no, gametype_id, hand_start_time, 
			names, player_ids, start_cashes, antes, card_values, card_suits, 
			winnings, rakes, action_types, action_amounts, hudImportData):
	fpdb_simple.fillCardArrays(len(names), 7, card_values, card_suits)
	
	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names)
	
	hands_players_ids=fpdb_simple.store_hands_players_stud(cursor, hands_id, player_ids, 
				start_cashes, antes, card_values, card_suits, winnings, rakes)
	
	fpdb_simple.storeHudData(cursor, category, player_ids, hudImportData)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, action_amounts)
	return site_hand_no
#end def ring_stud

def ring_holdem_omaha(cursor, category, site_hand_no, gametype_id, hand_start_time, names, player_ids, start_cashes, positions, card_values, card_suits, board_values, board_suits, winnings, rakes, action_types, action_amounts, actionNos, hudImportData, maxSeats, tableName):
	"""stores a holdem/omaha hand into the database"""
	
	#fill up the two player card arrays
	if (category=="holdem"):
		fpdb_simple.fillCardArrays(len(names), 2, card_values, card_suits)
	elif (category=="omahahi" or category=="omahahilo"):
		fpdb_simple.fillCardArrays(len(names), 4, card_values, card_suits)
	else:
		raise fpdb_simple.FpdbError ("invalid category: category")
	
	fpdb_simple.fill_board_cards(board_values, board_suits)

	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names, tableName)
	
	hands_players_ids=fpdb_simple.store_hands_players_holdem_omaha(cursor, category, hands_id, player_ids, 
				start_cashes, positions, card_values, card_suits, winnings, rakes)
				
	fpdb_simple.storeHudData(cursor, category, gametype_id, player_ids, hudImportData)
	
	fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, action_amounts, actionNos)
	return site_hand_no
#end def ring_holdem_omaha

def tourney_holdem_omaha(cursor, category, site_tourney_no, buyin, fee, knockout, entries, prizepool, tourney_start, payin_amounts, ranks, #end of tourney specific params
			site_hand_no, gametype_id, hand_start_time, names, player_ids, start_cashes, positions, card_values, card_suits, board_values, board_suits, winnings, rakes, action_types, action_amounts, actionNos, hudImportData):
	"""stores a tourney holdem/omaha hand into the database"""
	#fill up the two player card arrays
	if (category=="holdem"):
		fpdb_simple.fillCardArrays(len(names), 2, card_values, card_suits)
	elif (category=="omahahi" or category=="omahahilo"):
		fpdb_simple.fillCardArrays(len(names), 4, card_values, card_suits)
	else:
		raise fpdb_simple.FpdbError ("invalid category: category")
	
	fpdb_simple.fill_board_cards(board_values, board_suits)
	
	tourney_id=fpdb_simple.store_tourneys(cursor, site_id, site_tourney_no, buyin, fee, knockout, entries, prizepool, tourney_start)
	
	tourneys_players_ids=fpdb_simple.store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings)
	
	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names)
	
	hands_players_ids=fpdb_simple.store_hands_players_holdem_omaha_tourney(cursor, hands_id, player_ids, 
				start_cashes, positions, card_values, card_suits, winnings, rakes, tourneys_players_ids)
	
	fpdb_simple.storeHudData(cursor, category, player_ids, hudImportData)
	
	fpdb_simple.store_board_cards(cursor, hands_id, board_values, board_suits)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, action_amounts)
	return site_hand_no
#end def tourney_holdem_omaha

def tourney_stud(cursor, category, site_tourney_no, buyin, fee, knockout, entries, prizepool,
			    tourney_start, payin_amounts, ranks, #end of tourney specific params
			    site_hand_no, site_id, gametype_id, hand_start_time, names, player_ids,
			    start_cashes, antes, card_values, card_suits, winnings, rakes,
			    action_types, action_amounts, hudImportData):
#stores a tourney stud/razz hand into the database
	fpdb_simple.fillCardArrays(len(names), 7, card_values, card_suits)
	
	tourney_id=fpdb_simple.store_tourneys(cursor, site_id, site_tourney_no, buyin, fee, knockout, entries, prizepool, tourney_start)
	
	tourneys_players_ids=fpdb_simple.store_tourneys_players(cursor, tourney_id, player_ids, payin_amounts, ranks, winnings)
	
	hands_id=fpdb_simple.storeHands(cursor, site_hand_no, gametype_id, hand_start_time, names)
	
	hands_players_ids=fpdb_simple.store_hands_players_stud_tourney(cursor, hands_id, player_ids, 
				start_cashes, antes, card_values, card_suits, winnings, rakes, tourneys_players_ids)
	
	fpdb_simple.storeHudData(cursor, category, player_ids, hudImportData)
	
	fpdb_simple.storeActions(cursor, hands_players_ids, action_types, action_amounts)
	return site_hand_no
#end def tourney_stud

