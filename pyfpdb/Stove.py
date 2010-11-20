#!/usr/bin/python
# -*- coding: iso-8859-15
#
# stove.py
# Simple Hold'em equity calculator
# Copyright (C) 2007-2008 Mika Boström <bostik@iki.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#

import sys, random
import pokereval

SUITS = ['h', 'd', 's', 'c']

ANY = 0
SUITED = 1
OFFSUIT = 2

ev = pokereval.PokerEval()

holder = None

class Holder:
    def __init__(self):
        self.hand = None
        self.board = None
        self.range = None


class Cards:
    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2

    def get(self):
        return [c1, c2]

class Board:
    def __init__(self, b1=None, b2=None, b3=None, b4=None, b5=None):
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b4 = b4
        self.b5 = b5

    def get(self):
        b = []
        if self.b3 is not None:
            b.append(self.b1)
            b.append(self.b2)
            b.append(self.b3)
        else:
            b.extend(["__", "__", "__"])

        if self.b4 is not None:
            b.append(self.b4)
        else:
            b.append("__")

        if self.b5 is not None:
            b.append(self.b5)
        else:
            b.append("__")

        return b

class Range:
    def __init__(self):
        self.__hands = set()

    def add(self, hand):
        self.__hands.add(hand)

    def expand(self, hands):
        self.__hands.update(set(hands))

    def get(self):
        return sorted(self.__hands)

        

class EV:
    def __init__(self, plays, win, tie, lose):
        self.n_hands = plays
        self.n_wins = win
        self.n_ties = tie
        self.n_losses = lose


class SumEV:
    def __init__(self):
        self.n_hands = 0
        self.n_wins = 0
        self.n_ties = 0
        self.n_losses = 0

    def add(self, ev):
        self.n_hands += ev.n_hands
        self.n_wins += ev.n_wins
        self.n_ties += ev.n_ties
        self.n_losses += ev.n_losses

    def show(self, hand, range):
        win_pct = 100 * (float(self.n_wins) / float(self.n_hands))
        lose_pct = 100 * (float(self.n_losses) / float(self.n_hands))
        tie_pct = 100 * (float(self.n_ties) / float(self.n_hands))
        print 'Enumerated %d possible plays.' % self.n_hands
        print 'Your hand: (%s %s)' % (hand.c1, hand.c2)
        print 'Against the range: %s\n' % cards_from_range(range)
        print '  Win       Lose       Tie'
        print ' %5.2f%%    %5.2f%%    %5.2f%%' % (win_pct, lose_pct, tie_pct)


def usage(me):
    print """Texas Hold'Em odds calculator
Calculates odds against a range of hands.

To use: %s '<board cards>' '<your hand>' '<opponent's range>' [...]

Separate cards with space.
Separate hands in range with commas.
""" % me

def cards_from_range(range):
    s = '{'
    for h in range:
        if h.c1 == '__' and h.c2 == '__':
            s += 'random, '
        else:
            s += '%s%s, ' % (h.c1, h.c2)
    s = s.rstrip(', ')
    s += '}'
    return s


# Expands hand abbreviations such as JJ and AK to full hand ranges.
# Takes into account cards already known to be in player's hand and/or
# board. 
def expand_hands(abbrev, hand, board):
    selection = -1
    known_cards = set()
    known_cards.update(set([hand.c2, hand.c2]))
    known_cards.update(set([board.b1, board.b2, board.b3, board.b4, board.b5]))

    # Card ranks may be different
    r1 = abbrev[0]
    r2 = abbrev[1]
    # There may be a specifier: 's' for 'suited'; 'o' for 'off-suit'
    if len(abbrev) == 3:
        ltr = abbrev[2]
        if ltr == 'o':
            selection = OFFSUIT
        elif ltr == 's':
            selection = SUITED
    else:
        selection = ANY

    range = []
    considered = set()
    for s1 in SUITS:
        c1 = r1 + s1
        if c1 in known_cards:
            continue
        considered.add(c1)
        for s2 in SUITS:
            c2 = r2 + s2
            if selection == SUITED and s1 != s2:
                continue
            elif selection == OFFSUIT and s1 == s2:
                continue
            if c2 not in considered and c2 not in known_cards:
                range.append(Cards(c1, c2))
    return range



    

def parse_args(args, container):
    # args[0] is the path being executed; need 3 more args
    if len(args) < 4:
        return False

    board = Board()

    # Board
    b = args[1].strip().split()
    if len(b) > 4:
        board.b5 = b[4]
    if len(b) > 3:
        board.b4 = b[3]
    if len(b) > 2:
        board.b1 = b[0]
        board.b2 = b[1]
        board.b3 = b[2]

    # Our pocket cards
    cc = args[2].strip().split()
    c1 = cc[0]
    c2 = cc[1]
    pocket_cards = Cards(c1, c2)

    # Villain's range
    range = Range()
    hands_in_range = args[3].strip().split(',')
    for h in hands_in_range:
        _h = h.strip()
        if len(_h) > 3:
            cc = _h.split()
            r1 = cc[0]
            r2 = cc[1]
            vp = Cards(r1, r2)
            range.add(vp)
        else:
            range.expand(expand_hands(_h, pocket_cards, board))

    holder.hand = pocket_cards
    holder.range = range
    holder.board = board

    return True


def odds_for_hand(hand1, hand2, board, iterations):
    res = ev.poker_eval(game='holdem',
        pockets = [
            hand1,
            hand2
        ],
        dead = [],
        board = board,
        iterations = iterations
        )
    
    plays = int(res['info'][0])
    eval = res['eval'][0]

    win  = int(eval['winhi'])
    lose = int(eval['losehi'])
    tie  = int(eval['tiehi'])

    _ev = EV(plays, win, tie, lose)
    return _ev


def odds_for_range(holder):
    sev = SumEV()
    monte_carlo = False

    # Construct board list
    b = []
    board = holder.board
    if board.b3 is not None:
        b.extend([board.b1, board.b2, board.b3])
    else:
        b.extend(['__', '__', '__'])
        monte_carlo = True
    if board.b4 is not None:
        b.append(board.b4)
    else:
        b.append("__")
    if board.b5 is not None:
        b.append(board.b5)
    else:
        b.append("__")

    if monte_carlo:
        print 'No board given. Using Monte-Carlo simulation...'
        iters = random.randint(25000, 125000)
    else:
        iters = -1
    for h in holder.range.get():
        e = odds_for_hand(
            [holder.hand.c1, holder.hand.c2],
            [h.c1, h.c2],
            b,
            iterations=iters
            )
        sev.add(e)

    sev.show(holder.hand, holder.range.get())
    


holder = Holder()
if not parse_args(sys.argv, holder):
    usage(sys.argv[0])
    sys.exit(2)
odds_for_range(holder)

# debugs
#print '%s, %s' % ( holder.hand.c1, holder.hand.c2)
#print '%s %s %s %s %s' % (holder.board.b1, holder.board.b2,
#    holder.board.b3, holder.board.b4, holder.board.b5)
#while True:
#    try:
#        vl = holder.range.get()
#        v = vl.pop()
#        print '\t%s %s' % (v.c1, v.c2)
#    except IndexError:
#        break




