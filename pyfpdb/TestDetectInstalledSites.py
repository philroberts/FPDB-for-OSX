#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DetectInstalledSites import *
print "Following sites detected:"
print "------------------------------------"
#all sites example 
foo = DetectInstalledSites()


from DetectInstalledSites import *

#single site example
foo = DetectInstalledSites("PS")
if foo.detected:
    print foo.sitecode
    print foo.hhpath
    print foo.heroname

#all sites example
foo = DetectInstalledSites()
for sitecode in foo.sitestatusdict:
    if foo.sitestatusdict[sitecode]['detected']:
        print "sitecode:"+ sitecode
        print "hhpath:"+foo.sitestatusdict[sitecode]['hhpath']
        print "heroname:"+foo.sitestatusdict[sitecode]['heroname']
        print "------------------------------------"


#print foo.supportedSites
#print foo.supportedPlatforms
#print foo.userPlatform
