#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright 2008-2010 Carl Gherardi
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

# From fpdb_simple
card_map = { "0": 0, "2": 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8,
            "9" : 9, "T" : 10, "J" : 11, "Q" : 12, "K" : 13, "A" : 14}

# FIXME: the following is a workaround until switching to newimport.
#        This should be moved into DerivedStats
#        I'd also like to change HandsPlayers.startCards to a different datatype
#        so we can 'trivially' add different start card classifications

def calcStartCards(hand, player):
    if hand.gametype['category'] == 'holdem':
        hcs = hand.join_holecards(player, asList=True)
        #print "DEBUG: hcs: %s" % hcs
        value1 = card_map[hcs[0][0]]
        value2 = card_map[hcs[1][0]]
        return twoStartCards(value1, hcs[0][1], value2, hcs[1][1])
    else:
        # FIXME: Only do startCards value for holdem at the moment
        return 0


def twoStartCards(value1, suit1, value2, suit2):
    """ Function to convert 2 value,suit pairs into a Holdem style starting hand e.g. AQo
        Incoming values should be ints 2-14 (2,3,...K,A), suits are 'd'/'h'/'c'/'s'
        Hand is stored as an int 13 * x + y + 1 where (x+2) represents rank of 1st card and
        (y+2) represents rank of second card (2=2 .. 14=Ace)
        If x > y then pair is suited, if x < y then unsuited
        Examples:
           0  Unknown / Illegal cards
           1  22
           2  32o
           3  42o
              ...
          14  32s
          15  33
          16  42o
              ...
         170  AA
    """
    if value1 is None or value1 < 2 or value1 > 14 or value2 is None or value2 < 2 or value2 > 14:
        ret = 0
    elif value1 == value2: # pairs
        ret = (13 * (value2-2) + (value2-2) ) + 1
    elif suit1 == suit2:
        if value1 > value2:
            ret = 13 * (value1-2) + (value2-2) + 1
        else:
            ret = 13 * (value2-2) + (value1-2) + 1
    else:
        if value1 > value2:
            ret = 13 * (value2-2) + (value1-2) + 1
        else:
            ret = 13 * (value1-2) + (value2-2) + 1

#    print "twoStartCards(", value1, suit1, value2, suit2, ")=", ret
    return ret

def twoStartCardString(card):
    """ Function to convert an int representing 2 holdem hole cards (as created by twoStartCards)
        into a string like AQo """
    ret = 'xx'
    if card > 0:
        s = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        x = (card-1) / 13
        y = (card-1) - 13 * x
        if x == y:  ret = s[x] + s[y]
        elif x > y: ret = s[x] + s[y] + 's'
        else:       ret = s[y] + s[x] + 'o'
#    print "twoStartCardString(", card ,") = " + ret
    return ret

def fourStartCards(value1, suit1, value2, suit2, value3, suit3, value4, suit4):
    """ Function to convert 4 value,suit pairs into a Omaha style starting hand,
        haven't decided how to encode this yet """
        # This doesn't actually do anything yet - CG

        # What combinations do we need to store? just cards: AA23? some suits as well e.g. when
        # double suited ATcKTd? Lots more possible combos than holdem :-(  270K vs 1326? not sure
        # Probably need to use this field as a key into some other table  -  sc

        #AAKKds
        #AAKKs
        #AAKKr
        # Is probably what we are looking for

        # mct:
        # my maths says there are 4 classes of suitedness
        # SSSS SSSx SSxy SSHH
        # encode them as follows:
        # SSSS (K, J, 6, 3)
        # - 13C4 = 715 possibilities
        # SSSx (K, J, 6),(3)
        # - 13C3 * 13 = 3718 possibilities
        # SSxy (K, J),(6),(3)
        # - 13C2 * 13*13 = 13182 possibilities
        # SSHH (K, J),(6, 3)
        # - 13C2 * 13C2 = 6084 possibilities
        # Needless to say they won't fit on a 13x13 grid.
        # The actual number of hands in each class is far greater
    return(0)

def cardFromValueSuit(value, suit):
    """ 0=none, 1-13=2-Ah 14-26=2-Ad 27-39=2-Ac 40-52=2-As """
    if suit == 'h':  return(value-1)
    elif suit == 'd':  return(value+12)
    elif suit == 'c':  return(value+25)
    elif suit == 's':  return(value+38)
    else: return(0)

suitFromCardList = ['', '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah'
                     , '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad'
                     , '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac'
                     , '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As'
                ]
def valueSuitFromCard(card):
    """ Function to convert a card stored in the database (int 0-52) into value
        and suit like 9s, 4c etc """
    global suitFromCardList
    if card < 0 or card > 52 or not card:
        return('')
    else:
        return suitFromCardList[card]

encodeCardList = {'2h':  1, '3h':  2, '4h':  3, '5h':  4, '6h':  5, '7h':  6, '8h':  7, '9h':  8, 'Th':  9, 'Jh': 10, 'Qh': 11, 'Kh': 12, 'Ah': 13,
                  '2d': 14, '3d': 15, '4d': 16, '5d': 17, '6d': 18, '7d': 19, '8d': 20, '9d': 21, 'Td': 22, 'Jd': 23, 'Qd': 24, 'Kd': 25, 'Ad': 26,
                  '2c': 27, '3c': 28, '4c': 29, '5c': 30, '6c': 31, '7c': 32, '8c': 33, '9c': 34, 'Tc': 35, 'Jc': 36, 'Qc': 37, 'Kc': 38, 'Ac': 39,
                  '2s': 40, '3s': 41, '4s': 42, '5s': 43, '6s': 44, '7s': 45, '8s': 46, '9s': 47, 'Ts': 48, 'Js': 49, 'Qs': 50, 'Ks': 51, 'As': 52,
                  '  ':  0
                }

def encodeCard(cardString):
    """Take a card string (Ah) and convert it to the db card code (1)."""
    global encodeCardList
    if cardString not in encodeCardList: return 0
    return encodeCardList[cardString]

def encodeRazzStartHand(cards):
    """No idea how this is actually going to work, figured i'd record the top 10
       starting hands anyway
    """
#    (32)A (3A)2 (2A)3 (42)A (4A)2 (2A)4 (43)A (4A)3 (3A)4 (43)2
#    (42)3 (32)4 (52)A (5A)2 (2A)5 (53)A (5A)3 (3A)5 (53)2 (52)3
#    (32)5 (54)A (5A)4 (4A)5 (54)2 (52)4 (42)5 (54)3 (53)4 (43)5
#    (62)A (6A)2 (2A)6 (63)A (6A)3 (3A)6 (63)2 (62)3 (32)6 (64)A
#    (6A)4 (4A)6 (64)2 (62)4 (42)6 (64)3 (63)4 (43)6 (65)A (6A)5
#    (5A)6 (65)2 (62)5 (52)6 (65)3 (63)5 (53)6 (65)4 (64)5 (54)6
#    (72)A (7A)2 (2A)7 (73)A (7A)3 (3A)7 (73)2 (72)3 (32)7 (74)A
#    (7A)4 (4A)7 (74)2 (72)4 (42)7 (74)3 (73)4 (43)7 (75)A (7A)5
#    (5A)7 (75)2 (72)5 (52)7 (75)3 (73)5 (53)7 (75)4 (74)5 (54)7
#    (76)A (7A)6 (6A)7 (76)2 (72)6 (62)7 (76)3 (73)6 (63)7 (76)4
#    (74)6 (64)7 (76)5 (75)6 (65)7 (82)A (8A)2 (2A)8 (83)A (8A)3
#    (3A)8 (83)2 (82)3 (32)8 (84)A (8A)4 (4A)8 (84)2 (82)4 (42)8
#    (84)3 (83)4 (43)8 (85)A (8A)5 (5A)8 (85)2 (82)5 (52)8 (85)3
#    (83)5 (53)8 (85)4 (84)5 (54)8 (86)A (8A)6 (6A)8 (86)2 (82)6
#    (62)8 (86)3 (83)6 (63)8 (86)4 (84)6 (64)8 (86)5 (85)6 (65)8
#    (87)A (8A)7 (7A)8 (87)2 (82)7 (72)8 (87)3 (83)7 (73)8 (87)4
#    (84)7 (74)8 (87)5 (85)7 (75)8 (87)6 (86)7 (76)8 (92)A (9A)2
#    (2A)9 (93)A (9A)3 (3A)9 (93)2 (92)3 (32)9 (94)A (9A)4 (4A)9
#    (94)2 (92)4 (42)9 (94)3 (93)4 (43)9 (95)A (9A)5 (5A)9 (95)2
#    (92)5 (52)9 (95)3 (93)5 (53)9 (95)4 (94)5 (54)9 (96)A (9A)6
#    (6A)9 (96)2 (92)6 (62)9 (96)3 (93)6 (63)9 (96)4 (94)6 (64)9
#    (96)5 (95)6 (65)9 (97)A (9A)7 (7A)9 (97)2 (92)7 (72)9 (97)3
#    (93)7 (73)9 (97)4 (94)7 (74)9 (97)5 (95)7 (75)9 (97)6 (96)7
#    (76)9 (98)A (9A)8 (8A)9 (98)2 (92)8 (82)9 (98)3 (93)8 (83)9
#    (98)4 (94)8 (84)9 (98)5 (95)8 (85)9 (98)6 (96)8 (86)9 (98)7
#    (97)8 (87)9 (T2)A (TA)2 (2A)T (T3)A (TA)3 (3A)T (T3)2 (T2)3
#    (32)T (T4)A (TA)4 (4A)T (T4)2 (T2)4 (42)T (T4)3 (T3)4 (43)T
#    (T5)A (TA)5 (5A)T (T5)2 (T2)5 (52)T (T5)3 (T3)5 (53)T (T5)4
#    (T4)5 (54)T (T6)A (TA)6 (6A)T (T6)2 (T2)6 (62)T (T6)3 (T3)6
#    (63)T (T6)4 (T4)6 (64)T (T6)5 (T5)6 (65)T (T7)A (TA)7 (7A)T
#    (T7)2 (T2)7 (72)T (T7)3 (T3)7 (73)T (T7)4 (T4)7 (74)T (T7)5
#    (T5)7 (75)T (T7)6 (T6)7 (76)T (T8)A (TA)8 (8A)T (T8)2 (T2)8
#    (82)T (T8)3 (T3)8 (83)T (T8)4 (T4)8 (84)T (T8)5 (T5)8 (85)T
#    (T8)6 (T6)8 (86)T (T8)7 (T7)8 (87)T (T9)A (TA)9 (9A)T (T9)2
#    (T2)9 (92)T (T9)3 (T3)9 (93)T (T9)4 (T4)9 (94)T (T9)5 (T5)9
#    (95)T (T9)6 (T6)9 (96)T (T9)7 (T7)9 (97)T (T9)8 (T8)9 (98)T
#    (J2)A (JA)2 (2A)J (J3)A (JA)3 (3A)J (J3)2 (J2)3 (32)J (J4)A
#    (JA)4 (4A)J (J4)2 (J2)4 (42)J (J4)3 (J3)4 (43)J (J5)A (JA)5
#    (5A)J (J5)2 (J2)5 (52)J (J5)3 (J3)5 (53)J (J5)4 (J4)5 (54)J
#    (J6)A (JA)6 (6A)J (J6)2 (J2)6 (62)J (J6)3 (J3)6 (63)J (J6)4
#    (J4)6 (64)J (J6)5 (J5)6 (65)J (J7)A (JA)7 (7A)J (J7)2 (J2)7
#    (72)J (J7)3 (J3)7 (73)J (J7)4 (J4)7 (74)J (J7)5 (J5)7 (75)J
#    (J7)6 (J6)7 (76)J (J8)A (JA)8 (8A)J (J8)2 (J2)8 (82)J (J8)3
#    (J3)8 (83)J (J8)4 (J4)8 (84)J (J8)5 (J5)8 (85)J (J8)6 (J6)8
#    (86)J (J8)7 (J7)8 (87)J (J9)A (JA)9 (9A)J (J9)2 (J2)9 (92)J
#    (J9)3 (J3)9 (93)J (J9)4 (J4)9 (94)J (J9)5 (J5)9 (95)J (J9)6
#    (J6)9 (96)J (J9)7 (J7)9 (97)J (J9)8 (J8)9 (98)J (JT)A (JA)T
#    (TA)J (JT)2 (J2)T (T2)J (JT)3 (J3)T (T3)J (JT)4 (J4)T (T4)J
#    (JT)5 (J5)T (T5)J (JT)6 (J6)T (T6)J (JT)7 (J7)T (T7)J (JT)8
#    (J8)T (T8)J (JT)9 (J9)T (T9)J (Q2)A (QA)2 (2A)Q (Q3)A (QA)3
#    (3A)Q (Q3)2 (Q2)3 (32)Q (Q4)A (QA)4 (4A)Q (Q4)2 (Q2)4 (42)Q
#    (Q4)3 (Q3)4 (43)Q (Q5)A (QA)5 (5A)Q (Q5)2 (Q2)5 (52)Q (Q5)3
#    (Q3)5 (53)Q (Q5)4 (Q4)5 (54)Q (Q6)A (QA)6 (6A)Q (Q6)2 (Q2)6
#    (62)Q (Q6)3 (Q3)6 (63)Q (Q6)4 (Q4)6 (64)Q (Q6)5 (Q5)6 (65)Q
#    (Q7)A (QA)7 (7A)Q (Q7)2 (Q2)7 (72)Q (Q7)3 (Q3)7 (73)Q (Q7)4
#    (Q4)7 (74)Q (Q7)5 (Q5)7 (75)Q (Q7)6 (Q6)7 (76)Q (Q8)A (QA)8
#    (8A)Q (Q8)2 (Q2)8 (82)Q (Q8)3 (Q3)8 (83)Q (Q8)4 (Q4)8 (84)Q
#    (Q8)5 (Q5)8 (85)Q (Q8)6 (Q6)8 (86)Q (Q8)7 (Q7)8 (87)Q (Q9)A
#    (QA)9 (9A)Q (Q9)2 (Q2)9 (92)Q (Q9)3 (Q3)9 (93)Q (Q9)4 (Q4)9
#    (94)Q (Q9)5 (Q5)9 (95)Q (Q9)6 (Q6)9 (96)Q (Q9)7 (Q7)9 (97)Q
#    (Q9)8 (Q8)9 (98)Q (QT)A (QA)T (TA)Q (QT)2 (Q2)T (T2)Q (QT)3
#    (Q3)T (T3)Q (QT)4 (Q4)T (T4)Q (QT)5 (Q5)T (T5)Q (QT)6 (Q6)T
#    (T6)Q (QT)7 (Q7)T (T7)Q (QT)8 (Q8)T (T8)Q (QT)9 (Q9)T (T9)Q
#    (QJ)A (QA)J (JA)Q (QJ)2 (Q2)J (J2)Q (QJ)3 (Q3)J (J3)Q (QJ)4
#    (Q4)J (J4)Q (QJ)5 (Q5)J (J5)Q (QJ)6 (Q6)J (J6)Q (QJ)7 (Q7)J
#    (J7)Q (QJ)8 (Q8)J (J8)Q (QJ)9 (Q9)J (J9)Q (QJ)T (QT)J (JT)Q
#    (K2)A (KA)2 (2A)K (K3)A (KA)3 (3A)K (K3)2 (K2)3 (32)K (K4)A
#    (KA)4 (4A)K (K4)2 (K2)4 (42)K (K4)3 (K3)4 (43)K (K5)A (KA)5
#    (5A)K (K5)2 (K2)5 (52)K (K5)3 (K3)5 (53)K (K5)4 (K4)5 (54)K
#    (K6)A (KA)6 (6A)K (K6)2 (K2)6 (62)K (K6)3 (K3)6 (63)K (K6)4
#    (K4)6 (64)K (K6)5 (K5)6 (65)K (K7)A (KA)7 (7A)K (K7)2 (K2)7
#    (72)K (K7)3 (K3)7 (73)K (K7)4 (K4)7 (74)K (K7)5 (K5)7 (75)K
#    (K7)6 (K6)7 (76)K (K8)A (KA)8 (8A)K (K8)2 (K2)8 (82)K (K8)3
#    (K3)8 (83)K (K8)4 (K4)8 (84)K (K8)5 (K5)8 (85)K (K8)6 (K6)8
#    (86)K (K8)7 (K7)8 (87)K (K9)A (KA)9 (9A)K (K9)2 (K2)9 (92)K
#    (K9)3 (K3)9 (93)K (K9)4 (K4)9 (94)K (K9)5 (K5)9 (95)K (K9)6
#    (K6)9 (96)K (K9)7 (K7)9 (97)K (K9)8 (K8)9 (98)K (KT)A (KA)T
#    (TA)K (KT)2 (K2)T (T2)K (KT)3 (K3)T (T3)K (KT)4 (K4)T (T4)K
#    (KT)5 (K5)T (T5)K (KT)6 (K6)T (T6)K (KT)7 (K7)T (T7)K (KT)8
#    (K8)T (T8)K (KT)9 (K9)T (T9)K (KJ)A (KA)J (JA)K (KJ)2 (K2)J
#    (J2)K (KJ)3 (K3)J (J3)K (KJ)4 (K4)J (J4)K (KJ)5 (K5)J (J5)K
#    (KJ)6 (K6)J (J6)K (KJ)7 (K7)J (J7)K (KJ)8 (K8)J (J8)K (KJ)9
#    (K9)J (J9)K (KJ)T (KT)J (JT)K (KQ)A (KA)Q (QA)K (KQ)2 (K2)Q
#    (Q2)K (KQ)3 (K3)Q (Q3)K (KQ)4 (K4)Q (Q4)K (KQ)5 (K5)Q (Q5)K
#    (KQ)6 (K6)Q (Q6)K (KQ)7 (K7)Q (Q7)K (KQ)8 (K8)Q (Q8)K (KQ)9
#    (K9)Q (Q9)K (KQ)T (KT)Q (QT)K (KQ)J (KJ)Q (QJ)K (2A)A (22)A
#    (AA)2 (2A)2 (3A)A (33)A (AA)3 (3A)3 (32)2 (33)2 (22)3 (32)3
#    (4A)A (44)A (AA)4 (4A)4 (42)2 (44)2 (22)4 (42)4 (43)3 (44)3
#    (33)4 (43)4 (5A)A (55)A (AA)5 (5A)5 (52)2 (55)2 (22)5 (52)5
#    (53)3 (55)3 (33)5 (53)5 (54)4 (55)4 (44)5 (54)5 (6A)A (66)A
#    (AA)6 (6A)6 (62)2 (66)2 (22)6 (62)6 (63)3 (66)3 (33)6 (63)6
#    (64)4 (66)4 (44)6 (64)6 (65)5 (66)5 (55)6 (65)6 (7A)A (77)A
#    (AA)7 (7A)7 (72)2 (77)2 (22)7 (72)7 (73)3 (77)3 (33)7 (73)7
#    (74)4 (77)4 (44)7 (74)7 (75)5 (77)5 (55)7 (75)7 (76)6 (77)6
#    (66)7 (76)7 (8A)A (88)A (AA)8 (8A)8 (82)2 (88)2 (22)8 (82)8
#    (83)3 (88)3 (33)8 (83)8 (84)4 (88)4 (44)8 (84)8 (85)5 (88)5
#    (55)8 (85)8 (86)6 (88)6 (66)8 (86)8 (87)7 (88)7 (77)8 (87)8
#    (9A)A (99)A (AA)9 (9A)9 (92)2 (99)2 (22)9 (92)9 (93)3 (99)3
#    (33)9 (93)9 (94)4 (99)4 (44)9 (94)9 (95)5 (99)5 (55)9 (95)9
#    (96)6 (99)6 (66)9 (96)9 (97)7 (99)7 (77)9 (97)9 (98)8 (99)8
#    (88)9 (98)9 (TA)A (TT)A (AA)T (TA)T (T2)2 (TT)2 (22)T (T2)T
#    (T3)3 (TT)3 (33)T (T3)T (T4)4 (TT)4 (44)T (T4)T (T5)5 (TT)5
#    (55)T (T5)T (T6)6 (TT)6 (66)T (T6)T (T7)7 (TT)7 (77)T (T7)T
#    (T8)8 (TT)8 (88)T (T8)T (T9)9 (TT)9 (99)T (T9)T (JA)A (JJ)A
#    (AA)J (JA)J (J2)2 (JJ)2 (22)J (J2)J (J3)3 (JJ)3 (33)J (J3)J
#    (J4)4 (JJ)4 (44)J (J4)J (J5)5 (JJ)5 (55)J (J5)J (J6)6 (JJ)6
#    (66)J (J6)J (J7)7 (JJ)7 (77)J (J7)J (J8)8 (JJ)8 (88)J (J8)J
#    (J9)9 (JJ)9 (99)J (J9)J (JT)T (JJ)T (TT)J (JT)J (QA)A (QQ)A
#    (AA)Q (QA)Q (Q2)2 (QQ)2 (22)Q (Q2)Q (Q3)3 (QQ)3 (33)Q (Q3)Q
#    (Q4)4 (QQ)4 (44)Q (Q4)Q (Q5)5 (QQ)5 (55)Q (Q5)Q (Q6)6 (QQ)6
#    (66)Q (Q6)Q (Q7)7 (QQ)7 (77)Q (Q7)Q (Q8)8 (QQ)8 (88)Q (Q8)Q
#    (Q9)9 (QQ)9 (99)Q (Q9)Q (QT)T (QQ)T (TT)Q (QT)Q (QJ)J (QQ)J
#    (JJ)Q (QJ)Q (KA)A (KK)A (AA)K (KA)K (K2)2 (KK)2 (22)K (K2)K
#    (K3)3 (KK)3 (33)K (K3)K (K4)4 (KK)4 (44)K (K4)K (K5)5 (KK)5
#    (55)K (K5)K (K6)6 (KK)6 (66)K (K6)K (K7)7 (KK)7 (77)K (K7)K
#    (K8)8 (KK)8 (88)K (K8)K (K9)9 (KK)9 (99)K (K9)K (KT)T (KK)T
#    (TT)K (KT)K (KJ)J (KK)J (JJ)K (KJ)K (KQ)Q (KK)Q (QQ)K (KQ)K
#    (AA)A (22)2 (33)3 (44)4 (55)5 (66)6 (77)7 (88)8 (99)9 (TT)T
#    (JJ)J (QQ)Q (KK)K 
    pass

if __name__ == '__main__':
    print _("fpdb card encoding(same as pokersource)")
    for i in xrange(1, 14):
        print "card %2d = %s    card %2d = %s    card %2d = %s    card %2d = %s" % \
            (i, valueSuitFromCard(i), i+13, valueSuitFromCard(i+13), i+26, valueSuitFromCard(i+26), i+39, valueSuitFromCard(i+39))

        print
    print encodeCard('7c')
