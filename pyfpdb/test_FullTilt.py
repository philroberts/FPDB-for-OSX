# -*- coding: utf-8 -*-
import FulltiltToFpdb
import py

# regression-test-files/fulltilt/nlhe/NLHE-6max-1.txt
#   Sorrowful: start: $8.85 end: $14.70 total: $5.85 
    
def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = FulltiltToFpdb.Fulltilt(autostart=False)
    pairs = (
    ("Full Tilt Poker Game #10777181585: Table Deerfly (deep 6) - $0.01/$0.02 - Pot Limit Omaha Hi - 2:24:44 ET - 2009/02/22",
            {'type':'ring', 'base':'hold', 'category':'omahahi', 'limitType':'pl', 'sb':'0.01', 'bb':'0.02', 'currency':'USD'}),
    ("Full Tilt Poker Game #10773265574: Table Butte (6 max) - $0.01/$0.02 - Pot Limit Hold'em - 21:33:46 ET - 2009/02/21",
            {'type':'ring', 'base':'hold', 'category':'holdem', 'limitType':'pl', 'sb':'0.01', 'bb':'0.02', 'currency':'USD'}),
    ("Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09",
            {'type':'ring', 'base':'hold', 'category':'holdem', 'limitType':'nl', 'sb':'0.05', 'bb':'0.10', 'currency':'USD'}),
    ("Full Tilt Poker Game #10809877615: Table Danville - $0.50/$1 Ante $0.10 - Limit Razz - 21:47:27 ET - 2009/02/23",
            {'type':'ring', 'base':'stud', 'category':'razz', 'limitType':'fl', 'sb':'0.50', 'bb':'1', 'currency':'USD'})
    )
    for (header, info) in pairs:
        yield checkGameInfo, hhc, header, info

