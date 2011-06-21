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
                     'LEGAL_ISO' : "EUR|",
                           'PLYR': r'(?P<PNAME>.+?)',
                            'CUR': u"(\$|\xe2\x82\xac|\u20ac|)",
                    }
                    
#    Lim_Blinds = {  '0.04': ('0.01', '0.02'),        '0.08': ('0.02', '0.04'),
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
#                  }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                           'Omaha High' : ('hold','omahahi'),
               }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          \s(?P<HID>[0-9]+)\s-\s
          (?P<GAME>Omaha\sHigh|Holdem)\s
          (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
          (?P<CURRENCY>%(LEGAL_ISO)s|)?\s
          (?P<SB>[.0-9]+)/
          (?P<BB>[.0-9]+)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^(?P<PNAME>.*)\s
          \((%(LEGAL_ISO)s)\s(?P<CASH>[.0-9]+)\s
          in\sseat\s(?P<SEAT>[0-9]+)\)"""
            % substitutions, re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          \s(?P<HID>[0-9]+)\s-\s
          (?P<GAME>Omaha\sHigh|Holdem)\s
          (?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s
          (?P<CURRENCY>%(LEGAL_ISO)s|)?\s
          (?P<SB>[.0-9]+)/
          (?P<BB>[.0-9]+)(?P<BLAH>.*)
          Table\s(?P<TABLE>.+)
        """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('Game #')
    re_Button       = re.compile('^Dealer:\s+(?P<PNAME>.*)$', re.MULTILINE)
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_GameEnds     = re.compile(r"Game\sended\s(?P<Y>[0-9]{4})-(?P<M>[0-9]{2})-(?P<D>[0-9]{2})\s(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)", re.MULTILINE)

    re_DateTime     = re.compile("""(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)
    re_PostSB       = re.compile(r"^Small Blind: {16}(?P<PNAME>.*)\s+\((?P<SB>[.0-9]+)\)", re.MULTILINE)
    re_PostBB       = re.compile(r"^Big Blind: {18}(?P<PNAME>.*)\s+\((?P<BB>[.0-9]+)\)", re.MULTILINE)
    re_Antes        = re.compile(r"^%(PLYR)s: posts the ante %(CUR)s(?P<ANTE>[.0-9]+)" % substitutions, re.MULTILINE)
    re_BringIn      = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[.0-9]+)" % substitutions, re.MULTILINE)
    re_PostBoth     = re.compile(r"^%(PLYR)s: posts small \& big blinds %(CUR)s(?P<SBBB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_HeroCards    = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s:(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sdiscards|\sstands\spat)
                        (\s%(CUR)s(?P<BET>[.\d]+))?(\sto\s%(CUR)s(?P<BETTO>[.\d]+))?  # the number discarded goes in <BET>
                        \s*(and\sis\sall.in)?
                        (and\shas\sreached\sthe\s[%(CUR)s\d\.]+\scap)?
                        (\son|\scards?)?
                        (\s\[(?P<CARDS>.+?)\])?\s*$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s: shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  substitutions['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^Seat (?P<SEAT>[0-9]+): %s (\(.*\) )?(?P<SHOWED>showed|mucked) \[(?P<CARDS>.*)\]( and won \([.\d]+\) with (?P<STRING>.*))?" %  substitutions['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"Seat (?P<SEAT>[0-9]+): %(PLYR)s (\(button\) |\(small blind\) |\(big blind\) |\(button\) \(small blind\) |\(button\) \(big blind\) )?(collected|showed \[.*\] and won) \(%(CUR)s(?P<POT>[.\d]+)\)(, mucked| with.*|)" %  substitutions, re.MULTILINE)
    re_WinningRankOne   = re.compile(u"^%(PLYR)s wins the tournament and receives %(CUR)s(?P<AMT>[\.0-9]+) - congratulations!$" %  substitutions, re.MULTILINE)
    re_WinningRankOther = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place and received %(CUR)s(?P<AMT>[.0-9]+)\.$" %  substitutions, re.MULTILINE)
    re_RankOther        = re.compile(u"^%(PLYR)s finished the tournament in (?P<RANK>[0-9]+)(st|nd|rd|th) place$" %  substitutions, re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:150]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error("determineGameType: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            info['currency'] = mg['CURRENCY']

        info['type'] = 'ring'
#
#        if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring':
#            try:
#                info['sb'] = self.Lim_Blinds[mg['BB']][0]
#                info['bb'] = self.Lim_Blinds[mg['BB']][1]
#            except KeyError:
#                log.error(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])
#                log.error("determineGameType: " + _("Raising FpdbParseError"))
#                raise FpdbParseError(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])
#
        return info

    def readHandInfo(self, hand):
        info = {}
        m2 = self.re_GameInfo.search(hand.handText)
        m3 = self.re_GameEnds.search(hand.handText)
        m  = self.re_HandInfo.search(hand.handText)
        if m is None or m2 is None or m3 is None:
            log.error(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            raise FpdbParseError(_("No match in readHandInfo: '%s'") % hand.handText[0:100])

        info.update(m.groupdict())
        info.update(m2.groupdict())
        info.update(m3.groupdict())

        log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'Y':
                datetimestr = "%s/%s/%s %s:%s:%s" % (info['Y'], info['M'],info['D'],info['H'],info['MIN'],info['S'])
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
            if key == 'HID':
                hand.handid = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
            if key == 'BUTTON':
                hand.buttonpos = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            # FIXME: Button is a player name, not position. Needs translation
            #hand.buttonpos = int(m.group('BUTTON'))
            pass
        else:
            log.info(_('readButton: not found'))

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            name = a.group('PNAME').strip()
            hand.addPlayer(int(a.group('SEAT')), name, a.group('CASH'))

    def markStreets(self, hand):
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"Dealer:(?P<PREFLOP>.+(?=Flop {24})|.+)"
                       r"(Flop  {24}(?P<FLOP>\S\S - \S\S - \S\S\.+(?=Turn  {24})|.+))?"
                       r"(Turn  {24}\S\S - \S\S - \S\S - (?P<TURN>\S\S.+(?=River  {23})|.+))?"
                       r"(River  {23}\S\S - \S\S - \S\S - \S\S - (?P<RIVER>\S\S.+))?", hand.handText,re.DOTALL)
        #mg = m.groupdict()
        #print mg
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        pass
#        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
#            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
#            m = self.re_Board.search(hand.streets[street])
#            hand.setCommunityCards(street, m.group('CARDS').split(' '))

    def readAntes(self, hand):
        pass
#        log.debug(_("reading antes"))
#        m = self.re_Antes.finditer(hand.handText)
#        for player in m:
#            #~ logging.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
#            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
    
    def readBringIn(self, hand):
        pass
#        m = self.re_BringIn.search(hand.handText,re.DOTALL)
#        if m:
#            #~ logging.debug("readBringIn: %s for %s" %(m.group('PNAME'),  m.group('BRINGIN')))
#            hand.addBringIn(m.group('PNAME'),  m.group('BRINGIN'))
        
    def readBlinds(self, hand):
        liveBlind = True
        for a in self.re_PostSB.finditer(hand.handText):
            name = a.group('PNAME').strip()
            if liveBlind:
                hand.addBlind(name, 'small blind', a.group('SB'))
                liveBlind = False
            else:
                # Post dead blinds as ante
                hand.addBlind(name, 'secondsb', a.group('SB'))
        for a in self.re_PostBB.finditer(hand.handText):
            name = a.group('PNAME').strip()
            hand.addBlind(name, 'big blind', a.group('BB'))
#        for a in self.re_PostBoth.finditer(hand.handText):
#            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readHeroCards(self, hand):
        pass
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
#        for street in ('PREFLOP', 'DEAL'):
#            if street in hand.streets.keys():
#                m = self.re_HeroCards.finditer(hand.streets[street])
#                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
#                    hand.hero = found.group('PNAME')
#                    newcards = found.group('NEWCARDS').split(' ')
#                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)
#
#        for street, text in hand.streets.iteritems():
#            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
#            m = self.re_HeroCards.finditer(hand.streets[street])
#            for found in m:
#                player = found.group('PNAME')
#                if found.group('NEWCARDS') is None:
#                    newcards = []
#                else:
#                    newcards = found.group('NEWCARDS').split(' ')
#                if found.group('OLDCARDS') is None:
#                    oldcards = []
#                else:
#                    oldcards = found.group('OLDCARDS').split(' ')
#
#                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
#                    hand.hero = player
#                    hand.dealt.add(player) # need this for stud??
#                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
#                else:
#                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        pass
#        m = self.re_Action.finditer(hand.streets[street])
#        for action in m:
#            acts = action.groupdict()
#            #print "DEBUG: acts: %s" %acts
#            if action.group('ATYPE') == ' raises':
#                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
#            elif action.group('ATYPE') == ' calls':
#                hand.addCall( street, action.group('PNAME'), action.group('BET') )
#            elif action.group('ATYPE') == ' bets':
#                hand.addBet( street, action.group('PNAME'), action.group('BET') )
#            elif action.group('ATYPE') == ' folds':
#                hand.addFold( street, action.group('PNAME'))
#            elif action.group('ATYPE') == ' checks':
#                hand.addCheck( street, action.group('PNAME'))
#            elif action.group('ATYPE') == ' discards':
#                hand.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('CARDS'))
#            elif action.group('ATYPE') == ' stands pat':
#                hand.addStandsPat( street, action.group('PNAME'), action.group('CARDS'))
#            else:
#                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
        pass
#        for shows in self.re_ShowdownAction.finditer(hand.handText):            
#            cards = shows.group('CARDS').split(' ')
#            hand.addShownCards(cards, shows.group('PNAME'))
#
#        for winningrankone in self.re_WinningRankOne.finditer(hand.handText):
#            hand.addPlayerRank (winningrankone.group('PNAME'),int(100*Decimal(winningrankone.group('AMT'))),1)
#
#        for winningrankothers in self.re_WinningRankOther.finditer(hand.handText):
#            hand.addPlayerRank (winningrankothers.group('PNAME'),int(100*Decimal(winningrankothers.group('AMT'))),winningrankothers.group('RANK'))
#
#        for rankothers in self.re_RankOther.finditer(hand.handText):
#            hand.addPlayerRank (rankothers.group('PNAME'),0,rankothers.group('RANK'))

    def readCollectPot(self,hand):
        pass
#        for m in self.re_CollectPot.finditer(hand.handText):
#            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        pass
#        for m in self.re_ShownCards.finditer(hand.handText):
#            if m.group('CARDS') is not None:
#                cards = m.group('CARDS')
#                cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
#                string = m.group('STRING')
#
#                (shown, mucked) = (False, False)
#                if m.group('SHOWED') == "showed": shown = True
#                elif m.group('SHOWED') == "mucked": mucked = True
#
#                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
#                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked, string=string)
