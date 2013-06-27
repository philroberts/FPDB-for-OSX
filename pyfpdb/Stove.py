#!/usr/bin/env python
# -*- coding: iso-8859-15
#
# stove.py
# Simple Hold'em equity calculator
# Copyright (C) 2007-2011 Mika Boström <bostik@iki.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# TODO gettextify usage print

import L10n
_ = L10n.get_translation()

import sys, random
import re
import pokereval

SUITS = ['h', 'd', 's', 'c']

CONNECTORS = ['32', '43', '54', '65', '76', '87', '98', 'T9', 'JT', 'QJ', 'KQ', 'AK']
CARDS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']

ANY = 0
SUITED = 1
OFFSUIT = 2

ev = pokereval.PokerEval()


class Stove:
    def __init__(self):
        self.hand = None
        self.board = None
        self.h_range = None

    def set_board_with_list(self, board):
        pass

    def set_board_string(self, string):
        board = Board()

        # Board
        b = string.strip().split()
        if len(b) > 4:
            board.b5 = b[4]
        if len(b) > 3:
            board.b4 = b[3]
        if len(b) > 2:
            board.b1 = b[0]
            board.b2 = b[1]
            board.b3 = b[2]

        self.board = board

    def set_hero_cards_string(self, string):
        # Our pocket cards
        cc = string.strip().split()
        c1 = cc[0]
        c2 = cc[1]
        pocket_cards = Cards(c1, c2)
        self.hand = pocket_cards

    def set_villain_range_string(self, string):
        # Villain's range
        h_range = Range()
        hands_in_range = string.strip().split(',')
        for h in hands_in_range:
            _h = h.strip()
            h_range.expand(expand_hands(_h, self.hand, self.board))

        self.h_range = h_range


class Cards:
    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2

    def get(self):
        return [self.c1, self.c2]

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
        self.output = ""

    def add(self, ev):
        self.n_hands += ev.n_hands
        self.n_wins += ev.n_wins
        self.n_ties += ev.n_ties
        self.n_losses += ev.n_losses

    def show(self, hand, h_range):
        win_pct = 100 * (float(self.n_wins) / float(self.n_hands))
        lose_pct = 100 * (float(self.n_losses) / float(self.n_hands))
        tie_pct = 100 * (float(self.n_ties) / float(self.n_hands))
        equity = win_pct + tie_pct / 2.
        self.output = """
Enumerated %d possible plays.
Your hand: (%s %s)
Against the range: %s
Equity       Win         Lose         Tie
%5.2f%%    %5.2f%%    %5.2f%%    %5.2f%%
""" % (self.n_hands, hand.c1, hand.c2, cards_from_range(h_range), equity, win_pct, lose_pct, tie_pct)

        print self.output


# Expands hand abbreviations such as JJ and AK to full hand ranges.
# Takes into account cards already known to be in player's hand and/or
# board. 
def expand_hands(abbrev, hand, board):
    selection = -1
    known_cards = set()
    known_cards.update(set([hand.c1, hand.c2]))
    known_cards.update(set([board.b1, board.b2, board.b3, board.b4, board.b5]))

    re.search('[2-9TJQKA]{2}(s|o)',abbrev)

    if re.search('^[2-9TJQKA]{2}(s|o)?$',abbrev): #AKs, AKo or AK
        return standard_expand(abbrev, hand, known_cards)
    elif re.search('^[2-9TJQKA]{2}(s|o)?\+$',abbrev): #76s+ or 76o+
        return iterative_expand(abbrev, hand, known_cards)
#     elif re.search('^[2-9TJQKA]{2}', abbrev): #AK or KK
#         return standard_expand(abbrev, hand, known_cards)
    #elif: AhXh
    #elif: Ah6h+A

def iterative_expand(abbrev, hand, known_cards):
    r1 = abbrev[0]
    r2 = abbrev[1]
    c1 = CARDS.index(r1)
    c2 = CARDS.index(r2)
    h_range = []
    considered = set()
    if r1 == r2: #pocket pair
        for c in CARDS[c1:]:
            h_range += standard_expand(c+c, hand, known_cards)
            
    else:
        c_hi = max(c1,c2)
        c_low = min(c1,c2)
        if len(abbrev.strip('+')) == 3:
            ltr = abbrev[2]
        else:
            ltr = ''
        for idx, c in enumerate(CARDS[c_hi:]):
            h_range += standard_expand(c+CARDS[c_low+idx]+ltr, hand, known_cards)
#     idx = CONNECTORS.index('%s%s' % (r1, r2))
# 
#     ltr = abbrev[2]
# 
#     
#     for h in CONNECTORS[idx:]:
#         abr = "%s%s" % (h, ltr)
#         h_range += standard_expand(abr, hand, known_cards)
# 
    return h_range


def standard_expand(abbrev, hand, known_cards):
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

    h_range = []
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
                h_range.append(Cards(c1, c2))
    return h_range


def parse_args(args, container):
    # args[0] is the path being executed; need 3 more args
    if len(args) < 4:
        return False

    container.set_board_string(args[1])
    container.set_hero_cards_string(args[2])
    container.set_villain_range_string(args[3])

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
        print _('No board given. Using Monte-Carlo simulation...')
        iters = random.randint(25000, 125000)
    else:
        iters = -1
    for h in holder.h_range.get():
        e = odds_for_hand(
            [holder.hand.c1, holder.hand.c2],
            [h.c1, h.c2],
            b,
            iterations=iters
            )
        sev.add(e)

    sev.show(holder.hand, holder.h_range.get())
    return sev

def usage(me):
    print """Texas Hold'Em odds calculator
Calculates odds against a range of hands.

To use: %s '<board cards>' '<your hand>' '<opponent's range>' [...]

Separate cards with space.
Separate hands in range with commas.
""" % me

def cards_from_range(h_range):
    s = '{'
    for h in h_range:
        if h.c1 == '__' and h.c2 == '__':
            s += 'random, '
        else:
            s += '%s%s, ' % (h.c1, h.c2)
    s = s.rstrip(', ')
    s += '}'
    return s

def main(argv=None):
    stove = Stove()
    if not parse_args(sys.argv, stove):
        usage(sys.argv[0])
        sys.exit(2)
    odds_for_range(stove)

if __name__  == '__main__':
    sys.exit(main())
