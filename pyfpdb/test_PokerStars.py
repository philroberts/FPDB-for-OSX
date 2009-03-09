# -*- coding: utf-8 -*-
import PokerStarstoFpdb
import py


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = PokerStarstoFpdb.PokerStars(autostart=False)    
    pairs = (
    (u"PokerStars Game #20461877044:  Hold'em No Limit ($1/$2) - 2008/09/16 18:58:01 ET",
         {'type':'ring', 'base':"hold", 'category':'holdem', 'limitType':'nl', 'sb':'1', 'bb':'2', 'currency':'USD'}),
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info



