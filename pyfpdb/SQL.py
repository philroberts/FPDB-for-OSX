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
    
    def __init__(self, game = 'holdem', type = 'PT3', db_server = 'mysql'):
        self.query = {}

############################################################################
#
#    Support for the ptracks database, a cut down PT2 stud database.
#    You can safely ignore this unless you are me.
#
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

###############################################################################3
#    Support for the Free Poker DataBase = fpdb   http://fpdb.sourceforge.net/
#
        if type == 'fpdb':
   
            self.query['get_last_hand'] = "select max(id) from Hands"

            self.query['get_player_id'] = """
                    select Players.id AS player_id from Players, Sites 
                    where Players.name = %(player)s 
                    and Sites.name = %(site)s 
                    and Players.SiteId = Sites.id
                """

            self.query['get_stats_from_hand'] = """
                    SELECT hc.playerId                      AS player_id, 
                        hp.seatNo                           AS seat,
                        p.name                              AS screen_name,
                        sum(hc.HDs)                         AS n,
                        sum(hc.street0VPI)                  AS vpip,
                        sum(hc.street0Aggr)                 AS pfr,
                        sum(hc.street0_3BChance)            AS TB_opp_0,
                        sum(hc.street0_3BDone)              AS TB_0,
                        sum(hc.street1Seen)                 AS saw_f,
                        sum(hc.street1Seen)                 AS saw_1,
                        sum(hc.street2Seen)                 AS saw_2,
                        sum(hc.street3Seen)                 AS saw_3,
                        sum(hc.street4Seen)                 AS saw_4,
                        sum(hc.sawShowdown)                 AS sd,
                        sum(hc.street1Aggr)                 AS aggr_1,
                        sum(hc.street2Aggr)                 AS aggr_2,
                        sum(hc.street3Aggr)                 AS aggr_3,
                        sum(hc.street4Aggr)                 AS aggr_4,
                        sum(hc.otherRaisedStreet1)          AS was_raised_1,
                        sum(hc.otherRaisedStreet2)          AS was_raised_2,
                        sum(hc.otherRaisedStreet3)          AS was_raised_3,
                        sum(hc.otherRaisedStreet4)          AS was_raised_4,
                        sum(hc.foldToOtherRaisedStreet1)    AS f_freq_1,
                        sum(hc.foldToOtherRaisedStreet2)    AS f_freq_2,
                        sum(hc.foldToOtherRaisedStreet3)    AS f_freq_3,
                        sum(hc.foldToOtherRaisedStreet4)    AS f_freq_4,
                        sum(hc.wonWhenSeenStreet1)          AS w_w_s_1,
                        sum(hc.wonAtSD)                     AS wmsd,
                        sum(hc.stealAttemptChance)          AS steal_opp,
                        sum(hc.stealAttempted)              AS steal,
                        sum(hc.foldSbToStealChance)         AS SBstolen,
                        sum(hc.foldedSbToSteal)             AS SBnotDef,
                        sum(hc.foldBbToStealChance)         AS BBstolen,
                        sum(hc.foldedBbToSteal)             AS BBnotDef,
                        sum(hc.street1CBChance)             AS CB_opp_1,
                        sum(hc.street1CBDone)               AS CB_1,
                        sum(hc.street2CBChance)             AS CB_opp_2,
                        sum(hc.street2CBDone)               AS CB_2,
                        sum(hc.street3CBChance)             AS CB_opp_3,
                        sum(hc.street3CBDone)               AS CB_3,
                        sum(hc.street4CBChance)             AS CB_opp_4,
                        sum(hc.street4CBDone)               AS CB_4,
                        sum(hc.foldToStreet1CBChance)       AS f_cb_opp_1,
                        sum(hc.foldToStreet1CBDone)         AS f_cb_1,
                        sum(hc.foldToStreet2CBChance)       AS f_cb_opp_2,
                        sum(hc.foldToStreet2CBDone)         AS f_cb_2,
                        sum(hc.foldToStreet3CBChance)       AS f_cb_opp_3,
                        sum(hc.foldToStreet3CBDone)         AS f_cb_3,
                        sum(hc.foldToStreet4CBChance)       AS f_cb_opp_4,
                        sum(hc.foldToStreet4CBDone)         AS f_cb_4,
                        sum(hc.totalProfit)                 AS net,
                        sum(hc.street1CheckCallRaiseChance) AS ccr_opp_1,
                        sum(hc.street1CheckCallRaiseDone)   AS ccr_1,
                        sum(hc.street2CheckCallRaiseChance) AS ccr_opp_2,
                        sum(hc.street2CheckCallRaiseDone)   AS ccr_2,
                        sum(hc.street3CheckCallRaiseChance) AS ccr_opp_3,
                        sum(hc.street3CheckCallRaiseDone)   AS ccr_3,
                        sum(hc.street4CheckCallRaiseChance) AS ccr_opp_4,
                        sum(hc.street4CheckCallRaiseDone)   AS ccr_4
                    FROM Hands h
                         INNER JOIN HandsPlayers hp ON (hp.handId = %s)
                         INNER JOIN HudCache hc ON (    hc.PlayerId = hp.PlayerId+0
                                                    AND hc.gametypeId+0 = h.gametypeId+0)
                         INNER JOIN Players p ON (p.id = hp.PlayerId+0)
                    WHERE h.id = %s
                    AND   hc.styleKey > %s
                          /* styleKey is currently 'd' (for date) followed by a yyyymmdd
                             date key. Set it to 0000000 or similar to get all records  */
                    /* also check activeseats here? even if only 3 groups eg 2-3/4-6/7+ ??
                       e.g. could use a multiplier:
                       AND   h.seats > X / 1.25  and  hp.seats < X * 1.25
                       where X is the number of active players at the current table (and 
                       1.25 would be a config value so user could change it)
                    */
                    GROUP BY hc.PlayerId, hp.seatNo, p.name
                """

#    same as above except stats are aggregated for all blind/limit levels
            self.query['get_stats_from_hand_aggregated'] = """
                    SELECT hc.playerId                         AS player_id, 
                           max(case when hc.gametypeId = h.gametypeId 
                                    then hp.seatNo
                                    else -1
                               end)                            AS seat,
                           p.name                              AS screen_name,
                           sum(hc.HDs)                         AS n,
                           sum(hc.street0VPI)                  AS vpip,
                           sum(hc.street0Aggr)                 AS pfr,
                           sum(hc.street0_3BChance)            AS TB_opp_0,
                           sum(hc.street0_3BDone)              AS TB_0,
                           sum(hc.street1Seen)                 AS saw_f,
                           sum(hc.street1Seen)                 AS saw_1,
                           sum(hc.street2Seen)                 AS saw_2,
                           sum(hc.street3Seen)                 AS saw_3,
                           sum(hc.street4Seen)                 AS saw_4,
                           sum(hc.sawShowdown)                 AS sd,
                           sum(hc.street1Aggr)                 AS aggr_1,
                           sum(hc.street2Aggr)                 AS aggr_2,
                           sum(hc.street3Aggr)                 AS aggr_3,
                           sum(hc.street4Aggr)                 AS aggr_4,
                           sum(hc.otherRaisedStreet1)          AS was_raised_1,
                           sum(hc.otherRaisedStreet2)          AS was_raised_2,
                           sum(hc.otherRaisedStreet3)          AS was_raised_3,
                           sum(hc.otherRaisedStreet4)          AS was_raised_4,
                           sum(hc.foldToOtherRaisedStreet1)    AS f_freq_1,
                           sum(hc.foldToOtherRaisedStreet2)    AS f_freq_2,
                           sum(hc.foldToOtherRaisedStreet3)    AS f_freq_3,
                           sum(hc.foldToOtherRaisedStreet4)    AS f_freq_4,
                           sum(hc.wonWhenSeenStreet1)          AS w_w_s_1,
                           sum(hc.wonAtSD)                     AS wmsd,
                           sum(hc.stealAttemptChance)          AS steal_opp,
                           sum(hc.stealAttempted)              AS steal,
                           sum(hc.foldSbToStealChance)         AS SBstolen,
                           sum(hc.foldedSbToSteal)             AS SBnotDef,
                           sum(hc.foldBbToStealChance)         AS BBstolen,
                           sum(hc.foldedBbToSteal)             AS BBnotDef,
                           sum(hc.street1CBChance)             AS CB_opp_1,
                           sum(hc.street1CBDone)               AS CB_1,
                           sum(hc.street2CBChance)             AS CB_opp_2,
                           sum(hc.street2CBDone)               AS CB_2,
                           sum(hc.street3CBChance)             AS CB_opp_3,
                           sum(hc.street3CBDone)               AS CB_3,
                           sum(hc.street4CBChance)             AS CB_opp_4,
                           sum(hc.street4CBDone)               AS CB_4,
                           sum(hc.foldToStreet1CBChance)       AS f_cb_opp_1,
                           sum(hc.foldToStreet1CBDone)         AS f_cb_1,
                           sum(hc.foldToStreet2CBChance)       AS f_cb_opp_2,
                           sum(hc.foldToStreet2CBDone)         AS f_cb_2,
                           sum(hc.foldToStreet3CBChance)       AS f_cb_opp_3,
                           sum(hc.foldToStreet3CBDone)         AS f_cb_3,
                           sum(hc.foldToStreet4CBChance)       AS f_cb_opp_4,
                           sum(hc.foldToStreet4CBDone)         AS f_cb_4,
                           sum(hc.totalProfit)                 AS net,
                           sum(hc.street1CheckCallRaiseChance) AS ccr_opp_1,
                           sum(hc.street1CheckCallRaiseDone)   AS ccr_1,
                           sum(hc.street2CheckCallRaiseChance) AS ccr_opp_2,
                           sum(hc.street2CheckCallRaiseDone)   AS ccr_2,
                           sum(hc.street3CheckCallRaiseChance) AS ccr_opp_3,
                           sum(hc.street3CheckCallRaiseDone)   AS ccr_3,
                           sum(hc.street4CheckCallRaiseChance) AS ccr_opp_4,
                           sum(hc.street4CheckCallRaiseDone)   AS ccr_4
                    FROM Hands h
                         INNER JOIN HandsPlayers hp ON (hp.handId = %s)
                         INNER JOIN HudCache hc     ON (hc.playerId = hp.playerId)
                         INNER JOIN Players p       ON (p.id = hc.playerId)
                    WHERE h.id = %s
                    AND   hc.styleKey > %s
                          /* styleKey is currently 'd' (for date) followed by a yyyymmdd
                             date key. Set it to 0000000 or similar to get all records  */
                    /* also check activeseats here? even if only 3 groups eg 2-3/4-6/7+ ??
                       e.g. could use a multiplier:
                       AND   h.seats > %s / 1.25  and  hp.seats < %s * 1.25
                       where %s is the number of active players at the current table (and 
                       1.25 would be a config value so user could change it)
                    */
                    AND   hc.gametypeId+0 in
                          (SELECT gt1.id from Gametypes gt1, Gametypes gt2
                           WHERE  gt1.siteid = gt2.siteid
                           AND    gt1.type = gt2.type
                           AND    gt1.category = gt2.category
                           AND    gt1.limittype = gt2.limittype
                           AND    gt2.id = h.gametypeId)
                    GROUP BY hc.PlayerId, p.name, hc.styleKey
                """

            if db_server == 'mysql':
                self.query['get_stats_from_hand_session'] = """
                        SELECT hp.playerId                                              AS player_id,
                               hp.handId                                                AS hand_id,
                               hp.seatNo                                                AS seat,
                               p.name                                                   AS screen_name,
                               h.seats                                                  AS seats,
                               1                                                        AS n,
                               cast(hp2.street0VPI as <signed>integer)                  AS vpip,
                               cast(hp2.street0Aggr as <signed>integer)                 AS pfr,
                               cast(hp2.street0_3BChance as <signed>integer)            AS TB_opp_0,
                               cast(hp2.street0_3BDone as <signed>integer)              AS TB_0,
                               cast(hp2.street1Seen as <signed>integer)                 AS saw_f,
                               cast(hp2.street1Seen as <signed>integer)                 AS saw_1,
                               cast(hp2.street2Seen as <signed>integer)                 AS saw_2,
                               cast(hp2.street3Seen as <signed>integer)                 AS saw_3,
                               cast(hp2.street4Seen as <signed>integer)                 AS saw_4,
                               cast(hp2.sawShowdown as <signed>integer)                 AS sd,
                               cast(hp2.street1Aggr as <signed>integer)                 AS aggr_1,
                               cast(hp2.street2Aggr as <signed>integer)                 AS aggr_2,
                               cast(hp2.street3Aggr as <signed>integer)                 AS aggr_3,
                               cast(hp2.street4Aggr as <signed>integer)                 AS aggr_4,
                               cast(hp2.otherRaisedStreet1 as <signed>integer)          AS was_raised_1,
                               cast(hp2.otherRaisedStreet2 as <signed>integer)          AS was_raised_2,
                               cast(hp2.otherRaisedStreet3 as <signed>integer)          AS was_raised_3,
                               cast(hp2.otherRaisedStreet4 as <signed>integer)          AS was_raised_4,
                               cast(hp2.foldToOtherRaisedStreet1 as <signed>integer)    AS f_freq_1,
                               cast(hp2.foldToOtherRaisedStreet2 as <signed>integer)    AS f_freq_2,
                               cast(hp2.foldToOtherRaisedStreet3 as <signed>integer)    AS f_freq_3,
                               cast(hp2.foldToOtherRaisedStreet4 as <signed>integer)    AS f_freq_4,
                               cast(hp2.wonWhenSeenStreet1 as <signed>integer)          AS w_w_s_1,
                               cast(hp2.wonAtSD as <signed>integer)                     AS wmsd,
                               cast(hp2.stealAttemptChance as <signed>integer)          AS steal_opp,
                               cast(hp2.stealAttempted as <signed>integer)              AS steal,
                               cast(hp2.foldSbToStealChance as <signed>integer)         AS SBstolen,
                               cast(hp2.foldedSbToSteal as <signed>integer)             AS SBnotDef,
                               cast(hp2.foldBbToStealChance as <signed>integer)         AS BBstolen,
                               cast(hp2.foldedBbToSteal as <signed>integer)             AS BBnotDef,
                               cast(hp2.street1CBChance as <signed>integer)             AS CB_opp_1,
                               cast(hp2.street1CBDone as <signed>integer)               AS CB_1,
                               cast(hp2.street2CBChance as <signed>integer)             AS CB_opp_2,
                               cast(hp2.street2CBDone as <signed>integer)               AS CB_2,
                               cast(hp2.street3CBChance as <signed>integer)             AS CB_opp_3,
                               cast(hp2.street3CBDone as <signed>integer)               AS CB_3,
                               cast(hp2.street4CBChance as <signed>integer)             AS CB_opp_4,
                               cast(hp2.street4CBDone as <signed>integer)               AS CB_4,
                               cast(hp2.foldToStreet1CBChance as <signed>integer)       AS f_cb_opp_1,
                               cast(hp2.foldToStreet1CBDone as <signed>integer)         AS f_cb_1,
                               cast(hp2.foldToStreet2CBChance as <signed>integer)       AS f_cb_opp_2,
                               cast(hp2.foldToStreet2CBDone as <signed>integer)         AS f_cb_2,
                               cast(hp2.foldToStreet3CBChance as <signed>integer)       AS f_cb_opp_3,
                               cast(hp2.foldToStreet3CBDone as <signed>integer)         AS f_cb_3,
                               cast(hp2.foldToStreet4CBChance as <signed>integer)       AS f_cb_opp_4,
                               cast(hp2.foldToStreet4CBDone as <signed>integer)         AS f_cb_4,
                               cast(hp2.totalProfit as <signed>integer)                 AS net,
                               cast(hp2.street1CheckCallRaiseChance as <signed>integer) AS ccr_opp_1,
                               cast(hp2.street1CheckCallRaiseDone as <signed>integer)   AS ccr_1,
                               cast(hp2.street2CheckCallRaiseChance as <signed>integer) AS ccr_opp_2,
                               cast(hp2.street2CheckCallRaiseDone as <signed>integer)   AS ccr_2,
                               cast(hp2.street3CheckCallRaiseChance as <signed>integer) AS ccr_opp_3,
                               cast(hp2.street3CheckCallRaiseDone as <signed>integer)   AS ccr_3,
                               cast(hp2.street4CheckCallRaiseChance as <signed>integer) AS ccr_opp_4,
                               cast(hp2.street4CheckCallRaiseDone as <signed>integer)   AS ccr_4
                        FROM
                             Hands h         /* players in this hand */
                             INNER JOIN Hands h2         ON (h2.id > %s AND   h2.tableName = h.tableName)
                             INNER JOIN HandsPlayers hp  ON (h.id = hp.handId)
                             INNER JOIN HandsPlayers hp2 ON (hp2.playerId+0 = hp.playerId+0 AND (hp2.handId = h2.id+0))  /* other hands by these players */
                             INNER JOIN Players p        ON (p.id = hp2.PlayerId+0)
                        WHERE hp.handId = %s
                        /* check activeseats once this data returned? (don't want to do that here as it might 
                           assume a session ended just because the number of seats dipped for a few hands)
                        */
                        ORDER BY h.handStart desc, hp2.PlayerId
                        /* order rows by handstart descending so that we can stop reading rows when 
                           there's a gap over X minutes between hands (ie. when we get back to start of
                           the session */
                    """
            else:  # assume postgresql
                self.query['get_stats_from_hand_session'] = """
                        SELECT hp.playerId                                              AS player_id,
                               hp.handId                                                AS hand_id,
                               hp.seatNo                                                AS seat,
                               p.name                                                   AS screen_name,
                               h.seats                                                  AS seats,
                               1                                                        AS n,
                               cast(hp2.street0VPI as <signed>integer)                  AS vpip,
                               cast(hp2.street0Aggr as <signed>integer)                 AS pfr,
                               cast(hp2.street0_3BChance as <signed>integer)            AS TB_opp_0,
                               cast(hp2.street0_3BDone as <signed>integer)              AS TB_0,
                               cast(hp2.street1Seen as <signed>integer)                 AS saw_f,
                               cast(hp2.street1Seen as <signed>integer)                 AS saw_1,
                               cast(hp2.street2Seen as <signed>integer)                 AS saw_2,
                               cast(hp2.street3Seen as <signed>integer)                 AS saw_3,
                               cast(hp2.street4Seen as <signed>integer)                 AS saw_4,
                               cast(hp2.sawShowdown as <signed>integer)                 AS sd,
                               cast(hp2.street1Aggr as <signed>integer)                 AS aggr_1,
                               cast(hp2.street2Aggr as <signed>integer)                 AS aggr_2,
                               cast(hp2.street3Aggr as <signed>integer)                 AS aggr_3,
                               cast(hp2.street4Aggr as <signed>integer)                 AS aggr_4,
                               cast(hp2.otherRaisedStreet1 as <signed>integer)          AS was_raised_1,
                               cast(hp2.otherRaisedStreet2 as <signed>integer)          AS was_raised_2,
                               cast(hp2.otherRaisedStreet3 as <signed>integer)          AS was_raised_3,
                               cast(hp2.otherRaisedStreet4 as <signed>integer)          AS was_raised_4,
                               cast(hp2.foldToOtherRaisedStreet1 as <signed>integer)    AS f_freq_1,
                               cast(hp2.foldToOtherRaisedStreet2 as <signed>integer)    AS f_freq_2,
                               cast(hp2.foldToOtherRaisedStreet3 as <signed>integer)    AS f_freq_3,
                               cast(hp2.foldToOtherRaisedStreet4 as <signed>integer)    AS f_freq_4,
                               cast(hp2.wonWhenSeenStreet1 as <signed>integer)          AS w_w_s_1,
                               cast(hp2.wonAtSD as <signed>integer)                     AS wmsd,
                               cast(hp2.stealAttemptChance as <signed>integer)          AS steal_opp,
                               cast(hp2.stealAttempted as <signed>integer)              AS steal,
                               cast(hp2.foldSbToStealChance as <signed>integer)         AS SBstolen,
                               cast(hp2.foldedSbToSteal as <signed>integer)             AS SBnotDef,
                               cast(hp2.foldBbToStealChance as <signed>integer)         AS BBstolen,
                               cast(hp2.foldedBbToSteal as <signed>integer)             AS BBnotDef,
                               cast(hp2.street1CBChance as <signed>integer)             AS CB_opp_1,
                               cast(hp2.street1CBDone as <signed>integer)               AS CB_1,
                               cast(hp2.street2CBChance as <signed>integer)             AS CB_opp_2,
                               cast(hp2.street2CBDone as <signed>integer)               AS CB_2,
                               cast(hp2.street3CBChance as <signed>integer)             AS CB_opp_3,
                               cast(hp2.street3CBDone as <signed>integer)               AS CB_3,
                               cast(hp2.street4CBChance as <signed>integer)             AS CB_opp_4,
                               cast(hp2.street4CBDone as <signed>integer)               AS CB_4,
                               cast(hp2.foldToStreet1CBChance as <signed>integer)       AS f_cb_opp_1,
                               cast(hp2.foldToStreet1CBDone as <signed>integer)         AS f_cb_1,
                               cast(hp2.foldToStreet2CBChance as <signed>integer)       AS f_cb_opp_2,
                               cast(hp2.foldToStreet2CBDone as <signed>integer)         AS f_cb_2,
                               cast(hp2.foldToStreet3CBChance as <signed>integer)       AS f_cb_opp_3,
                               cast(hp2.foldToStreet3CBDone as <signed>integer)         AS f_cb_3,
                               cast(hp2.foldToStreet4CBChance as <signed>integer)       AS f_cb_opp_4,
                               cast(hp2.foldToStreet4CBDone as <signed>integer)         AS f_cb_4,
                               cast(hp2.totalProfit as <signed>integer)                 AS net,
                               cast(hp2.street1CheckCallRaiseChance as <signed>integer) AS ccr_opp_1,
                               cast(hp2.street1CheckCallRaiseDone as <signed>integer)   AS ccr_1,
                               cast(hp2.street2CheckCallRaiseChance as <signed>integer) AS ccr_opp_2,
                               cast(hp2.street2CheckCallRaiseDone as <signed>integer)   AS ccr_2,
                               cast(hp2.street3CheckCallRaiseChance as <signed>integer) AS ccr_opp_3,
                               cast(hp2.street3CheckCallRaiseDone as <signed>integer)   AS ccr_3,
                               cast(hp2.street4CheckCallRaiseChance as <signed>integer) AS ccr_opp_4,
                               cast(hp2.street4CheckCallRaiseDone as <signed>integer)   AS ccr_4
                        FROM Hands h                                                  /* this hand */
                             INNER JOIN Hands h2         ON (    h2.id > %s           /* other hands */
                                                             AND h2.tableName = h.tableName)
                             INNER JOIN HandsPlayers hp  ON (h.id = hp.handId)        /* players in this hand */
                             INNER JOIN HandsPlayers hp2 ON (    hp2.playerId+0 = hp.playerId+0 
                                                             AND hp2.handId = h2.id)  /* other hands by these players */
                             INNER JOIN Players p        ON (p.id = hp2.PlayerId+0)
                        WHERE h.id = %s
                        /* check activeseats once this data returned? (don't want to do that here as it might 
                           assume a session ended just because the number of seats dipped for a few hands)
                        */
                        ORDER BY h.handStart desc, hp2.PlayerId
                        /* order rows by handstart descending so that we can stop reading rows when 
                           there's a gap over X minutes between hands (ie. when we get back to start of
                           the session */
                    """
         
            self.query['get_players_from_hand'] = """
                    SELECT HandsPlayers.playerId, seatNo, name
                    FROM  HandsPlayers INNER JOIN Players ON (HandsPlayers.playerId = Players.id)
                    WHERE handId = %s
                """
#                    WHERE handId = %s AND Players.id LIKE %s

            self.query['get_winners_from_hand'] = """
                    SELECT name, winnings
                    FROM HandsPlayers, Players
                    WHERE winnings > 0
                        AND Players.id = HandsPlayers.playerId
                        AND handId = %s;
                """

            self.query['get_table_name'] = """
                    select tableName, maxSeats, category, type 
                    from Hands,Gametypes 
                    where Hands.id = %s
                    and Gametypes.id = Hands.gametypeId
                """

            self.query['get_actual_seat'] = """
                    select seatNo
                    from HandsPlayers
                    where HandsPlayers.handId = %s
                    and   HandsPlayers.playerId  = (select Players.id from Players
                                                    where Players.name = %s)
                """

            self.query['get_cards'] = """
                    select 
                        seatNo     AS seat_number, 
                        card1, /*card1Value, card1Suit, */
                        card2, /*card2Value, card2Suit, */
                        card3, /*card3Value, card3Suit, */
                        card4, /*card4Value, card4Suit, */
                        card5, /*card5Value, card5Suit, */
                        card6, /*card6Value, card6Suit, */
                        card7  /*card7Value, card7Suit */
                    from HandsPlayers, Players 
                    where handID = %s and HandsPlayers.playerId = Players.id 
                    order by seatNo
                """

            self.query['get_common_cards'] = """
                    select
                    boardcard1, 
                    boardcard2, 
                    boardcard3, 
                    boardcard4, 
                    boardcard5 
                    from Hands
                    where Id = %s
                """

            self.query['get_action_from_hand'] = """
                SELECT street, Players.name, HandsActions.action, HandsActions.amount, actionno
                FROM Players, HandsActions, HandsPlayers
                WHERE HandsPlayers.handid = %s
                AND HandsPlayers.playerid = Players.id
                AND HandsActions.handsPlayerId = HandsPlayers.id
                ORDER BY street, actionno
            """

            if db_server == 'mysql':
                self.query['get_hand_1day_ago'] = """
                    select coalesce(max(id),0)
                    from Hands
                    where handStart < date_sub(utc_timestamp(), interval '1' day)"""
            else:  # assume postgresql
                self.query['get_hand_1day_ago'] = """
                    select coalesce(max(id),0)
                    from Hands
                    where handStart < now() at time zone 'UTC' - interval '1 day'"""

            #if db_server == 'mysql':
            self.query['get_hand_nhands_ago'] = """
                select coalesce(greatest(max(id),%s)-%s,0)
                from Hands"""

            # used in GuiPlayerStats:
            self.query['getPlayerId'] = """SELECT id from Players where name = %s"""

            # used in Filters:
            self.query['getSiteId'] = """SELECT id from Sites where name = %s"""
            self.query['getGames'] = """SELECT DISTINCT category from Gametypes"""
            self.query['getLimits'] = """SELECT DISTINCT bigBlind from Gametypes ORDER by bigBlind DESC"""

            if db_server == 'mysql':
                self.query['playerDetailedStats'] = """
                         select  <hgameTypeId>                                                          AS hgametypeid
                                ,gt.base
                                ,gt.category
                                ,upper(gt.limitType)                                                    AS limittype
                                ,s.name
                                ,min(gt.bigBlind)                                                       AS minbigblind
                                ,max(gt.bigBlind)                                                       AS maxbigblind
                                /*,<hcgametypeId>                                                         AS gtid*/
                                ,<position>                                                             AS plposition
                                ,count(1)                                                               AS n
                                ,100.0*sum(cast(hp.street0VPI as <signed>integer))/count(1)             AS vpip
                                ,100.0*sum(cast(hp.street0Aggr as <signed>integer))/count(1)            AS pfr
                                ,case when sum(cast(hp.street0_3Bchance as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street0_3Bdone as <signed>integer))/sum(cast(hp.street0_3Bchance as <signed>integer))
                                 end                                                                    AS pf3
                                ,case when sum(cast(hp.stealattemptchance as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.stealattempted as <signed>integer))/sum(cast(hp.stealattemptchance as <signed>integer))
                                 end                                                                    AS steals
                                ,100.0*sum(cast(hp.street1Seen as <signed>integer))/count(1)           AS saw_f
                                ,100.0*sum(cast(hp.sawShowdown as <signed>integer))/count(1)           AS sawsd
                                ,case when sum(cast(hp.street1Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.sawShowdown as <signed>integer))/sum(cast(hp.street1Seen as <signed>integer))
                                 end                                                                    AS wtsdwsf
                                ,case when sum(cast(hp.sawShowdown as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.wonAtSD as <signed>integer))/sum(cast(hp.sawShowdown as <signed>integer))
                                 end                                                                    AS wmsd
                                ,case when sum(cast(hp.street1Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street1Aggr as <signed>integer))/sum(cast(hp.street1Seen as <signed>integer))
                                 end                                                                    AS flafq
                                ,case when sum(cast(hp.street2Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street2Aggr as <signed>integer))/sum(cast(hp.street2Seen as <signed>integer))
                                 end                                                                    AS tuafq
                                ,case when sum(cast(hp.street3Seen as <signed>integer)) = 0 then -999
                                     else 100.0*sum(cast(hp.street3Aggr as <signed>integer))/sum(cast(hp.street3Seen as <signed>integer))
                                 end                                                                    AS rvafq
                                ,case when sum(cast(hp.street1Seen as <signed>integer))+sum(cast(hp.street2Seen as <signed>integer))+sum(cast(hp.street3Seen as <signed>integer)) = 0 then -999
                                     else 100.0*(sum(cast(hp.street1Aggr as <signed>integer))+sum(cast(hp.street2Aggr as <signed>integer))+sum(cast(hp.street3Aggr as <signed>integer)))
                                              /(sum(cast(hp.street1Seen as <signed>integer))+sum(cast(hp.street2Seen as <signed>integer))+sum(cast(hp.street3Seen as <signed>integer)))
                                 end                                                                    AS pofafq
                                ,sum(hp.totalProfit)/100.0                                              AS net
                                ,sum(hp.rake)/100.0                                                     AS rake
                                ,100.0*avg(hp.totalProfit/(gt.bigBlind+0.0))                            AS bbper100
                                ,avg(hp.totalProfit)/100.0                                              AS profitperhand
                                ,100.0*avg((hp.totalProfit+hp.rake)/(gt.bigBlind+0.0))                  AS bb100xr
                                ,avg((hp.totalProfit+hp.rake)/100.0)                                    AS profhndxr
                                ,avg(h.seats+0.0)                                                       AS avgseats
                                ,variance(hp.totalProfit/100.0)                                         AS variance
                          from HandsPlayers hp
                               inner join Hands h       on  (h.id = hp.handId)
                               inner join Gametypes gt  on  (gt.Id = h.gameTypeId)
                               inner join Sites s       on  (s.Id = gt.siteId)
                          where hp.playerId in <player_test>
                          and   hp.tourneysPlayersId IS NULL
                          and   h.seats <seats_test>
                          <flagtest>
                          <gtbigBlind_test>
                          and   date_format(h.handStart, '%Y-%m-%d') <datestest>
                          group by hgameTypeId
                                  ,hp.playerId
                                  ,gt.base
                                  ,gt.category
                                  <groupbyseats>
                                  ,plposition
                                  ,upper(gt.limitType)
                                  ,s.name
                          order by hp.playerId
                                  ,gt.base
                                  ,gt.category
                                  <orderbyseats>
                                  ,case <position> when 'B' then 'B'
                                                   when 'S' then 'S'
                                                   else concat('Z', <position>)
                                   end
                                  <orderbyhgameTypeId>
                                  ,maxbigblind desc
                                  ,upper(gt.limitType)
                                  ,s.name
                          """
            else:   # assume postgresql
                self.query['playerDetailedStats'] = """
                         select  <hgameTypeId>                                                          AS hgametypeid
                                ,gt.base
                                ,gt.category
                                ,upper(gt.limitType)                                                    AS limittype
                                ,s.name
                                ,min(gt.bigBlind)                                                       AS minbigblind
                                ,max(gt.bigBlind)                                                       AS maxbigblind
                                /*,<hcgametypeId>                                                       AS gtid*/
                                ,<position>                                                             AS plposition
                                ,count(1)                                                               AS n
                                ,100.0*sum(cast(hp.street0VPI as <signed>integer))/count(1)             AS vpip
                                ,100.0*sum(cast(hp.street0Aggr as <signed>integer))/count(1)            AS pfr
                                ,case when sum(cast(hp.street0_3Bchance as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street0_3Bdone as <signed>integer))/sum(cast(hp.street0_3Bchance as <signed>integer))
                                 end                                                                    AS pf3
                                ,case when sum(cast(hp.stealattemptchance as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.stealattempted as <signed>integer))/sum(cast(hp.stealattemptchance as <signed>integer))
                                 end                                                                    AS steals
                                ,100.0*sum(cast(hp.street1Seen as <signed>integer))/count(1)            AS saw_f
                                ,100.0*sum(cast(hp.sawShowdown as <signed>integer))/count(1)            AS sawsd
                                ,case when sum(cast(hp.street1Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.sawShowdown as <signed>integer))/sum(cast(hp.street1Seen as <signed>integer))
                                 end                                                                    AS wtsdwsf
                                ,case when sum(cast(hp.sawShowdown as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.wonAtSD as <signed>integer))/sum(cast(hp.sawShowdown as <signed>integer))
                                 end                                                                    AS wmsd
                                ,case when sum(cast(hp.street1Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street1Aggr as <signed>integer))/sum(cast(hp.street1Seen as <signed>integer))
                                 end                                                                    AS flafq
                                ,case when sum(cast(hp.street2Seen as <signed>integer)) = 0 then -999
                                      else 100.0*sum(cast(hp.street2Aggr as <signed>integer))/sum(cast(hp.street2Seen as <signed>integer))
                                 end                                                                    AS tuafq
                                ,case when sum(cast(hp.street3Seen as <signed>integer)) = 0 then -999
                                     else 100.0*sum(cast(hp.street3Aggr as <signed>integer))/sum(cast(hp.street3Seen as <signed>integer))
                                 end                                                                    AS rvafq
                                ,case when sum(cast(hp.street1Seen as <signed>integer))+sum(cast(hp.street2Seen as <signed>integer))+sum(cast(hp.street3Seen as <signed>integer)) = 0 then -999
                                     else 100.0*(sum(cast(hp.street1Aggr as <signed>integer))+sum(cast(hp.street2Aggr as <signed>integer))+sum(cast(hp.street3Aggr as <signed>integer)))
                                              /(sum(cast(hp.street1Seen as <signed>integer))+sum(cast(hp.street2Seen as <signed>integer))+sum(cast(hp.street3Seen as <signed>integer)))
                                 end                                                                    AS pofafq
                                ,sum(hp.totalProfit)/100.0                                              AS net
                                ,sum(hp.rake)/100.0                                                     AS rake
                                ,100.0*avg(hp.totalProfit/(gt.bigBlind+0.0))                            AS bbper100
                                ,avg(hp.totalProfit)/100.0                                              AS profitperhand
                                ,100.0*avg((hp.totalProfit+hp.rake)/(gt.bigBlind+0.0))                  AS bb100xr
                                ,avg((hp.totalProfit+hp.rake)/100.0)                                    AS profhndxr
                                ,avg(h.seats+0.0)                                                       AS avgseats
                                ,variance(hp.totalProfit/100.0)                                         AS variance
                          from HandsPlayers hp
                               inner join Hands h       on  (h.id = hp.handId)
                               inner join Gametypes gt  on  (gt.Id = h.gameTypeId)
                               inner join Sites s       on  (s.Id = gt.siteId)
                          where hp.playerId in <player_test>
                          and   hp.tourneysPlayersId IS NULL
                          and   h.seats <seats_test>
                          <flagtest>
                          <gtbigBlind_test>
                          and   to_char(h.handStart, 'YYYY-MM-DD') <datestest>
                          group by hgameTypeId
                                  ,hp.playerId
                                  ,gt.base
                                  ,gt.category
                                  <groupbyseats>
                                  ,plposition
                                  ,upper(gt.limitType)
                                  ,s.name
                          order by hp.playerId
                                  ,gt.base
                                  ,gt.category
                                  <orderbyseats>
                                  ,case <position> when 'B' then 'B'
                                                   when 'S' then 'S'
                                                   when '0' then 'Y'
                                                   else 'Z'||<position>
                                   end
                                  <orderbyhgameTypeId>
                                  ,maxbigblind desc
                                  ,upper(gt.limitType)
                                  ,s.name
                          """
            #elif(self.dbname == 'SQLite'):
            #    self.query['playerDetailedStats'] = """ """

            if db_server == 'mysql':
                self.query['playerStats'] = """
                    SELECT 
                          concat(upper(stats.limitType), ' '
                                ,concat(upper(substring(stats.category,1,1)),substring(stats.category,2) ), ' '
                                ,stats.name, ' '
                                ,cast(stats.bigBlindDesc as char)
                                )                                                      AS Game
                         ,stats.n
                         ,stats.vpip
                         ,stats.pfr
                         ,stats.pf3
                         ,stats.steals
                         ,stats.saw_f
                         ,stats.sawsd
                         ,stats.wtsdwsf
                         ,stats.wmsd
                         ,stats.FlAFq
                         ,stats.TuAFq
                         ,stats.RvAFq
                         ,stats.PoFAFq
                         ,stats.Net
                         ,stats.BBper100
                         ,stats.Profitperhand
                         ,case when hprof2.variance = -999 then '-'
                               else format(hprof2.variance, 2)
                          end                                                          AS Variance
                         ,stats.AvgSeats
                    FROM
                        (select /* stats from hudcache */
                                gt.base
                               ,gt.category
                               ,upper(gt.limitType) as limitType
                               ,s.name
                               ,<selectgt.bigBlind>                                             AS bigBlindDesc
                               ,<hcgametypeId>                                                  AS gtId
                               ,sum(HDs)                                                        AS n
                               ,format(100.0*sum(street0VPI)/sum(HDs),1)                        AS vpip
                               ,format(100.0*sum(street0Aggr)/sum(HDs),1)                       AS pfr
                               ,case when sum(street0_3Bchance) = 0 then '0'
                                     else format(100.0*sum(street0_3Bdone)/sum(street0_3Bchance),1)
                                end                                                             AS pf3
                               ,case when sum(stealattemptchance) = 0 then '-'
                                     else format(100.0*sum(stealattempted)/sum(stealattemptchance),1)
                                end                                                             AS steals
                               ,format(100.0*sum(street1Seen)/sum(HDs),1)                       AS saw_f
                               ,format(100.0*sum(sawShowdown)/sum(HDs),1)                       AS sawsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else format(100.0*sum(sawShowdown)/sum(street1Seen),1)
                                end                                                             AS wtsdwsf
                               ,case when sum(sawShowdown) = 0 then '-'
                                     else format(100.0*sum(wonAtSD)/sum(sawShowdown),1)
                                end                                                             AS wmsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else format(100.0*sum(street1Aggr)/sum(street1Seen),1)
                                end                                                             AS FlAFq
                               ,case when sum(street2Seen) = 0 then '-'
                                     else format(100.0*sum(street2Aggr)/sum(street2Seen),1)
                                end                                                             AS TuAFq
                               ,case when sum(street3Seen) = 0 then '-'
                                    else format(100.0*sum(street3Aggr)/sum(street3Seen),1)
                                end                                                             AS RvAFq
                               ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                    else format(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                             /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),1)
                                end                                                             AS PoFAFq
                               ,format(sum(totalProfit)/100.0,2)                                AS Net
                               ,format((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0),2)
                                                                                                AS BBper100
                               ,format( (sum(totalProfit)/100.0) / sum(HDs), 4)                 AS Profitperhand
                               ,format( sum(activeSeats*HDs)/(sum(HDs)+0.0), 2)                 AS AvgSeats
                         from Gametypes gt
                              inner join Sites s on s.Id = gt.siteId
                              inner join HudCache hc on hc.gameTypeId = gt.Id
                         where hc.playerId in <player_test>
                         and   <gtbigBlind_test>
                         and   hc.activeSeats <seats_test>
                         and   concat( '20', substring(hc.styleKey,2,2), '-', substring(hc.styleKey,4,2), '-' 
                                     , substring(hc.styleKey,6,2) ) <datestest>
                         group by gt.base
                              ,gt.category
                              ,upper(gt.limitType)
                              ,s.name
                              <groupbygt.bigBlind>
                              ,gtId
                        ) stats
                    inner join
                        ( select # profit from handsplayers/handsactions
                                 hprof.gtId, sum(hprof.profit) sum_profit,
                                 avg(hprof.profit/100.0) profitperhand,
                                 case when hprof.gtId = -1 then -999
                                      else variance(hprof.profit/100.0)
                                 end as variance
                          from
                              (select hp.handId, <hgameTypeId> as gtId, hp.totalProfit as profit
                               from HandsPlayers hp
                               inner join Hands h        ON h.id            = hp.handId
                               where hp.playerId in <player_test>
                               and   hp.tourneysPlayersId IS NULL
                               and   date_format(h.handStart, '%Y-%m-%d') <datestest>
                               group by hp.handId, gtId, hp.totalProfit
                              ) hprof
                          group by hprof.gtId
                         ) hprof2
                        on hprof2.gtId = stats.gtId
                    order by stats.category, stats.limittype, stats.bigBlindDesc desc <orderbyseats>"""
            else:  # assume postgres
                self.query['playerStats'] = """
                    SELECT upper(stats.limitType) || ' '
                           || initcap(stats.category) || ' '
                           || stats.name || ' '
                           || stats.bigBlindDesc                                          AS Game
                          ,stats.n
                          ,stats.vpip
                          ,stats.pfr
                          ,stats.pf3
                          ,stats.steals
                          ,stats.saw_f
                          ,stats.sawsd
                          ,stats.wtsdwsf
                          ,stats.wmsd
                          ,stats.FlAFq
                          ,stats.TuAFq
                          ,stats.RvAFq
                          ,stats.PoFAFq
                          ,stats.Net
                          ,stats.BBper100
                          ,stats.Profitperhand
                          ,case when hprof2.variance = -999 then '-'
                                else to_char(hprof2.variance, '0D00')
                           end                                                          AS Variance
                          ,AvgSeats
                    FROM
                        (select gt.base
                               ,gt.category
                               ,upper(gt.limitType)                                             AS limitType
                               ,s.name
                               ,<selectgt.bigBlind>                                             AS bigBlindDesc
                               ,<hcgametypeId>                                                  AS gtId
                               ,sum(HDs) as n
                               ,to_char(100.0*sum(street0VPI)/sum(HDs),'990D0')                 AS vpip
                               ,to_char(100.0*sum(street0Aggr)/sum(HDs),'90D0')                 AS pfr
                               ,case when sum(street0_3Bchance) = 0 then '0'
                                     else to_char(100.0*sum(street0_3Bdone)/sum(street0_3Bchance),'90D0')
                                end                                                             AS pf3
                               ,case when sum(stealattemptchance) = 0 then '-'
                                     else to_char(100.0*sum(stealattempted)/sum(stealattemptchance),'90D0')
                                end                                                             AS steals
                               ,to_char(100.0*sum(street1Seen)/sum(HDs),'90D0')                 AS saw_f
                               ,to_char(100.0*sum(sawShowdown)/sum(HDs),'90D0')                 AS sawsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else to_char(100.0*sum(sawShowdown)/sum(street1Seen),'90D0')
                                end                                                             AS wtsdwsf
                               ,case when sum(sawShowdown) = 0 then '-'
                                     else to_char(100.0*sum(wonAtSD)/sum(sawShowdown),'90D0')
                                end                                                             AS wmsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else to_char(100.0*sum(street1Aggr)/sum(street1Seen),'90D0')
                                end                                                             AS FlAFq
                               ,case when sum(street2Seen) = 0 then '-'
                                     else to_char(100.0*sum(street2Aggr)/sum(street2Seen),'90D0')
                                end                                                             AS TuAFq
                               ,case when sum(street3Seen) = 0 then '-'
                                    else to_char(100.0*sum(street3Aggr)/sum(street3Seen),'90D0')
                                end                                                             AS RvAFq
                               ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                    else to_char(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                             /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),'90D0')
                                end                                                             AS PoFAFq
                               ,round(sum(totalProfit)/100.0,2)                                 AS Net
                               ,to_char((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0), '990D00')
                                                                                                AS BBper100
                               ,to_char(sum(totalProfit/100.0) / (sum(HDs)+0.0), '990D0000')    AS Profitperhand
                               ,to_char(sum(activeSeats*HDs)/(sum(HDs)+0.0),'90D00')            AS AvgSeats
                         from Gametypes gt
                              inner join Sites s on s.Id = gt.siteId
                              inner join HudCache hc on hc.gameTypeId = gt.Id
                         where hc.playerId in <player_test>
                         and   <gtbigBlind_test>
                         and   hc.activeSeats <seats_test>
                         and   '20' || SUBSTR(hc.styleKey,2,2) || '-' || SUBSTR(hc.styleKey,4,2) || '-' 
                               || SUBSTR(hc.styleKey,6,2) <datestest>
                         group by gt.base
                              ,gt.category
                              ,upper(gt.limitType)
                              ,s.name
                              <groupbygt.bigBlind>
                              ,gtId
                        ) stats
                    inner join
                        ( select
                                 hprof.gtId, sum(hprof.profit) AS sum_profit,
                                 avg(hprof.profit/100.0) AS profitperhand,
                                 case when hprof.gtId = -1 then -999
                                      else variance(hprof.profit/100.0)
                                 end as variance
                          from
                              (select hp.handId, <hgameTypeId> as gtId, hp.totalProfit as profit
                               from HandsPlayers hp
                               inner join Hands h   ON (h.id = hp.handId)
                               where hp.playerId in <player_test>
                               and   hp.tourneysPlayersId IS NULL
                               and   to_char(h.handStart, 'YYYY-MM-DD') <datestest>
                               group by hp.handId, gtId, hp.totalProfit
                              ) hprof
                          group by hprof.gtId
                         ) hprof2
                        on hprof2.gtId = stats.gtId
                    order by stats.base, stats.limittype, stats.bigBlindDesc desc <orderbyseats>"""
            #elif(self.dbname == 'SQLite'):
            #    self.query['playerStats'] = """ """

            if db_server == 'mysql':
                self.query['playerStatsByPosition'] = """
                    SELECT 
                          concat(upper(stats.limitType), ' '
                                ,concat(upper(substring(stats.category,1,1)),substring(stats.category,2) ), ' '
                                ,stats.name, ' '
                                ,cast(stats.bigBlindDesc as char)
                                )                                                      AS Game
                         ,case when stats.PlPosition = -2 then 'BB'
                               when stats.PlPosition = -1 then 'SB'
                               when stats.PlPosition =  0 then 'Btn'
                               when stats.PlPosition =  1 then 'CO'
                               when stats.PlPosition =  2 then 'MP'
                               when stats.PlPosition =  5 then 'EP'
                               else '??'
                          end                                                          AS PlPosition
                         ,stats.n
                         ,stats.vpip
                         ,stats.pfr
                         ,stats.pf3
                         ,stats.steals
                         ,stats.saw_f
                         ,stats.sawsd
                         ,stats.wtsdwsf
                         ,stats.wmsd
                         ,stats.FlAFq
                         ,stats.TuAFq
                         ,stats.RvAFq
                         ,stats.PoFAFq
                         ,stats.Net
                         ,stats.BBper100
                         ,stats.Profitperhand
                         ,case when hprof2.variance = -999 then '-'
                               else format(hprof2.variance, 2)
                          end                                                          AS Variance
                         ,stats.AvgSeats
                    FROM
                        (select /* stats from hudcache */
                                gt.base
                               ,gt.category
                               ,upper(gt.limitType)                                             AS limitType
                               ,s.name
                               ,<selectgt.bigBlind>                                             AS bigBlindDesc
                               ,<hcgametypeId>                                                  AS gtId
                               ,case when hc.position = 'B' then -2
                                     when hc.position = 'S' then -1
                                     when hc.position = 'D' then  0
                                     when hc.position = 'C' then  1
                                     when hc.position = 'M' then  2
                                     when hc.position = 'E' then  5
                                     else 9
                                end                                                             as PlPosition
                               ,sum(HDs)                                                        AS n
                               ,format(100.0*sum(street0VPI)/sum(HDs),1)                        AS vpip
                               ,format(100.0*sum(street0Aggr)/sum(HDs),1)                       AS pfr
                               ,case when sum(street0_3Bchance) = 0 then '0'
                                     else format(100.0*sum(street0_3Bdone)/sum(street0_3Bchance),1)
                                end                                                             AS pf3
                               ,case when sum(stealattemptchance) = 0 then '-'
                                     else format(100.0*sum(stealattempted)/sum(stealattemptchance),1)
                                end                                                             AS steals
                               ,format(100.0*sum(street1Seen)/sum(HDs),1)                       AS saw_f
                               ,format(100.0*sum(sawShowdown)/sum(HDs),1)                       AS sawsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else format(100.0*sum(sawShowdown)/sum(street1Seen),1)
                                end                                                             AS wtsdwsf
                               ,case when sum(sawShowdown) = 0 then '-'
                                     else format(100.0*sum(wonAtSD)/sum(sawShowdown),1)
                                end                                                             AS wmsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else format(100.0*sum(street1Aggr)/sum(street1Seen),1)
                                end                                                             AS FlAFq
                               ,case when sum(street2Seen) = 0 then '-'
                                     else format(100.0*sum(street2Aggr)/sum(street2Seen),1)
                                end                                                             AS TuAFq
                               ,case when sum(street3Seen) = 0 then '-'
                                    else format(100.0*sum(street3Aggr)/sum(street3Seen),1)
                                end                                                             AS RvAFq
                               ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                    else format(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                             /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen)),1)
                                end                                                             AS PoFAFq
                               ,format(sum(totalProfit)/100.0,2)                                AS Net
                               ,format((sum(totalProfit/(gt.bigBlind+0.0))) / (sum(HDs)/100.0),2)
                                                                                                AS BBper100
                               ,format( (sum(totalProfit)/100.0) / sum(HDs), 4)                 AS Profitperhand
                               ,format( sum(activeSeats*HDs)/(sum(HDs)+0.0), 2)                 AS AvgSeats
                         from Gametypes gt
                              inner join Sites s on s.Id = gt.siteId
                              inner join HudCache hc on hc.gameTypeId = gt.Id
                         where hc.playerId in <player_test>
                         and   <gtbigBlind_test>
                         and   hc.activeSeats <seats_test>
                         and   concat( '20', substring(hc.styleKey,2,2), '-', substring(hc.styleKey,4,2), '-' 
                                     , substring(hc.styleKey,6,2) ) <datestest>
                         group by gt.base
                              ,gt.category
                              ,upper(gt.limitType)
                              ,s.name
                              <groupbygt.bigBlind>
                              ,gtId
                              <groupbyseats>
                              ,PlPosition
                        ) stats
                    inner join
                        ( select # profit from handsplayers/handsactions
                                 hprof.gtId, 
                                 case when hprof.position = 'B' then -2
                                      when hprof.position = 'S' then -1
                                      when hprof.position in ('3','4') then 2
                                      when hprof.position in ('6','7') then 5
                                      else hprof.position
                                 end                                      as PlPosition,
                                 sum(hprof.profit) as sum_profit,
                                 avg(hprof.profit/100.0) as profitperhand,
                                 case when hprof.gtId = -1 then -999
                                      else variance(hprof.profit/100.0)
                                 end as variance
                          from
                              (select hp.handId, <hgameTypeId> as gtId, hp.position
                                    , hp.totalProfit as profit
                               from HandsPlayers hp
                               inner join Hands h  ON  (h.id = hp.handId)
                               where hp.playerId in <player_test>
                               and   hp.tourneysPlayersId IS NULL
                               and   date_format(h.handStart, '%Y-%m-%d') <datestest>
                               group by hp.handId, gtId, hp.position, hp.totalProfit
                              ) hprof
                          group by hprof.gtId, PlPosition
                         ) hprof2
                        on (    hprof2.gtId = stats.gtId
                            and hprof2.PlPosition = stats.PlPosition)
                    order by stats.category, stats.limitType, stats.bigBlindDesc desc
                             <orderbyseats>, cast(stats.PlPosition as signed)
                    """
            else:  # assume postgresql
                self.query['playerStatsByPosition'] = """
                    select /* stats from hudcache */
                           upper(stats.limitType) || ' '
                           || upper(substr(stats.category,1,1)) || substr(stats.category,2) || ' '
                           || stats.name || ' '
                           || stats.bigBlindDesc                                        AS Game
                          ,case when stats.PlPosition = -2 then 'BB'
                                when stats.PlPosition = -1 then 'SB'
                                when stats.PlPosition =  0 then 'Btn'
                                when stats.PlPosition =  1 then 'CO'
                                when stats.PlPosition =  2 then 'MP'
                                when stats.PlPosition =  5 then 'EP'
                                else '??'
                           end                                                          AS PlPosition
                          ,stats.n
                          ,stats.vpip
                          ,stats.pfr
                          ,stats.pf3
                          ,stats.steals
                          ,stats.saw_f
                          ,stats.sawsd
                          ,stats.wtsdwsf
                          ,stats.wmsd
                          ,stats.FlAFq
                          ,stats.TuAFq
                          ,stats.RvAFq
                          ,stats.PoFAFq
                          ,stats.Net
                          ,stats.BBper100
                          ,stats.Profitperhand
                          ,case when hprof2.variance = -999 then '-'
                                else to_char(hprof2.variance, '0D00')
                           end                                                          AS Variance
                          ,stats.AvgSeats
                    FROM
                        (select /* stats from hudcache */
                                gt.base
                               ,gt.category
                               ,upper(gt.limitType)                                             AS limitType
                               ,s.name
                               ,<selectgt.bigBlind>                                             AS bigBlindDesc
                               ,<hcgametypeId>                                                  AS gtId
                               ,case when hc.position = 'B' then -2
                                     when hc.position = 'S' then -1
                                     when hc.position = 'D' then  0
                                     when hc.position = 'C' then  1
                                     when hc.position = 'M' then  2
                                     when hc.position = 'E' then  5
                                     else 9
                                end                                                             AS PlPosition
                               ,sum(HDs)                                                        AS n
                               ,to_char(round(100.0*sum(street0VPI)/sum(HDs)),'990D0')          AS vpip
                               ,to_char(round(100.0*sum(street0Aggr)/sum(HDs)),'90D0')          AS pfr
                               ,case when sum(street0_3Bchance) = 0 then '0'
                                     else to_char(100.0*sum(street0_3Bdone)/sum(street0_3Bchance),'90D0')
                                end                                                             AS pf3
                               ,case when sum(stealattemptchance) = 0 then '-'
                                     else to_char(100.0*sum(stealattempted)/sum(stealattemptchance),'90D0')
                                end                                                             AS steals
                               ,to_char(round(100.0*sum(street1Seen)/sum(HDs)),'90D0')          AS saw_f
                               ,to_char(round(100.0*sum(sawShowdown)/sum(HDs)),'90D0')          AS sawsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else to_char(round(100.0*sum(sawShowdown)/sum(street1Seen)),'90D0')
                                end                                                             AS wtsdwsf
                               ,case when sum(sawShowdown) = 0 then '-'
                                     else to_char(round(100.0*sum(wonAtSD)/sum(sawShowdown)),'90D0')
                                end                                                             AS wmsd
                               ,case when sum(street1Seen) = 0 then '-'
                                     else to_char(round(100.0*sum(street1Aggr)/sum(street1Seen)),'90D0')
                                end                                                             AS FlAFq
                               ,case when sum(street2Seen) = 0 then '-'
                                     else to_char(round(100.0*sum(street2Aggr)/sum(street2Seen)),'90D0')
                                end                                                             AS TuAFq
                               ,case when sum(street3Seen) = 0 then '-'
                                    else to_char(round(100.0*sum(street3Aggr)/sum(street3Seen)),'90D0')
                                end                                                             AS RvAFq
                               ,case when sum(street1Seen)+sum(street2Seen)+sum(street3Seen) = 0 then '-'
                                    else to_char(round(100.0*(sum(street1Aggr)+sum(street2Aggr)+sum(street3Aggr))
                                             /(sum(street1Seen)+sum(street2Seen)+sum(street3Seen))),'90D0')
                                end                                                             AS PoFAFq
                               ,to_char(sum(totalProfit)/100.0,'9G999G990D00')                  AS Net
                               ,case when sum(HDs) = 0 then '0'
                                     else to_char(sum(totalProfit/(gt.bigBlind+0.0)) / (sum(HDs)/100.0), '990D00')
                                end                                                             AS BBper100
                               ,case when sum(HDs) = 0 then '0'
                                     else to_char( (sum(totalProfit)/100.0) / sum(HDs), '90D0000')
                                end                                                             AS Profitperhand
                               ,to_char(sum(activeSeats*HDs)/(sum(HDs)+0.0),'90D00')            AS AvgSeats
                         from Gametypes gt
                              inner join Sites s     on (s.Id = gt.siteId)
                              inner join HudCache hc on (hc.gameTypeId = gt.Id)
                         where hc.playerId in <player_test>
                         and   <gtbigBlind_test>
                         and   hc.activeSeats <seats_test>
                         and   '20' || SUBSTR(hc.styleKey,2,2) || '-' || SUBSTR(hc.styleKey,4,2) || '-' 
                               || SUBSTR(hc.styleKey,6,2) <datestest>
                         group by gt.base
                              ,gt.category
                              ,upper(gt.limitType)
                              ,s.name
                              <groupbygt.bigBlind>
                              ,gtId
                              <groupbyseats>
                              ,PlPosition
                        ) stats
                    inner join
                        ( select /* profit from handsplayers/handsactions */
                                 hprof.gtId, 
                                 case when hprof.position = 'B' then -2
                                      when hprof.position = 'S' then -1
                                      when hprof.position in ('3','4') then 2
                                      when hprof.position in ('6','7') then 5
                                      else cast(hprof.position as smallint)
                                 end                                      as PlPosition,
                                 sum(hprof.profit) as sum_profit,
                                 avg(hprof.profit/100.0) as profitperhand,
                                 case when hprof.gtId = -1 then -999
                                      else variance(hprof.profit/100.0)
                                 end as variance
                          from
                              (select hp.handId, <hgameTypeId> as gtId, hp.position
                                    , hp.totalProfit as profit
                               from HandsPlayers hp
                               inner join Hands h  ON  (h.id = hp.handId)
                               where hp.playerId in <player_test>
                               and   hp.tourneysPlayersId IS NULL
                               and   to_char(h.handStart, 'YYYY-MM-DD') <datestest>
                               group by hp.handId, gameTypeId, hp.position, hp.totalProfit
                              ) hprof
                          group by hprof.gtId, PlPosition
                        ) hprof2
                        on (    hprof2.gtId = stats.gtId
                            and hprof2.PlPosition = stats.PlPosition)
                    order by stats.category, stats.limitType, stats.bigBlindDesc desc
                             <orderbyseats>, cast(stats.PlPosition as smallint)
                    """
            #elif(self.dbname == 'SQLite'):
            #    self.query['playerStatsByPosition'] = """ """

            self.query['getRingProfitAllHandsPlayerIdSite'] = """
                SELECT hp.handId, hp.totalProfit, hp.totalProfit, hp.totalProfit
                FROM HandsPlayers hp
                INNER JOIN Players pl      ON  (hp.playerId  = pl.id)
                INNER JOIN Hands h         ON  (h.id         = hp.handId)
                INNER JOIN Gametypes g     ON  (h.gametypeId = g.id)
                where pl.id in <player_test>
                AND   pl.siteId in <site_test>
                AND   h.handStart > '<startdate_test>'
                AND   h.handStart < '<enddate_test>'
                AND   g.bigBlind in <limit_test>
                AND   hp.tourneysPlayersId IS NULL
                GROUP BY h.handStart, hp.handId, hp.totalProfit
                ORDER BY h.handStart"""


            ####################################
            # Queries to rebuild/modify hudcache
            ####################################
           
            self.query['clearHudCache'] = """DELETE FROM HudCache"""
           
            if db_server == 'mysql':
                self.query['rebuildHudCache'] = """
                    INSERT INTO HudCache
                    (gametypeId
                    ,playerId
                    ,activeSeats
                    ,position
                    ,tourneyTypeId
                    ,styleKey
                    ,HDs
                    ,wonWhenSeenStreet1
                    ,wonAtSD
                    ,street0VPI
                    ,street0Aggr
                    ,street0_3BChance
                    ,street0_3BDone
                    ,street1Seen
                    ,street2Seen
                    ,street3Seen
                    ,street4Seen
                    ,sawShowdown
                    ,street1Aggr
                    ,street2Aggr
                    ,street3Aggr
                    ,street4Aggr
                    ,otherRaisedStreet1
                    ,otherRaisedStreet2
                    ,otherRaisedStreet3
                    ,otherRaisedStreet4
                    ,foldToOtherRaisedStreet1
                    ,foldToOtherRaisedStreet2
                    ,foldToOtherRaisedStreet3
                    ,foldToOtherRaisedStreet4
                    ,stealAttemptChance
                    ,stealAttempted
                    ,foldBbToStealChance
                    ,foldedBbToSteal
                    ,foldSbToStealChance
                    ,foldedSbToSteal
                    ,street1CBChance
                    ,street1CBDone
                    ,street2CBChance
                    ,street2CBDone
                    ,street3CBChance
                    ,street3CBDone
                    ,street4CBChance
                    ,street4CBDone
                    ,foldToStreet1CBChance
                    ,foldToStreet1CBDone
                    ,foldToStreet2CBChance
                    ,foldToStreet2CBDone
                    ,foldToStreet3CBChance
                    ,foldToStreet3CBDone
                    ,foldToStreet4CBChance
                    ,foldToStreet4CBDone
                    ,totalProfit
                    ,street1CheckCallRaiseChance
                    ,street1CheckCallRaiseDone
                    ,street2CheckCallRaiseChance
                    ,street2CheckCallRaiseDone
                    ,street3CheckCallRaiseChance
                    ,street3CheckCallRaiseDone
                    ,street4CheckCallRaiseChance
                    ,street4CheckCallRaiseDone
                    )
                    SELECT h.gametypeId
                          ,hp.playerId
                          ,h.seats
                          ,case when hp.position = 'B' then 'B'
                                when hp.position = 'S' then 'S'
                                when hp.position = '0' then 'D'
                                when hp.position = '1' then 'C'
                                when hp.position = '2' then 'M'
                                when hp.position = '3' then 'M'
                                when hp.position = '4' then 'M'
                                when hp.position = '5' then 'E'
                                when hp.position = '6' then 'E'
                                when hp.position = '7' then 'E'
                                when hp.position = '8' then 'E'
                                when hp.position = '9' then 'E'
                                else 'E'
                           end                                            AS hc_position
                          ,hp.tourneyTypeId
                          ,date_format(h.handStart, 'd%y%m%d')
                          ,count(1)
                          ,sum(wonWhenSeenStreet1)
                          ,sum(wonAtSD)
                          ,sum(CAST(street0VPI as integer)) 
                          ,sum(CAST(street0Aggr as integer)) 
                          ,sum(CAST(street0_3BChance as integer)) 
                          ,sum(CAST(street0_3BDone as integer)) 
                          ,sum(CAST(street1Seen as integer)) 
                          ,sum(CAST(street2Seen as integer)) 
                          ,sum(CAST(street3Seen as integer)) 
                          ,sum(CAST(street4Seen as integer)) 
                          ,sum(CAST(sawShowdown as integer)) 
                          ,sum(CAST(street1Aggr as integer)) 
                          ,sum(CAST(street2Aggr as integer)) 
                          ,sum(CAST(street3Aggr as integer)) 
                          ,sum(CAST(street4Aggr as integer)) 
                          ,sum(CAST(otherRaisedStreet1 as integer)) 
                          ,sum(CAST(otherRaisedStreet2 as integer)) 
                          ,sum(CAST(otherRaisedStreet3 as integer)) 
                          ,sum(CAST(otherRaisedStreet4 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet1 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet2 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet3 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet4 as integer)) 
                          ,sum(CAST(stealAttemptChance as integer)) 
                          ,sum(CAST(stealAttempted as integer)) 
                          ,sum(CAST(foldBbToStealChance as integer)) 
                          ,sum(CAST(foldedBbToSteal as integer)) 
                          ,sum(CAST(foldSbToStealChance as integer)) 
                          ,sum(CAST(foldedSbToSteal as integer)) 
                          ,sum(CAST(street1CBChance as integer)) 
                          ,sum(CAST(street1CBDone as integer)) 
                          ,sum(CAST(street2CBChance as integer)) 
                          ,sum(CAST(street2CBDone as integer)) 
                          ,sum(CAST(street3CBChance as integer)) 
                          ,sum(CAST(street3CBDone as integer)) 
                          ,sum(CAST(street4CBChance as integer)) 
                          ,sum(CAST(street4CBDone as integer)) 
                          ,sum(CAST(foldToStreet1CBChance as integer)) 
                          ,sum(CAST(foldToStreet1CBDone as integer)) 
                          ,sum(CAST(foldToStreet2CBChance as integer)) 
                          ,sum(CAST(foldToStreet2CBDone as integer)) 
                          ,sum(CAST(foldToStreet3CBChance as integer)) 
                          ,sum(CAST(foldToStreet3CBDone as integer)) 
                          ,sum(CAST(foldToStreet4CBChance as integer)) 
                          ,sum(CAST(foldToStreet4CBDone as integer)) 
                          ,sum(CAST(totalProfit as integer)) 
                          ,sum(CAST(street1CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street1CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street2CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street2CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street3CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street3CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street4CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street4CheckCallRaiseDone as integer)) 
                    FROM HandsPlayers hp
                    INNER JOIN Hands h ON (h.id = hp.handId)
                    GROUP BY h.gametypeId
                            ,hp.playerId
                            ,h.seats
                            ,hc_position
                            ,hp.tourneyTypeId
                            ,date_format(h.handStart, 'd%y%m%d')
"""
            else:   # assume postgres
                self.query['rebuildHudCache'] = """
                    INSERT INTO HudCache
                    (gametypeId
                    ,playerId
                    ,activeSeats
                    ,position
                    ,tourneyTypeId
                    ,styleKey
                    ,HDs
                    ,wonWhenSeenStreet1
                    ,wonAtSD
                    ,street0VPI
                    ,street0Aggr
                    ,street0_3BChance
                    ,street0_3BDone
                    ,street1Seen
                    ,street2Seen
                    ,street3Seen
                    ,street4Seen
                    ,sawShowdown
                    ,street1Aggr
                    ,street2Aggr
                    ,street3Aggr
                    ,street4Aggr
                    ,otherRaisedStreet1
                    ,otherRaisedStreet2
                    ,otherRaisedStreet3
                    ,otherRaisedStreet4
                    ,foldToOtherRaisedStreet1
                    ,foldToOtherRaisedStreet2
                    ,foldToOtherRaisedStreet3
                    ,foldToOtherRaisedStreet4
                    ,stealAttemptChance
                    ,stealAttempted
                    ,foldBbToStealChance
                    ,foldedBbToSteal
                    ,foldSbToStealChance
                    ,foldedSbToSteal
                    ,street1CBChance
                    ,street1CBDone
                    ,street2CBChance
                    ,street2CBDone
                    ,street3CBChance
                    ,street3CBDone
                    ,street4CBChance
                    ,street4CBDone
                    ,foldToStreet1CBChance
                    ,foldToStreet1CBDone
                    ,foldToStreet2CBChance
                    ,foldToStreet2CBDone
                    ,foldToStreet3CBChance
                    ,foldToStreet3CBDone
                    ,foldToStreet4CBChance
                    ,foldToStreet4CBDone
                    ,totalProfit
                    ,street1CheckCallRaiseChance
                    ,street1CheckCallRaiseDone
                    ,street2CheckCallRaiseChance
                    ,street2CheckCallRaiseDone
                    ,street3CheckCallRaiseChance
                    ,street3CheckCallRaiseDone
                    ,street4CheckCallRaiseChance
                    ,street4CheckCallRaiseDone
                    )
                    SELECT h.gametypeId
                          ,hp.playerId
                          ,h.seats
                          ,case when hp.position = 'B' then 'B'
                                when hp.position = 'S' then 'S'
                                when hp.position = '0' then 'D'
                                when hp.position = '1' then 'C'
                                when hp.position = '2' then 'M'
                                when hp.position = '3' then 'M'
                                when hp.position = '4' then 'M'
                                when hp.position = '5' then 'E'
                                when hp.position = '6' then 'E'
                                when hp.position = '7' then 'E'
                                when hp.position = '8' then 'E'
                                when hp.position = '9' then 'E'
                                else 'E'
                           end                                            AS hc_position
                          ,hp.tourneyTypeId
                          ,'d' || to_char(h.handStart, 'YYMMDD')
                          ,count(1)
                          ,sum(wonWhenSeenStreet1)
                          ,sum(wonAtSD)
                          ,sum(CAST(street0VPI as integer)) 
                          ,sum(CAST(street0Aggr as integer)) 
                          ,sum(CAST(street0_3BChance as integer)) 
                          ,sum(CAST(street0_3BDone as integer)) 
                          ,sum(CAST(street1Seen as integer)) 
                          ,sum(CAST(street2Seen as integer)) 
                          ,sum(CAST(street3Seen as integer)) 
                          ,sum(CAST(street4Seen as integer)) 
                          ,sum(CAST(sawShowdown as integer)) 
                          ,sum(CAST(street1Aggr as integer)) 
                          ,sum(CAST(street2Aggr as integer)) 
                          ,sum(CAST(street3Aggr as integer)) 
                          ,sum(CAST(street4Aggr as integer)) 
                          ,sum(CAST(otherRaisedStreet1 as integer)) 
                          ,sum(CAST(otherRaisedStreet2 as integer)) 
                          ,sum(CAST(otherRaisedStreet3 as integer)) 
                          ,sum(CAST(otherRaisedStreet4 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet1 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet2 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet3 as integer)) 
                          ,sum(CAST(foldToOtherRaisedStreet4 as integer)) 
                          ,sum(CAST(stealAttemptChance as integer)) 
                          ,sum(CAST(stealAttempted as integer)) 
                          ,sum(CAST(foldBbToStealChance as integer)) 
                          ,sum(CAST(foldedBbToSteal as integer)) 
                          ,sum(CAST(foldSbToStealChance as integer)) 
                          ,sum(CAST(foldedSbToSteal as integer)) 
                          ,sum(CAST(street1CBChance as integer)) 
                          ,sum(CAST(street1CBDone as integer)) 
                          ,sum(CAST(street2CBChance as integer)) 
                          ,sum(CAST(street2CBDone as integer)) 
                          ,sum(CAST(street3CBChance as integer)) 
                          ,sum(CAST(street3CBDone as integer)) 
                          ,sum(CAST(street4CBChance as integer)) 
                          ,sum(CAST(street4CBDone as integer)) 
                          ,sum(CAST(foldToStreet1CBChance as integer)) 
                          ,sum(CAST(foldToStreet1CBDone as integer)) 
                          ,sum(CAST(foldToStreet2CBChance as integer)) 
                          ,sum(CAST(foldToStreet2CBDone as integer)) 
                          ,sum(CAST(foldToStreet3CBChance as integer)) 
                          ,sum(CAST(foldToStreet3CBDone as integer)) 
                          ,sum(CAST(foldToStreet4CBChance as integer)) 
                          ,sum(CAST(foldToStreet4CBDone as integer)) 
                          ,sum(CAST(totalProfit as integer)) 
                          ,sum(CAST(street1CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street1CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street2CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street2CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street3CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street3CheckCallRaiseDone as integer)) 
                          ,sum(CAST(street4CheckCallRaiseChance as integer)) 
                          ,sum(CAST(street4CheckCallRaiseDone as integer)) 
                    FROM HandsPlayers hp
                    INNER JOIN Hands h ON (h.id = hp.handId)
                    GROUP BY h.gametypeId
                            ,hp.playerId
                            ,h.seats
                            ,hc_position
                            ,hp.tourneyTypeId
                            ,to_char(h.handStart, 'YYMMDD')
"""

if __name__== "__main__":
#    just print the default queries and exit
    s = Sql(game = 'razz', type = 'ptracks')
    for key in s.query:
        print "For query " + key + ", sql ="
        print s.query[key]
