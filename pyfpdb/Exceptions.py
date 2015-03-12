#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2009-2011 Matt Turnbull 
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

class FpdbError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FpdbParseError(FpdbError):
    def __init__(self,value='',hid=''):
        self.value = value
        self.hid = hid
    def __str__(self):
        if self.hid:
            return repr("HID:"+self.hid+", "+self.value)
        else:
            return repr(self.value)

class FpdbDatabaseError(FpdbError):
    pass

class FpdbMySQLError(FpdbDatabaseError):
    pass

class FpdbMySQLAccessDenied(FpdbDatabaseError):
    def __init__(self, value='', errmsg=''):
        self.value = value
        self.errmsg = errmsg
    def __str__(self):
        return repr(self.value +" " + self.errmsg)

class FpdbMySQLNoDatabase(FpdbDatabaseError):
    def __init__(self, value='', errmsg=''):
        self.value = value
        self.errmsg = errmsg
    def __str__(self):
        return repr(self.value +" " + self.errmsg)

class FpdbPostgresqlAccessDenied(FpdbDatabaseError):
    def __init__(self, value='', errmsg=''):
        self.value = value
        self.errmsg = errmsg
    def __str__(self):
        return repr(self.value +" " + self.errmsg)

class FpdbPostgresqlNoDatabase(FpdbDatabaseError):
    def __init__(self, value='', errmsg=''):
        self.value = value
        self.errmsg = errmsg
    def __str__(self):
        return repr(self.value +" " + self.errmsg)

class FpdbHandError(FpdbError):
    pass

class FpdbHandDuplicate(FpdbHandError):
    pass

class FpdbHandPartial(FpdbParseError):
    pass

class FpdbHandSkipped(FpdbParseError):
    pass

class FpdbEndOfFile(FpdbHandError):
    pass
