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
sys.path.insert(0, ".")
sys.path.insert(0, ".libs")

from pokereval import PokerEval

iterations_low = 100000
iterations_high = 200000

pokereval = PokerEval()

if pokereval.best_hand_value("hi", ["Ah", "Ad", "As", "Kh", "Ks" ]) != 101494784:
    sys.exit(1)

if pokereval.string2card("2h") != 0:
    sys.exit(1)

print ""
pockets = [ ["As", "Ad", "Ac", "Tc", "Ts", "2d", "5c" ],
            ["Js", "Jc", "7s", "8c", "8d", "3c", "3h" ],
            [255, 255 ] ]
print "stud7 (1) result = %s\n" % pokereval.winners(game = "7stud", pockets = pockets, dead = [], board = [])

pockets = [[22, 18, 21, 3, 41, 1, 30], [39, 255, 255, 15, 13, 17, 255]]
print "stud7 (2) result = %s\n" % pokereval.winners(game = "7stud", pockets = pockets, dead = [], board = [])

print [ j + i + "/%d" % pokereval.string2card(j + i) for i in "hdcs" for j in "23456789TJQKA" ]
print "deck = %s\n" % pokereval.deck()

print "result = %s\n" % pokereval.poker_eval(game = "holdem", pockets = [ ["tc", "ac"],  ["3h", "ah"],  ["8c", "6h"]], dead = [], board = ["7h", "3s", "2c"])
print "winners = %s\n" % pokereval.winners(game = "holdem", pockets = [ ["tc", "ac"],  ["3h", "ah"],  ["8c", "6h"]], dead = [], board = ["7h", "3s", "2c"])

print "result = %s\n" % pokereval.poker_eval(game = "holdem", pockets = [ ["tc", "ac"],  ["th", "ah"],  ["8c", "6h"]], dead = [], board = ["7h", "3s", "2c", "7s", "7d"])
print "winners = %s\n" % pokereval.winners(game = "holdem", pockets = [ ["tc", "ac"],  ["th", "ah"],  ["8c", "6h"]], dead = [], board = ["7h", "3s", "2c", "7s", "7d"])

print "winners (filthy pockets) = %s\n" % pokereval.winners(game = "holdem", pockets = [ ["tc", "ac", 255],  [], [255, 255], ["th", "ah"],  ["8c", "6h"]], dead = [], board = ["7h", "3s", "2c", "7s", "7d"])

print "winners omaha = %s\n" % pokereval.winners(game = "omaha", pockets = [ ["tc", "ac", "ks", "kc" ],  ["th", "ah", "qs", "qc" ],  ["8c", "6h", "js", "jc" ]], dead = [], board = ["7h", "3s", "2c", "7s", "7d"])
print "winners omaha8 = %s\n" % pokereval.winners(game = "omaha8", pockets = [ ["tc", "ac", "ks", "kc" ],  ["th", "ah", "qs", "qc" ],  ["8c", "6h", "js", "jc" ]], dead = [], board = ["7h", "3s", "2c", "7s", "7d"])

hand = ["Ac", "As", "Td", "7s", "7h", "3s", "2c"]
best_hand = pokereval.best_hand("hi", hand)
print "best hand from %s = %s" % ( hand, pokereval.best_hand("hi", hand) )
print "best hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ["Ah", "Ts", "Kh", "Qs", "Js" ]
best_hand = pokereval.best_hand("hi", hand)
print "best hand from %s = %s" % ( hand, pokereval.best_hand("hi", hand) )
print "best hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ["2h", "Kh", "Qh", "Jh", "Th" ]
best_hand = pokereval.best_hand("hi", hand)
print "best hand from %s = %s" % ( hand, pokereval.best_hand("hi", hand) )
print "best hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ['2s', '3s', 'Jd', 'Ks', 'As', '4d', '5h', '7d', '9c']
best_hand = pokereval.best_hand("hi", hand)
print "best hand from %s = %s" % ( hand, pokereval.best_hand("hi", hand) )
print "best hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ['As', '2s', '4d', '4s', '5c', '5d', '7s']
best_hand = pokereval.best_hand("low", hand)
print "1/ low hand from %s = %s" % ( hand, pokereval.best("low", hand) )
print "best low hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ['As', '2s', '4d', '4s', '5c', '5d', '8s']
best_hand = pokereval.best_hand("low", hand)
print "2/ low hand from %s = %s" % ( hand, pokereval.best("low", hand) )
print "best low hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
hand = ['7d', '6c', '5h', '4d', 'As']
best_hand = pokereval.best_hand("low", hand)
print "3/ low hand from %s = %s" % ( hand, pokereval.best("low", hand) )
print "best low hand from %s = (%s) %s " % (hand, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
board = [ 'As', '4d', '5h', '7d', '9c' ]
hand = [ '2s', 'Ts', 'Jd', 'Ks' ]
best_hand = pokereval.best_hand("low", hand, board)
print "4/ low hand from %s / %s = %s" % ( hand, board, pokereval.best("low", hand, board) )
print "best low hand from %s / %s = (%s) %s " % (hand, board, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
board = [ 'As', '4d', '6h', '7d', '3c' ]
hand = [ '2s', '5s', 'Jd', 'Ks' ]
best_hand = pokereval.best_hand("low", hand, board)
print "low hand from %s / %s = %s" % ( hand, board, pokereval.best("low", hand, board) )
print "best low hand from %s / %s = (%s) %s " % (hand, board, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
board = [ 'Jc', '4c', '3c', '5c', '9c' ]
hand = [ '2c', 'Ac', '5h', '9d' ]
best_hand = pokereval.best_hand("hi", hand, board)
print "hi hand from %s / %s = %s" % ( hand, board, pokereval.best("hi", hand, board) )
print "best hi hand from %s / %s = (%s) %s " % (hand, board, best_hand[0], pokereval.card2string(best_hand[1:]))

print ""
board = [ 'Jd', '9c', 'Jc', 'Tc', '2h' ]
hand = [ '2c', '4c', 'Th', '6s' ]
best_hand = pokereval.best_hand("low", hand, board)
print "5/ low hand from %s / %s = %s" % ( hand, board, pokereval.best("low", hand, board) )
print "best low hand from %s / %s = (%s) %s " % (hand, board, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

print ""
board = [ 'Ks', 'Jd', '7s', '4d', 'Js' ]
hand = [ '2d', '6c', 'Ac', '5c' ]
best_hand = pokereval.best_hand("low", hand, board)
print "6/ low hand from %s / %s = %s" % ( hand, board, pokereval.best("low", hand, board) )
print "best low hand from %s / %s = (%s) %s " % (hand, board, best_hand[0], [ pokereval.card2string(i) for i in best_hand[1:] ])

if len(sys.argv) > 2:

    print "f0 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, pockets = [ ["As", "3s"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "Qs", "2c", "Ac", "Kc"])

    print ""
    print "f1 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, pockets = [ ["As", "3s"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["7s", "Qs", "2c", "Ac", "Kc"])


    print ""
    print "f2 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, iterations = iterations_low, pockets = [ ["As", "3s"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

    print ""
    print "f3 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, iterations = iterations_high, pockets = [ ["As", "Ac"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

    print ""
    print "f4 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, iterations = iterations_high, pockets = [ ["As", "Ks"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

    print ""
    print "f5 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, iterations = iterations_high, pockets = [ ["2s", "2c"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

    print ""
    print "f6 result = %s\n" % pokereval.poker_eval(game = "holdem", fill_pockets = 1, iterations = iterations_high, pockets = [ ["Js", "Jc"],  ["__", "__"],  ["__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

    print ""
    print "f7 result = %s\n" % pokereval.poker_eval(game = "omaha", fill_pockets = 1, iterations = iterations_high, pockets = [ ["Js", "Jc", "7s", "8c"],  ["__", "__", "__", "__"],  ["__", "__", "__", "__"]], dead = [], board = ["__", "__", "__", "__", "__"])

print ""
hand = ['As', 'Ad']
print "handval %s = %d " % (hand, pokereval.evaln(hand))

print ""
hand = ['Qc', '7d']
print "handval %s = %d " % (hand, pokereval.evaln(hand))

pokereval = None
