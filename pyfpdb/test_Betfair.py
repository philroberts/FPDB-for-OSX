# -*- coding: utf-8 -*-
import BetfairToFpdb
import py


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = BetfairToFpdb.Betfair(autostart=False)    
    pairs = (
    (u"""***** Betfair Poker Hand History for Game 472386869 *****
NL $0.02/$0.04 Texas Hold'em - Sunday, January 25, 10:10:42 GMT 2009
Table Rookie 191 6-max (Real Money)
Seat 1 is the button
Total number of active players : 6""",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'0.02', 'bb':'0.04', 'currency':'USD'}),
    )

    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info
