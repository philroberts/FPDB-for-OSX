#!/usr/bin/python

#Copyright 2008 Carl Gherardi
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




def twoStartCards(value1, suit1, value2, suit2):
    """ Function to convert 2 value,suit pairs into a Holdem style starting hand e.g. AQo
        Hand is stored as an int 13 * x + y where (x+2) represents rank of 1st card and
        (y+2) represents rank of second card (2=2 .. 14=Ace)
        If x > y then pair is suited, if x < y then unsuited"""
    if value1 < 2 or value2 < 2:
        return(0)
    if (suit1 == suit2 and value1 < value2) or (suit1 != suit2 and value2 > value1):
        return(13 * (value2-2) + (value1-1))
    else:
        return(13 * (value1-2) + (value2-1))

def twoStartCardString(card):
    """ Function to convert an int representing 2 holdem hole cards (as created by twoStartCards)
        into a string like AQo """
    if card <= 0:
        return 'xx'
    else:
        card -= 1
        s = ('2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        x = card/13
        y = card - 13*x
        if x == y:  return(s[x] + s[y])
        elif x > y: return(s[x] + s[y] + 's')
        else:       return(s[y] + s[x] + 'o')

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

def valueSuitFromCard(card):
    """ Function to convert a card stored in the database (int 0-52) into value 
        and suit like 9s, 4c etc """
    if card < 0 or card > 52 or not card:
        return('')
    else:
        return( ['', '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah'
                     , '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad'
                     , '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac'
                     , '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As'
                ][card] )



