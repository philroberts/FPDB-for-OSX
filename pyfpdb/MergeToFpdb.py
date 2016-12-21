#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2010-2011, Matthew Boss
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

# TODO:
#
# -- Assumes that the currency of ring games is USD
# -- Only accepts 'realmoney="true"'
# -- A hand's time-stamp does not record seconds past the minute (a limitation of the history format)
# -- hand.maxseats can only be guessed at
# -- Cannot parse tables that run it twice
# -- Cannot parse hands in which someone is all in in one of the blinds.

import sys
from HandHistoryConverter import *
import MergeStructures
from decimal_wrapper import Decimal


class Merge(HandHistoryConverter):
    sitename = "Merge"
    filetype = "text"
    codepage = ("cp1252", "utf8")
    siteId   = 12
    copyGameHeader = True
    Structures = MergeStructures.MergeStructures()

    limits = { 'No Limit':'nl', 'No Limit ':'nl', 'Limit':'fl', 'Pot Limit':'pl', 'Pot Limit ':'pl', 'Half Pot Limit':'hp'}
    games = {              # base, category
                    'Holdem' : ('hold','holdem'),
                    'Omaha'  : ('hold','omahahi'),
               'Omaha H/L8'  : ('hold','omahahilo'),
              '2-7 Lowball'  : ('draw','27_3draw'),
              'A-5 Lowball'  : ('draw','a5_3draw'),
                   'Badugi'  : ('draw','badugi'),
           '5-Draw w/Joker'  : ('draw','fivedraw'),
                   '5-Draw'  : ('draw','fivedraw'),
                   '7-Stud'  : ('stud','studhi'),
              '7-Stud H/L8'  : ('stud','studhilo'),
                   '5-Stud'  : ('stud','5_studhi'),
                     'Razz'  : ('stud','razz'),
            }
    
    mixes = {
                   'HA' : 'ha',
                 'RASH' : 'rash',
                   'HO' : 'ho',
                 'SHOE' : 'shoe',
                'HORSE' : 'horse',
                 'HOSE' : 'hose',
                  'HAR' : 'har'
        }
    
    Lim_Blinds = {      '0.04': ('0.01', '0.02'),    '0.10': ('0.02', '0.05'),
                        '0.20': ('0.05', '0.10'),
                        '0.25': ('0.05', '0.10'),    '0.50': ('0.10', '0.25'),
                        '1.00': ('0.25', '0.50'),       '1': ('0.25', '0.50'),
                        '2.00': ('0.50', '1.00'),       '2': ('0.50', '1.00'),
                        '4.00': ('1.00', '2.00'),       '4': ('1.00', '2.00'),
                        '6.00': ('1.50', '3.00'),       '6': ('1.50', '3.00'),
                        '8.00': ('2.00', '4.00'),       '8': ('2.00', '4.00'),
                       '10.00': ('2.00', '5.00'),      '10': ('2.00', '5.00'),
                       '12.00': ('3.00', '6.00'),      '12': ('3.00', '6.00'),
                       '20.00': ('5.00', '10.00'),     '20': ('5.00', '10.00'),
                       '30.00': ('10.00', '15.00'),    '30': ('10.00', '15.00'),
                       '40.00': ('10.00', '20.00'),    '40': ('10.00', '20.00'),
                       '50.00': ('10.00', '25.00'),    '50': ('10.00', '25.00'),
                       '60.00': ('15.00', '30.00'),    '60': ('15.00', '30.00'),
                      '100.00': ('25.00', '50.00'),   '100': ('25.00', '50.00'),
                      '200.00': ('50.00', '100.00'),  '200': ('50.00', '100.00'),
                      '400.00': ('100.00', '200.00'), '400': ('100.00', '200.00'),
                  }

    Multigametypes = {  '1': ('hold','holdem'),
                        '2': ('hold','holdem'),
                        '4': ('hold','omahahi'),
                        '9': ('hold', 'holdem'),
                        '23': ('hold', 'holdem'),
                        '34': ('hold','omahahilo'),
                        '35': ('hold','omahahilo'),
                        '37': ('hold','omahahilo'),
                        '38': ('stud','studhi'),
                        '39': ('stud','studhi'),
                        '41': ('stud','studhi'),
                        '42': ('stud','studhi'),
                        '43': ('stud','studhilo'),
                        '45': ('stud','studhilo'),
                        '46': ('stud','razz'),
                        '47': ('stud','razz'),
                        '49': ('stud','razz')
                  }    


    # Static regexes
    re_Identify = re.compile(u'<game\sid=\"[0-9]+\-[0-9]+\"\sstarttime')
    re_SplitHands = re.compile(r'</game>\n+(?=<)')
    re_TailSplitHands = re.compile(r'(</game>)')
    re_GameInfo = re.compile(r'<description type="(?P<GAME>Holdem|Omaha|Omaha|Omaha\sH/L8|2\-7\sLowball|A\-5\sLowball|Badugi|5\-Draw\sw/Joker|5\-Draw|7\-Stud|7\-Stud\sH/L8|5\-Stud|Razz|HORSE|RASH|HA|HO|SHOE|HOSE|HAR)(?P<TYPE>\sTournament)?" stakes="(?P<LIMIT>(No Limit|Limit|Pot Limit|Half Pot Limit)\s?)(\sLevel\s\d+\sBlinds)?(\s\(?\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)?(?P<blah>.*)\)?)?"(\sversion="\d+")?\s?/>\s?', re.MULTILINE)
    # <game id="46154255-645" starttime="20111230232051" numholecards="2" gametype="1" seats="9" realmoney="false" data="20111230|Play Money (46154255)|46154255|46154255-645|false">
    # <game id="46165919-1" starttime="20111230161824" numholecards="2" gametype="23" seats="10" realmoney="true" data="20111230|Fun Step 1|46165833-1|46165919-1|true">
    # <game id="46289039-1" starttime="20120101200100" numholecards="2" gametype="23" seats="9" realmoney="true" data="20120101|$200 Freeroll - NL Holdem - 20%3A00|46245544-1|46289039-1|true">
    re_HandInfo = re.compile(r'<game id="(?P<HID1>[0-9]+)-(?P<HID2>[0-9]+)" starttime="(?P<DATETIME>.+?)" numholecards="[0-9]+" gametype="[0-9]+" (stakes=".*" )?(multigametype="(?P<MULTIGAMETYPE1>\d+)" )?(seats="(?P<SEATS>[0-9]+)" )?realmoney="(?P<REALMONEY>(true|false))" (multigametype="(?P<MULTIGAMETYPE2>\d+)" )?(data="[0-9]+[|:](?P<TABLENAME>[^|:]+)[|:](?P<TDATA>[^|:]+)[|:]?)?.*>', re.MULTILINE)
    re_Button = re.compile(r'<players dealer="(?P<BUTTON>[0-9]+)"\s?>')
    re_PlayerInfo = re.compile(r'<player seat="(?P<SEAT>[0-9]+)" nickname="(?P<PNAME>.+)" balance="\$?(?P<CASH>[.0-9]+)" dealtin="(?P<DEALTIN>(true|false))" />', re.MULTILINE)
    re_Board = re.compile(r'<cards type="COMMUNITY" cards="(?P<CARDS>[^"]+)"', re.MULTILINE)
    re_Buyin = re.compile(r'\$(?P<BUYIN>[.,0-9]+)\s(?P<TYPE>Freeroll|Satellite|Guaranteed)?', re.MULTILINE)
    re_secondGame = re.compile(r'\$?(?P<SB>[.0-9]+)?/?\$?(?P<BB>[.0-9]+)', re.MULTILINE)
    
    # The following are also static regexes: there is no need to call
    # compilePlayerRegexes (which does nothing), since players are identified
    # not by name but by seat number
    re_PostSB = re.compile(r'<event sequence="[0-9]+" type="SMALL_BLIND" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SB>[.0-9]+)"\s?/>', re.MULTILINE)
    re_PostBB = re.compile(r'<event sequence="[0-9]+" type="(BIG_BLIND|INITIAL_BLIND)" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BB>[.0-9]+)"\s?/>', re.MULTILINE)
    re_PostBoth = re.compile(r'<event sequence="[0-9]+" type="RETURN_BLIND" (?P<TIMESTAMP>timestamp="[0-9]+" )?player="(?P<PSEAT>[0-9])" amount="(?P<SBBB>[.0-9]+)"\s?/>', re.MULTILINE)
    re_Antes = re.compile(r'<event sequence="[0-9]+" type="ANTE" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<ANTE>[.0-9]+)"\s?/>', re.MULTILINE)
    re_BringIn = re.compile(r'<event sequence="[0-9]+" type="BRING_IN" (?P<TIMESTAMP>timestamp="\d+" )?player="(?P<PSEAT>[0-9])" amount="(?P<BRINGIN>[.0-9]+)"\s?/>', re.MULTILINE)
    re_HeroCards = re.compile(r'<cards type="(HOLE|DRAW_DRAWN_CARDS)" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_Action = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT|DRAW|COMPLETE)"( timestamp="(?P<TIMESTAMP>[0-9]+)")? player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?( text="(?P<TXT>.+)")?\s?/>', re.MULTILINE)
    re_AllActions = re.compile(r'<event sequence="[0-9]+" type="(?P<ATYPE>FOLD|CHECK|CALL|BET|RAISE|ALL_IN|SIT_OUT|DRAW|COMPLETE|BIG_BLIND|INITIAL_BLIND|SMALL_BLIND|RETURN_BLIND|BRING_IN|ANTE)"( timestamp="(?P<TIMESTAMP>[0-9]+)")? player="(?P<PSEAT>[0-9])"( amount="(?P<BET>[.0-9]+)")?( text="(?P<TXT>.+)")?\s?/>', re.MULTILINE)
    re_CollectPot = re.compile(r'<winner amount="(?P<POT>[.0-9]+)" uncalled="(?P<UNCALLED>false|true)" potnumber="[0-9]+" player="(?P<PSEAT>[0-9])"', re.MULTILINE)
    re_SitsOut = re.compile(r'<event sequence="[0-9]+" type="SIT_OUT" player="(?P<PSEAT>[0-9])"\s?/>', re.MULTILINE)
    re_ShownCards     = re.compile(r'<cards type="(?P<SHOWED>SHOWN|MUCKED)" cards="(?P<CARDS>.+)" player="(?P<PSEAT>[0-9])"\s?/>', re.MULTILINE)
    re_Connection  = re.compile(r'<event sequence="[0-9]+" type="(?P<TYPE>RECONNECTED|DISCONNECTED)" timestamp="[0-9]+" player="[0-9]"\s?/>', re.MULTILINE)
    re_Cancelled   = re.compile(r'<event sequence="\d+" type="GAME_CANCELLED" timestamp="\d+"\s?/>', re.MULTILINE)
    re_LeaveTable  = re.compile(r'<event sequence="\d+" type="LEAVE" timestamp="\d+" player="\d"\s?/>', re.MULTILINE)
    re_PlayerOut   = re.compile(r'<event sequence="\d+" type="(PLAYER_OUT|LEAVE)" timestamp="\d+" player="(?P<PSEAT>[0-9])"\s?/>', re.MULTILINE)
    re_EndOfHand   = re.compile(r'<round id="END_OF_GAME"', re.MULTILINE)
    re_DateTime    = re.compile(r'(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)', re.MULTILINE)
    re_PlayMoney   = re.compile(r'realmoney="false"')

    def compilePlayerRegexs(self, hand):
        pass

    def playerNameFromSeatNo(self, seatNo, hand):
        # This special function is required because Merge Poker records
        # actions by seat number (0 based), not by the player's name
        for p in hand.players:
            if p[0] == int(seatNo)+1:
                return p[1]

    def readSupportedGames(self):
        return [["ring", "hold", "nl"],
                ["ring", "hold", "pl"],
                ["ring", "hold", "fl"],
                ["ring", "hold", "hp"],

                ["ring", "stud", "fl"],
                ["ring", "stud", "pl"],
                ["ring", "stud", "nl"],

                ["ring", "draw", "fl"],
                ["ring", "draw", "pl"],
                ["ring", "draw", "nl"],
                ["ring", "draw", "hp"],

                ["tour", "hold", "nl"],
                ["tour", "hold", "pl"],
                ["tour", "hold", "fl"],

                ["tour", "stud", "fl"],
                ["tour", "stud", "pl"],
                ["tour", "stud", "nl"],
                
                ["tour", "draw", "fl"],
                ["tour", "draw", "pl"],
                ["tour", "draw", "nl"],
                ]

    def parseHeader(self, handText, whole_file):
        gametype = self.determineGameType(handText)
        if gametype is None:
            gametype = self.determineGameType(whole_file)
            if gametype is None:
                if not re.search('<description', whole_file):
                    raise FpdbHandPartial("Partial hand history: No <desription> tag")
                else:
                    tmp = handText[0:200]
                    log.error(_("MergeToFpdb.determineGameType: '%s'") % tmp)
                    raise FpdbParseError
            else:
                if 'mix' in gametype and gametype['mix']!=None:
                    self.mergeMultigametypes(handText)
        return gametype        

    def determineGameType(self, handText):
        """return dict with keys/values:
    'type'       in ('ring', 'tour')
    'limitType'  in ('nl', 'cn', 'pl', 'cp', 'fl', 'hp')
    'base'       in ('hold', 'stud', 'draw')
    'category'   in ('holdem', 'omahahi', omahahilo', 'razz', 'studhi', 'studhilo', 'fivedraw', '27_1draw', '27_3draw', 'badugi')
    'hilo'       in ('h','l','s')
    'smallBlind' int?
    'bigBlind'   int?
    'smallBet'
    'bigBet'
    'currency'  in ('USD', 'EUR', 'T$', <countrycode>)
or None if we fail to get the info """

        m = self.re_GameInfo.search(handText)
        if not m: return None

        self.info = {}
        mg = m.groupdict()
        #print "DEBUG: mg: %s" % mg

        if 'LIMIT' in mg:
            self.info['limitType'] = self.limits[mg['LIMIT']]
        if 'GAME' in mg:
            if mg['GAME'] in self.mixes:
                self.info['mix'] = self.mixes[mg['GAME']]
                self.mergeMultigametypes(handText)
            else:
                (self.info['base'], self.info['category']) = self.games[mg['GAME']]
        if 'SB' in mg:
            self.info['sb'] = mg['SB']
        if 'BB' in mg:
            self.info['bb'] = mg['BB']
        self.info['secondGame'] = False
        if mg['blah'] is not None:
            if self.re_secondGame.search(mg['blah']):
                self.info['secondGame'] = True
        if ' Tournament' == mg['TYPE']:
            self.info['type'] = 'tour'
            self.info['currency'] = 'T$'
        else:
            self.info['type'] = 'ring'
            if self.re_PlayMoney.search(handText):
                self.info['currency'] = 'play'
            else:
                self.info['currency'] = 'USD'

        if self.info['limitType'] == 'fl' and self.info['bb'] is not None and self.info['type'] == 'ring':
            try:
                self.info['sb'] = self.Lim_Blinds[mg['BB']][0]
                self.info['bb'] = self.Lim_Blinds[mg['BB']][1]
            except KeyError:
                tmp = handText[0:200]
                log.error(_("MergeToFpdb.determineGameType: Lim_Blinds has no lookup for '%s' - '%s'") % (mg['BB'], tmp))
                raise FpdbParseError

        return self.info

    def readHandInfo(self, hand):
        m = self.re_HandInfo.search(hand.handText)
        if m is None:
            tmp = hand.handText[0:200]
            log.error(_("MergeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: mg: %s" % m.groupdict()
        self.determineErrorType(hand, None)

        hand.handid = m.group('HID1') + m.group('HID2')
              
        m1 = self.re_DateTime.search(m.group('DATETIME'))
        if m1:
            mg = m1.groupdict()
            datetimestr = "%s/%s/%s %s:%s:%s" % (mg['Y'], mg['M'],mg['D'],mg['H'],mg['MIN'],mg['S'])
            #tz = a.group('TZ')  # just assume ET??
            hand.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S") # also timezone at end, e.g. " ET"
        else:
            hand.startTime = datetime.datetime.strptime(m.group('DATETIME')[:14],'%Y%m%d%H%M%S')
            
        hand.startTime = HandHistoryConverter.changeTimezone(hand.startTime, "ET", "UTC")
        hand.newFormat = datetime.datetime.strptime('20100908000000','%Y%m%d%H%M%S')
        hand.newFormat = HandHistoryConverter.changeTimezone(hand.newFormat, "ET", "UTC")

        if hand.gametype['type'] == 'tour':
            tid_table = m.group('TDATA').split('-')
            tid = tid_table[0]
            if len(tid_table)>1:
                table = tid_table[1]
            else:
                table = '0'
            self.info['tablename'] = m.group('TABLENAME').replace('  - ', ' - ').strip()
            self.info['tourNo'] = hand.tourNo
            hand.tourNo = tid
            hand.tablename = table
            structure = self.Structures.lookupSnG(self.info['tablename'], hand.startTime)
            if structure!=None:
                hand.buyin = int(100*structure['buyIn'])
                hand.fee   = int(100*structure['fee'])
                hand.buyinCurrency=structure['currency']
                hand.maxseats = structure['seats']
                hand.isSng = True
                self.summaryInFile = True
            else:
                #print 'DEBUG', 'no match for tourney %s tourNo %s' % (self.info['tablename'], tid)
                hand.buyin = 0
                hand.fee = 0
                hand.buyinCurrency="NA"
                hand.maxseats = None
                if m.group('SEATS')!=None:
                    hand.maxseats = int(m.group('SEATS'))                    
        else:
            #log.debug("HID %s-%s, Table %s" % (m.group('HID1'), m.group('HID2'), m.group('TABLENAME')))
            hand.maxseats = None
            if  m.group('TABLENAME')!=None:
                hand.tablename = m.group('TABLENAME')
            else:
                hand.tablename = self.base_name
            if m.group('SEATS')!=None:
                hand.maxseats = int(m.group('SEATS')) 
        # Check that the hand is complete up to the awarding of the pot; if
        # not, the hand is unparseable
        if self.re_EndOfHand.search(hand.handText) is None:
            self.determineErrorType(hand, "readHandInfo")

    def readPlayerStacks(self, hand):
        acted = {}
        seated = {}
        m = self.re_PlayerInfo.finditer(hand.handText)
        for a in m:
            seatno = a.group('SEAT')
            seated[seatno] = [a.group('PNAME'), a.group('CASH')]

        if hand.gametype['type'] == "ring" :
            # We can't 100% trust the 'dealtin' field. So read the actions and see if the players acted
            m2 = self.re_AllActions.finditer(hand.handText)
            fulltable = False
            for action in m2:
                acted[action.group('PSEAT')] = True
                if acted.keys() == seated.keys(): # We've faound all players
                    fulltable = True
                    break
            if fulltable != True:
                for seatno in seated.keys():
                    if seatno not in acted:
                        del seated[seatno]

                for seatno in acted.keys():
                    if seatno not in seated:
                        log.error(_("MergeToFpdb.readPlayerStacks: '%s' Seat:%s acts but not listed") % (hand.handid, seatno))
                        raise FpdbParseError

        for seat in seated:
            name, stack = seated[seat]
            # Merge indexes seats from 0. Add 1 so we don't have to add corner cases everywhere else.
            hand.addPlayer(int(seat) + 1, name, stack)
            
        if hand.maxseats==None:
            if hand.gametype['type'] == 'tour' and self.maxseats==0:
                hand.maxseats = self.guessMaxSeats(hand)
                self.maxseats = hand.maxseats
            elif hand.gametype['type'] == 'tour':
                hand.maxseats = self.maxseats
            else:
                hand.maxseats = None

        # No players found at all.
        if not hand.players:
            self.determineErrorType(hand, "readPlayerStacks")

    def markStreets(self, hand):
        if hand.gametype['base'] == 'hold':
            m = re.search(r'<round id="PREFLOP" sequence="[0-9]+"\s?>(?P<PREFLOP>.+(?=<round id="POSTFLOP")|.+)'
                         r'(<round id="POSTFLOP" sequence="[0-9]+"\s?>(?P<FLOP>.+(?=<round id="POSTTURN")|.+))?'
                         r'(<round id="POSTTURN" sequence="[0-9]+"\s?>(?P<TURN>.+(?=<round id="POSTRIVER")|.+))?'
                         r'(<round id="POSTRIVER" sequence="[0-9]+"\s?>(?P<RIVER>.+))?', hand.handText, re.DOTALL)
        elif hand.gametype['base'] == 'draw':
            if hand.gametype['category'] in ('27_3draw','badugi','a5_3draw'):
                m =  re.search(r'(?P<PREDEAL>.+(?=<round id="PRE_FIRST_DRAW" sequence="[0-9]+">)|.+)'
                           r'(<round id="PRE_FIRST_DRAW" sequence="[0-9]+"\s?>(?P<DEAL>.+(?=<round id="FIRST_DRAW")|.+))?'
                           r'(<round id="FIRST_DRAW" sequence="[0-9]+"\s?>(?P<DRAWONE>.+(?=<round id="SECOND_DRAW")|.+))?'
                           r'(<round id="SECOND_DRAW" sequence="[0-9]+"\s?>(?P<DRAWTWO>.+(?=<round id="THIRD_DRAW")|.+))?'
                           r'(<round id="THIRD_DRAW" sequence="[0-9]+"\s?>(?P<DRAWTHREE>.+))?', hand.handText,re.DOTALL)
            else:
                m =  re.search(r'(?P<PREDEAL>.+(?=<round id="PRE_FIRST_DRAW" sequence="[0-9]+"\s?>)|.+)'
                           r'(<round id="PRE_FIRST_DRAW" sequence="[0-9]+"\s?>(?P<DEAL>.+(?=<round id="FIRST_DRAW")|.+))?'
                           r'(<round id="FIRST_DRAW" sequence="[0-9]+"\s?>(?P<DRAWONE>.+(?=<round id="SECOND_DRAW")|.+))?', hand.handText,re.DOTALL)
        elif hand.gametype['base'] == 'stud':
            m =  re.search(r'(?P<ANTES>.+(?=<round id="BRING_IN" sequence="[0-9]+"\s?>)|.+)'
                       r'(<round id="BRING_IN" sequence="[0-9]+"\s?>(?P<THIRD>.+(?=<round id="FOURTH_STREET")|.+))?'
                       r'(<round id="FOURTH_STREET" sequence="[0-9]+"\s?>(?P<FOURTH>.+(?=<round id="FIFTH_STREET")|.+))?'
                       r'(<round id="FIFTH_STREET" sequence="[0-9]+"\s?>(?P<FIFTH>.+(?=<round id="SIXTH_STREET")|.+))?'
                       r'(<round id="SIXTH_STREET" sequence="[0-9]+"\s?>(?P<SIXTH>.+(?=<round id="SEVENTH_STREET")|.+))?'
                       r'(<round id="SEVENTH_STREET" sequence="[0-9]+"\s?>(?P<SEVENTH>.+))?', hand.handText,re.DOTALL)
        if m == None:
            self.determineErrorType(hand, "markStreets")
        hand.addStreets(m)

    def readCommunityCards(self, hand, street):
        m = self.re_Board.search(hand.streets[street])
        if m and street in ('FLOP','TURN','RIVER'):
            if street == 'FLOP':
                hand.setCommunityCards(street, m.group('CARDS').split(','))
            elif street in ('TURN','RIVER'):
                hand.setCommunityCards(street, [m.group('CARDS').split(',')[-1]])
        else:
            self.determineErrorType(hand, "readCommunityCards")

    def readAntes(self, hand):
        for player in self.re_Antes.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(player.group('PSEAT'), hand)
            #print "DEBUG: hand.addAnte(%s,%s)" %(pname, player.group('ANTE'))
            self.adjustMergeTourneyStack(hand, pname, player.group('ANTE'))
            hand.addAnte(pname, player.group('ANTE'))

    def readBringIn(self, hand):
        m = self.re_BringIn.search(hand.handText)
        if m:
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            #print "DEBUG: hand.addBringIn(%s,%s)" %(pname, m.group('BRINGIN'))
            self.adjustMergeTourneyStack(hand, pname, m.group('BRINGIN'))
            hand.addBringIn(pname, m.group('BRINGIN'))
            
        if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
            hand.gametype['sb'] = "1"
            hand.gametype['bb'] = "2"

    def readBlinds(self, hand):
        if (hand.gametype['category'], hand.gametype['limitType']) == ("badugi", "hp"):
            if hand.gametype['sb'] == None and hand.gametype['bb'] == None:
                hand.gametype['sb'] = "1"
                hand.gametype['bb'] = "2"
        else:
            if hand.gametype['base'] == 'hold':
                street = 'PREFLOP'
            elif hand.gametype['base'] == 'draw':
                street = 'DEAL'
            allinBlinds = {}
            blindsantes = hand.handText.split(street)[0]
            bb, sb = None, None
            for a in self.re_PostSB.finditer(blindsantes):
                #print "DEBUG: found sb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('SB'))
                sb = a.group('SB')
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, sb)
                hand.addBlind(player,'small blind', sb)
                if not hand.gametype['sb'] or hand.gametype['secondGame']:
                    hand.gametype['sb'] = sb
            for a in self.re_PostBB.finditer(blindsantes):
                #print "DEBUG: found bb: '%s' '%s'" %(self.playerNameFromSeatNo(a.group('PSEAT'), hand), a.group('BB'))
                bb = a.group('BB')
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, bb)
                hand.addBlind(player, 'big blind', bb)
                if not hand.gametype['bb'] or hand.gametype['secondGame']:
                    hand.gametype['bb'] = bb
            for a in self.re_PostBoth.finditer(blindsantes):
                bb = Decimal(self.info['bb'])
                amount = Decimal(a.group('SBBB'))
                player = self.playerNameFromSeatNo(a.group('PSEAT'), hand)
                self.adjustMergeTourneyStack(hand, player, a.group('SBBB'))
                if amount < bb:
                    hand.addBlind(player, 'small blind', a.group('SBBB'))
                elif amount == bb:
                    hand.addBlind(player, 'big blind', a.group('SBBB'))
                else:
                    hand.addBlind(player, 'both', a.group('SBBB'))
            if sb is None or bb is None:
                m = self.re_Action.finditer(blindsantes)
                for action in m:
                    player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
                    #print "DEBUG: found: '%s' '%s'" %(self.playerNameFromSeatNo(action.group('PSEAT'), hand), action.group('BET'))
                    if sb is None:
                        if action.group('BET') and action.group('BET')!= '0.00':
                            sb = action.group('BET')  
                            self.adjustMergeTourneyStack(hand, player, sb)
                            hand.addBlind(player, 'small blind', sb)
                            if not hand.gametype['sb'] or hand.gametype['secondGame']:
                                hand.gametype['sb'] = sb
                        elif action.group('BET') == '0.00':
                            allinBlinds[player] = 'small blind'
                            #log.error(_(_("MergeToFpdb.readBlinds: Cannot calcualte tourney all-in blind for hand '%s'")) % hand.handid)
                            #raise FpdbParseError
                    elif sb and bb is None:
                        if action.group('BET') and action.group('BET')!= '0.00':
                            bb = action.group('BET')
                            self.adjustMergeTourneyStack(hand, player, bb)
                            hand.addBlind(player, 'big blind', bb)
                            if not hand.gametype['bb'] or hand.gametype['secondGame']:
                                hand.gametype['bb'] = bb
                        elif action.group('BET') == '0.00':
                            allinBlinds[player] = 'big blind'
                            #log.error(_(_("MergeToFpdb.readBlinds: Cannot calcualte tourney all-in blind for hand '%s'")) % hand.handid)
                            #raise FpdbParseError
            self.fixTourBlinds(hand, allinBlinds)

    def fixTourBlinds(self, hand, allinBlinds):
        # FIXME
        # The following should only trigger when a small blind is missing in a tournament, or the sb/bb is ALL_IN
        # see http://sourceforge.net/apps/mantisbt/fpdb/view.php?id=115
        if hand.gametype['type'] == 'tour' or hand.gametype['secondGame']:
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
            hand.sb = hand.gametype['sb']
            hand.bb = hand.gametype['bb']
            for player, blindtype in allinBlinds.iteritems():
                if blindtype=='big blind':
                    self.adjustMergeTourneyStack(hand, player, hand.bb)
                    hand.addBlind(player, 'big blind', hand.bb)
                else:
                    self.adjustMergeTourneyStack(hand, player, hand.sb)
                    hand.addBlind(player, 'small blind', hand.sb)
                    
    def mergeMultigametypes(self, handText):
        m2 = self.re_HandInfo.search(handText)
        if m2 is None:
            tmp = handText[0:200]
            log.error(_("MergeToFpdb.readHandInfo: '%s'") % tmp)
            raise FpdbParseError
        multigametype = m2.group('MULTIGAMETYPE1') if m2.group('MULTIGAMETYPE1') else m2.group('MULTIGAMETYPE2')
        if multigametype:
            try:
                (self.info['base'], self.info['category']) = self.Multigametypes[multigametype]
            except KeyError:
                tmp = handText[0:200]
                log.error(_("MergeToFpdb.determineGameType: Multigametypes has no lookup for '%s'") % multigametype)
                raise FpdbParseError
                    
    def adjustMergeTourneyStack(self, hand, player, amount):
        amount = Decimal(amount)
        if hand.gametype['type'] == 'tour':
            for p in hand.players:
                if p[1]==player:
                    stack  = Decimal(p[2])
                    stack += amount
                    p[2]   = str(stack)
            hand.stacks[player] += amount

    def readButton(self, hand):
        hand.buttonpos = int(self.re_Button.search(hand.handText).group('BUTTON'))
                    
    def readHoleCards(self, hand):
#    streets PREFLOP, PREDRAW, and THIRD are special cases beacause
#    we need to grab hero's cards
        herocards = []
        for street in ('PREFLOP', 'DEAL'):
            if street in hand.streets.keys():
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
#                    if m == None:
#                        hand.involved = False
#                    else:
                    hand.hero = self.playerNameFromSeatNo(found.group('PSEAT'), hand)
                    cards = found.group('CARDS').split(',')
                    hand.addHoleCards(street, hand.hero, closed=cards, shown=False, mucked=False, dealt=True)

        for street in hand.holeStreets:
            if hand.streets.has_key(street):
                if not hand.streets[street] or street in ('PREFLOP', 'DEAL') or hand.gametype['base'] == 'hold': continue  # already done these
                m = self.re_HeroCards.finditer(hand.streets[street])
                for found in m:
                    player = self.playerNameFromSeatNo(found.group('PSEAT'), hand)
                    if player in hand.stacks:
                        if found.group('CARDS') is None:
                            cards    = []
                            newcards = []
                            oldcards = []
                        else:
                            if hand.gametype['base'] == 'stud':
                                cards = found.group('CARDS').replace('null', '').split(',')
                                cards = [c for c in cards if c!='']
                                oldcards = cards[:-1]
                                newcards = [cards[-1]]
                            else:
                                cards = found.group('CARDS').split(',')
                                oldcards = cards
                                newcards = []
                        if street == 'THIRD' and len(cards) == 3: # hero in stud game
                            hand.hero = player
                            herocards = cards
                            hand.dealt.add(hand.hero) # need this for stud??
                            hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                        elif (cards != herocards and hand.gametype['base'] == 'stud'):
                            if hand.hero == player:
                                herocards = cards
                                hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                            elif (len(cards)<5):
                                if street == 'SEVENTH':
                                    oldcards = []
                                    newcards = []
                                hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)
                            elif (len(cards)==7):
                                for street in hand.holeStreets:
                                    hand.holecards[street][player] = [[], []]
                                hand.addHoleCards(street, player, closed=cards, open=[], shown=False, mucked=False, dealt=False)
                        elif (hand.gametype['base'] == 'draw'):
                            hand.addHoleCards(street, player, closed=oldcards, open=newcards, shown=False, mucked=False, dealt=False)

    def readAction(self, hand, street):
        #log.debug("readAction (%s)" % street)
        m = self.re_Action.finditer(hand.streets[street])
        for action in m:
            player = self.playerNameFromSeatNo(action.group('PSEAT'), hand)
            if player in hand.stacks and player not in hand.folded:
                if action.group('ATYPE') in ('FOLD', 'SIT_OUT'):
                    hand.addFold(street, player)
                elif action.group('ATYPE') == 'CHECK':
                    hand.addCheck(street, player)
                elif action.group('ATYPE') == 'CALL':
                    hand.addCall(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'RAISE':
                    if hand.startTime < hand.newFormat:
                        hand.addCallandRaise(street, player, action.group('BET'))
                    else:
                        hand.addRaiseTo(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'BET':
                    hand.addBet(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'ALL_IN' and action.group('BET') != None:
                    hand.addAllIn(street, player, action.group('BET'))
                elif action.group('ATYPE') == 'DRAW':
                    hand.addDiscard(street, player, action.group('TXT'))
                elif action.group('ATYPE') == 'COMPLETE':
                    if hand.gametype['base'] != 'stud':
                        hand.addRaiseTo(street, player, action.group('BET'))
                    else:
                        hand.addComplete( street, player, action.group('BET') )
                else:
                    log.debug(_("Unimplemented %s: '%s' '%s'") % ("readAction", action.group('PSEAT'), action.group('ATYPE')))

    def readShowdownActions(self, hand):
        pass

    def readCollectPot(self, hand):
        hand.setUncalledBets(True)
        for m in self.re_CollectPot.finditer(hand.handText):
            pname = self.playerNameFromSeatNo(m.group('PSEAT'), hand)
            if pname!=None:
                pot = m.group('POT')
                hand.addCollectPot(player=pname, pot=pot)

    def readShownCards(self, hand):
        for m in self.re_ShownCards.finditer(hand.handText):
            if m.group('CARDS') is not None:
                cards = m.group('CARDS')
                cards = m.group('CARDS').split(',')

                (shown, mucked) = (False, False)
                if m.group('SHOWED') == "SHOWN": shown = True
                elif m.group('SHOWED') == "MUCKED": mucked = True

                #print "DEBUG: hand.addShownCards(%s, %s, %s, %s)" %(cards, m.group('PNAME'), shown, mucked)
                hand.addShownCards(cards=cards, player=self.playerNameFromSeatNo(m.group('PSEAT'),hand), shown=shown, mucked=mucked)

    def determineErrorType(self, hand, function):
        message = False
        m = self.re_Connection.search(hand.handText)
        if m:
            message = _("Found %s. Hand missing information.") % m.group('TYPE')
        m = self.re_LeaveTable.search(hand.handText)
        if m:
            message = _("Found LEAVE. Player left table before hand completed")
        m = self.re_Cancelled.search(hand.handText)
        if m:
            message = _("Found CANCELLED")
        if message == False and function == "markStreets":
            message = _("Failed to identify all streets")
        if message == False and function == "readHandInfo":
            message = _("END_OF_HAND not found. No obvious reason")
        if message:
            raise FpdbHandPartial("Partial hand history: %s '%s' %s" % (function, hand.handid, message))

    @staticmethod
    def getTableTitleRe(type, table_name=None, tournament = None, table_number=None):
        "Returns string to search in windows titles"
        regex = re.escape(str(table_name))
        if type=="tour":
            # Ignoring table number as it doesn't appear to be in the window title
            # "$200 Freeroll - NL Holdem - 20:00 (46302299) - Table 1" -- the table number doesn't matter, it seems to always be 1 in the HH.
            # "Fun Step 1 (4358174) - Table 1"
            regex = re.escape(str(tournament))
        log.info("Merge.getTableTitleRe: table_name='%s' tournament='%s' table_number='%s'" % (table_name, tournament, table_number))
        log.info("Merge.getTableTitleRe: returns: '%s'" % (regex))
        return regex
