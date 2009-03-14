# -*- coding: utf-8 -*-
import PokerStarsToFpdb
import py

#regression-test-files/stars/badugi/ring-fl-badugi.txt
#   s0rrow: start $30.00 end: $22.65 total: ($7.35)


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
    {'type':'ring', 'base':'draw', 'category':'badugi', 'limitType':'fl', 'sb':'0.25', 'bb':'0.50','currency':'USD'})
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info

