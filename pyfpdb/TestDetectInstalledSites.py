#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DetectInstalledSites import *
print "Following sites detected:"
print "------------------------------------"

#single site example
foo = DetectInstalledSites("PokerStars")
if foo.detected:
    print foo.sitename
    print foo.hhpath
    print foo.heroname
    
print "------------------------------------"

#all sites example
foo = DetectInstalledSites()
for sitename in foo.sitestatusdict:
    if foo.sitestatusdict[sitename]['detected']:
        print "sitename:"+ sitename
        print "hhpath:"+foo.sitestatusdict[sitename]['hhpath']
        print "heroname:"+foo.sitestatusdict[sitename]['heroname']
        print "------------------------------------"


#print foo.supportedSites
#print foo.supportedPlatforms
#print foo.userPlatform
