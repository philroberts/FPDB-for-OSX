class FpdbParseError(Exception): 
    def __init__(self,hid=None):
        self.hid = hid

