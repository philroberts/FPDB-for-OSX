import objc
from Cocoa import *

app = NSApplication.sharedApplication()

objc.loadBundle("axlib", globals(), "build/Release/axlib.framework")
tm = tablemonitor.alloc().init()
tm.detectFakePS()
tm.doObserver()

class mycallback(tmcallback):
    def callback_event_(self, tablename, eventtype):
        print "foo", tablename, eventtype

mycb = mycallback.alloc().init()

tm.registerCallback_(mycb)
tm.runCallback()

app.run()
