#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        print sitecode
        print foo.sitestatusdict[sitecode]['hhpath']
        print foo.sitestatusdict[sitecode]['heroname']

#print foo.supportedSites
#print foo.supportedPlatforms
#print foo.userPlatform
