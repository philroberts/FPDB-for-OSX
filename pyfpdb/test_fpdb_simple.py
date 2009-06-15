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

#def testTableDetection():
#    result = Tables.clean_title("French (deep)")
#    assert  result == "French"
#    result = Tables.clean_title("French (deep) - $0.25/$0.50 - No Limit Hold'em - Logged In As xxxx")
#    assert  result == "French"
#
#    for (header, site, result) in tuples:
#        yield checkDateParse, header, site, result

