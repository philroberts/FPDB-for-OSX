Qt branch notes
===============

This is a port of fpdb to Qt (specifically, PyQt5).  It is a work in
progress.  Please
[report](https://github.com/philroberts/FPDB-for-OSX/issues) bugs or
missing features!  Note: despite the name of this repository, I have
been publishing windows builds with releases for a while now.

Why?
----

I use a mac.  To use the GTK version of fpdb, I need to install a
bunch of libraries, and install and run an X server.  This irks me.
There was recently some talk on the fpdb mailing list suggesting a
port to Qt would make Windows development easier too.

Another win is that it is now possible to build an OSX app for
distribution using pyinstaller.

How?
----

If you just want to try the prebuilt app, check the
[wiki](https://github.com/philroberts/FPDB-for-OSX/wiki/Initial-install).

Otherwise, read on:

Grab the code from this git branch.  Install dependencies - I use
macports to install things on mac.

I _believe_ these are the required packages:

py27-matplotlib, py27-pyqt5, py27-pyobjc-quartz.

A couple of the HH parsers (Merge and Winamax) require
py27-beautifulsoup.  I have not installed this package or tested those
parsers.

Macports should install everything else you need automagically.

Users on other platforms don't need the pyobjc stuff.

If you want all-in EV calculation, you'll also want pokereval and
pypokereval.  I had to build pypokereval myself to add python 2.7
support, so if you can't be bothered with that you'll want to
substitute the py26 versions of the above.

Next you'll have to run `sudo port select --set python python27` and
possibly `hash -r` in case your shell has the system python command
cached.

Now you should be able to start fpdb like this:
`./run_fpdb.py`

Caveats/Known Bugs
------------------

Almost all of the basic functionality has now been ported.  Exceptions:

* Configure -> HUD Stats Settings.  This probably merits a rework.
* Import -> Import through eMail/IMAP.  Is this solving a real problem?  I'll port this when someone tells me they use it.
* Cash -> Positional Stats.  This seems to replicate functionality available in Ring Player Stats.  Again, I'll port this when someone complains.
* Cash -> Stove.  This doesn't do anything useful anyway.
* Tournament -> Tourney Viewer.  Unless I'm missing something, this is not very functional yet anyway.

Please report any problems using the
[github issue tracker](https://github.com/philroberts/FPDB-for-OSX/issues).
