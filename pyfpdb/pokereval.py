#
# Copyright (C) 2007, 2008 Loic Dachary <loic@dachary.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep
#
# Mekensleep
# 24 rue vieille du temple
# 75004 Paris
#       licensing@mekensleep.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#  Loic Dachary <loic@dachary.org>
#
# 
import sys

# for fpdb alter the following line from __import__ to import...as... .
# fpdb py2exe package build does no recognise __import__ statement,
# and fails at runtime with _pokereval_2_6 not found

#_pokereval = __import__('_pokereval_' + sys.version[0] + '_' + sys.version[2])
import _pokereval_2_6 as _pokereval

from types import *

class PokerEval:
    """\
Evaluate the strengh of a poker hand for a given poker variant.
In all methods, when a list of cards is to be provided (for instance
with the "hand" argument of the "best" method), each member of the
list may be a number or a string designating a card according to
the following table:

       2h/00  2d/13  2c/26  2s/39
       3h/01  3d/14  3c/27  3s/40
       4h/02  4d/15  4c/28  4s/41
       5h/03  5d/16  5c/29  5s/42
       6h/04  6d/17  6c/30  6s/43
       7h/05  7d/18  7c/31  7s/44
       8h/06  8d/19  8c/32  8s/45
       9h/07  9d/20  9c/33  9s/46
       Th/08  Td/21  Tc/34  Ts/47
       Jh/09  Jd/22  Jc/35  Js/48
       Qh/10  Qd/23  Qc/36  Qs/49
       Kh/11  Kd/24  Kc/37  Ks/50
       Ah/12  Ad/25  Ac/38  As/51

The string __ (two underscore) or the number 255 are placeholders
meaning that the card is unknown.
"""

    def best(self, side, hand, board = []):
        """\
Return the best five card combination that can be made with the cards
listed in "hand" and, optionally, board. The "side" may be "hi" or
"low". The "board" argument must only be provided for variants where
knowing if a given card is taken from the board or not is significant
(such as Omaha but not Holdem).

A list is returned. The first element is the numerical value
of the hand (better hands have higher values if "side" is "hi" and
lower values if "side" is "low"). The second element is a list whose
first element is the strength of the hand among the following:

Nothing (only if "side" equals "low")
NoPair
TwoPair
Trips
Straight
Flush
FlHouse
Quads
StFlush

The last five elements are numbers describing the best hand properly
sorted (for instance the ace is at the end for no pair if "side" is low or
at the beginning if "side" high).

Examples:

[134414336, ['StFlush', 29, 28, 27, 26, 38]] is the wheel five to ace, clubs
[475920, ['NoPair', 45, 29, 41, 39, 51]] is As, 8s, 5c, 4s, 2s 
[268435455, ['Nothing']] means there is no qualifying low
"""
        if len(hand + board) >= 5:
            return _pokereval.eval_hand(side, hand, board)
        else:
            return False

    def best_hand(self, side, hand, board = []):
        """\
Return the best five card combination that can be made with the cards
listed in "hand" and, optionaly, board. The "side" may be "hi" or
"low". The returned value is the second element of the list returned
by the "best" method.
"""
        if len(hand + board) >= 5:
            return _pokereval.eval_hand(side, hand, board)[1]
        else:
            return False

    def best_hand_value(self, side, hand, board = []):
        """\
Return the best five card combination that can be made with the cards
listed in "hand" and, optionaly, board. The "side" may be "hi" or
"low". The returned value is the first element of the list returned
by the "best" method.
"""
        if len(hand + board) >= 5:
            return _pokereval.eval_hand(side, hand, board)[0]
        else:
            return False

    def evaln(self, cards):
        """\
Call the poker-eval Hand_EVAL_N function with the "cards" argument.
Return the strength of the "cards" as a number. The higher the
better.
"""
        return _pokereval.evaln(cards)
    
    def winners(self, *args, **kwargs):
        """\
Return a list of the indexes of the best hands, relative to the "pockets"
keyword argument. For instance, if the first pocket and third pocket cards
tie, the list would be [0, 2]. Since there may be more than one way to
win a hand, a hash is returned with the list of the winners for each so
called side. For instace {'hi': [0], 'low': [1]} means pocket cards
at index 0 won the high side of the hand and pocket cards at index 1
won the low side.

See the"poker_eval" method for a detailed
explanation of the semantics of the arguments.

If the keyword argument "fill_pockets" is set, pocket cards
can contain a placeholder (i.e. 255 or __) that will be be
used as specified in the "poker_eval" method documentation.

If the keyword argument "fill_pockets" is not set, pocket cards
that contain at least one placeholder (i.e. 255 or __) are
ignored completly. For instance if winners is called as follows
o.winners(game = 'holdem', pockets = [ [ '__', 'As' ], [ 'Ks', 'Kd'] ])
it is strictly equivalent as calling
o.winners(game = 'holdem', pockets = [ [ 'Ks', 'Kd'] ]).
"""
        index2index = {}
        normalized_pockets = []
        normalized_index = 0
        pockets = kwargs["pockets"][:]
        for index in xrange(len(pockets)):
            if not kwargs.has_key("fill_pockets"):
                if 255 in pockets[index] or "__" in pockets[index]:
                    pockets[index] = []

            if pockets[index] != []:
                normalized_pockets.append(pockets[index])
                index2index[index] = normalized_index
                normalized_index += 1
        kwargs["pockets"] = normalized_pockets
        
        results = _pokereval.poker_eval(*args, **kwargs)

        (count, haslopot, hashipot) = results.pop(0)
        winners = { 'low': [], 'hi': [] }
        for index in xrange(len(pockets)):
            if index2index.has_key(index):
                result = results[index2index[index]]
                if result[1] == 1 or result[3] == 1:
                    winners["hi"].append(index)
                if result[4] == 1 or result[6] == 1:
                    winners["low"].append(index)

        if not haslopot or len(winners["low"]) == 0:
            del winners["low"]
        if not hashipot:
            del winners["hi"]
        return winners
        
    def poker_eval(self, *args, **kwargs):
        """\
Provided with a description of a poker game, return the outcome (if at showdown) or
the expected value of each hand. The poker game description is provided as a set
of keyword arguments with the following meaning:

game      : the variant (holdem, holdem8, omaha, omaha8, 7stud, 7stud8, razz,
            5draw, 5draw8, 5drawnsq, lowball, lowball27). 
            Mandatory, no default.
                    
pockets   : list of pocket cards for each player still in game. Each member
            of the list is a list of cards. The position of the pocket cards
            in the list is meaningfull for the value returned will refer to
            this position when stating which player wins, tie or loose.
            Example: [ ["tc", "ac"],  ["3h", "ah"],  ["8c", "6h"]]
            Cards do not have to be real cards like "tc" or "4s". They may also be a 
            placeholder, denoted by "__" or 255. When using placeholders, the 
            keyword argument "iterations" may be specified to use Monte Carlo instead of
            exhaustive exploration of all the possible combinations.
            Example2: [ ["tc", "__"],  [255, "ah"],  ["8c", "6h"]]

            Mandatory, no default.

board     : list of community cards, for games where this is meaningfull. If
            specified when irrelevant, the return value cannot be predicted.
            Default: []

dead      : list of dead cards. These cards won't be accounted for when exloring
            the possible hands.
            Default: []

iterations: the maximum number of iterations when exploring the
            possible outcome of a given hand. Roughly speaking, each
            iteration means to distribute cards that are missing (for
            which there are place holders in the board or pockets
            keywords arguments, i.e. 255 or __). If the number of
            iterations is not specified and there are place holders,
            the return value cannot be predicted.
            Default: +infinite (i.e. exhaustive exploration)

Example: object.poker_eval(game = "holdem",
                           pockets = [ ["tc", "ac"],  ["3h", "ah"],  ["8c", "6h"]],
                           dead = [],
                           board = ["7h", "3s", "2c"])

The return value is a map of two entries:
'info' contains three integers:
 - the number of samples (which must be equal to the number of iterations given
   in argument).
 - 1 if the game has a low side, 0 otherwise
 - 1 if the game has a high side, 0 otherwise
'eval' is a list of as many maps as there are pocket cards, each
made of the following entries:
 'scoop': the number of time these pocket cards scoop
 'winhi': the number of time these pocket cards win the high side
 'losehi': the number of time these pocket cards lose the high side
 'tiehi': the number of time these pocket cards tie for the high side
 'winlo': the number of time these pocket cards win the low side
 'loselo': the number of time these pocket cards lose the low side
 'tielo': the number of time these pocket cards tie for the low side
 'ev': the EV of these pocket cards as an int in the range [0,1000] with
       1000 being the best.

It should be clear that if there is only one sample (i.e. because all the
cards are known which is the situation that occurs at showdown) the details
provided by the 'eval' entry is mostly irrelevant and the caller might
prefer to call the winners method instead.
"""
        result = _pokereval.poker_eval(*args, **kwargs)
        return {
            'info': result[0],
            'eval': [ { 'scoop': x[0],
                        'winhi': x[1],
                        'losehi': x[2],
                        'tiehi': x[3],
                        'winlo': x[4],
                        'loselo': x[5],
                        'tielo': x[6],
                        'ev': int(x[7] * 1000) } for x in result[1:] ]
            }

    def deck(self):
        """\
Return the list of all cards in the deck.
"""
        return [ self.string2card(i + j) for i in "23456789TJQKA" for j in "hdcs" ]

    def nocard(self):
        """Return 255, the numerical value of a place holder in a list of cards."""
        return 255

    def string2card(self, cards):
        """\
Convert card names (strings) to card numbers (integers) according to the
following map:

       2h/00  2d/13  2c/26  2s/39
       3h/01  3d/14  3c/27  3s/40
       4h/02  4d/15  4c/28  4s/41
       5h/03  5d/16  5c/29  5s/42
       6h/04  6d/17  6c/30  6s/43
       7h/05  7d/18  7c/31  7s/44
       8h/06  8d/19  8c/32  8s/45
       9h/07  9d/20  9c/33  9s/46
       Th/08  Td/21  Tc/34  Ts/47
       Jh/09  Jd/22  Jc/35  Js/48
       Qh/10  Qd/23  Qc/36  Qs/49
       Kh/11  Kd/24  Kc/37  Ks/50
       Ah/12  Ad/25  Ac/38  As/51

The "cards" argument may be either a list in which case a converted list
is returned or a string in which case the corresponding number is
returned.
"""
        if type(cards) is ListType or type(cards) is TupleType:
            return [ _pokereval.string2card(card) for card in cards ]
        else:
            return _pokereval.string2card(cards)

    def card2string(self, cards):
        """\
Convert card numbers (integers) to card names (strings) according to the
following map:

       2h/00  2d/13  2c/26  2s/39
       3h/01  3d/14  3c/27  3s/40
       4h/02  4d/15  4c/28  4s/41
       5h/03  5d/16  5c/29  5s/42
       6h/04  6d/17  6c/30  6s/43
       7h/05  7d/18  7c/31  7s/44
       8h/06  8d/19  8c/32  8s/45
       9h/07  9d/20  9c/33  9s/46
       Th/08  Td/21  Tc/34  Ts/47
       Jh/09  Jd/22  Jc/35  Js/48
       Qh/10  Qd/23  Qc/36  Qs/49
       Kh/11  Kd/24  Kc/37  Ks/50
       Ah/12  Ad/25  Ac/38  As/51

The "cards" argument may be either a list in which case a converted list
is returned or an integer in which case the corresponding string is
returned.
"""
        if type(cards) is ListType or type(cards) is TupleType:
            return [ _pokereval.card2string(card) for card in cards ]
        else:
            return _pokereval.card2string(cards)
        
