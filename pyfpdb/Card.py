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

if __name__ == '__main__':
    print _("fpdb card encoding(same as pokersource)")
    for i in xrange(1, 14):
        print "card %2d = %s    card %2d = %s    card %2d = %s    card %2d = %s" % \
            (i, valueSuitFromCard(i), i+13, valueSuitFromCard(i+13), i+26, valueSuitFromCard(i+26), i+39, valueSuitFromCard(i+39))

        print
    print encodeCard('7c')
