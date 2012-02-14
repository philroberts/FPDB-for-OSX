#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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
#In the "official" distribution you can find the license in agpl-3.0.txt

"""A script for fetching Winamax tourney results"""
import L10n
_ = L10n.get_translation()

import Configuration
import Database

import logging, os, sys
import re, urllib2


def fetch_results_page(tourney_id):
    url = "http://www.carbonpoker.ag/tournaments/tournament-details.html?id=%s-1" % tourney_id
    try:
        data = urllib2.urlopen(url).read()
        return data
    except urllib2.HTTPError, e:
        print e, tourney_id
        return None

def write_file(filename, data):
    f = open(filename, 'w')
    f.write(data)
    f.close()

def main():
    Configuration.set_logfile("fpdb-log.txt")
    config = Configuration.Config()
    db = Database.Database(config)

    tourney_ids = db.getSiteTourneyNos("Merge")
    tids = []

    for tid in tourney_ids:
        blah, = tid # Unpack tuple
        tids.append(str(blah))
    #    winamax_get_winning(tid,"blah")
    results_dir = config.get_import_parameters().get("ResultsDirectory")
    results_dir = os.path.expanduser(results_dir)
    site_dir = os.path.join(results_dir, "Merge")
    print "DEBUG: site_dir: %s" % site_dir
    filelist = [file for file in os.listdir(site_dir) if not file in [".",".."]]
    print "DEBUG: filelist : %s" % filelist
    print "DEBUG: tids     : %s" % tids

    for f in filelist:
        try:
            tids.remove(f)
        except ValueError:
            print "Warning: '%s' is not a known tourney_id" % f

    if len(tids) == 0:
        print "No tourney results files to fetch"
    else:
        for tid in tids:
            filename = os.path.join(site_dir, tid)
            data = fetch_results_page(tid)
            if data != None:
                print u"DEBUG: write_file(%s)" %(filename)
                write_file(filename, data)

if __name__ == '__main__':
    main()
