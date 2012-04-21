#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2011, Carl Gherardi
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

from HandHistoryConverter import *
from decimal_wrapper import Decimal


class Cake(HandHistoryConverter):

    # Class Variables

    sitename = "Cake"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 17
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\xa3", "play": ""}
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac|)",
                            'NUM' :u".,\d",
                    }
                    
    # translations from captured groups to fpdb info strings
    Lim_Blinds = {  '0.04': ('0.01', '0.02'),        '0.08': ('0.02', '0.04'),
#                        '0.10': ('0.02', '0.05'),    '0.20': ('0.05', '0.10'),
#                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
#                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
#                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
#                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
#                        '6.00': ('1.00', '3.00'),       '6': ('1.00', '3.00'),
#                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
#                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
#                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
#                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
#                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
#                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
#                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
#                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
#                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
#                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
#                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
#                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00')
                  }

    limits = { 'NL':'nl', 'PL':'pl', 'FL':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
               }
    currencies = { u'€':'EUR', '$':'USD', '':'T$' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          Hand\#(?P<HID>[0-9]+)\s+\-\s+
          (?P<TABLE>[\-\ \#a-zA-Z\d\']+?)(\s\-)?\s
          (\((Turbo\s)?(?P<MAX>\d+)\-max\)\s)?
          (Turbo\s\((?P<TMAX>\d)\sChips\)\s)?
          (?P<TOURNO>T\d+)?(\d+)?\s(\-\-\sTable\s\d\s)?\-\-\s
          (?P<CURRENCY>%(LS)s|)?
          (?P<ANTESB>[%(NUM)s]+)/(%(LS)s)?
          (?P<SBBB>[%(NUM)s]+)
          (/(%(LS)s)?(?P<BB>[%(NUM)s]+))?\s
          (?P<LIMIT>NL|FL||PL)\s
          (?P<GAME>Hold\'em|Omaha|Omaha\sHi/Lo)\s--\s
          (?P<DATETIME>.*$)
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \((%(LS)s)?(?P<CASH>[%(NUM)s]+)\sin\schips\)""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('\n\n+')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")

    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_PostSB       = re.compile(r"^%(PLYR)s: posts small blind %(CUR)s(?P<SB>[%(NUM)s]+)$" %  substitutions, re.MULTILINE)
    re_PostBB       = re.compile(r"^%(PLYR)s: posts big blind %(CUR)s(?P<BB>[%(NUM)s]+)$" %  substitutions, re.MULTILINE)
    re_Antes        = re.compile(r"^%(PLYR)s: posts ante of %(CUR)s(?P<ANTE>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_BringIn      = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_PostBoth     = re.compile(r"^%(PLYR)s:posts dead blind %(CUR)s(?P<SB>[%(NUM)s]+) and big blind %(CUR)s(?P<BB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_HeroCards    = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action       = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sis\sall\sin)
                        (\s(%(CUR)s)?(?P<BET>[%(NUM)s]+))?(\sto\s%(CUR)s(?P<BETTO>[%(NUM)s]+))?$
                        """
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s (\(.*\) )?(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\]( and won \([.\d]+\) with (?P<STRING>.*))?" %  substitutions['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"%(PLYR)s wins %(CUR)s(?P<POT>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_WinningRankOne   = re.compile(u"^%(PLYR)s wins the tournament and receives %(CUR)s(?P<AMT>[%(NUM)s]+) - congratulations!$" %  substitutions, re.MULTILINE)
    re_WinningRankOther = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place and received %(CUR)s(?P<AMT>[%(NUM)s]+)\.$" %  substitutions, re.MULTILINE)
    re_RankOther        = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place$" %  substitutions, re.MULTILINE)

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
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("CakeToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'BB' in mg:
            if not mg['BB']:
                info['bb'] = mg['SBBB']
            else:
                info['bb'] = mg['BB']
        if 'SBBB' in mg:
            if not mg['BB']:
                info['sb'] = mg['ANTESB']
            else:
                info['sb'] = mg['SBBB']
        if 'CURRENCY' in mg:
            info['currency'] = self.currencies[mg['CURRENCY']]
        if 'MIXED' in mg:
            if mg['MIXED'] is not None: info['mix'] = self.mixes[mg['MIXED']]
            
        if info['currency']=='T$':
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = self.Lim_Blinds[info['bb']][0]
                    info['bb'] = self.Lim_Blinds[info['bb']][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("CakeToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(info['sb'])/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(info['sb']).quantize(Decimal("0.01")))

        return info

    def readHandInfo(self, hand):
        info = {}
        m = self.re_GameInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("CakeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())

        log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key]:
                hand.maxseats = int(info[key])
            if key == 'TOURNO' and info[key]:
                hand.tourNo = info[key].replace('T', '')
            if key == 'TMAX' and info[key]:
                hand.maxseats = int(info[key])
                
        if hand.gametype['type'] == 'tour':
            hand.buyin = 0
            hand.fee = 0
            hand.buyinCurrency="NA"

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
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S,\S\S,\S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* (?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* (?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        if street in ('FLOP','TURN','RIVER'):
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(','))

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            if liveBlind:
                hand.addBlind(a.group('PNAME'), 'small blind', a.group('SB'))
                liveBlind = False
            else:
                # Post dead blinds as ante
                hand.addBlind(a.group('PNAME'), 'secondsb', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
            hand.setUncalledBets(Decimal(a.group('BB')))
        for a in self.re_PostBoth.finditer(hand.handText):
            sb = Decimal(a.group('SB'))
            bb = Decimal(a.group('BB'))
            sbbb = sb + bb
            hand.addBlind(a.group('PNAME'), 'both', str(sbbb))

    def readHeroCards(self, hand):
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = found.group('PNAME')
                    newcards = found.group('NEWCARDS').split(',')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            amount = action.group('BET') if action.group('BET') else None
            actionType = action.group('ATYPE')

            if actionType == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif actionType == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif actionType == ' calls':
                hand.setUncalledBets(None)
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif actionType == ' raises':
                hand.setUncalledBets(None)
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BETTO') )
            elif actionType == ' bets':
                hand.setUncalledBets(None)
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif actionType == ' is all in':
                hand.setUncalledBets(None)
                hand.addAllIn(street, action.group('PNAME'), action.group('BET'))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(' ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=re.sub(u',',u'',m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
                string = m.group('STRING')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)
