#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Matt Turnbull
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#   
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#       
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

import PokerStarsToFpdb
from Hand import *
import py

import Configuration
import Database
import SQL
import fpdb_import

config = Configuration.Config(file = "HUD_config.test.xml")
db = Database.Database(config)
sql = SQL.Sql(db_server = 'sqlite')

settings = {}
settings.update(config.get_db_parameters())
settings.update(config.get_import_parameters())
settings.update(config.get_default_paths())

#regression-test-files/stars/badugi/ring-fl-badugi.txt
#   s0rrow: input: $30.00 end: $22.65 total: ($7.35)
#regression-test-files/stars/plo/PLO-6max.txt
#   s0rrow: input: $18.35 end: $0 total: ($18.35)
#   Notes: last hand #25975302416 s0rrow aifp against 2 players

gametype = {'type':'ring', 'base':'draw', 'category':'badugi', 'limitType':'fl', 'sb':'0.25', 'bb':'0.50','currency':'USD'}
text = ""

hhc = PokerStarsToFpdb.PokerStars(config, autostart=False)

h = HoldemOmahaHand(config, None, "PokerStars", gametype, text, builtFrom = "Test")
h.addPlayer("1", "s0rrow", "100000")

hhc.compilePlayerRegexs(h)


def checkGameInfo(hhc, header, info):
    assert hhc.determineGameType(header) == info

def testGameInfo():
    hhc = PokerStarsToFpdb.PokerStars(config, autostart=False)
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


def testFlopImport():
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Flop/NLHE-6max-EUR-0.05-0.10-200911.txt""", site="PokerStars")
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Flop/NLHE-6max-USD-0.05-0.10-200911.txt""", site="PokerStars")
    #importer.addBulkImportImportFileOrDir(
    #        """regression-test-files/tour/Stars/Flop/NLHE-USD-MTT-5r-200710.txt""", site="PokerStars")
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Flop/PLO8-6max-USD-0.01-0.02-200911.txt""", site="PokerStars")
    #HID - 36185273365
    # Besides the horrible play it contains lots of useful cases
    # Preflop: raise, then 3bet chance for seat 2
    # Flop: Checkraise by hero, 4bet chance not taken by villain
    # Turn: Turn continuation bet by hero, called
    # River: hero (continuation bets?) all-in and is not called
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Flop/NLHE-6max-USD-0.05-0.10-200912.Stats-comparision.txt""", site="PokerStars")
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Flop/NLHE-6max-USD-0.05-0.10-200912.Allin-pre.txt""", site="PokerStars")
    importer.setCallHud(False)
    (stored, dups, partial, errs, ttime) = importer.runImport()
    print "DEBUG: stored: %s dups: %s partial: %s errs: %s ttime: %s" %(stored, dups, partial, errs, ttime)
    importer.clearFileList()

    col = { 'sawShowdown': 2, 'street0Aggr':3
          }

    q = """SELECT
    s.name,
    p.name,
    hp.sawShowdown,
    hp.street0Aggr
FROM
    Hands as h,
    Sites as s,
    Gametypes as g,
    HandsPlayers as hp,
    Players as p
WHERE
    h.siteHandNo = 36185273365
and g.id = h.gametypeid
and hp.handid = h.id
and p.id = hp.playerid
and s.id = p.siteid"""
    c = db.get_cursor()
    c.execute(q)
    result = c.fetchall()
    for row, data in enumerate(result):
        print "DEBUG: result[%s]: %s" %(row, result[row])
        # Assert if any sawShowdown = True
        assert result[row][col['sawShowdown']] == 0

    q = """SELECT
    s.name,
    p.name,
    hp.sawShowdown,
    hp.street0Aggr
FROM
    Hands as h,
    Sites as s,
    Gametypes as g,
    HandsPlayers as hp,
    Players as p
WHERE
    h.siteHandNo = 37165169101
and g.id = h.gametypeid
and hp.handid = h.id
and p.id = hp.playerid
and s.id = p.siteid"""
    c = db.get_cursor()
    c.execute(q) 
    result = c.fetchall()
    pstats = { u'Kinewma':0, u'Arbaz':0, u's0rrow':1, u'bys7':0, u'AAALISAAAA':1, u'Bl\xe5veis':0 }
    for row, data in enumerate(result):
        print "DEBUG: result[%s]: %s == %s" %(row, result[row], pstats[data[1]])
        assert result[row][col['sawShowdown']] == pstats[data[1]]

    assert 0 == 1

def testStudImport():
    db.recreate_tables()
    importer = fpdb_import.Importer(False, settings, config)
    importer.setDropIndexes("don't drop")
    importer.setFailOnError(True)
    importer.setThreads(-1)
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Stud/7-Stud-USD-0.04-0.08-200911.txt""", site="PokerStars")
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Stud/7-StudHL-USD-0.04-0.08-200911.txt""", site="PokerStars")
    importer.addBulkImportImportFileOrDir(
            """regression-test-files/cash/Stars/Stud/Razz-USD-0.04-0.08-200911.txt""", site="PokerStars")
    importer.setCallHud(False)
    (stored, dups, partial, errs, ttime) = importer.runImport()
    importer.clearFileList()

    # Should actually do some testing here
    assert 1 == 1

def testDrawImport():
    try:
        db.recreate_tables()
        importer = fpdb_import.Importer(False, settings, config)
        importer.setDropIndexes("don't drop")
        importer.setFailOnError(True)
        importer.setThreads(-1)
        importer.addBulkImportImportFileOrDir(
                """regression-test-files/cash/Stars/Draw/3-Draw-Limit-USD-0.10-0.20-200911.txt""", site="PokerStars")
        importer.addBulkImportImportFileOrDir(
                """regression-test-files/cash/Stars/Draw/5-Carddraw-USD-0.10-0.20-200911.txt""", site="PokerStars")
        importer.setCallHud(False)
        (stored, dups, partial, errs, ttime) = importer.runImport()
        importer.clearFileList()
    except FpdbError:
        assert 0 == 1

    # Should actually do some testing here
    assert 1 == 1
