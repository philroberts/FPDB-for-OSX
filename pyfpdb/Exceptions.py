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

class FpdbHandPartial(FpdbHandError):
    pass
