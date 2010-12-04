# -*- coding: utf-8 -*-

# Code from http://ender.snowburst.org:4747/~jjohns/interlocks.py
# Thanks JJ!

import L10n
_ = L10n.get_translation()

import sys
import os, os.path
import subprocess
import time
import signal
import base64

InterProcessLock = None

"""
Just use me like a thread lock.  acquire() / release() / locked()

Differences compared to thread locks:
1. By default, acquire()'s wait parameter is false.
2. When acquire fails, SingleInstanceError is thrown instead of simply returning false.
3. acquire() can take a 3rd parameter retry_time, which, if wait is True, tells the locking 
   mechanism how long to sleep between retrying the lock.  Has no effect for unix/InterProcessLockFcntl.

Differences in fpdb version to JJ's original:
1. Changed acquire() to return false like other locks
2. Made acquire fail if same process already has the lock
"""

class SingleInstanceError(RuntimeError):
    "Thrown when you try to acquire an InterProcessLock and another version of the process is already running."

class InterProcessLockBase:
    def __init__(self, name=None ):
        self._has_lock = False
        if not name:
            name = sys.argv[0]
        self.name = name
        self.heldBy = None

    def getHashedName(self):
        return base64.b64encode(self.name).replace('=','')

    def acquire_impl(self, wait): abstract
        
    def acquire(self, source, wait=False, retry_time=1):
        if source == None:
            source="Unknown"
        if self._has_lock:             # make sure 2nd acquire in same process fails
            print _("lock already held by:"),self.heldBy
            return False
        while not self._has_lock:
            try:
                self.acquire_impl(wait)
                self._has_lock = True
                self.heldBy=source
                #print 'i have the lock'
            except SingleInstanceError:
                if not wait:
                    # raise            # change back to normal acquire functionality, sorry JJ!
                    return False
                time.sleep(retry_time)
        return True

    def release(self):
        self.release_impl()
        self._has_lock = False
        self.heldBy=None

    def locked(self):
        if self.acquire():
            self.release()
            return False
        return True    

LOCK_FILE_DIRECTORY = '/tmp'

class InterProcessLockFcntl(InterProcessLockBase):
    def __init__(self, name=None):
        InterProcessLockBase.__init__(self, name)
        self.lockfd = 0
        self.lock_file_name = os.path.join(LOCK_FILE_DIRECTORY, self.getHashedName() + '.lck')
        assert(os.path.isdir(LOCK_FILE_DIRECTORY))

    # This is the suggested way to get a safe file name, but I like having a descriptively named lock file.
    def getHashedName(self):
        import re
        bad_filename_character_re = re.compile(r'/\?<>\\\:;\*\|\'\"\^=\.\[\]')
        return bad_filename_character_re.sub('_',self.name)

    def acquire_impl(self, wait):
        self.lockfd = open(self.lock_file_name, 'w')
        fcntrl_options = fcntl.LOCK_EX
        if not wait:
            fcntrl_options |= fcntl.LOCK_NB
        try:
            fcntl.flock(self.lockfd, fcntrl_options)
        except IOError:
            self.lockfd.close()
            self.lockfd = 0
            raise SingleInstanceError('Could not acquire exclusive lock on '+self.lock_file_name)
            
    def release_impl(self):
        fcntl.lockf(self.lockfd, fcntl.LOCK_UN)
        self.lockfd.close()
        self.lockfd = 0
        try:
            os.unlink(self.lock_file_name)
        except IOError:
            # We don't care about the existence of the file too much here.  It's the flock() we care about,
            # And that should just go away magically.
            pass

class InterProcessLockWin32(InterProcessLockBase):
    def __init__(self, name=None):
        InterProcessLockBase.__init__(self, name)        
        self.mutex = None
            
    def acquire_impl(self,wait):
        self.mutex = win32event.CreateMutex(None, 0, self.getHashedName())
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            self.mutex.Close()
            self.mutex = None
            raise SingleInstanceError('Could not acquire exclusive lock on ' + self.name)
            
    def release_impl(self):
        self.mutex.Close()
        
class InterProcessLockSocket(InterProcessLockBase):
    def __init__(self, name=None):
        InterProcessLockBase.__init__(self, name)        
        self.socket = None
        self.portno = 65530 - abs(self.getHashedName().__hash__()) % 32749
        
    def acquire_impl(self, wait):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind(('127.0.0.1', self.portno))
        except socket.error:
            self.socket.close()
            self.socket = None
            raise SingleInstanceError('Could not acquire exclusive lock on ' + self.name)
        
    def release_impl(self):
        self.socket.close()
        self.socket = None

# Set InterProcessLock to the correct type given the sysem parameters available
try:
    import fcntl
    InterProcessLock = InterProcessLockFcntl
except ImportError:
    try:
        import win32event
        import win32api
        import winerror
        InterProcessLock = InterProcessLockWin32
    except ImportError:
        import socket
        InterProcessLock = InterProcessLockSocket

def test_construct():
    """
    # Making the name of the test unique so it can be executed my multiple users on the same machine.
    >>> test_name = 'InterProcessLockTest' +str(os.getpid()) + str(time.time())

    >>> lock1 = InterProcessLock(name=test_name)
    >>> lock1.acquire()
    True

    >>> lock2 = InterProcessLock(name=test_name)
    >>> lock3 = InterProcessLock(name=test_name)

    # Since lock1 is locked, other attempts to acquire it fail.
    >>> lock2.acquire()
    False

    >>> lock3.acquire()
    False

    # Release the lock and let lock2 have it.
    >>> lock1.release()
    >>> lock2.acquire()
    True

    >>> lock3.acquire()
    False

    # Release it and give it back to lock1
    >>> lock2.release()
    >>> lock1.acquire()
    True

    >>> lock2.acquire()
    False

    # Test lock status
    >>> lock2.locked()
    True
    >>> lock3.locked()
    True
    >>> lock1.locked()
    True

    >>> lock1.release()

    >>> lock2.locked()
    False
    >>> lock3.locked()
    False
    >>> lock1.locked()
    False

    >>> if os.name == 'posix':
    ...    def os_independent_kill(pid):
    ...        import signal
    ...        os.kill(pid, signal.SIGKILL)
    ... else:
    ...        assert(os.name == 'nt')
    ...        def os_independent_kill(pid):
    ...            ''' http://www.python.org/doc/faq/windows/#how-do-i-emulate-os-kill-in-windows '''
    ...            import win32api
    ...            import win32con
    ...            import pywintypes
    ...            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE , pywintypes.FALSE, pid)
    ...            #return (0 != win32api.TerminateProcess(handle, 0))

    # Test to acquire the lock in another process.
    >>> def execute(cmd):
    ...    cmd = 'import time;' + cmd + 'time.sleep(10);'
    ...    process = subprocess.Popen([sys.executable, '-c', cmd])
    ...    pid = process.pid
    ...    time.sleep(2) # quick hack, but we test synchronization in the end
    ...    return pid

    >>> pid = execute('import interlocks;a=interlocks.InterProcessLock(name=\\''+test_name+ '\\');a.acquire();')

    >>> lock1.acquire()
    False

    >>> os_independent_kill(pid)

    >>> time.sleep(1)

    >>> lock1.acquire()
    True
    >>> lock1.release()

    # Testing wait

    >>> pid = execute('import interlocks;a=interlocks.InterProcessLock(name=\\''+test_name+ '\\');a.acquire();')

    >>> lock1.acquire()
    False

    >>> os_independent_kill(pid)

    >>> lock1.acquire(True)
    True
    >>> lock1.release()

    """
    
    pass

if __name__=='__main__':
    import doctest
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
