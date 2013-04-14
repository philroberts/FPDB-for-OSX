#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2012, Chaz Littlejohn
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

# Enet HH Format

class Enet(HandHistoryConverter):

    # Class Variables

    sitename = "Enet"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 22 # Needs to match id entry in Sites database
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\£", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|\£|", # legal currency symbols - Euro(cp1252, utf-8)
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac||\£|)",
                          'BRKTS': r'(\(dealer\) |\(small blind\) |\(big blind\) |\(dealer\)\(small blind\) |\(dealer\)\(big blind\) | )?',
                           'NUM' : r'.,\d',
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

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
               }
    currencies = { u'€':'EUR', '$':'USD', '':'T$', u'£':'GBP' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          Game\s\#(?P<HID>[0-9]+):\s+
          (\{.*\}\s+)?(Tournament\s\#                # open paren of tournament info
          (?P<TOURNO>\d+),\s
          # here's how I plan to use LS
          (?P<BUYIN>(?P<BIAMT>[%(LS)s%(NUM)s]+)?\+?(?P<BIRAKE>[%(LS)s%(NUM)s]+)?\+?\s?(?P<TOUR_ISO>%(LEGAL_ISO)s)?|Freeroll)\s+)?
          # close paren of tournament info
          (?P<GAME>Hold\'em|Omaha)\s
          \(?                            # open paren of the stakes
          (?P<CURRENCY>%(LS)s|)?
          (?P<SB>[%(NUM)s]+)/(%(LS)s)?
          (?P<BB>[%(NUM)s]+)
          \)                        # close paren of the stakes
          \s-\s
          (?P<DATETIME>.*$)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \((%(LS)s)?(?P<CASH>[%(NUM)s]+)\sin\schips\)""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^Table\s\'(?P<TABLE>.+?)\s\-\s(?P<LIMIT>No\sLimit|Limit|Pot\sLimit)\)?\'\s
          ((?P<MAX>\d+)-max\s)?
          (?P<PLAY>\(Play\sMoney\)\s)?
          (Seat\s\#(?P<BUTTON>\d+)\sis\sthe\sbutton)?""", 
          re.MULTILINE|re.VERBOSE)

    re_Identify     = re.compile(u'^Game\s\#\d+:')
    re_SplitHands   = re.compile('\n\n+')
    re_TailSplitHands   = re.compile('(\n\n+)')
    re_Button       = re.compile('Seat #(?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[?(?P<CARDS>.+)\]")
    re_DateTime     = re.compile("""(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s(?P<D>[0-9]{1,2})\.(?P<M>[0-9]{1,2})\.(?P<Y>[0-9]{4})""", re.MULTILINE)
    # revised re including timezone (not currently used):
    #re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+) \(?(?P<TZ>[A-Z0-9]+)""", re.MULTILINE)

    # These used to be compiled per player, but regression tests say
    # we don't have to, and it makes life faster.
    re_PostSB           = re.compile(r"^%(PLYR)s: posts small blind %(CUR)s(?P<SB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s: posts big blind %(CUR)s(?P<BB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_PostDead         = re.compile(r"^%(PLYR)s: posts small blind $" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s: posts the ante %(CUR)s(?P<ANTE>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_BringIn          = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[%(NUM)s]+)" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s: posts small \& big blinds %(CUR)s(?P<SBBB>[%(NUM)s]+)" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sgoes\sall\-in)
                        (\s%(CUR)s(?P<BET>[%(NUM)s]+))?
                        (\son|\scards?)?
                        (\s\[(?P<CARDS>.+?)\])?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %(PLYR)s %(BRKTS)s(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\]( and (lost|won \(%(CUR)s(?P<POT>[%(NUM)s]+)\)) with (?P<STRING>.*))?" % substitutions, re.MULTILINE)
    re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s %(BRKTS)s(collected|showed \[.*\] and won) \(%(CUR)s(?P<POT>[%(NUM)s]+)\)(, mucked| with.*|)" %  substitutions, re.MULTILINE)
    re_Rake             = re.compile(r"^Rake: %(CUR)s(?P<RAKE>[%(NUM)s]+)" %  substitutions, re.MULTILINE)

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
            log.error(_("EnetToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        info['limitType'] = 'pl'
        #if 'LIMIT' in mg:
        #    info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = self.clearMoneyString(mg['SB'])
        if 'BB' in mg:
            info['bb'] = self.clearMoneyString(mg['BB'])
        if 'CURRENCY' in mg:
            info['currency'] = self.currencies[mg['CURRENCY']]
                
        if 'TOURNO' in mg and mg['TOURNO'] is None:
            info['type'] = 'ring'
        else:
            info['type'] = 'tour'
            
        if not mg['CURRENCY'] and info['type']=='ring':
            info['currency'] = 'play'

        if info['limitType'] == 'fl' and info['bb'] is not None:
            if info['type'] == 'ring':
                try:
                    info['sb'] = self.Lim_Blinds[self.clearMoneyString(mg['BB'])][0]
                    info['bb'] = self.Lim_Blinds[self.clearMoneyString(mg['BB'])][1]
                except KeyError:
                    tmp = handText[0:200]
                    log.error(_("EnetToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                    raise FpdbParseError
            else:
                info['sb'] = str((Decimal(self.clearMoneyString(mg['SB']))/2).quantize(Decimal("0.01")))
                info['bb'] = str(Decimal(self.clearMoneyString(mg['SB'])).quantize(Decimal("0.01")))    

        return info

    def readHandInfo(self, hand):
        info = {}
        m  = self.re_HandInfo.search(hand.handText,re.DOTALL)
        m2 = self.re_GameInfo.search(hand.handText)
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("EnetToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        info.update(m2.groupdict())

        #log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'LIMIT':
                hand.gametype['limitType'] = self.limits[info[key]]
            if key == 'DATETIME':
                #2008/11/12 10:00:48 CET [2008/11/12 4:00:48 ET] # (both dates are parsed so ET date overrides the other)
                #2008/08/17 - 01:14:43 (ET)
                #2008/09/07 06:23:14 ET
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000/01/01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    #tz = a.group('TZ')  # just assume ET??
                    #print "   tz = ", tz, " datetime =", datetimestr
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
                #hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TOURNO':
                hand.tourNo = info[key]
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
                            log.error(_("EnetToFpdb.readHandInfo: Failed to detect currency.") + " Hand ID: %s: '%s'" % (hand.handid, info[key]))
                            raise FpdbParseError

                        info['BIAMT'] = info['BIAMT'].strip(u'$€£')
                        info['BIRAKE'] = info['BIRAKE'].strip(u'$€£')
                        hand.buyin = int(100*Decimal(self.clearMoneyString(info['BIAMT'])))
                        hand.fee = int(100*Decimal(self.clearMoneyString(info['BIRAKE'])))
            if key == 'LEVEL':
                hand.level = info[key]
            if key == 'TABLE':
                if hand.tourNo != None:
                    hand.tablename = re.split(" ", info[key])[1]
                else:
                    hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])
    
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
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), self.clearMoneyString(a.group('CASH')))

    def markStreets(self, hand):

        # There is no marker between deal and draw in Stars single draw games
        #  this upsets the accounting, incorrectly sets handsPlayers.cardxx and 
        #  in consequence the mucked-display is incorrect.
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"\*\*\* HOLECARDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\* \[(?P<FLOP>\S\S\S\S\S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S\S\S\S\S(?P<TURN>\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S\S\S\S\S\S\S(?P<RIVER>\S\S\].+))?", hand.handText,re.DOTALL)
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            cards = m.group('CARDS')
            cards = [cards[i:i+2] for i in range(len(cards)) if i%2==0 and i+2<=len(cards)]
            hand.setCommunityCards(street, cards)

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), self.clearMoneyString(player.group('ANTE')))
    
    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText,re.DOTALL)
        if m:
            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
            hand.addBringIn(m.group('PNAME'),  self.clearMoneyString(m.group('BRINGIN')))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            if liveBlind:
                hand.addBlind(a.group('PNAME'), 'small blind', self.clearMoneyString(a.group('SB')))
                liveBlind = False
            else:
                # Post dead blinds as ante
                hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(a.group('SB')))
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', self.clearMoneyString(a.group('BB')))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', self.clearMoneyString(a.group('SBBB')))
        for a in self.re_PostDead.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'secondsb', self.clearMoneyString(hand.sb))

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
                    cards = found.group('NEWCARDS')
                    cards = [cards[i:i+2] for i in range(len(cards)) if i%2==0 and i+2<=len(cards)]
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                if street =='PREFLOP' and action.group('PNAME') not in [p for (p,b) in hand.posted]:
                    both = str(Decimal(str(hand.bb)) + Decimal(str(hand.sb)))
                    hand.addBlind(action.group('PNAME'), 'both', both)
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == ' raises':
                hand.addCallandRaise( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            elif action.group('ATYPE') == ' goes all-in':
                hand.addAllIn(street, action.group('PNAME'), self.clearMoneyString(action.group('BET')) )
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            cards = shows.group('CARDS')  
            cards = [cards[i:i+2] for i in range(len(cards)) if i%2==0 and i+2<=len(cards)]
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        hand.adjustCollected = True
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=self.clearMoneyString(m.group('POT')))
        for m in self.re_Rake.finditer(hand.handText):
            if hand.rakes.get('rake'):
                hand.rakes['rake'] += Decimal(self.clearMoneyString(m.group('RAKE')))
            else:
                hand.rakes['rake'] = Decimal(self.clearMoneyString(m.group('RAKE')))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = [cards[i:i+2] for i in range(len(cards)) if i%2==0 and i+2<=len(cards)]
                string = m.group('STRING')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)          
    