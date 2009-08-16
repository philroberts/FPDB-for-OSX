class FPDBError(Exception):
    pass

class FpdbParseError(FPDBError): 
    def __init__(self,hid=None):
        self.hid = hid

