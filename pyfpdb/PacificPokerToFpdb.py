#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2008-2010, Carl Gherardi
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

# PacificPoker HH Format

class PacificPoker(HandHistoryConverter):

    # Class Variables

    sitename = "PacificPoker"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 13 # Needs to match id entry in Sites database

    mixes = { 'HORSE': 'horse', '8-Game': '8game', 'HOSE': 'hose'} # Legal mixed games
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": "\xe2\x82\xac", "GBP": "\xa3", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols - Euro(cp1252, utf-8)
                    }
                    
    # translations from captured groups to fpdb info strings
# :: TODO 0.02 limit does not seem right
    Lim_Blinds = {      '0.02': ('0.01', '0.02'),    '0.04': ('0.01', '0.02'),
                        '0.10': ('0.02', '0.05'),    '0.20': ('0.05', '0.10'),
                        '0.40': ('0.10', '0.20'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.00', '3.00'),       '6': ('1.00', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                       '80.00': ('20.00', '40.00'),    '80': ('20.00', '40.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                      '800.00': ('200.00', '400.00'), '800': ('200.00', '400.00'),
                     '1000.00': ('250.00', '500.00'),'1000': ('250.00', '500.00')
                  }

    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl', 'Fix Limit':'fl' }

    games = {                          # base, category
                               "Holdem" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                              'OmahaHL' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
              'Single Draw 2-7 Lowball' : ('draw','27_1draw'),
                          '5 Card Draw' : ('draw','fivedraw')
               }

    currencies = { u'€':'EUR', '$':'USD', '':'T$' }

    # Static regexes
    re_GameInfo     = re.compile(u"""
          \#Game\sNo\s:\s(?P<HID>[0-9]+)\\n
          \*\*\*\*\*\sCassava\sHand\sHistory\sfor\sGame\s[0-9]+\s\*\*\*\*\*\\n
          (?P<CURRENCY>%(LS)s)?(?P<SB>[.,0-9]+)/(%(LS)s)?(?P<BB>[.,0-9]+)\sBlinds\s
          (?P<LIMIT>No\sLimit|Fix\sLimit|Pot\sLimit)\s
	  (?P<GAME>Holdem|Omaha|OmahaHL)
          \s-\s\*\*\*\s
          (?P<DATETIME>.*$)
          """ % substitutions, re.MULTILINE|re.VERBOSE)

    re_PlayerInfo   = re.compile(u"""
          ^Seat\s(?P<SEAT>[0-9]+):\s
          (?P<PNAME>.*)\s
          \(\s(%(LS)s)?(?P<CASH>[.,0-9]+)\s\)""" % substitutions, 
          re.MULTILINE|re.VERBOSE)

    re_HandInfo     = re.compile("""
          ^Table\s(?P<TABLE>[-\ \#a-zA-Z\d]+)\s
          (\(Real\sMoney\))?
          (?P<PLAY>\(Practice\sPlay\))?
	  \\n
	  Seat\s(?P<BUTTON>[0-9]+)\sis\sthe\sbutton
          """, re.MULTILINE|re.VERBOSE)

    re_SplitHands   = re.compile('\n\n+')
    re_TailSplitHands   = re.compile('(\n\n\n+)')
    re_Button       = re.compile('Seat (?P<BUTTON>\d+) is the button', re.MULTILINE)
    re_Board        = re.compile(r"\[\s(?P<CARDS>.+)\s\]")

    re_DateTime     = re.compile("""(?P<D>[0-9]{2})\s(?P<M>[0-9]{2})\s(?P<Y>[0-9]{4})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)""", re.MULTILINE)

    # These used to be compiled per player, but regression tests say
    # we don't have to, and it makes life faster.
    short_subst = {'PLYR': r'(?P<PNAME>.+?)', 'CUR': '\$?'}
    re_PostSB           = re.compile(r"^%(PLYR)s posts small blind \[%(CUR)s(?P<SB>[.,0-9]+)\]" %  short_subst, re.MULTILINE)
    re_PostBB           = re.compile(r"^%(PLYR)s posts big blind \[%(CUR)s(?P<BB>[.,0-9]+)\]" %  short_subst, re.MULTILINE)
    re_Antes            = re.compile(r"^%(PLYR)s posts the ante \[%(CUR)s(?P<ANTE>[.,0-9]+)\]" % short_subst, re.MULTILINE)
    re_BringIn          = re.compile(r"^%(PLYR)s: brings[- ]in( low|) for %(CUR)s(?P<BRINGIN>[.,0-9]+)" % short_subst, re.MULTILINE)
    re_PostBoth         = re.compile(r"^%(PLYR)s posts dead blind \[%(CUR)s(?P<SBBB>[.,0-9]+)\s\+\s%(CUR)s[.,0-9]+\]" %  short_subst, re.MULTILINE)
    re_HeroCards        = re.compile(r"^Dealt to %(PLYR)s( \[\s(?P<NEWCARDS>.+?)\s\])" % short_subst, re.MULTILINE)
    re_Action           = re.compile(r"""
                        ^%(PLYR)s(?P<ATYPE>\sbets|\schecks|\sraises|\scalls|\sfolds|\sdiscards|\sstands\spat)
                        (\s\[(%(CUR)s)?(?P<BET>[.,0-9]+)\])?
                        (\s*and\sis\sall.in)?
                        (\s*and\shas\sreached\sthe\s[%(CUR)s\d\.]+\scap)?
                        (\s*cards?(\s\[(?P<DISCARDED>.+?)\])?)?\s*$"""
                         %  short_subst, re.MULTILINE|re.VERBOSE)
    re_ShowdownAction   = re.compile(r"^%s shows \[(?P<CARDS>.*)\]" % short_subst['PLYR'], re.MULTILINE)
    re_sitsOut          = re.compile("^%s sits out" %  short_subst['PLYR'], re.MULTILINE)
    re_ShownCards       = re.compile("^%s ?(?P<SHOWED>shows|mucks) \[ (?P<CARDS>.*) \]$" %  short_subst['PLYR'], re.MULTILINE)
    re_CollectPot       = re.compile(r"^%(PLYR)s collected \[ %(CUR)s(?P<POT>[.,0-9]+) \]$" %  short_subst, re.MULTILINE)

    def compilePlayerRegexs(self,  hand):
        pass

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],

                ["ring", "stud", "fl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                ["tour", "stud", "fl"],
                
                ["tour", "draw", "fl"],
                ["tour", "draw", "pl"],
                ["tour", "draw", "nl"],
                ]

    def determineGameType(self, handText):
        info = {}
        m = self.re_GameInfo.search(handText)
        if not m:
            tmp = handText[0:120]
            log.error(_("Unable to recognise gametype from: '%s'") % tmp)
            log.error("determineGameType: " + _("Raising FpdbParseError"))
            raise FpdbParseError(_("Unable to recognise gametype from: '%s'") % tmp)

        mg = m.groupdict()
        if 'LIMIT' in mg:
            #print "DEBUG: re_GameInfo[LIMIT] \'", mg['LIMIT'], "\'"
            info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            #print "DEBUG: re_GameInfo[GAME] \'", mg['GAME'], "\'"
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            #print "DEBUG: re_GameInfo[SB] \'", mg['SB'], "\'"
            info['sb'] = mg['SB']
        if 'BB' in mg:
            #print "DEBUG: re_GameInfo[BB] \'", mg['BB'], "\'"
            info['bb'] = mg['BB']
        if 'CURRENCY' in mg:
            #print "DEBUG: re_GameInfo[CURRENCY] \'", mg['CURRENCY'], "\'"
            info['currency'] = self.currencies[mg['CURRENCY']]

        if 'TOURNO' in mg and mg['TOURNO'] is not None:
            info['type'] = 'tour'
        else:
            info['type'] = 'ring'

        if info['limitType'] == 'fl' and info['bb'] is not None and info['type'] == 'ring' and info['base'] != 'stud':
            try:
                info['sb'] = self.Lim_Blinds[mg['BB']][0]
                info['bb'] = self.Lim_Blinds[mg['BB']][1]
            except KeyError:
                log.error(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])
                log.error("determineGameType: " + _("Raising FpdbParseError"))
                raise FpdbParseError(_("Lim_Blinds has no lookup for '%s'") % mg['BB'])

        return info

    def readHandInfo(self, hand):
        info = {}
        m  = self.re_HandInfo.search(hand.handText,re.DOTALL)
        m2 = self.re_GameInfo.search(hand.handText)
        if m is None or m2 is None:
            log.error(_("No match in readHandInfo: '%s'") % hand.handText[0:100])
            raise FpdbParseError(_("No match in readHandInfo: '%s'") % hand.handText[0:100])

        info.update(m.groupdict())
        info.update(m2.groupdict())

        log.debug("readHandInfo: %s" % info)
        for key in info:
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
                hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
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
                        elif info[key].find(u"€")!=-1:
                            hand.buyinCurrency="EUR"
                        elif info[key].find("FPP")!=-1:
                            hand.buyinCurrency="PSFP"
                        else:
                            #FIXME: handle other currencies, FPP, play money
                            raise FpdbParseError(_("Failed to detect currency.") + " " + _("Hand ID: %s: '%s'") % (hand.handid, info[key]))

                        info['BIAMT'] = info['BIAMT'].strip(u'$€FPP')
                        
                        if hand.buyinCurrency!="PSFP":
                            if info['BOUNTY'] != None:
                                # There is a bounty, Which means we need to switch BOUNTY and BIRAKE values
                                tmp = info['BOUNTY']
                                info['BOUNTY'] = info['BIRAKE']
                                info['BIRAKE'] = tmp
                                info['BOUNTY'] = info['BOUNTY'].strip(u'$€') # Strip here where it isn't 'None'
                                hand.koBounty = int(100*Decimal(info['BOUNTY']))
                                hand.isKO = True
                            else:
                                hand.isKO = False

                            info['BIRAKE'] = info['BIRAKE'].strip(u'$€')

                            hand.buyin = int(100*Decimal(info['BIAMT']))
                            hand.fee = int(100*Decimal(info['BIRAKE']))
                        else:
                            hand.buyin = int(Decimal(info['BIAMT']))
                            hand.fee = 0
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

            if key == 'MIXED':
                hand.mixed = self.mixes[info[key]] if info[key] is not None else None
            if key == 'PLAY' and info['PLAY'] is not None:
#                hand.currency = 'play' # overrides previously set value
                hand.gametype['currency'] = 'play'
    
    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
        else:
            log.info(_('readButton: not found'))

    def readPlayerStacks(self, hand):
        log.debug("readPlayerStacks")
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
	    #print "DEBUG: Seat[", a.group('SEAT'), "]; PNAME[", a.group('PNAME'), "]; CASH[", a.group('CASH'), "]"
            hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))

    def markStreets(self, hand):
        # PREFLOP = ** Dealing down cards **
        # This re fails if,  say, river is missing; then we don't get the ** that starts the river.
        if hand.gametype['base'] in ("hold"):
            m =  re.search(r"\*\* Dealing down cards \*\*(?P<PREFLOP>.+(?=\*\* Dealing flop \*\*)|.+)"
                       r"(\*\* Dealing flop \*\* (?P<FLOP>\[ \S\S, \S\S, \S\S \].+(?=\*\* Dealing turn \*\*)|.+))?"
                       r"(\*\* Dealing turn \*\* (?P<TURN>\[ \S\S \].+(?=\*\* Dealing river \*\*)|.+))?"
                       r"(\*\* Dealing river \*\* (?P<RIVER>\[ \S\S \].+))?"
		       , hand.handText,re.DOTALL)
        if m is None:
            log.error("Didn't match markStreets")
            raise FpdbParseError(_("No match in markStreets"))
	else:
            #print "DEBUG: Matched markStreets"
	    mg = m.groupdict()
#	    if 'PREFLOP' in mg:
#                print "DEBUG: PREFLOP: ", [mg['PREFLOP']]
#	    if 'FLOP' in mg:
#                print "DEBUG: FLOP: ", [mg['FLOP']]
#	    if 'TURN' in mg:
#                print "DEBUG: TURN: ", [mg['TURN']]
#	    if 'RIVER' in mg:
#                print "DEBUG: RIVER: ", [mg['RIVER']]

        hand.addStreets(m)

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(', '))

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
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'both', a.group('SBBB'))

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
                    newcards = found.group('NEWCARDS').split(', ')
                    hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)

        for street, text in hand.streets.iteritems():
            if not text or street in ('PREFLOP', 'DEAL'): continue  # already done these
            m = self.re_HeroCards.finditer(hand.streets[street])
            for found in m:
                player = found.group('PNAME')
                if found.group('NEWCARDS') is None:
                    newcards = []
                else:
                    newcards = found.group('NEWCARDS').split(', ')
                if found.group('OLDCARDS') is None:
                    oldcards = []
                else:
                    oldcards = found.group('OLDCARDS').split(', ')

                if street == 'THIRD' and len(newcards) == 3: # hero in stud game
                    hand.hero = player
                    hand.dealt.add(player) # need this for stud??
                    hand.addHoleCards(street, player, closed=newcards[0:2], open=[newcards[2]], shown=False, mucked=False, dealt=False)
                else:
                    hand.addHoleCards(street, player, open=newcards, closed=oldcards, shown=False, mucked=False, dealt=False)


    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            acts = action.groupdict()
            #print "DEBUG: acts: %s" %acts
            if action.group('ATYPE') == ' raises':
                hand.addRaiseTo( street, action.group('PNAME'), action.group('BET').replace(',','') )
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET').replace(',','') )
            elif action.group('ATYPE') == ' bets':
                hand.addBet( street, action.group('PNAME'), action.group('BET').replace(',','') )
            elif action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, action.group('PNAME'), action.group('BET').replace(',',''), action.group('DISCARDED'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'))
            else:
                print (_("DEBUG: ") + _("Unimplemented readAction: '%s' '%s'") % (action.group('PNAME'), action.group('ATYPE')))


    def readShowdownActions(self, hand):
# TODO: pick up mucks also??
        for shows in self.re_ShowdownAction.finditer(hand.handText):            
            cards = shows.group('CARDS').split(', ')
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        for m in self.re_CollectPot.finditer(hand.handText):
            #print "DEBUG: hand.addCollectPot(player=", m.group('PNAME'), ", pot=", m.group('POT'), ")"
            hand.addCollectPot(player=m.group('PNAME'),pot=m.group('POT').replace(',',''))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = cards.split(', ') # needs to be a list, not a set--stud needs the order

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "showed": shown = True
                elif m.group('SHOWED') == "mucked": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="ipath", help=_("parse input hand history"), default="regression-test-files/stars/horse/HH20090226 Natalie V - $0.10-$0.20 - HORSE.txt")
    parser.add_option("-o", "--output", dest="opath", help=_("output translation to"), default="-")
    parser.add_option("-f", "--follow", dest="follow", help=_("follow (tail -f) the input"), action="store_true", default=False)
    #parser.add_option("-q", "--quiet", action="store_const", const=logging.CRITICAL, dest="verbosity", default=logging.INFO)
    #parser.add_option("-v", "--verbose", action="store_const", const=logging.INFO, dest="verbosity")
    #parser.add_option("--vv", action="store_const", const=logging.DEBUG, dest="verbosity")

    (options, args) = parser.parse_args()

    e = PacificPoker(in_path = options.ipath, out_path = options.opath, follow = options.follow)
