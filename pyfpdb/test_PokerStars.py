# -*- coding: utf-8 -*-
import PokerStarsToFpdb
from Hand import *
import py

#regression-test-files/stars/badugi/ring-fl-badugi.txt
#   s0rrow: input: $30.00 end: $22.65 total: ($7.35)
#regression-test-files/stars/plo/PLO-6max.txt
#   s0rrow: input: $18.35 end: $0 total: ($18.35)
#   Notes: last hand #25975302416 s0rrow aifp against 2 players

gametype = {'type':'ring', 'base':'draw', 'category':'badugi', 'limitType':'fl', 'sb':'0.25', 'bb':'0.50','currency':'USD'}
text = ""

hhc = PokerStarsToFpdb.PokerStars(autostart=False)

h = HoldemOmahaHand(None, "ASite", gametype, text, builtFrom = "Test")
h.addPlayer("1", "s0rrow", "100000")

hhc.compilePlayerRegexs(h)


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = PokerStarsToFpdb.PokerStars(autostart=False)    
    pairs = (
    (u"PokerStars Game #20461877044:  Hold'em No Limit ($1/$2) - 2008/09/16 18:58:01 ET",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'1', 'bb':'2', 'currency':'USD'}),
         
    (u"PokerStars Game #5999635897:  HORSE (Omaha Hi/Lo Limit, $2/$4) - 2006/08/21 - 13:59:19 (ET)",
    {'type':'ring', 'base':'hold', 'category':'omahahilo', 'limitType':'fl', 'sb':'2', 'bb':'4','currency':'USD'}),

    (u"PokerStars Game #25923772706:  Badugi Limit ($0.25/$0.50) - 2009/03/13 16:40:58 ET",
    {'type':'ring', 'base':'draw', 'category':'badugi', 'limitType':'fl', 'sb':'0.25', 'bb':'0.50','currency':'USD'}),

    (u"PokerStars Game #22073591924:  Hold'em No Limit ($0.50/$1.00) - 2008/11/16 1:22:21 CET [2008/11/15 19:22:21 ET]",
    {'type':'ring', 'base':'hold', 'category':'holdem', 'limitType':'nl', 'sb':'0.50', 'bb':'1.00','currency':'USD'}),

    (u"PokerStars Game #25974627364:  Omaha Pot Limit ($0.05/$0.10) - 2009/03/15 0:29:00 ET",
    {'type':'ring', 'base':'hold', 'category':'omahahi', 'limitType':'pl', 'sb':'0.05', 'bb':'0.10','currency':'USD'})
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info


def testHandInfo():
    text = u"""PokerStars Game #20461877044:  Hold'em No Limit ($1/$2) - 2008/09/16 18:58:01 ET"""
    hhc = PokerStarsToFpdb.PokerStars(autostart=False)
    h = HoldemOmahaHand(None, "PokerStars", gametype, text, builtFrom = "Test")
    hhc.readHandInfo(h)
    assert h.handid == '20461877044'
    assert h.sitename == 'PokerStars'
    assert h.starttime == (2008, 9, 16, 18, 58, 1, 1, 260, -1)
    
    text = u"""PokerStars Game #18707234955:  Razz Limit ($0.50/$1.00) - 2008/07/09 - 21:41:43 (ET)
Table 'Lepus II' 8-max"""
    hhc = PokerStarsToFpdb.PokerStars(autostart=False)
    h = HoldemOmahaHand(None, "PokerStars", gametype, text, builtFrom = "Test")
    hhc.readHandInfo(h)
    assert h.handid == '18707234955'
    assert h.sitename == 'PokerStars'
    assert h.maxseats == 8
    assert h.tablename == 'Lepus II'
    assert h.starttime == (2008,7 , 9, 21, 41, 43, 2, 191, -1)
    
    
    text = u"""PokerStars Game #22073591924:  Hold'em No Limit ($0.50/$1.00) - 2008/11/16 1:22:21 CET [2008/11/15 19:22:21 ET]
Table 'Caia II' 6-max Seat #2 is the button"""
    hhc = PokerStarsToFpdb.PokerStars(autostart=False)
    h = HoldemOmahaHand(None, "PokerStars", gametype, text, builtFrom = "Test")
    hhc.readHandInfo(h)
    assert h.handid == '22073591924'
    assert h.sitename == 'PokerStars'
    assert h.maxseats == 6
    assert h.tablename == 'Caia II'
    assert h.buttonpos == '2' # TODO: should this be an int?
    assert h.starttime == (2008,11 , 15, 19, 22, 21, 5, 320, -1)
    
    
