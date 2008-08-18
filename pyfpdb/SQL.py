#!/usr/bin/env python
"""SQL.py

Set up all of the SQL statements for a given game and database type.
"""
#    Copyright 2008, Ray E. Barker
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

#    Standard Library modules

#    pyGTK modules

#    FreePokerTools modules

class Sql:
    
    def __init__(self, game = 'holdem', type = 'PT3'):
        self.query = {}

        if game == 'razz' and type == 'ptracks':
            
            self.query['get_table_name'] = "select table_name from game where game_id = %s"

            self.query['get_last_hand'] = "select max(game_id) from game"

            self.query['get_recent_hands'] = "select game_id from game where game_id > %(last_hand)d"
            
            self.query['get_xml'] = "select xml from hand_history where game_id = %s"

            self.query['get_player_id'] = """
                    select player_id from players 
                    where screen_name = %(player)s 
                """
                
            self.query['get_hand_info'] = """
                    SELECT 
                        game_id, 
                        CONCAT(hole_card_1, hole_card_2, hole_card_3, hole_card_4, hole_card_5, hole_card_6, hole_card_7) AS hand,  
                        total_won-total_bet AS net
                    FROM game_players 
                    WHERE game_id = %s AND player_id = 3
                """
                
            self.query['get_cards'] = """
                    select 
                        seat_number, 
                        screen_name, 
                        hole_card_1, 
                        hole_card_2, 
                        hole_card_3, 
                        hole_card_4, 
                        hole_card_5, 
                        hole_card_6, 
                        hole_card_7 
                    from game_players, players 
                    where game_id = %s and game_players.player_id = players.player_id 
                    order by seat_number
                """
        
            self.query['get_stats_from_hand'] = """
                    SELECT player_id, 
                        count(*)                    AS n,
                        sum(pre_fourth_raise_n)     AS pfr,
                        sum(fourth_raise_n)         AS raise_n_2,
                        sum(fourth_ck_raise_n)      AS cr_n_2,
                        sum(fifth_bet_raise_n)      AS br_n_3,
                        sum(fifth_bet_ck_raise_n)   AS cr_n_3,
                        sum(sixth_bet_raise_n)      AS br_n_4,
                        sum(sixth_bet_ck_raise_n)   AS cr_n_4,
                        sum(river_bet_raise_n)      AS br_n_5,
                        sum(river_bet_ck_raise_n)   AS cr_n_5,
                        sum(went_to_showdown_n)     AS sd,
                        sum(saw_fourth_n)           AS saw_f,
                        sum(raised_first_pf)        AS first_pfr,
                        sum(vol_put_money_in_pot)   AS vpip,
                        sum(limp_with_prev_callers) AS limp_w_callers,

                        sum(ppossible_actions)      AS poss_a_pf, 
                        sum(pfold)                  AS fold_pf, 
                        sum(pcheck)                 AS check_pf, 
                        sum(praise)                 AS raise_pf, 
                        sum(pcall)                  AS raise_pf, 
                        sum(limp_call_reraise_pf)   AS limp_call_pf,

                        sum(pfr_check)              AS check_after_raise, 
                        sum(pfr_call)               AS call_after_raise, 
                        sum(pfr_fold)               AS fold_after_raise, 
                        sum(pfr_bet)                AS bet_after_raise, 
                        sum(pfr_raise)              AS raise_after_raise, 
                        sum(folded_to_river_bet)    AS fold_to_r_bet, 

                        sum(fpossible_actions)      AS poss_a_2, 
                        sum(ffold)                  AS fold_2,
                        sum(fcheck)                 AS check_2, 
                        sum(fbet)                   AS bet_2, 
                        sum(fraise)                 AS raise_2, 
                        sum(fcall)                  AS raise_2,

                        sum(fifpossible_actions)    AS poss_a_3, 
                        sum(fiffold)                AS fold_3,
                        sum(fifcheck)               AS check_3, 
                        sum(fifbet)                 AS bet_3, 
                        sum(fifraise)               AS raise_3, 
                        sum(fifcall)                AS call_3,

                        sum(spossible_actions)      AS poss_a_4, 
                        sum(sfold)                  AS fold_4,
                        sum(scheck)                 AS check_4, 
                        sum(sbet)                   AS bet_4, 
                        sum(sraise)                 AS raise_4, 
                        sum(scall)                  AS call_4,

                        sum(rpossible_actions)      AS poss_a_5, 
                        sum(rfold)                  AS fold_5,
                        sum(rcheck)                 AS check_5, 
                        sum(rbet)                   AS bet_5, 
                        sum(rraise)                 AS raise_5, 
                        sum(rcall)                  AS call_5,

                        sum(cold_call_pf)           AS cc_pf,
                        sum(saw_fifth_n)            AS saw_3,
                        sum(saw_sixth_n)            AS saw_4,
                        sum(saw_river_n)            AS saw_5
                    FROM game_players
                    WHERE player_id in 
                        (SELECT player_id FROM game_players 
                        WHERE game_id = %s AND NOT player_id = %s)
                    GROUP BY player_id
                """
# alternate form of WHERE for above
#                        WHERE game_id = %(hand)d AND NOT player_id = %(hero)d)
#                        WHERE game_id = %s AND NOT player_id = %s)

            self.query['get_players_from_hand'] = """
                    SELECT game_players.player_id, seat_number, screen_name
                    FROM game_players INNER JOIN players ON (game_players.player_id = players.player_id)
                    WHERE game_id = %s
                """
                
        if game == 'holdem' and type == 'PT3':
   
            self.query['get_last_hand'] = "select max(id_hand) from holdem_hand_summary"

            self.query['get_player_id'] = """
                    select id_player from player, lookup_sites 
                    where player_name = %(player)s 
                    and site_name = %(site)s 
                    and player.id_site = lookup_sites.id_site
                """
         
            self.query['get_stats_from_hand'] = """
                    select id_player AS player_id, 
                    count(*) AS n,
                    sum(CAST (flg_vpip          AS integer)) as vpip,
                    sum(CAST (flg_p_first_raise AS integer)) as p_first_raise,
                    sum(CAST (flg_f_saw         AS integer)) as f_saw,
                    sum(CAST (flg_p_open        AS integer)) as p_open,
                    sum(CAST (flg_p_limp        AS integer)) as p_limp,
                    sum(CAST (flg_p_fold        AS integer)) as p_fold,
                    sum(CAST (flg_p_ccall       AS integer)) as p_ccall,
                    sum(CAST (flg_f_bet         AS integer)) as f_bet,
                    sum(CAST (flg_f_first_raise AS integer)) as f_first_raise,
                    sum(CAST (flg_f_check       AS integer)) as f_check,
                    sum(CAST (flg_f_check_raise AS integer)) as f_check_raise,
                    sum(CAST (flg_f_fold        AS integer)) as f_fold,
                    sum(CAST (flg_f_saw         AS integer)) as f_saw,
                    sum(CAST (flg_t_bet         AS integer)) as t_bet,
                    sum(CAST (flg_t_first_raise AS integer)) as t_first_raise,
                    sum(CAST (flg_t_check       AS integer)) as t_check,
                    sum(CAST (flg_t_check_raise AS integer)) as t_check_raise,
                    sum(CAST (flg_t_fold        AS integer)) as t_fold,
                    sum(CAST (flg_t_saw         AS integer)) as t_saw,
                    sum(CAST (flg_r_bet         AS integer)) as r_bet,
                    sum(CAST (flg_r_first_raise AS integer)) as r_first_raise,
                    sum(CAST (flg_r_check       AS integer)) as r_check,
                    sum(CAST (flg_r_check_raise AS integer)) as r_check_raise,
                    sum(CAST (flg_r_fold        AS integer)) as r_fold,
                    sum(CAST (flg_r_saw         AS integer)) as r_saw,
                    sum(CAST (flg_sb_steal_fold AS integer)) as sb_steal_fold,
                    sum(CAST (flg_bb_steal_fold AS integer)) as bb_steal_fold,
                    sum(CAST (flg_blind_def_opp AS integer)) as blind_def_opp,
                    sum(CAST (flg_steal_att     AS integer)) as steal_att,
                    sum(CAST (flg_steal_opp     AS integer)) as steal_opp,
                    sum(CAST (flg_blind_k       AS integer)) as blind_k,
                    sum(CAST (flg_showdown      AS integer)) as showdown,

                    sum(CAST (flg_p_squeeze         AS integer)) as p_squeeze,
                    sum(CAST (flg_p_squeeze_opp     AS integer)) as p_squeeze_opp,
                    sum(CAST (flg_p_squeeze_def_opp AS integer)) as p_squeeze_def_opp,

                    sum(CAST (flg_f_cbet            AS integer)) as f_cbet,
                    sum(CAST (flg_f_cbet_opp        AS integer)) as f_cbet_opp,
                    sum(CAST (flg_f_cbet_def_opp    AS integer)) as f_cbet_def_opp
                    
                    from holdem_hand_player_statistics 
                    where id_hand = %(hand)d and not id_player = %(hero)d
                    group by id_player
              """

        if game == 'holdem' and type == 'fpdb':
   
            self.query['get_last_hand'] = "select max(id) from Hands"

            self.query['get_player_id'] = """
                    select Players.id AS player_id from Players, Sites 
                    where Players.name = %(player)s 
                    and Sites.name = %(site)s 
                    and Players.SiteId = Sites.id
                """

            self.query['get_stats_from_hand'] = """
                    SELECT HudCache.playerId                 AS player_id, 
                        sum(HDs)                    AS n,
                        sum(street0Aggr)            AS pfr,
                        sum(street0VPI)             AS vpip,
                        sum(sawShowdown)            AS sd,
                        sum(wonAtSD)                AS wmsd,
                        sum(street1Seen)            AS saw_f,
                        sum(totalProfit)            AS net
                    FROM HudCache, Hands
                    WHERE HudCache.PlayerId in 
                        (SELECT PlayerId FROM HandsPlayers 
                        WHERE handId = %s)
                    AND   Hands.id = %s
                    AND   Hands.gametypeId = HudCache.gametypeId
                    GROUP BY HudCache.PlayerId
                """
         
            self.query['get_players_from_hand'] = """
                    SELECT HandsPlayers.playerId, seatNo, name
                    FROM  HandsPlayers INNER JOIN Players ON (HandsPlayers.playerId = Players.id)
                    WHERE handId = %s
                """

            self.query['get_table_name'] = """
                    select tableName, maxSeats, category 
                    from Hands,Gametypes 
                    where Hands.id = %s
                    and Gametypes.id = Hands.gametypeId
                """

if __name__== "__main__":
#    just print the default queries and exit
    s = Sql(game = 'razz', type = 'ptracks')
    for key in s.query:
        print "For query " + key + ", sql ="
        print s.query[key]
