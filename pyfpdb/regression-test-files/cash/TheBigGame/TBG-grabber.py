#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to fetch all the of the data file from thebiggame.pokerstars.net"""
#wget http://thebiggame.pokerstars.net/data/s1/w12/d2/d12h60.js

import urllib2

def generate_url_list(week, day, hand):
    subst = { 'week': week, 'day': day, 'hand': hand }
    url= "http://thebiggame.pokerstars.net/data/s1/w%(week)s/d%(day)s/d%(week)sh%(hand)s.js" % subst
    return url

def modify_url_list(urls):
    """Data on website not 100% in corret places"""
    # Week 1, hand 122 is missing from the website.
    idx  = urls.index ("http://thebiggame.pokerstars.net/data/s1/w1/d5/d1h122.js")
    urls.remove("http://thebiggame.pokerstars.net/data/s1/w1/d5/d1h122.js")

    return urls
    

def fetch_url_list(urls):
    for url in urls:
        print "URL: %s" % url
        data = urllib2.urlopen(url).read()
        print data

def get_all_data():
    s1w1 =  [(1,32), (33,57), (58,85), (86,121), (122,150)]
    s1w2 =  [(1,30), (31,60), (61,89), (90,121), (122,150)]
    s1w3 =  [(1,28), (29,60), (61,81), (82,114), (115,150)]
    s1w4 =  [(1,29), (30,55), (56,87), (88,117), (118,150)]
    s1w5 =  [(1,34), (35,57), (58,90), (91,119), (120,150)]
    s1w6 =  [(1,29), (30,61), (62,86), (87,118), (119,150)] 
    s1w7 =  [(1,29), (30,58), (59,90), (91,120), (121,150)] 
    s1w8 =  [(1,29), (30,58), (59,90), (91,120), (121,150)] 
    s1w9 =  [(1,30), (31,59), (60,90), (91,121), (122,150)] 
    s1w10 = [(1,31), (32,60), (61,92), (93,121), (122,150)] 
    s1w11 = [(1,33), (34,62), (63,92), (93,118), (119,150)]
    s1w12 = [(1,28), (29,60), (61,92), (93,120), (121,150)]

    season1 = [s1w1, s1w2, s1w3, s1w4, s1w5, s1w6, s1w7, s1w8, s1w9, s1w10, s1w11, s1w12]
    count = 0
    urllist = []

    for i, week in enumerate(season1, start = 1):
        print "Total: %s" % count
        for j, days in enumerate(week, start = 1):
            start_hand, end_hand = days
            for k in range(start_hand, end_hand+1):
                urllist.append(generate_url_list(i, j, k))
                count += 1

    urllist = modify_url_list(urllist)
    fetch_url_list(urllist)

    print "Total: %s" % count

def main():
    get_all_data()

if __name__ == '__main__':
    main()
