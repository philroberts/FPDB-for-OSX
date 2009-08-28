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
        if hid:
            return repr("HID:"+hid+", "+self.value)
        else:
            return repr(self.value)

class DuplicateError(FpdbError):
    pass
