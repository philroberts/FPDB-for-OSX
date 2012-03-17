#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2012, Chaz Littlejohn
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
########################################################################

import L10n
_ = L10n.get_translation()

# TODO: straighten out discards for draw games

import sys
from HandHistoryConverter import *
from decimal_wrapper import Decimal

# PokerTracker HH Format

class PokerTracker(HandHistoryConverter):

    # Class Variables

    filetype = "text"
    codepage = ("utf8", "cp1252")
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\£", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                           'NUM' : u".,\d",
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac||\£|)",
                          'BRKTS': r'(\(button\) |\(small blind\) |\(big blind\) |\(button\) \(small blind\) |\(button\) \(big blind\) )?',
                    }
                    
    # translations from captured groups to fpdb info strings
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),         '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),         '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),         '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),         '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),         '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),         '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),         '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),         '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),        '10': ('2.00', '5.00'),
                       '20.00': ('5.00', '10.00'),       '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),      '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),      '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),      '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),      '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),     '100': ('25.00', '50.00'),
                      '150.00': ('50.00', '75.00'),     '150': ('50.00', '75.00'),
                      '200.00': ('50.00', '100.00'),    '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'),   '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'),   '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),  '1000': ('250.00', '500.00'),
                     '2000.00': ('500.00', '1000.00'), '2000': ('500.00', '1000.00'),
                  }

    limits = { 'NL':'nl', 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                        "Texas Hold'em" : ('hold','holdem'),
                               "Holdem" : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo')
               }
    sites = {     'EverestPoker Game #' : ('Everest', 16),
                               'GAME #' : ('iPoker', 14),
                         'MERGE_GAME #' : ('Merge', 12),
                          '** Game ID ' : ('Microgaming', 20)
             
             }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }


    re_Site = re.compile(u'(?P<SITE>EverestPoker\sGame\s\#|GAME\s\#|MERGE_GAME\s\#|\*{2}\sGame\sID\s)\d+')
    # Static regexes
    re_GameInfo1     = re.compile(u"""
          (?P<SITE>GAME\s\#|MERGE_GAME\s\#)(?P<HID>[0-9]+):\s+
          (?P<GAME>Holdem|Texas\sHold\'em|Omaha|Omaha\sHi/Lo)\s\s?
          (?P<LIMIT>NL|No\sLimit|Limit|LIMIT|Pot\sLimit)\s\s?
          (?P<TOUR>Tournament)?
          (                            # open paren of the stakes
          (?P<CURRENCY>%(LS)s|)?
          (?P<SB>[%(NUM)s]+)/(%(LS)s)?
          (?P<BB>[%(NUM)s]+)
          (?P<BLAH>\s-\s[%(LS)s\d\.]+\sCap\s-\s)?        # Optional Cap part
          \s?(?P<ISO>%(LEGAL_ISO)s)?
          )?\s                        # close paren of the stakes
          (?P<DATETIME>.*$)
        """ % substitutions, re.MULTILINE|re.VERBOSE)
    
    re_GameInfo2     = re.compile(u"""
          EverestPoker\sGame\s\#(?P<HID>[0-9]+):\s+
          (?P<TOUR>Tourney\sID:\s(?P<TOURNO>\d+),\s)?
          Table\s(?P<TABLE>.+)?
          \s-\s
          ((?P<CURRENCY>%(LS)s|)?
          (?P<SB>[%(NUM)s]+)/(%(LS)s)?
          (?P<BB>[%(NUM)s]+))?
          \s-\s
          (?P<LIMIT>No\sLimit|Limit|Pot\sLimit)\s
          (?P<GAME>Hold\'em|Omaha|Omaha\sHi/Lo)\s
          (-\s)?
          (?P<DATETIME>.*$)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \((%(LS)s)?(?P<CASH>[%(NUM)s]+)(\sin\schips)?\)
          (?P<BUTTON>\sDEALER)?""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^Table\s(?P<TABLE>[^(\n]+)
          (?P<TOUR>\(Tournament:\s(.+)?,\s(?P<TOURNO>\d+)\sBuy\-In:\s(?P<BIAMT>[%(LS)s\d\.]+)\+?(?P<BIRAKE>[%(LS)s\d\.]+)\))?
          (,\sSeats\s(?P<MAX>\d+))?""" % substitutions
          , re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('(?:\s?\n){2,}')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('The button is in seat #(?P<BUTTON>\d+)', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_DateTime1    = re.compile("""(?P<Y>[0-9]{4})\-(?P<M>[0-9]{2})\-(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_DateTime2    = re.compile("""(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})\/(?P<Y>[0-9]{4})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_DateTime3    = re.compile("""(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)[\- ]+(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})""", re.MULTILINE)
    # revised re including timezone (not currently used):
    #re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+) \(?(?P<TZ>[A-Z0-9]+)""", re.MULTILINE)

    # These used to be compiled per player, but regression tests say
    # we don't have to, and it makes life faster.
    re_PostSB           = re.compile(r"^%(PLYR)s:? (posts the small blind of|Post SB) %(CUR)s(?P<SB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s:? (posts the big blind of|posts the dead blind of|Post BB|Post DB) %(CUR)s(?P<BB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s:? (posts the ante of|Post Ante) %(CUR)s(?P<ANTE>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s:? (posts|Post) %(CUR)s(?P<SBBB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s:?(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sBet|\sCheck|\sRaise|\sCall|\sFold|\sAllin)
                        (\s\(NF\))?
                        (\sto)?(\s%(CUR)s(?P<BET>[%(NUM)s]+))?  # the number discarded goes in <BET>
                        \s*(and\sis\sall.in)?
                        (and\shas\sreached\sthe\s[%(CUR)s\d\.,]+\scap)?
                        (\son|\scards?)?
                        (\s\[(?P<CARDS>.+?)\])?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    #re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^%(PLYR)s:? (?P<SHOWED>shows|Shows|mucked) \[(?P<CARDS>.*)\]" % substitutions, re.MULTILINE)
    #re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s %(BRKTS)s(collected|showed \[.*\] and won) \(%(CUR)s(?P<POT>[%(NUM)s]+)\)(, mucked| with.*|)" %  substitutions, re.MULTILINE)
    re_CollectPot      = re.compile(r"^%(PLYR)s:? (collects|wins) %(CUR)s(?P<POT>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_WinningRankOne   = re.compile(u"^%(PLYR)s wins the tournament and receives %(CUR)s(?P<AMT>[%(NUM)s]+) - congratulations!$" %  substitutions, re.MULTILINE)
    re_WinningRankOther = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place and received %(CUR)s(?P<AMT>[%(NUM)s]+)\.$" %  substitutions, re.MULTILINE)
    re_RankOther        = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place$" %  substitutions, re.MULTILINE)
    re_Cancelled        = re.compile('Hand\scancelled', re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],
                ]

    def determineGameType(self, handText):
        m = self.re_Site.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("PokerTrackerToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError
        
        self.sitename = self.sites[m.group('SITE')][0]
        self.siteId   = self.sites[m.group('SITE')][1] # Needs to match id entry in Sites database
        if self.sitename == 'Microgaming':
            log.error(_("PokerTrackerToFpdb.determineGameType: Microgaming not yet supported"))
            raise FpdbParseError
        
        info = {}
        if self.sitename in ('iPoker', 'Merge'):
            m = self.re_GameInfo1.search(handText)
        elif self.sitename=='Everest':
            m = self.re_GameInfo2.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("PokerTrackerToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError
        
        mg = m.groupdict()
        #print 'DEBUG determineGameType', mg
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg and mg['CURRENCY'] is not None:
            info['currency'] = self.currencies[mg['CURRENCY']]
        if 'MIXED' in mg:
            if mg['MIXED'] is not None: info['mix'] = self.mixes[mg['MIXED']]
                
        if mg['TOUR'] is None:
            info['type'] = 'ring'
        else:
            info['type'] = 'tour'
            info['currency'] = 'T$'

        if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring':
            try:
                bb = self.clearMoneyString(mg['BB'])
                info['sb'] = self.Lim_Blinds[bb][0]
                info['bb'] = self.Lim_Blinds[bb][1]
            except KeyError:
                tmp = handText[0:200]
                log.error(_("PokerTrackerToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                raise FpdbParseError

        return info

    def readHandInfo(self, hand):
        info = {}
        m  = self.re_HandInfo.search(hand.handText,re.DOTALL)
        if self.sitename in ('iPoker', 'Merge'):
            m2 = self.re_GameInfo1.search(hand.handText)
        elif self.sitename=='Everest':
            m2 = self.re_GameInfo2.search(hand.handText)
        if (m is None and self.sitename != 'Everest')  or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("PokerTrackerToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        
        if self.sitename!='Everest':
            info.update(m.groupdict())
        info.update(m2.groupdict())

        #print 'readHandInfo', info
        for key in info:
            if key == 'DATETIME':
                #2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET] # (both dates are parsed so ET date overrides the other)
                #2008/08/17 - 01:14:43 (ET)
                #2008/09/07 06:23:14 ET
                if self.sitename == 'iPoker':
                    m1 = self.re_DateTime1.finditer(info[key])
                elif self.sitename == 'Merge':
                    m1 = self.re_DateTime2.finditer(info[key])
                elif self.sitename == 'Everest':
                    m1 = self.re_DateTime3.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    #tz = a.group('TZ')  # just assume ET??
                    #print "   tz = ", tz, " datetime =", datetimestr
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                if self.sitename == 'Merge':
                    hand.handid = info[key][:8] + str(int(info[key][8:]))
                else:
                    hand.handid = info[key]
            if key == 'TOURNO':
                hand.tourNo = info[key]
                if info['TOUR']!=None:
                    hand.tourNo = re.split(",", info['TABLE'])[-1].strip()
                    hand.tourNo = re.split("-", hand.tourNo)[0].strip()
            if key == 'BUYIN':
                if hand.tourNo!=None:
                    #print "DEBUG: info['BUYIN']: %s" % info['BUYIN']
                    #print "DEBUG: info['BIAMT']: %s" % info['BIAMT']
                    #print "DEBUG: info['BIRAKE']: %s" % info['BIRAKE']
                    #print "DEBUG: info['BOUNTY']: %s" % info['BOUNTY']
                    if info[key] == 'Freeroll':
                        hand.buyin = 0
                        hand.fee = 0
                        hand.buyinCurrency = "FREE"
                    else:
                        if info[key].find("$")!=-1:
                            hand.buyinCurrency="USD"
                        elif info[key].find(u"£")!=-1:
                            hand.buyinCurrency="GBP"
                        elif info[key].find(u"€")!=-1:
                            hand.buyinCurrency="EUR"
                        elif re.match("^[0-9+]*$", info[key]):
                            hand.buyinCurrency="play"
                        else:
                            #FIXME: handle other currencies, play money
                            log.error(_("PokerTrackerToFpdb.readHandInfo: Failed to detect currency.") + " Hand ID: %s: '%s'" % (hand.handid, info[key]))
                            raise FpdbParseError

                        info['BIAMT'] = info['BIAMT'].strip(u'$€£FPP')
                        
                        if hand.buyinCurrency!="PSFP":
                            if info['BOUNTY'] != None:
                                # There is a bounty, Which means we need to switch BOUNTY and BIRAKE values
                                tmp = info['BOUNTY']
                                info['BOUNTY'] = info['BIRAKE']
                                info['BIRAKE'] = tmp
                                info['BOUNTY'] = info['BOUNTY'].strip(u'$€£') # Strip here where it isn't 'None'
                                hand.koBounty = int(100*Decimal(info['BOUNTY']))
                                hand.isKO = True
                            else:
                                hand.isKO = False

                            info['BIRAKE'] = info['BIRAKE'].strip(u'$€£')

                            hand.buyin = int(100*Decimal(info['BIAMT']))
                            hand.fee = int(100*Decimal(info['BIRAKE']))
                        else:
                            hand.buyin = int(Decimal(info['BIAMT']))
                            hand.fee = 0
            if key == 'TABLE':
                hand.tablename = re.split(",", info[key])[0]
                hand.tablename = hand.tablename.strip()
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])

            if key == 'PLAY' and info['PLAY'] is not None:
#                hand.currency = 'play' # overrides previously set value
                hand.gametype['currency'] = 'play'
                
        if self.re_Cancelled.search(hand.handText):
            raise FpdbHandPartial(_("Hand '%s' was cancelled.") % hand.handid)
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            #print a.group('SEAT'), a.group('PNAME'), a.group('CASH')
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))
            if a.group('BUTTON')!=None:
                hand.buttonpos = int(a.group('SEAT'))

    def markStreets(self, hand):

        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        m =  re.search(r"\*\*\* HOLE CARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                   r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S\S? \S\S\S? \S\S\S?\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                   r"(\*\*\* TURN \*\*\* (?P<TURN>\[\S\S\S?\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                   r"(\*\*\* RIVER \*\*\* (?P<RIVER>\[\S\S\S?\].+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            if self.sitename=='iPoker':
                cards = [c[1:].replace('10', 'T') + c[0].lower() for c in m.group('CARDS').split(' ')]
            else:
                cards = [c.replace('10', 'T').strip() for c in m.group('CARDS').split(' ')]
            hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            self.adjustMergeTourneyStack(hand, player.group('PNAME'), player.group('ANTE'))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            if liveBlind:
                self.adjustMergeTourneyStack(hand, a.group('PNAME'), a.group('SB'))
                hand.addBlind(a.group('PNAME'), 'small blind', a.group('SB'))
                if not hand.gametype['sb']:
                    hand.gametype['sb'] = self.clearMoneyString(a.group('SB'))
                liveBlind = False
            else:
                # Post dead blinds as ante
                self.adjustMergeTourneyStack(hand, a.group('PNAME'), a.group('SB'))
                hand.addBlind(a.group('PNAME'), 'secondsb', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            self.adjustMergeTourneyStack(hand, a.group('PNAME'), a.group('BB'))
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
            if not hand.gametype['bb']:
                hand.gametype['bb'] = self.clearMoneyString(a.group('BB'))
        for a in self.re_PostBoth.finditer(hand.handText):
            self.adjustMergeTourneyStack(hand, a.group('PNAME'), a.group('SBBB'))
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))
            
        # FIXME
        # The following should only trigger when a small blind is missing in a tournament, or the sb/bb is ALL_IN
        # see http://sourceforge.net/apps/mantisbt/fpdb/view.php?id=115
        if hand.gametype['type'] == 'tour' and self.sitename in ('Merge', 'iPoker'):
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
            elif hand.gametype['sb'] == None:
                hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)
            elif hand.gametype['bb'] == None:
                hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
            if int(Decimal(hand.gametype['bb']))/2 != int(Decimal(hand.gametype['sb'])):
                if int(Decimal(hand.gametype['bb']))/2 < int(Decimal(hand.gametype['sb'])):
                    hand.gametype['bb'] = str(int(Decimal(hand.gametype['sb']))*2)
                else:
                    hand.gametype['sb'] = str(int(Decimal(hand.gametype['bb']))/2)

    def readHeroCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
                    hand.hero = found.group('PNAME')
                    if self.sitename=='iPoker':
                        newcards = [c[1:].replace('10', 'T') + c[0].lower() for c in found.group('NEWCARDS').split(' ')]
                    else:
                        newcards = [c.replace('10', 'T').strip() for c in found.group('NEWCARDS').split(' ')]
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    if self.sitename=='iPoker':
                        newcards = [c[1:].replace('10', 'T') + c[0].lower() for c in found.group('NEWCARDS').split(' ')]
                    else:
                        newcards = [c.replace('10', 'T').strip() for c in found.group('NEWCARDS').split(' ')]
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    if self.sitename=='iPoker':
                        oldcards = [c[1:].replace('10', 'T') + c[0].lower() for c in found.group('OLDCARDS').split(' ')]
                    else:
                        oldcards = [c.replace('10', 'T').strip() for c in found.group('OLDCARDS').split(' ')]

                hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') in (' folds', ' Fold'):
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') in (' checks', ' Check'):
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') in (' calls', ' Call'):
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') in (' raises', ' Raise'):
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') in (' bets', ' Bet'):
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' Allin':
                hand.addAllIn(street, action.group('PNAME'), action.group('BET'))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def adjustMergeTourneyStack(self, hand, player, amount):
        if self.sitename == 'Merge':
            amount = Decimal(amount)
            if hand.gametype['type'] == 'tour':
                for p in hand.players:
                    if p[1]==player:
                        stack  = Decimal(p[2])
                        stack += amount
                        p[2]   = str(stack)
                hand.stacks[player] += amount

    def readCollectPot(self,hand):
        if self.sitename != 'Everest':
            hand.setUncalledBets(True)
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))
                
    def readShowdownActions(self, hand):
        pass

    def readShownCards(self,hand):
        found = []
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None and m.group('PNAME') not in found:
                if self.sitename=='iPoker':
                    cards = [c[1:].replace('10', 'T') + c[0].lower() for c in m.group('CARDS').split(' ')]
                else:
                    cards = [c.replace('10', 'T').strip() for c in m.group('CARDS').split(' ')]

                (shown, mucked) = (False, False)
                if m.group('SHOWED') in ("shows", 'Shows'): shown = True
                elif m.group('SHOWED') == "mucked": mucked = True
                found.append(m.group('PNAME'))

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)
 