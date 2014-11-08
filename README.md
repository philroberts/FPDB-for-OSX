Qt branch notes
===============

This is a port of fpdb to Qt (specifically, PyQt5).  It is a work in
progress.  Please
[report](https://github.com/philroberts/FPDB-for-OSX/issues) bugs or
missing features!

Why?
----

I use a mac.  To use the GTK version of fpdb, I need to install a
bunch of libraries, and install and run an X server.  This irks me.
There was recently some talk on the fpdb mailing list suggesting a
port to Qt would make Windows development easier too.

Another win is that it should now be possible to build an OSX app for
distribution using pyinstaller.  This is almost, but not quite, ready
for an alpha release.

How?
----

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

Next you'll have to run `port select --set python python27` and
possibly `hash -r` in case your shell has the system python command
cached.

Now you should be able to start fpdb like this:
`run_fpdb.py`

Caveats/Known Bugs
------------------

Too many to list.  This should be considered alpha software at best.
Please report any problems using the
[github issue tracker](https://github.com/philroberts/FPDB-for-OSX/issues).
