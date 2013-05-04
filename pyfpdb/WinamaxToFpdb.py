#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import exceptions

from HandHistoryConverter import *
from decimal_wrapper import Decimal

# Winamax HH Format

class Winamax(HandHistoryConverter):
    def Trace(f):
        def my_f(*args, **kwds):
            print ( "entering " +  f.__name__)
            result= f(*args, **kwds)
            print ( "exiting " +  f.__name__)
            return result
        my_f.__name = f.__name__
        my_f.__doc__ = f.__doc__
        return my_f

    filter = "Winamax"
    siteName = "Winamax"
    filetype = "text"
    codepage = ("utf8", "cp1252")
    siteId   = 15 # Needs to match id entry in Sites database

    mixes = { } # Legal mixed games
    sym = {'USD': "\$", 'CAD': "\$", 'T$': "", "EUR": u"\xe2\x82\xac|\u20ac", "GBP": "\xa3", "play": ""}         # ADD Euro, Sterling, etc HERE
    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|" # legal currency symbols - Euro(cp1252, utf-8)
                    }

    limits = { 'no limit':'nl', 'pot limit' : 'pl', 'fixed limit':'fl'}

    games = {                          # base, category
                                "Holdem" : ('hold','holdem'),
                                 'Omaha' : ('hold','omahahi'),
                # It appears French law prevents any other games from being spread.
               }

    # Static regexes
    # ***** End of hand R5-75443872-57 *****
    re_Identify = re.compile(u'Winamax\sPoker\s\-\s(CashGame|Tournament\s")')
    re_SplitHands = re.compile(r'\n\n')



# Winamax Poker - CashGame - HandId: #279823-223-1285031451 - Holdem no limit (0.02€/0.05€) - 2010/09/21 03:10:51 UTC
# Table: 'Charenton-le-Pont' 9-max (real money) Seat #5 is the button
    re_HandInfo = re.compile(u"""
            \s*Winamax\sPoker\s-\s
            (?P<RING>CashGame)?
            (?P<TOUR>Tournament\s
            (?P<TOURNAME>.+)?\s
            buyIn:\s(?P<BUYIN>(?P<BIAMT>[%(LS)s\d\,.]+)?(\s\+?\s|-)(?P<BIRAKE>[%(LS)s\d\,.]+)?\+?(?P<BOUNTY>[%(LS)s\d\.]+)?\s?(?P<TOUR_ISO>%(LEGAL_ISO)s)?|(?P<FREETICKET>[\sa-zA-Z]+))?\s
            (level:\s(?P<LEVEL>\d+))?
            .*)?
            \s-\sHandId:\s\#(?P<HID1>\d+)-(?P<HID2>\d+)-(?P<HID3>\d+).*\s  # REB says: HID3 is the correct hand number
            (?P<GAME>Holdem|Omaha)\s
            (?P<LIMIT>fixed\slimit|no\slimit|pot\slimit)\s
            \(
            (((%(LS)s)?(?P<ANTE>[.0-9]+)(%(LS)s)?)/)?
            ((%(LS)s)?(?P<SB>[.0-9]+)(%(LS)s)?)/
            ((%(LS)s)?(?P<BB>[.0-9]+)(%(LS)s)?)
            \)\s-\s
            (?P<DATETIME>.*)
            Table:\s\'(?P<TABLE>[^(]+)
            (.(?P<TOURNO>\d+).\#(?P<TABLENO>\d+))?.*
            \'
            \s(?P<MAXPLAYER>\d+)\-max
            \s(?P<MONEY>\(real\smoney\))?
            """ % substitutions, re.MULTILINE|re.DOTALL|re.VERBOSE)

    re_TailSplitHands = re.compile(r'\n\s*\n')
    re_Button       = re.compile(r'Seat\s#(?P<BUTTON>\d+)\sis\sthe\sbutton')
    re_Board        = re.compile(r"\[(?P<CARDS>.+)\]")
    re_Total        = re.compile(r"Total pot (?P<TOTAL>[\.\d]+).*(No rake|Rake (?P<RAKE>[\.\d]+))" % substitutions)

    # 2010/09/21 03:10:51 UTC
    re_DateTime = re.compile("""
            (?P<Y>[0-9]{4})/
            (?P<M>[0-9]+)/
            (?P<D>[0-9]+)\s
            (?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)\s
            UTC
            """, re.MULTILINE|re.VERBOSE)

# Seat 1: some_player (5€)
# Seat 2: some_other_player21 (6.33€)

    re_PlayerInfo        = re.compile(u'Seat\s(?P<SEAT>[0-9]+):\s(?P<PNAME>.*)\s\((%(LS)s)?(?P<CASH>[.0-9]+)(%(LS)s)?\)' % substitutions)
    re_PlayerInfoSummary = re.compile(u'Seat\s(?P<SEAT>[0-9]+):\s(?P<PNAME>.+?)\s' % substitutions)

    def compilePlayerRegexs(self, hand):
        players = set([player[1] for player in hand.players])
        if not players <= self.compiledPlayers: # x <= y means 'x is subset of y'
            # we need to recompile the player regexs.
# TODO: should probably rename re_HeroCards and corresponding method,
#    since they are used to find all cards on lines starting with "Dealt to:"
#    They still identify the hero.
            self.compiledPlayers = players
            #ANTES/BLINDS
            #helander2222 posts blind ($0.25), lopllopl posts blind ($0.50).
            player_re = "(?P<PNAME>" + "|".join(map(re.escape, players)) + ")"
            subst = {'PLYR': player_re, 'CUR': self.sym[hand.gametype['currency']]}
            self.re_PostSB    = re.compile('%(PLYR)s posts small blind (%(CUR)s)?(?P<SB>[\.0-9]+)(%(CUR)s)?' % subst, re.MULTILINE)
            self.re_PostBB    = re.compile('%(PLYR)s posts big blind (%(CUR)s)?(?P<BB>[\.0-9]+)(%(CUR)s)?' % subst, re.MULTILINE)
            self.re_DenySB    = re.compile('(?P<PNAME>.*) deny SB' % subst, re.MULTILINE)
            self.re_Antes     = re.compile(r"^%(PLYR)s posts ante (%(CUR)s)?(?P<ANTE>[\.0-9]+)(%(CUR)s)?" % subst, re.MULTILINE)
            self.re_BringIn   = re.compile(r"^%(PLYR)s brings[- ]in( low|) for (%(CUR)s)?(?P<BRINGIN>[\.0-9]+(%(CUR)s)?)" % subst, re.MULTILINE)
            self.re_PostBoth  = re.compile('(?P<PNAME>.*): posts small \& big blind \( (%(CUR)s)?(?P<SBBB>[\.0-9]+)(%(CUR)s)?\)' % subst)
            self.re_PostDead  = re.compile('(?P<PNAME>.*) posts dead blind \((%(CUR)s)?(?P<DEAD>[\.0-9]+)(%(CUR)s)?\)' % subst, re.MULTILINE)
            self.re_HeroCards = re.compile('Dealt\sto\s%(PLYR)s\s\[(?P<CARDS>.*)\]' % subst)

            self.re_Action = re.compile('(, )?(?P<PNAME>.*?)(?P<ATYPE> bets| checks| raises| calls| folds)( (%(CUR)s)?(?P<BET>[\d\.]+)(%(CUR)s)?)?( and is all-in)?' % subst)
            self.re_ShowdownAction = re.compile('(?P<PNAME>[^\(\)\n]*) (\((small blind|big blind|button)\) )?shows \[(?P<CARDS>.+)\]')

            self.re_CollectPot = re.compile('\s*(?P<PNAME>.*)\scollected\s(%(CUR)s)?(?P<POT>[\.\d]+)(%(CUR)s)?.*' % subst)
            self.re_ShownCards = re.compile("^Seat (?P<SEAT>[0-9]+): %(PLYR)s showed \[(?P<CARDS>.*)\].*" % subst, re.MULTILINE)

    def readSupportedGames(self):
        return [
                ["ring", "hold", "fl"],
                ["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["tour", "hold", "fl"],
                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
               ]

    def determineGameType(self, handText):
        # Inspect the handText and return the gametype dict
        # gametype dict is: {'limitType': xxx, 'base': xxx, 'category': xxx}
        info = {}

        m = self.re_HandInfo.search(handText)
        if not m:
            tmp = handText[0:200]
            log.error(_("WinamaxToFpdb.determineGameType: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()

        if mg.get('TOUR'):
            info['type'] = 'tour'
        elif mg.get('RING'):
            info['type'] = 'ring'
        
        if mg.get('MONEY'):
            info['currency'] = 'EUR'
        else:
            info['currency'] = 'play'

        if 'LIMIT' in mg:
            if mg['LIMIT'] in self.limits:
                info['limitType'] = self.limits[mg['LIMIT']]
            else:
                tmp = handText[0:100]
                log.error(_("WinamaxToFpdb.determineGameType: Limit not found in %s.") % tmp)
                raise FpdbParseError
        if 'GAME' in mg:
            (info['base'], info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            info['sb'] = mg['SB']
        if 'BB' in mg:
            info['bb'] = mg['BB']
            
        if info['limitType'] == 'fl' and info['bb'] is not None:
            info['sb'] = str((Decimal(mg['SB'])/2).quantize(Decimal("0.01")))
            info['bb'] = str(Decimal(mg['SB']).quantize(Decimal("0.01")))

        return info

    def readHandInfo(self, hand):
        info = {}
        m =  self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("WinamaxToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        info.update(m.groupdict())
        #log.debug("readHandInfo: %s" % info)
        for key in info:
            if key == 'DATETIME':
                a = self.re_DateTime.search(info[key])
                if a:
                    datetimestr = "%s/%s/%s %s:%s:%s" % (a.group('Y'),a.group('M'), a.group('D'), a.group('H'),a.group('MIN'),a.group('S'))
                else:
                    datetimestr = "2010/Jan/01 01:01:01"
                    log.error("readHandInfo: " + _("DATETIME not matched: '%s'") % info[key])
                    #print "DEBUG: readHandInfo: DATETIME not matched: '%s'" % info[key]
                hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
            if key == 'HID1':
                # Need to remove non-alphanumerics for MySQL
                # Concatenating all three or just HID2 + HID3 can produce out of range values
                # HID should not be greater than 14 characters to ensure this
                hand.handid = "%s%s" % (int(info['HID1'][:14]), int(info['HID2']))
                    
#            if key == 'HID3':
#                hand.handid = int(info['HID3'])   # correct hand no (REB)
            if key == 'TOURNO':
                hand.tourNo = info[key]
            if key == 'TABLE':
                hand.tablename = info[key]
                if hand.gametype['type'] == 'tour':
                    hand.tablename = info['TABLENO']
                    hand.roundPenny = True
                # TODO: long-term solution for table naming on Winamax.
                if hand.tablename.endswith(u'No Limit Hold\'em'):
                    hand.tablename = hand.tablename[:-len(u'No Limit Hold\'em')] + u'NLHE'
            if key == 'MAXPLAYER' and info[key] != None:
                hand.maxseats = int(info[key])

            if key == 'BUYIN':
                if hand.tourNo!=None:
                    #print "DEBUG: info['BUYIN']: %s" % info['BUYIN']
                    #print "DEBUG: info['BIAMT']: %s" % info['BIAMT']
                    #print "DEBUG: info['BIRAKE']: %s" % info['BIRAKE']
                    #print "DEBUG: info['BOUNTY']: %s" % info['BOUNTY']
                    for k in ['BIAMT','BIRAKE']:
                        if k in info.keys() and info[k]:
                            info[k] = info[k].replace(',','.')

                    if info['FREETICKET'] is not None:
                        hand.buyin = 0
                        hand.fee = 0
                        hand.buyinCurrency = "FREE"
                    else:
                        if info[key].find("$")!=-1:
                            hand.buyinCurrency="USD"
                        elif info[key].find(u"€")!=-1:
                            hand.buyinCurrency="EUR"
                        elif info[key].find("FPP")!=-1:
                            hand.buyinCurrency="WIFP"
                        elif info[key].find("Free")!=-1:
                            hand.buyinCurrency="WIFP"
                        elif info['MONEY']:
                            hand.buyinCurrency="EUR"
                        else:
                            hand.buyinCurrency="play"

                        if info['BIAMT'] is not None:
                            info['BIAMT'] = info['BIAMT'].strip(u'$€FPP')
                        else:
                            info['BIAMT'] = 0

                        if hand.buyinCurrency!="WIFP":
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

                            # TODO: Is this correct? Old code tried to
                            # conditionally multiply by 100, but we
                            # want hand.buyin in 100ths of
                            # dollars/euros (so hand.buyin = 90 for $0.90 BI).
                            hand.buyin = int(100 * Decimal(info['BIAMT']))
                            hand.fee = int(100 * Decimal(info['BIRAKE']))
                        else:
                            hand.buyin = int(Decimal(info['BIAMT']))
                            hand.fee = 0
                        if hand.buyin == 0 and hand.fee == 0:
                            hand.buyinCurrency = "FREE"

            if key == 'LEVEL':
                hand.level = info[key]

        hand.mixed = None

    def readPlayerStacks(self, hand):
        # Split hand text for Winamax, as the players listed in the hh preamble and the summary will differ
        # if someone is sitting out.
        # Going to parse both and only add players in the summary.
        handsplit = hand.handText.split('*** SUMMARY ***')
        if len(handsplit)!=2:
            raise FpdbHandPartial(_("Hand is not cleanly split into pre and post Summary %s.") % hand.handid)
        pre, post = handsplit
        m = self.re_PlayerInfo.finditer(pre)
        plist = {}

        # Get list of players in header.
        for a in m:
            if plist.get(a.group('PNAME')) is None:
                hand.addPlayer(int(a.group('SEAT')), a.group('PNAME'), a.group('CASH'))
                plist[a.group('PNAME')] = [int(a.group('SEAT')), a.group('CASH')]

    def markStreets(self, hand):
        m =  re.search(r"\*\*\* ANTE\/BLINDS \*\*\*(?P<PREFLOP>.+(?=\*\*\* FLOP \*\*\*)|.+)"
                       r"(\*\*\* FLOP \*\*\*(?P<FLOP> \[\S\S \S\S \S\S\].+(?=\*\*\* TURN \*\*\*)|.+))?"
                       r"(\*\*\* TURN \*\*\* \[\S\S \S\S \S\S](?P<TURN>\[\S\S\].+(?=\*\*\* RIVER \*\*\*)|.+))?"
                       r"(\*\*\* RIVER \*\*\* \[\S\S \S\S \S\S \S\S](?P<RIVER>\[\S\S\].+))?", hand.handText,re.DOTALL)

        try:
            hand.addStreets(m)
#            print "adding street", m.group(0)
#            print "---"
        except:
            log.info(_("Failed to add streets. handtext=%s"))

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb,
    # addtional players are assumed to post a bb oop

    def readButton(self, hand):
        m = self.re_Button.search(hand.handText)
        if m:
            hand.buttonpos = int(m.group('BUTTON'))
            #log.debug(_('readButton: button on pos %d') % hand.buttonpos)
        else:
            log.info('readButton: ' + _('not found'))

#    def readCommunityCards(self, hand, street):
#        #print hand.streets.group(street)
#        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
#            m = self.re_Board.search(hand.streets.group(street))
#            hand.setCommunityCards(street, m.group('CARDS').split(','))

    def readCommunityCards(self, hand, street): # street has been matched by markStreets, so exists in this hand
        if street in ('FLOP','TURN','RIVER'):   # a list of streets which get dealt community cards (i.e. all but PREFLOP)
            #print "DEBUG readCommunityCards:", street, hand.streets.group(street)
            m = self.re_Board.search(hand.streets[street])
            hand.setCommunityCards(street, m.group('CARDS').split(' '))

    def readBlinds(self, hand):
        if not self.re_DenySB.search(hand.handText):
            try:
                m = self.re_PostSB.search(hand.handText)
                hand.addBlind(m.group('PNAME'), 'small blind', m.group('SB'))
            except exceptions.AttributeError: # no small blind
                log.warning( _("No small blinds found.")+str(sys.exc_info()) )
            #hand.addBlind(None, None, None)
        for a in self.re_PostBB.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'big blind', a.group('BB'))
            amount = Decimal(a.group('BB').replace(u',', u''))
            hand.lastBet['PREFLOP'] = amount
        for a in self.re_PostDead.finditer(hand.handText):
            #print "DEBUG: Found dead blind: addBlind(%s, 'secondsb', %s)" %(a.group('PNAME'), a.group('DEAD'))
            hand.addBlind(a.group('PNAME'), 'secondsb', a.group('DEAD'))
        for a in self.re_PostBoth.finditer(hand.handText):
            hand.addBlind(a.group('PNAME'), 'small & big blinds', a.group('SBBB'))

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

    def readHeroCards(self, hand):
        # streets PREFLOP, PREDRAW, and THIRD are special cases beacause
        # we need to grab hero's cards
        for street in ('PREFLOP', 'DEAL', 'BLINDSANTES'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
            if m == []:
                log.debug(_("No hole cards found for %s") % street)
            for found in m:
                hand.hero = found.group('PNAME')
                newcards = found.group('CARDS').split(' ')
#                print "DEBUG: %s addHoleCards(%s, %s, %s)" %(hand.handid, street, hand.hero, newcards)
                hand.addHoleCards(street, hand.hero, closed=newcards, shown=False, mucked=False, dealt=True)
                log.debug(_("Hero cards %s: %s") % (hand.hero, newcards))

    def readAction(self, hand, street):
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            #acts = action.groupdict()
            #print "DEBUG: acts: %s" % acts
            if action.group('ATYPE') == ' folds':
                hand.addFold( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' checks':
                hand.addCheck( street, action.group('PNAME'))
            elif action.group('ATYPE') == ' calls':
                hand.addCall( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' raises':
                hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' bets':
                if street in ('PREFLOP', 'DEAL', 'BLINDSANTES'):
                    hand.addRaiseBy( street, action.group('PNAME'), action.group('BET') )
                else:
                    hand.addBet( street, action.group('PNAME'), action.group('BET') )
            elif action.group('ATYPE') == ' discards':
                hand.addDiscard(street, action.group('PNAME'), action.group('BET'), action.group('DISCARDED'))
            elif action.group('ATYPE') == ' stands pat':
                hand.addStandsPat( street, action.group('PNAME'))
            else:
                log.fatal(_("DEBUG:") + _("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PNAME'), action.group('ATYPE')))
#            print "Processed %s"%acts
#            print "committed=",hand.pot.committed

    def readShowdownActions(self, hand):
        for shows in self.re_ShowdownAction.finditer(hand.handText):
            #log.debug(_("add show actions %s") % shows)
            cards = shows.group('CARDS')
            cards = cards.split(' ')
#            print "DEBUG: addShownCards(%s, %s)" %(cards, shows.group('PNAME'))
            hand.addShownCards(cards, shows.group('PNAME'))

    def readCollectPot(self,hand):
        hand.setUncalledBets(True)
        for m in self.re_CollectPot.finditer(hand.handText):
            hand.addCollectPot(player=m.group('PNAME'), pot=m.group('POT'))

    def readShownCards(self,hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            log.debug(_("Read shown cards: %s") % m.group(0))
            cards = m.group('CARDS')
            cards = cards.split(' ') # needs to be a list, not a set--stud needs the order
            (shown, mucked) = (False, False)
            if m.group('CARDS') is not None:
                shown = True
                hand.addShownCards(cards=cards, player=m.group('PNAME'), shown=shown, mucked=mucked)

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        """
        SnG's
        No Limit Hold'em(17027463)#0 - 20-40 NL Holdem  - Buy-in: 1€
        No Limit Hold'em(17055704)#0 - 300-600 (ante 75) NL Holdem  - Buy-in: 0,50€
        No Limit Hold'em(17056243)#2 - 400-800 (ante 40) NL Holdem  - Buy-in: 0,50€
        Deglingos !(17060078)#0 - 30-60 NL Holdem  - Buy-in: 0,50€
        Deglingos Qualif. 2€(17060167)#0 - 20-40 NL Holdem  - Buy-in: 0,50€
        Double Shootout(17059623)#1 - 15-30 NL Holdem  - Buy-in: 0,50€
        Double Shootout(17060527)#1 - 40-80 NL Holdem  - Buy-in: 0,50€
        No Limit Hold'em(17056975)#0 - 300-600 (ante 75) NL Holdem  - Buy-in: 0,50€
        No Limit Hold'em(17056975)#0 - 300-600 (ante 75) NL Holdem  - Buy-in: 0,50€
        No Limit Hold'em(17059475)#2 - 15-30 NL Holdem  - Buy-in: 1€
        No Limit Hold'em(17059934)#0 - 15-30 NL Holdem  - Buy-in: 0,50€
        No Limit Hold'em(17059934)#0 - 20-40 NL Holdem  - Buy-in: 0,50€
        Pot Limit Omaha(17059108)#0 - 60-120 PL Omaha  - Buy-in: 0,50€
        Qualificatif 2€(17057954)#0 - 80-160 NL Holdem  - Buy-in: 0,50€
        Qualificatif 5€(17057018)#0 - 300-600 (ante 30) NL Holdem  - Buy-in: 1€
        Quitte ou Double(17057267)#0 - 150-300 PL Omaha  - Buy-in: 0,50€
        Quitte ou Double(17058093)#0 - 100-200 (ante 10) NL Holdem  - Buy-in: 0,50€
        Starting Block Winamax Poker Tour(17059192)#0 - 30-60 NL Holdem  - Buy-in: 0€
        MTT's
        1€ et un autre...(16362149)#016 - 60-120 (ante 10) NL Holdem  - Buy-in: 1€
        2€ et l'apéro...(16362145)#000 - 5k-10k (ante 1k) NL Holdem  - Buy-in: 2€
        Deepstack Hold'em(16362363)#013 - 200-400 (ante 30) NL Holdem  - Buy-in: 5€
        Deglingos MAIN EVENT(16362466)#002 - 10-20 NL Holdem  - Buy-in: 2€
        Hold'em(16362170)#013 - 30-60 NL Holdem  - Buy-in: 2€
        MAIN EVENT(16362311)#008 - 300-600 (ante 60) NL Holdem  - Buy-in: 150€
        MiniRoll 0.25€(16362117)#045 - 1,25k-2,50k (ante 250) NL Holdem  - Buy-in: 0,25€
        MiniRoll 0.50€(16362116)#018 - 20k-40k (ante 4k) NL Holdem  - Buy-in: 0,50€
        MiniRoll 0.50€(16362118)#007 - 75-150 (ante 15) NL Holdem  - Buy-in: 0,50€
        Qualificatif 5€(16362201)#010 - 10-20 NL Holdem  - Buy-in: 0,50€
        Tremplin Caen 2(15290669)#026 - 2,50k-5k (ante 500) NL Holdem  - Buy-in: 0€
        Freeroll 250€(16362273)#035 - 2,50k-5k (ante 500) NL Holdem  - Buy-in: 0€
        """
        log.info("Winamax.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        regex = "%s /" % (table_name)
        if tournament:
            regex = "\(%s\)#(%s|%03d)" % (tournament, table_number,int(table_number))
        log.info("Winamax.getTableTitleRe: returns: '%s'" % (regex))
        return regex

