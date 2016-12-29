#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2012, Carl Gherardi
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

import sys
from HandHistoryConverter import *
from decimal_wrapper import Decimal

class Entraction(HandHistoryConverter):
    sitename = "Entraction"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 18
    
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\xa3", "play": ""}
    substitutions = {
                     'LEGAL_ISO' : "EUR|Fun|",
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac|)",
                            'NUM': u".,\d",
                    }
                    
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),
                        '0.08': ('0.02', '0.04'),    '0.20': ('0.05', '0.10'),    
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.12', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),     '10': ('2.50', '5.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('7.50', '15.00'),     '30': ('7.50', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00')
                  }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Fixed Limit': 'fl'}
    games = {                          # base, category
                           'Omaha High' : ('hold','omahahi'),
                        "Texas Hold'em" : ('hold','holdem'), 
                    '5-Card Omaha High' : ('hold','5_omahahi'),
               }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          \s(?P<HID>[0-9]+)\s-\s
          (?P<GAME>Texas\sHold\'em|Omaha\sHigh|5-Card\sOmaha\sHigh)\s
          (?P<LIMIT>No\sLimit|Pot\sLimit|Fixed\sLimit)\s
          (?P<CURRENCY>%(LEGAL_ISO)s|)?\s?
          (?P<SB>[%(NUM)s]+)/
          (?P<BB>[%(NUM)s]+)\s
          (and\s[%(NUM)s]+\sante\s)?
          \-\sTable\s\"(?P<TABLE>.+?)(\s(?P<TOURNO>\d+)\s(?P<TABLENO>\d+))?\"
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^(?P<PNAME>.*)\s
          \((%(LEGAL_ISO)s)?\s?(?P<CASH>[%(NUM)s]+)\s
          in\sseat\s(?P<SEAT>[0-9]+)\)"""
            % substitutions, re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          \s(?P<HID>[0-9]+)\s-\s.+?
          Table\s"(?P<TABLE>(?P<BUYIN>(?P<BIAMT>[%(LS)s%(NUM)s]+)?\+?(?P<BIRAKE>[%(NUM)s]+)?)?.+?)(\s(?P<TOURNO>\d+)\s(?P<TABLENO>\d+))?\"
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_Identify     = re.compile(u'Game\s\#\s\d+\s\-\s')
    re_SplitHands   = re.compile(r"\n\n(?=Game\s#)")
    re_Button       = re.compile(r'^Dealer:\s+(?P<PNAME>.*)$', re.MULTILINE)
    re_Board        = re.compile(r"^(?P<CARDS>.+)$", re.MULTILINE)
    re_GameEnds     = re.compile(r"Game\sended\s(?P<Y>[0-9]{4})-(?P<M>[0-9]{2})-(?P<D>[0-9]{2})\s(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)(\s(?P<TZ>[A-Z]+))?", re.MULTILINE)
    re_Max          = re.compile(r"Players\(max\s(?P<MAX>\d+)\):")

    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_PostSB       = re.compile(r"^Small Blind: {16}(?P<PNAME>.*)\s+\((?P<SB>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_PostBB       = re.compile(r"^Big Blind: {18}(?P<PNAME>.*)\s+\((?P<BB>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_PostBoth     = re.compile(r"^Small \+ Big Blind: {10}(?P<PNAME>.*)\s+\((?P<SBBB>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_PostSecondSB = re.compile(r"^Blind out of turn: {10}(?P<PNAME>.*)\s+\((?P<SB>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_Antes        = re.compile(r"^%(PLYR)s\s+Ante\s+\((?P<ANTE>[%(NUM)s]+)\)" % substitutions, re.MULTILINE)
    re_BringIn      = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_HeroCards    = re.compile(r"^%(PLYR)s was dealt:\s+(?P<CARDS>.+)" % substitutions, re.MULTILINE)
    re_Action       = re.compile(r"""
                        ^%(PLYR)s\s+(?P<ATYPE>Fold|Check|Call|Bet|Raise|All\-In)\s+?
                        (\((?P<BET>[%(NUM)s]+)\))?$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction = re.compile(r"^%(PLYR)s\sdidn\'t\sshow\shand\s\((?P<CARDS>.+)\)" % substitutions, re.MULTILINE)
    re_ShownCards     = re.compile(r"^%(PLYR)s\sshows:\s+(?P<CARDS>.+)\s\((?P<STRING>.+?)\)" % substitutions, re.MULTILINE)
    re_CollectPot     = re.compile(r"^%(PLYR)s\swins:\s+(%(LEGAL_ISO)s)\s(?P<POT>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    
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
            log.error(_("EntractionToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg:
            if mg['CURRENCY'] == 'Fun':
                info['currency'] = 'play'
            else:
                info['currency'] = mg['CURRENCY']
        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
            info['currency'] = 'T$'
        else:
            info['type'] = 'ring'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = self.Lim_Blinds[info['bb']][0]
                    info['bb'] = self.Lim_Blinds[info['bb']][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("PokerStarsToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (info['bb'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(info['sb'])/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(info['sb']).quantize(Decimal("0.01")))   
#
        return info

    def readHandInfo(self, hand):
        info = {}
        m2 = self.re_Max.search(hand.handText)
        m3 = self.re_GameEnds.search(hand.handText)
        m  = self.re_HandInfo.search(hand.handText)
        
        if m3 is None:
            raise FpdbHandPartial
        
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("EntractionToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        info.update(m2.groupdict())
        info.update(m3.groupdict())

        for key in info:
            if key == 'Y':
                datetimestr = "%s/%s/%s %s:%s:%s" % (info['Y'], info['M'],info['D'],info['H'],info['MIN'],info['S'])
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                if info['TZ']:
                    hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, info['TZ'], "UTC")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'BUYIN':
                if hand.tourNo!=None:
                    if info[key] == 'Freeroll' or info['BIAMT'] is None:
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
                            log.error(_("EntractionToFpdb.readHandInfo: Failed to detect currency.") + " Hand ID: %s: '%s'" % (hand.handid, info[key]))
                            raise FpdbParseError

                        info['BIAMT'] = self.clearMoneyString(info['BIAMT'].strip(u'$€£'))
                        info['BIRAKE'] = self.clearMoneyString(info['BIRAKE'].strip(u'$€£'))
                        hand.buyin = int(100*Decimal(info['BIAMT']))
                        hand.fee = int(100*Decimal(info['BIRAKE']))
            if key == 'TABLE':
                if hand.gametype['type'] == 'tour':
                    hand.tablename = info['TABLENO']
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            for p in hand.players:
                if p[1]==m.group('PNAME'):
                    hand.buttonpos = p[0]
        else:
            log.info('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            name = a.group('PNAME').strip()
            hand.addPlayer(int(a.group('SEAT')), name, self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"Dealer:(?P<PREFLOP>.+(?=Flop {24})|.+)"
                       r"(Flop {24}(?P<FLOP>\S\S - \S\S - \S\S.+(?=Turn {24})|.+))?"
                       r"(Turn {24}\S\S - \S\S - \S\S - (?P<TURN>\S\S.+(?=River {23})|.+))?"
                       r"(River {23}\S\S - \S\S - \S\S - \S\S - (?P<RIVER>\S\S.+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        #print "DEBUG: readCommunityCards"
        if street in ('FLOP','TURN','RIVER'):
            #print "DEBUG readCommunityCards: %s %s" %(street, hand.streets[street])
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' - '))

    def readAntes(self, hand):
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
    
    def readBringIn(self, hand):
        pass
#        m = self.re_BringIn.search(hand.handText,re.DOTALL)
#        if m:
#            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
#            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        for a in self.re_PostSB.finditer(hand.handText):
            name = a.group('PNAME').strip()
            blind = self.clearMoneyString(a.group('SB'))
            hand.addBlind(name, 'small blind', blind)
        for a in self.re_PostBB.finditer(hand.handText):
            name = a.group('PNAME').strip()
            blind = self.clearMoneyString(a.group('BB'))
            hand.addBlind(name, 'big blind', blind)
        for a in self.re_PostBoth.finditer(hand.handText):
            name = a.group('PNAME').strip()
            hand.addBlind(name, 'both', a.group('SBBB'))
        for a in self.re_PostSecondSB.finditer(hand.handText):
            name = a.group('PNAME').strip()
            blind = self.clearMoneyString(a.group('SB'))
            hand.addBlind(name, 'big blind', blind)

    def readHoleCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = [p[1] for p in hand.players if p[1].lower()==found.group('PNAME').lower()][0]
                    newcards = found.group('CARDS').split(' - ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') == 'Fold':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'Check':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == 'Call':
                hand.addCall( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == 'Raise':
                hand.addCallandRaise( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == 'Bet':
                hand.addBet( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == 'All-In':
                hand.addAllIn(street, action.group('PNAME'), self.clearMoneyString(action.group('BET')))
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(' - ')
            hand.addShownCards(cards, shows.group('PNAME'), shown=False, mucked=True)

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=self.clearMoneyString(m.group('POT')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(' - ') # needs to be a list, not a set--stud needs the order
                string = m.group('STRING')

                (shown, mucked) = (True, False)

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)
                
