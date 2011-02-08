aux to write fpdb data to player notes on Full Tilt
---------------------------------------------------

by Gimick 30th Dec 2010

RushNotesAux - auxillary processed attached to the full tilt hud 
                builds up fpdb notes "queue" for each villain met while the autoimport is running
                uses HUD aggregation stats to do this

RushNotesMerge - stand alone process to merge the existing ftp notes, together with queue
                 produced by Aux.
                the output file can then be renamed to become the new ftp notes file

Important info:
The Merge process can only be run when ftp client is shutdown
 - otherwise ftp overwrites the xml on exit.

Existing ftp notes _SHOULD_ be preserved, but this isn't guaranteed, 
 you have been warned!
 
Existing colour codings should be preserved, 
 this process does not change or set colourcodings.

Copies of the live ftp notes file should be preserved everytime
  RushNotesAux (i.e. the HUD is started).  If you play at different
  rush tables, the backup will be created several times.

The AW is hard-coded with just the table names of Micro Rush Poker, 
  and should ignore all other hands.

What might not work?
--------------------

This should work with windows sourcecode version, but will not work with the exe download.
Hasn't been tested for co-existance with other sites, feedback welcome.
Whenever FTP change their notes file format, this will all break rather spectacularly,
    you have been warned!
    
Getting started:
---------------

1. Set the Hero aggregation to alltime.  hero_stat_range="A" 
 This overcomes a sqlite "bug" which has nothing to do with auxillary windows
  not doing this will slow processing down to about 1 hand per minute.

2. Set the site_path to be the folder containing the FTP notes xml file
(on wine this is normally site_path="/home/blah/.wine/Program Files/Full Tilt Poker/")


Wire-up the aux process:
-----------------------

<aw class="RushNotes" module="RushNotesAux" name="Rush1"> </aw>
<game aux="Rush1" cols="3" db="fpdb" game_name="holdem" rows="3">

or whatever works for you.


Play some poker
---------------

Start Autoimport, and rearrange the on-screen stats out of the way
    (the full HUD must run, killing the HUD kills the AW updates)

Play whatever you want

Stop the autoimport

Exit the Full tilt poker client (ensure it has fully stopped with ps -A)

execute the following:

./pyfpdb/RushNotesMerge.py "/home/foo/.wine/drive_c/Program Files/Full Tilt Poker/myname.xml"

A revised notes file (blah.merge) should automagically appear in the full tilt root directory.
If you are happy with it, replace the existing (myname.xml file) and delete the .queue file.


Since the updates aren't real time, it would be ok to play the rush
    session with fpdb inactive, but before quitting any of the tables, 
    start the HUD and wait for it to catch-up processing all the hands played.


Summary
-------

This is very rough and ready, but it does what I set-out to achieve.  

All feedback welcome, and if this is useful as a basis for general notes
 processing in future, then thats great.

As I find bugs and make improvements, I will push to git.


Much more information below:
----------------------------

Background
----------

When playing rush poker, some sort of rudimentary HUD would answer simple questions 
like "is this allin overbet being made by a nit, or a maniac".  Although some 
notes may have been made previously, some statistics would help to backup the decision.

Currently fpdb cannot support rush because the HUD is always 1 hand or more 
behind the current action.

The only way to do this at the moment is to switch to GuiPlayerStats and make a quick 
enquiry by player name.  However, this effectively times you out of all other 
action if multitabling.

Full Tilt situation
-------------------

Full Tilt notes are stored in xml format ("hero.xml").  Previously these could 
be updated while the game was in progress, however, FullTilt now cache the
notes and write them out when the application exits.  This makes it impossible
to use the notes as a real-time HUD, and therefore real-time huds are now
forced to screen-scrape or poke around in the client memory.

Accepting this a limitation, this implementation updates the notes only once
the FullTilt client has been closed.  Obviously, the villain HUD stats are only
as at the end of the last session, however, it is hoped this is significantly
better than having nothing at all.  As the hero's hand history increases, the
notes should progressively mature in accuracy.

Preamble
--------

Note that this implementation was written purely to be "good enough" to work
for the author, and is not intended as package or production quality.  It 
is contributed as a starting point for others, or for experimental use.

Thanks to Ray Barker who gave a great deal of help throughout.


The implementation
-------------------

RushNotesAux is an fpdb auxilliary process, and is called for every hand
processed by autoimport.  Each villain has a note prepared based on the current
fpdb data, and this note (in XML format) is stored in a queue file.

Auxilliary windows were chosen because 
a) the author has limited fpdb and programming skill
b) the auxillary windows handler is well documented and supported
c) any code created has access to the full range of stats with little or no extra work
d) runs within the HUD, so the aggregation parameters are already available


Limitations
-----------

The notes are only regenerated if a hand is played against the villain.  The 
process does not "bulk load" notes based upon all the player stats in FPDB.

It is hoped that due to the relatively large hand volume and relatively small
 player pools, this limitation will be largely overcome after a few sessions
although there will obviously be a number of players with no fpdb note. 

The aggregation parameters used for the notes are based upon the HUD parameters.
 (with the exception of the hand-ranges, which uses its' own criteria (see source)

Stopping and starting the HUD will erase the previously created notes queue file.

The HUD must run, so the individual player popups need to be manually relocated.

Although hard-coded for micro RUSH tablenames, the auxilliary window  could
probably happily update notes of all cash and tournament players.

Process overview
----------------

1/ The HUD process is started.  
1.1/ when the first hand is received, a queue file is created if not already there, and 
a copy of the current live xml note file is created as a security backup.
2/ For every hand played, the auxillary window is called
3/ Based upon the players in the hand, fpdb will be interrogated
and key stats are formatted in xml-style and written out to a holding file.
4/ At the end of the session, the HUD is stopped and the poker client closed

5/ The user can then review the contents of the holding file.
6/ A process is begun to "merge" the holding file into the existing player notes
7/ A new "merged" file is created.  The process attempts to preserve any
existing notes, but this cannot be guaranteed.
8/ The user can review this merged file, and if they are happy, 
they replace the existing note file.
9/ Note that this process never updates the live notes file in situ, but
there is a risk that something goes wrong, and that existing notes could be destroyed.
10/ the queue file can be deleted to reduce re-processing next time.
