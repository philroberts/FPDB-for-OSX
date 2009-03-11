# -*- coding: utf-8 -*-
import PokerStarsToFpdb
import py


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = PokerStarsToFpdb.PokerStars(autostart=False)    
    pairs = (
    (u"PokerStars Game #20461877044:  Hold'em No Limit ($1/$2) - 2008/09/16 18:58:01 ET",
    {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'1', 'bb':'2', 'currency':'USD'}),
         
    (u"PokerStars Game #5999635897:  HORSE (Omaha Hi/Lo Limit, $2/$4) - 2006/08/21 - 13:59:19 (ET)",
    {'type':'ring', 'base':'hold', 'category':'omahahilo', 'limitType':'fl', 'sb':'2', 'bb':'4','currency':'USD'})
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info

