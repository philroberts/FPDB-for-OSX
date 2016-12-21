#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2013, Carl Gherardi
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

# SealsWithClubs HH Format

class SealsWithClubs(HandHistoryConverter):

    # Class Variables

    sitename = "SealsWithClubs"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 23 # Needs to match id entry in Sites database
    substitutions = {
                           'PLYR': r'\s?(?P<PNAME>.+?)',
                          'BRKTS': r'(\(button\) |\(small blind\) |\(big blind\) |\(button\) \(small blind\) |\(button\) \(big blind\) )?',
                    }

    limits = { "NL":'nl', 'PL': 'pl', 'Limit':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'),
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi-Lo' : ('hold','omahahilo')
               }

    # Static regexes
    re_GameInfo = re.compile(ur"""Hand\s*\#(?P<HID>\d+)-\d+\s*-\s*(?P<DATETIME>[\-:\d ]+)\s*
                         Game:\s*(?P<LIMIT>(NL|PL|Limit))\s*(?P<GAME>(Hold'em|Omaha|Omaha\ Hi-Lo))
                         \s*\([\d\.]+\s*-\s*(?P<BUYIN>\d+)\)\s*-\s*
                         (Blinds|Stakes)\s*(?P<SB>[\d\.]+)/(?P<BB>[\d.]+)\s*
                         Site:\s+Seals\s+With\s+Clubs\s*
                         (Table:\sL\w+\s\d+(max|half|deep)\s(?P<SB1>[\d\.]+)/(?P<BB1>[\d.]+))?""",re.VERBOSE)
    # TODO: for tournaments: (?P<BIAMT>[\d\.]+)\+(?P<BIRAKE>[\d\.]+)

    re_PlayerInfo   = re.compile(ur"""
        ^\s?Seat\s+(?P<SEAT>\d+):\s*
        (?P<PNAME>.*)\s+
        \((?P<CASH>[.\d]+)\)""" % substitutions, 
        re.MULTILINE|re.VERBOSE)

    re_HandInfo = re.compile(ur"""^Table:\s(?P<TABLE>(.+)?((?P<HU>HU)|((?P<MAX>\d+)(max|half|deep))|No Rake Micro Stakes).*)""",re.MULTILINE)

    re_Identify     = re.compile(u"Site:\s*Seals\s*With\s*Clubs")
    re_SplitHands   = re.compile('(?:\s?\n){2,}')
    re_ButtonName   = re.compile(ur"""^(?P<BUTTONNAME>.*) has the dealer button""",re.MULTILINE)
    
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_DateTime     = re.compile(ur"""(?P<Y>\d{4})-(?P<M>\d{2})-(?P<D>\d{2})[\-\s]+(?P<H>\d+):(?P<MIN>\d+):(?P<S>\d+)""", re.MULTILINE)

    # These used to be compiled per player, but regression tests say
    # we don't have to, and it makes life faster.
    re_PostSB           = re.compile(r"^%(PLYR)s posts small blind (?P<SB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s posts big blind (?P<BB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s posts the ante (?P<ANTE>[.0-9]+)" % substitutions, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s posts small \& big blind (?P<SBBB>[.0-9]+)" %  substitutions, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s(?: \[(?P<OLDCARDS>.+?)\])?( \[(?P<NEWCARDS>.+?)\])" % substitutions, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sdiscards|\sstands\spat)
                        (\s+(to\s+)?(?P<BET>[.\d]+)?\s*)?( \(All-in\))?$"""
                         %  substitutions, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % substitutions['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"%(PLYR)s\s+(wins|splits)\s+((Side|Main|Hi|Lo)\s+)?Pot[\d\s]+\((?P<POT>[.\d]+)\)" %  substitutions, re.MULTILINE)
    re_Cancelled        = re.compile('Hand\scancelled', re.MULTILINE)
    
    re_Flop             = re.compile('\*\* Flop \*\*')
    re_Turn             = re.compile('\*\* Turn \*\*')
    re_River            = re.compile('\*\* River \*\*')

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"]]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("SealsWithClubsToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()
        if 'LIMIT' in mg:
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        
        if info['limitType'] != 'fl':
            if 'SB' in mg:
                info['sb'] = mg['SB']
            if 'BB' in mg:
                info['bb'] = mg['BB']
        else:
            if 'SB1' in mg:
                info['sb'] = mg['SB1']
            if 'BB1' in mg:
                info['bb'] = mg['BB1']
            
        info['currency'] = 'mBTC'
        # TODO: NO TOURNO so cash only for now
        info['type'] = 'ring' 

        return info

    def readHandInfo(self, hand):
        info = {}
        m  = self.re_HandInfo.search(hand.handText,re.DOTALL)
        m2 = self.re_GameInfo.search(hand.handText)
        if m is None or m2 is None:
            tmp = hand.handText[0:200]
            log.error(_("SealsWithClubsToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        if info['TABLE'] == "No Rake Micro Stakes":
            info['MAX'] = '9'
        info.update(m2.groupdict())

        #log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                #2013-01-31 05:55:42
                #2008/09/07 06:23:14 ET
                m1 = self.re_DateTime.finditer(info[key])
                datetimestr = "2000-01-01 00:00:00"  # default used if time not found
                for a in m1:
                    datetimestr = "%s-%s-%s %s:%s:%s" % (a.group('Y'), a.group('M'),a.group('D'),a.group('H'),a.group('MIN'),a.group('S'))
                    #tz = a.group('TZ')  # just assume ET??
                    #print "   tz = ", tz, " datetime =", datetimestr
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y-%m-%d %H:%M:%S") # also timezone at end, e.g. " ET"
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
            if key == 'HID':
                hand.handid = info[key]
            #if key == 'TOURNO':
            #    hand.tourNo = info[key]
            #if key == 'BUYIN':
            #    if hand.tourNo!=None:
                    #print "DEBUG: info['BUYIN']: %s" % info['BUYIN']
                    #print "DEBUG: info['BIAMT']: %s" % info['BIAMT']
                    #print "DEBUG: info['BIRAKE']: %s" % info['BIRAKE']
                    
            #        if info[key] == 'Freeroll':
            #            hand.buyin = 0
            #            hand.fee = 0
            #            hand.buyinCurrency = "FREE"
            #        else:
                        ##FIXME: currency set as EUR
            #            hand.buyinCurrency="EUR"
                        #info['BIRAKE'] = info['BIRAKE'].strip(u'$€£')

            #            hand.buyin = int(100*Decimal(info['BIAMT']))
            #            hand.fee = int(100*Decimal(info['BIRAKE']))
                        
            #if key == 'LEVEL':
            #    hand.level = info[key]       
            if key == 'TABLE':
                tablesplit = re.split(" ", info[key])
                if hand.tourNo != None and len(tablesplit)>1:
                    hand.tablename = tablesplit[1]
                else:
                    hand.tablename = info[key]
            if key == 'MAX' and info[key] != None:
                hand.maxseats = int(info[key])
            if key == 'HU' and info[key] != None:
                hand.maxseats = 2
                
        if self.re_Cancelled.search(hand.handText):
            raise FpdbHandPartial(_("Hand '%s' was cancelled.") % hand.handid)
    
    def readButton(self, hand):
        m = self.re_ButtonName.search(hand.handText)
        if m:
            dealer = m.group('BUTTONNAME')
            re_Button = re.compile(ur"""Seat\s+(?P<BUTTON>\d+):\s+%s""" % dealer)
            m = re_Button.search(hand.handText)
            hand.buttonpos = int(m.group('BUTTON'));
        else:
            log.debug('readButton: ' + _('not found'))

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'), None)

    def markStreets(self, hand):

        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        
        
        
        if hand.gametype['base'] in ("hold"):
            m =  re.search(
                        r"(\*\* Hole Cards \*\*(?P<PREFLOP>.+(?=\*\* (FIRST\s)?Flop \*\*)|.+))"
                        r"(\*\* Flop \*\*\s+(?P<FLOP>\[\S\S\s+\S\S\s+\S\S\].+(?=\*\* (FIRST\s)?Turn \*\*)|.+))?"
                        r"(\*\* Turn \*\*\s+(?P<TURN>\[\S\S\].+(?=\*\* (FIRST\s)?River \*\*)|.+))?"
                        r"(\*\* River \*\*\s+(?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)
        
        # some hand histories on swc are missing a flop
        if (self.re_Turn.search(hand.handText) and not self.re_Flop.search(hand.handText)):
            raise FpdbParseError
        if (self.re_River.search(hand.handText) and not self.re_Turn.search(hand.handText)):
            raise FpdbParseError
        
        # some hand histories on swc don't have hole cards either
        if not m:
            raise FpdbParseError
     
        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))

    def readAntes(self, hand):
        log.debug(_("reading antes"))
        m = self.re_Antes.finditer(hand.handText)
        for player in m:
            log.debug("hand.addAnte(%s,%s)" %(player.group('PNAME'), player.group('ANTE')))
            hand.addAnte(player.group('PNAME'), player.group('ANTE'))
        
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
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

    def readHoleCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    hand.hero = found.group('PNAME')
                    newcards = found.group('NEWCARDS').split(' ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' raises':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET') )
            else:
                print (_("DEBUG:") + " " + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(' ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT'))

    def readShownCards(self,hand):
        # TODO: something here?
        return

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        regex = re.escape(str(table_name))
        if type=="tour":
            pass
            #regex = re.escape(str(tournament)) + ".* (Table|Tisch) " + re.escape(str(table_number))
        log.debug("Seals.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.debug("Seals.getTableTitleRe: returns: '%s'" % (regex))
        return regex
