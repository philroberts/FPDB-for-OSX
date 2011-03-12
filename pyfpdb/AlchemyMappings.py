#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Grigorij Indigirkin
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

"""@package AlchemyMappings
This package contains all classes to be mapped and mappers themselves
"""

#TODO: gettextify if file is used again

import logging
import re
from decimal_wrapper import Decimal
from sqlalchemy.orm import mapper, relation, reconstructor
from sqlalchemy.sql import select
from collections import defaultdict


from AlchemyTables import *
from AlchemyFacilities import get_or_create, MappedBase
from DerivedStats import DerivedStats
from Exceptions import IncompleteHandError, FpdbError


class Player(MappedBase):
    """Class reflecting Players db table"""

    @staticmethod
    def get_or_create(session, siteId, name):
        return get_or_create(Player, session, siteId=siteId, name=name)[0]

    def __str__(self):
        return '<Player "%s" on %s>' % (self.name, self.site and self.site.name)


class Gametype(MappedBase):
    """Class reflecting Gametypes db table"""

    @staticmethod
    def get_or_create(session, siteId, gametype):
        map = zip(
            ['type', 'base', 'category', 'limitType', 'smallBlind', 'bigBlind', 'smallBet', 'bigBet', 'currency'],
            ['type', 'base', 'category', 'limitType', 'sb', 'bb', 'dummy', 'dummy', 'currency'])
        gametype = dict([(new, gametype.get(old)) for new, old in map  ])

        hilo = "h"
        if gametype['category'] in ('studhilo', 'omahahilo'):
            hilo = "s"
        elif gametype['category'] in ('razz','27_3draw','badugi'):
            hilo = "l"
        gametype['hiLo'] = hilo

        for f in ['smallBlind', 'bigBlind', 'smallBet', 'bigBet']:
            if gametype[f] is None: 
                gametype[f] = 0
            gametype[f] = int(Decimal(gametype[f])*100)

        gametype['siteId'] = siteId
        return get_or_create(Gametype, session, **gametype)[0]


class HandActions(object):
    """Class reflecting HandsActions db table"""
    def initFromImportedHand(self, hand, actions):
        self.hand = hand
        self.actions = {}
        for street, street_actions in actions.iteritems():
            self.actions[street] = []
            for v in street_actions:
                hp = hand.handplayers_by_name[v[0]]
                self.actions[street].append({'street': street, 'pid': hp.id, 'seat': hp.seatNo, 'action':v})

    @property
    def flat_actions(self):
        actions = []
        for street in self.hand.allStreets:
            actions += self.actions[street]
        return actions



class HandInternal(DerivedStats):
    """Class reflecting Hands db table"""

    def parseImportedHandStep1(self, hand):
        """Extracts values to insert into from hand returned by HHC. No db is needed he"""
        hand.players = hand.getAlivePlayers() 

        # also save some data for step2. Those fields aren't in Hands table
        self.siteId = hand.siteId 
        self.gametype_dict = hand.gametype 

        self.attachHandPlayers(hand)
        self.attachActions(hand) 

        self.assembleHands(hand)
        self.assembleHandsPlayers(hand)

    def parseImportedHandStep2(self, session):
        """Fetching ids for gametypes and players"""
        gametype = Gametype.get_or_create(session, self.siteId, self.gametype_dict)
        self.gametypeId = gametype.id
        for hp in self.handPlayers:
            hp.playerId = Player.get_or_create(session, self.siteId, hp.name).id

    def getPlayerByName(self, name):
        if not hasattr(self, 'handplayers_by_name'):
            self.handplayers_by_name = {}
            for hp in self.handPlayers:
                pname = getattr(hp, 'name', None) or hp.player.name
                self.handplayers_by_name[pname] = hp
        return self.handplayers_by_name[name]

    def attachHandPlayers(self, hand):
        """Fill HandInternal.handPlayers list. Create self.handplayers_by_name"""
        hand.noSb = getattr(hand, 'noSb', None)
        if hand.noSb is None and self.gametype_dict['base']=='hold':
            saw_sb = False
            for action in hand.actions[hand.actionStreets[0]]: # blindsantes
                if action[1] == 'posts' and action[2] == 'small blind' and action[0] is not None:
                    saw_sb = True
            hand.noSb = saw_sb

        self.handplayers_by_name = {}
        for seat, name, chips in hand.players:
            p = HandPlayer(hand = self, imported_hand=hand, seatNo=seat, 
                           name=name, startCash=chips)         
            self.handplayers_by_name[name] = p
        
    def attachActions(self, hand):
        """Create HandActions object"""
        a = HandActions()
        a.initFromImportedHand(self, hand.actions)

    def parseImportedTournament(self, hand, session):
        """Fetching tourney, its type and players
        
        Must be called after Step2
        """
        if self.gametype_dict['type'] != 'tour': return

        # check for consistense
        for i in ('buyin', 'tourNo'):
            if not hasattr(hand, i):
                raise IncompleteHandError( 
                    "Field '%s' required for tournaments" % i, self.id, hand )

        # repair old-style buyin value
        m = re.match('\$(\d+)\+\$(\d+)', hand.buyin)
        if m is not None:
            hand.buyin, self.fee = m.groups()

        # fetch tourney type
        tour_type_hand2db = {
            'buyin':         'buyin',
            'fee':           'fee',
            'speed':         'speed',
            'maxSeats':      'maxseats',
            'knockout':      'isKO',
            'rebuy':         'isRebuy',
            'addOn':         'isAddOn',
            'shootout':      'isShootout',
            'matrix':        'isMatrix',
            'sng':           'isSNG',
        }
        tour_type_index = dict([
                    ( i_db, getattr(hand, i_hand, None) )
                    for i_db, i_hand in tour_type_hand2db.iteritems() 
                ])
        tour_type_index['siteId'] = self.siteId
        tour_type = TourneyType.get_or_create(session, **tour_type_index)

        # fetch and update tourney
        tour  = Tourney.get_or_create(session, hand.tourNo, tour_type.id)
        cols = tour.get_columns_names()
        for col in cols:
            hand_val = getattr(hand, col, None)
            if col in ('id', 'tourneyTypeId', 'comment', 'commentTs') or hand_val is None:
                continue
            db_val = getattr(tour, col, None)
            if db_val is None:
                setattr(tour, col, hand_val)
            elif col == 'koBounty':
                setattr(tour, col, max(db_val, hand_val))
            elif col == 'tourStartTime' and hand.startTime:
                setattr(tour, col, min(db_val, hand.startTime))

        if tour.entries is None and tour_type.sng:
            tour.entries = tour_type.maxSeats

        # fetch and update tourney players
        for hp in self.handPlayers:
            tp = TourneysPlayer.get_or_create(session, tour.id, hp.playerId)
            # FIXME: other TourneysPlayers should be added here

        session.flush()

    def isDuplicate(self, session):
        """Checks if current hand already exists in db
        
        siteHandNo ans gametypeId have to be setted
        """
        return session.query(HandInternal).filter_by(
                siteHandNo=self.siteHandNo, gametypeId=self.gametypeId).count()!=0

    def __str__(self):
        s = list()
        for i in self._sa_class_manager.mapper.c:
            s.append('%25s     %s' % (i, getattr(self, i.name)))

        s+=['', '']
        for i,p in enumerate(self.handPlayers):
            s.append('%d. %s' % (i, p.name or '???'))
            s.append(str(p))
        return '\n'.join(s)

    @property
    def boardcards(self):
        cards = []
        for i in range(5):
            cards.append(getattr(self, 'boardcard%d' % (i+1), None))
        return filter(bool, cards)

    @property
    def HandClass(self):
        """Return HoldemOmahaHand or something like this"""
        import Hand
        if self.gametype.base == 'hold':
            return Hand.HoldemOmahaHand
        elif self.gametype.base == 'draw':
            return Hand.DrawHand
        elif self.gametype.base == 'stud':
            return Hand.StudHand
        raise Exception("Unknow gametype.base: '%s'" % self.gametype.base)

    @property
    def allStreets(self):
        return self.HandClass.allStreets

    @property
    def actionStreets(self):
        return self.HandClass.actionStreets



class HandPlayer(MappedBase):
    """Class reflecting HandsPlayers db table"""
    def __init__(self, **kwargs):
        if 'imported_hand' in kwargs and 'seatNo' in kwargs:
            imported_hand = kwargs.pop('imported_hand')
            self.position = self.getPosition(imported_hand, kwargs['seatNo'])
        super(HandPlayer, self).__init__(**kwargs)

    @reconstructor
    def init_on_load(self):
        self.name = self.player.name

    @staticmethod
    def getPosition(hand, seat):
        """Returns position value like 'B', 'S', '0', '1', ...

        >>> class A(object): pass
        ... 
        >>> A.noSb = False
        >>> A.maxseats = 6
        >>> A.buttonpos = 2
        >>> A.gametype = {'base': 'hold'}
        >>> A.players = [(i, None, None) for i in (2, 4, 5, 6)]
        >>> HandPlayer.getPosition(A, 6) # cut off
        '1'
        >>> HandPlayer.getPosition(A, 2) # button
        '0'
        >>> HandPlayer.getPosition(A, 4) # SB
        'S'
        >>> HandPlayer.getPosition(A, 5) # BB
        'B'
        >>> A.noSb = True
        >>> HandPlayer.getPosition(A, 5) # MP3
        '2'
        >>> HandPlayer.getPosition(A, 6) # cut off
        '1'
        >>> HandPlayer.getPosition(A, 2) # button
        '0'
        >>> HandPlayer.getPosition(A, 4) # BB
        'B'
        """
        from itertools import chain
        if hand.gametype['base'] == 'stud':
            # FIXME: i've never played stud so plz check & del comment \\grindi
            bringin = None
            for action in chain(*[self.actions[street] for street in hand.allStreets]):
                if action[1]=='bringin':
                    bringin = action[0]
                    break
            if bringin is None:
                raise Exception, "Cannot find bringin"
            # name -> seat
            bringin = int(filter(lambda p: p[1]==bringin, bringin)[0])
            seat = (int(seat) - int(bringin))%int(hand.maxseats)
            return str(seat)
        else:
            seats_occupied = sorted([seat_ for seat_, name, chips in hand.players], key=int)
            if hand.buttonpos not in seats_occupied:
                # i.e. something like
                # Seat 3: PlayerX ($0), is sitting out
                # The button is in seat #3
                hand.buttonpos = max(seats_occupied, 
                                     key = lambda s: int(s) 
                                        if int(s) <= int(hand.buttonpos) 
                                        else int(s) - int(hand.maxseats)
                                    )
            seats_occupied = sorted(seats_occupied, 
                    key = lambda seat_: (
                        - seats_occupied.index(seat_) 
                        + seats_occupied.index(hand.buttonpos) 
                        + 2) % len(seats_occupied)
                    )
            # now (if SB presents) seats_occupied contains seats in order: BB, SB, BU, CO, MP3, ...
            if hand.noSb:
                # fix order in the case nosb
                seats_occupied = seats_occupied[1:] + seats_occupied[0:1]
                seats_occupied.insert(1, -1)
            seat = seats_occupied.index(seat)
            if seat == 0:
                return 'B'
            elif seat == 1:
                return 'S'
            else:
                return str(seat-2)

    @property
    def cards(self):
        cards = []
        for i in range(7):
            cards.append(getattr(self, 'card%d' % (i+1), None))
        return filter(bool, cards)

    def __str__(self):
        s = list()
        for i in self._sa_class_manager.mapper.c:
            s.append('%45s     %s' % (i, getattr(self, i.name)))
        return '\n'.join(s)


class Site(object):
    """Class reflecting Players db table"""
    INITIAL_DATA = [
            (1 , 'Full Tilt Poker','FT'),
            (2 , 'PokerStars',     'PS'),
            (3 , 'Everleaf',       'EV'),
            (4 , 'Win2day',        'W2'),
            (5 , 'OnGame',         'OG'),
            (6 , 'UltimateBet',    'UB'),
            (7 , 'Betfair',        'BF'),
            (8 , 'Absolute',       'AB'),
            (9 , 'PartyPoker',     'PP'),
            (10, 'Partouche',      'PA'),
            (11, 'Carbon',         'CA'),
            (12, 'PKR',            'PK'),
            (13, 'PacificPoker',            'P8'),
        ]
    INITIAL_DATA_KEYS = ('id', 'name', 'code')

    INITIAL_DATA_DICTS = [ dict(zip(INITIAL_DATA_KEYS, datum)) for datum in INITIAL_DATA ] 

    @classmethod
    def insert_initial(cls, connection):
        connection.execute(sites_table.insert(), cls.INITIAL_DATA_DICTS)


class Tourney(MappedBase):
    """Class reflecting Tourneys db table"""

    @classmethod
    def get_or_create(cls, session, siteTourneyNo, tourneyTypeId):
        """Fetch tourney by index or creates one if none.  """
        return get_or_create(cls, session, siteTourneyNo=siteTourneyNo, 
                                tourneyTypeId=tourneyTypeId)[0]
    


class TourneyType(MappedBase):
    """Class reflecting TourneyType db table"""

    @classmethod
    def get_or_create(cls, session, **kwargs):
        """Fetch tourney type by index or creates one if none

        Required kwargs: 
            buyin fee speed maxSeats knockout 
            rebuy addOn shootout matrix sng currency
        """
        return get_or_create(cls, session, **kwargs)[0]


class TourneysPlayer(MappedBase):
    """Class reflecting TourneysPlayers db table"""

    @classmethod
    def get_or_create(cls, session, tourneyId, playerId):
        """Fetch tourney player by index or creates one if none """
        return get_or_create(cls, session, tourneyId=tourneyId, playerId=playerId)


class Version(object):
    """Provides read/write access for version var"""
    CURRENT_VERSION = 120 # db version for current release
    # 119 - first alchemy version
    # 120 - add m_factor

    conn = None 
    ver  = None
    def __init__(self, connection=None):
        if self.__class__.conn is None:
            self.__class__.conn = connection

    @classmethod
    def is_wrong(cls):
        return cls.get() != cls.CURRENT_VERSION

    @classmethod
    def get(cls):
        if cls.ver is None:
            try:
                cls.ver = cls.conn.execute(select(['version'], settings_table)).fetchone()[0]
            except:
                return None
        return cls.ver

    @classmethod
    def set(cls, value):
        if cls.conn.execute(settings_table.select()).rowcount==0:
            cls.conn.execute(settings_table.insert(), version=value)
        else:
            cls.conn.execute(settings_table.update().values(version=value))
        cls.ver = value
    
    @classmethod
    def set_initial(cls):
        cls.set(cls.CURRENT_VERSION)


mapper (Gametype, gametypes_table, properties={
    'hands': relation(HandInternal, backref='gametype'),
})
mapper (Player, players_table, properties={
    'playerHands': relation(HandPlayer, backref='player'),
    'playerTourney': relation(TourneysPlayer, backref='player'),
})
mapper (Site, sites_table, properties={
    'gametypes': relation(Gametype, backref = 'site'),
    'players': relation(Player, backref = 'site'),
    'tourneyTypes': relation(TourneyType, backref = 'site'),
})
mapper (HandActions, hands_actions_table, properties={})
mapper (HandInternal, hands_table, properties={
    'handPlayers': relation(HandPlayer, backref='hand'),
    'actions_all':     relation(HandActions, backref='hand', uselist=False),
})
mapper (HandPlayer, hands_players_table, properties={})

mapper (Tourney, tourneys_table) 
mapper (TourneyType, tourney_types_table, properties={
    'tourneys': relation(Tourney, backref='type'),
})
mapper (TourneysPlayer, tourneys_players_table) 

class LambdaKeyDict(defaultdict):
    """Operates like defaultdict but passes key argument to the factory function"""
    def __missing__(key):
        return self.default_factory(key)

