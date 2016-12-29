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
                            'NUM' :u".,\d\xa0",
                    }
                    
    # translations from captured groups to fpdb info strings
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),    '0.08': ('0.02', '0.04'),
                        '0.10': ('0.02', '0.05'),    '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),       '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.50', '5.00'),      '10': ('2.50', '5.00'),
                       '12.00': ('3.00', '6.00'),      '12': ('3.00', '6.00'),
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

    limits = { 'NL':'nl', 'PL':'pl', 'FL':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                            'OmahaHiLo' : ('hold','omahahilo'),
               }
    currencies = { u'€':'EUR', '$':'USD', '':'T$' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          Hand\#(?P<HID>[A-Z0-9]+)\s+\-\s+
          (?P<TABLE>(?P<BUYIN1>(?P<BIAMT1>(%(LS)s)[%(NUM)s]+)\sNLH\s(?P<MAX1>\d+)\smax)?.+?)\s(\((Turbo,\s)?(?P<MAX>\d+)\-[Mm]ax\)\s)?((?P<TOURNO>T\d+)|\d+)\s
          (\-\-\s(TICKET|CASH|TICKETCASH)\s\-\-\s(?P<BUYIN>(?P<BIAMT>(%(LS)s)[%(NUM)s]+)\s\+\s(?P<BIRAKE>(%(LS)s)[%(NUM)s]+))\s\-\-\s(?P<TMAX>\d+)\sMax\s)?
          (\-\-\sTable\s(?P<TABLENO>\d+)\s)?\-\-\s
          (?P<CURRENCY>%(LS)s|)?
          (?P<ANTESB>(\-)?[%(NUM)s]+)/(%(LS)s)?
          (?P<SBBB>[%(NUM)s]+)
          (/(%(LS)s)?(?P<BB>[%(NUM)s]+))?\s
          (?P<LIMIT>NL|FL||PL)\s
          (?P<GAME>Hold\'em|Omaha|Omaha\sHi/Lo|OmahaHiLo)\s--\s
          (?P<DATETIME>.*$)
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.+?)\s
          \((%(LS)s)?(?P<CASH>[%(NUM)s]+)\sin\schips\)
          (\s\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_Trim         = re.compile("(Hand\#)")
    re_Identify     = re.compile(u'Hand\#[A-Z0-9]+\s\-\s')
    re_SplitHands   = re.compile('\n\n+')
    re_Button       = re.compile('Dealer: Seat (?P<BUTTON>\d+)', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")

    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})[\/\-\.](?P<M>[0-9]{2})[\/\-\.](?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_PostSB       = re.compile(r"^%(PLYR)s: posts small blind %(CUR)s(?P<SB>[%(NUM)s]+)(\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?$" %  substitutions, re.MULTILINE)
    re_PostBB       = re.compile(r"^%(PLYR)s: posts big blind %(CUR)s(?P<BB>[%(NUM)s]+)(\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?$" %  substitutions, re.MULTILINE)
    re_Antes        = re.compile(r"^%(PLYR)s: posts ante of %(CUR)s(?P<ANTE>[%(NUM)s]+)(\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?" % substitutions, re.MULTILINE)
    re_BringIn      = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[%(NUM)s]+)(\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?" % substitutions, re.MULTILINE)
    re_PostBoth     = re.compile(r"^%(PLYR)s:posts dead blind %(CUR)s(\-)?(?P<SB>[%(NUM)s]+) and big blind %(CUR)s(?P<BB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_HeroCards    = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action       = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sis\sall\sin)
                        (\s(to\s)?(%(CUR)s)?(?P<BET>[%(NUM)s]+))?(\s\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?$
                        """
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile(r"^%s: (?P<SHOWED>shows|mucks) \[(?P<CARDS>.*)\] (\((?P<STRING>.*)\))?" % substitutions['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"^%(PLYR)s:? wins (low pot |high pot )?%(CUR)s(?P<POT>[%(NUM)s]+)((\swith.+?)?\s+\(EUR\s(%(CUR)s)?(?P<EUROVALUE>[%(NUM)s]+)\))?" %  substitutions, re.MULTILINE)
    re_Finished         = re.compile(r"%(PLYR)s:? finished \d+ out of \d+ players" %  substitutions, re.MULTILINE)
    re_Dealer           = re.compile(r"Dealer:") #Some Cake hands just omit the game line so we can just discard them as partial
    re_CoinFlip         = re.compile(r"Coin\sFlip\sT\d+", re.MULTILINE)
    re_ReturnBet        = re.compile(r"returns\suncalled\sbet", re.MULTILINE)
    re_ShowDown         = re.compile(r"\*\*\*SHOW DOWN\*\*\*")
    re_ShowDownLeft     = re.compile(r"\*\*\*SHOW\sDOWN\*\*\*\nPlayer\sleft\sthe\stable$", re.MULTILINE)

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
            if self.re_Finished.search(handText):
                raise FpdbHandPartial
            if self.re_Dealer.match(handText):
                raise FpdbHandPartial
            tmp = handText[0:200]
            log.error(_("CakeToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError
        
        if not self.re_ShowDown.search(handText) or self.re_ShowDownLeft.search(handText):
            raise FpdbHandPartial

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'BB' in mg:
            if not mg['BB']:
                info['bb'] = self.clearMoneyString(mg['SBBB'])
            else:
                info['bb'] = self.clearMoneyString(mg['BB'])
        if 'SBBB' in mg:
            if not mg['BB']:
                info['sb'] = self.clearMoneyString(mg['ANTESB'])
            else:
                info['sb'] = self.clearMoneyString(mg['SBBB'])
        if 'CURRENCY' in mg:
            info['currency'] = self.currencies[mg['CURRENCY']]
        if 'MIXED' in mg:
            if mg['MIXED'] is not None: info['mix'] = self.mixes[mg['MIXED']]
            
        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'
            
        if 'TABLE' in mg and 'Play Money' in mg['TABLE']:
            info['currency'] = 'play'

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
        #trim off malformatted text from partially written hands
        if not self.re_Trim.match(hand.handText):
            hand.handText = "".join(self.re_Trim.split(hand.handText)[1:])
        
        info = {}
        m = self.re_GameInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("CakeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())

        for key in info:
            if key == 'DATETIME':
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S')) 
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                hand.handid = re.sub('[A-Z]+', '', info[key])
            if key == 'TABLE' and hand.gametype['type'] == 'ring':
                hand.tablename = info[key]
            if key == 'TABLENO' and hand.gametype['type'] == 'tour':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key]:
                hand.maxseats = int(info[key])
            if key == 'TOURNO' and info[key]:
                hand.tourNo = info[key].replace('T', '')
            if key == 'TMAX' and info[key]:
                hand.maxseats = int(info[key])
            if key == 'TMAX1' and info[key]:
                hand.maxseats = int(info[key])
            if (key == 'BUYIN' or key == 'BUYIN1') and info[key]:
                if hand.tourNo!=None:
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
                        log.error(_("CakeToFpdb.readHandInfo: Failed to detect currency.") + " Hand ID: %s: '%s'" % (hand.handid, info[key]))
                        raise FpdbParseError
                    
                    if key == 'BUYIN1':
                        info['BIAMT1']  = self.clearMoneyString(info['BIAMT1'].strip(u'$€£'))
                        hand.buyin = int(100*Decimal(info['BIAMT1']))
                        hand.fee = 0
                    else:
                        info['BIAMT']  = self.clearMoneyString(info['BIAMT'].strip(u'$€£'))
                        info['BIRAKE'] = self.clearMoneyString(info['BIRAKE'].strip(u'$€£'))
                        hand.buyin = int(100*Decimal(info['BIAMT']))
                        hand.fee = int(100*Decimal(info['BIRAKE']))
                
        if hand.gametype['type'] == 'tour' and not hand.buyin:
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
        m = self.re_PlayerInfo.finditer(hand.handText)
        if self.re_CoinFlip.search(hand.handText):
            coinflip = True
        else:
            coinflip = False
        for a in m:
            if a.group('EUROVALUE'):
                hand.roundPenny = True
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.convertMoneyString('CASH', a))
            if coinflip:
                hand.addAnte(a.group('PNAME'), self.convertMoneyString('CASH', a))

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
            hand.addAnte(player.group('PNAME'), self.convertMoneyString('ANTE', player))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.convertMoneyString('BRINGIN', m))
        
    def readBlinds(self, hand):
        liveBlind = True
        if not self.re_ReturnBet.search(hand.handText):
            hand.setUncalledBets(True)
        for a in self.re_PostSB.finditer(hand.handText):
            if liveBlind:
                hand.addBlind(a.group('PNAME'), 'small blind', self.convertMoneyString('SB',a))
                liveBlind = False
            else:
                # Post dead blinds as ante
                hand.addBlind(a.group('PNAME'), 'secondsb', self.convertMoneyString('SB', a))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.convertMoneyString('BB', a))
        for a in self.re_PostBoth.finditer(hand.handText):
            sb = Decimal(self.clearMoneyString(a.group('SB')))
            bb = Decimal(self.clearMoneyString(a.group('BB')))
            sbbb = sb + bb
            hand.addBlind(a.group('PNAME'), 'both', str(sbbb))

    def readHoleCards(self, hand):
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
            bet = self.convertMoneyString('BET', action)
            actionType = action.group('ATYPE')
            if street != 'PREFLOP' or actionType != ' folds':
                hand.setUncalledBets(False)
            if actionType == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif actionType == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif actionType == ' calls':
                hand.addCall( street, action.group('PNAME'), bet )
            elif actionType == ' raises':
                hand.setUncalledBets(None)
                hand.addRaiseTo( street, action.group('PNAME'), bet )
            elif actionType == ' bets':
                hand.addBet( street, action.group('PNAME'), bet )
            elif actionType == ' is all in':
                hand.addAllIn(street, action.group('PNAME'), bet)
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        pass

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            if not re.search('Tournament:\s', m.group('PNAME')):
                hand.addCollectPot(player=m.group('PNAME'),pot=self.convertMoneyString('POT', m))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                
                string = m.group('STRING')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "shows":
                    shown = True
                    cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
                elif m.group('SHOWED') == "mucks":
                    mucked = True
                    cards = [c.strip() for c in cards.split(',')] # needs to be a list, not a set--stud needs the order

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                try:
                    hand.checkPlayerExists(m.group('PNAME'))
                    player = m.group('PNAME')
                except FpdbParseError:
                    player = m.group('PNAME').replace('_', ' ')
                hand.addShownCards(cards=cards, player=player, shown=shown, mucked=mucked, string=string)
                
    def convertMoneyString(self, type, match):
        if match.group('EUROVALUE'):
            value = self.clearMoneyString(match.group('EUROVALUE'))
        elif match.group(type):
            value = self.clearMoneyString(match.group(type))
        else:
            value = None
        return value    
