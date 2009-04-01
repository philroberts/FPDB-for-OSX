# -*- coding: utf-8 -*-
import fpdb_simple
import datetime
import py

def checkDateParse(header, site, result):
    assert fpdb_simple.parseHandStartTime(header, site) == result

def testPokerStarsHHDate():
    tuples = (
        ("PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET]", "ps",
                    datetime.datetime(2008,11,12,15,00,48)),
        ("PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/08/17 - 01:14:43 (ET)", "ps",
                    datetime.datetime(2008,8,17,6,14,43)),
        ("PokerStars Game #21969660557:  Hold'em No Limit ($0.50/$1.00) - 2008/09/07 06:23:14 ET", "ps",
                    datetime.datetime(2008,9,7,11,23,14))
    )

def testFullTiltHHDate():
    sitngo1 = "Full Tilt Poker Game #10311865543: $1 + $0.25 Sit & Go (78057629), Table 1 - 25/50 - No Limit Hold'em - 0:07:45 ET - 2009/01/29"
    cash1 = "Full Tilt Poker Game #9403951181: Table CR - tay - $0.05/$0.10 - No Limit Hold'em - 9:40:20 ET - 2008/12/09"
    cash2 = "Full Tilt Poker Game #9468383505: Table Bike (deep 6) - $0.05/$0.10 - No Limit Hold'em - 5:09:36 ET - 2008/12/13"

    result = fpdb_simple.parseHandStartTime(sitngo1,"ftp")
    assert result==datetime.datetime(2009,1,29,05,07,45)
    result = fpdb_simple.parseHandStartTime(cash1,"ftp")
    assert result==datetime.datetime(2008,12,9,14,40,20)
    result = fpdb_simple.parseHandStartTime(cash2,"ftp")
    assert result==datetime.datetime(2008,12,13,10,9,36)

    def testTableDetection():
        result = Tables.clean_title("French (deep)")
        assert  result == "French"
        result = Tables.clean_title("French (deep) - $0.25/$0.50 - No Limit Hold'em - Logged In As xxxx")
        assert  result == "French"

        for (header, site, result) in tuples:
            yield checkDateParse, header, site, result

