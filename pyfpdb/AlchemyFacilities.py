#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2010 Grigorij Indigirkin
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

#TODO: gettextify if file is used again

from decimal_wrapper import Decimal

from sqlalchemy import types
from sqlalchemy.orm.exc import NoResultFound 
from sqlalchemy.exc import IntegrityError

import Card

class CardColumn(types.TypeDecorator):
    """Stores cards as smallints
    
    Automatically converts values like '9h' to smallint

    >>> CardColumn().process_bind_param( 'Td', '' )
    22
    >>> CardColumn().process_bind_param( u'Td', '' )
    22
    >>> CardColumn().process_bind_param( 22, '' )
    22
    >>> CardColumn().process_result_value( 22, '' )
    'Td'
    """

    impl = types.SmallInteger

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, int):
            return value
        elif isinstance(value, basestring) and len(value) == 2:
            return Card.encodeCard(str(value))
        else:
            raise Exception, "Incorrect card value: " + repr(value)

    def process_result_value(self, value, dialect):
        return Card.valueSuitFromCard( value )


class MoneyColumn(types.TypeDecorator):
    """Stores money: bets, pots, etc
    
    Understands: 
        Decimal as real amount
        int     as amount mupliplied by 100
        string  as decimal
    Returns Decimal
    >>> MoneyColumn().process_bind_param( 230, '' )
    230
    >>> MoneyColumn().process_bind_param( Decimal('2.30'), '' )
    230
    >>> MoneyColumn().process_bind_param( '2.30', '' )
    230
    >>> MoneyColumn().process_result_value( 230, '' )
    Decimal('2.3')
    """

    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, int):
            return value
        elif isinstance(value, basestring) or isinstance(value, Decimal): 
            return int(Decimal(value)*100)
        else:
            raise Exception, "Incorrect amount:" + repr(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(value)/100


class BigIntColumn(types.TypeDecorator, types.Integer): 
    """Representing db-independent big integer """
    # Integer inheritance required for auto_increment flag

    impl = types.Integer

    def load_dialect_impl(self, dialect):
        from sqlalchemy import databases
        if dialect.name == 'mysql':
            return databases.mysql.MSBigInteger()
        elif dialect.name == 'postgres':
            return databases.mysql.PGBigInteger()
        return types.Integer()


class MappedBase(object):
    """Provide dummy contrcutor"""

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def get_columns_names(self):
        return [i.name for i in self._sa_class_manager.mapper.c]

def get_or_create(klass, session, **kwargs):
    """ 
    Looks up an object with the given kwargs, creating one if necessary.
    Returns a tuple of (object, created), where created is a boolean
    specifying whether an object was created.
    """
    assert kwargs, \
            'get_or_create() must be passed at least one keyword argument'
    try:
        return session.query(klass).filter_by(**kwargs).one(), False
    except NoResultFound:
        try:
            obj = klass(**kwargs)
            session.add(obj)
            session.flush()
            return obj, True
        except IntegrityError:
            return session.query(klass).filter_by(**kwargs).one(), False

