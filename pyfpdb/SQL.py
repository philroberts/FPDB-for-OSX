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
                        card1Value AS card1value,
                        card1Suit  AS card1suit,
                        card2Value AS card2value,
                        card2Suit  AS card2suit,
                        card3Value AS card3value,
                        card3Suit  AS card3suit,
                        card4Value AS card4value,
                        card4Suit  AS card4suit,
                        card5Value AS card5value,
                        card5Suit  AS card5suit
                    from BoardCards
                    where handId = %s
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

if __name__== "__main__":
#    just print the default queries and exit
    s = Sql(game = 'razz', type = 'ptracks')
    for key in s.query:
        print "For query " + key + ", sql ="
        print s.query[key]
