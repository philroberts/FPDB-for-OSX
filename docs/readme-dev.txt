Hi,
This document is to serve as a little overview (later: full technical doc) for current and prospective developers with:
a) introduction into the code structure
b) organisational/legal things

What to do?
===========
- Anything you want.
- The most useful (because it's the most boring) would be to update print_hand.py, update the expected files (testdata/*.found.txt) and create more .found.txt to ensure import processing is running correctly.
- There's a list of various bugs, deficiencies and important missing features in known_bugs_and_planned_features.txt.
- In the main GUI there's various menu points marked with todo - all of these will have to be done eventually.

If you want to take a look at coding-style.txt.
Ideally use git (see git-instructions.txt for some commands) and let me know where to pull from, alternatively feel free to send patches or even just changed file in whatever code layout or naming convention you like best. I will, of course, still give you full credit.

Contact/Communication
=====================
If you start working on something please open a bug or feature request at sf to avoid someone else from doing the same
Please see readme-overview

Dependencies
============
Please let me know before you add any new dependencies and ensure that they are source-compatible between *nix and Windows

Code/File/Class Structure
=========================
Basically the code runs like this

fpdb.py	-> bulk importer tab (import_threaded.py) -> fpdb_import.py -> fpdb_parse_logic.py -> fpdb_save_to_db.py
or
fpdb.py	-> table viewer tab (table_viewer.py) (todo: -> libTableViewer)
		
All files call the simple methods that I just collected in fpdb_simple.py, to abstract the other files off the nitty gritty details as I was learning python.
I'm currently working on (amongst other things) integrating everything into the fpdb.py GUI with a view to allow easy creation of a CLI client, too.

Also see filelist.txt.

How to Commit
=============
Please make sure you read and accept the copyright policy as stated in this file. Then see git-instructions.txt. Don't get me wrong, I hate all this legalese, but unfortunately it's kinda necessary.

Copyright/Licensing
===================
Copyright by default is handled on a per-file basis. If you send in a patch or make a commit to an existing file it is done on the understanding that you transfer all rights (as far as legally possible in your jurisdiction) to the current copyright holder of that file, unless otherwise stated. If you create a new file please ensure to include a copyright and license statement.

The licenses used by this project are the AGPL3 for code and FDL1.2 for documentation. See readme-overview.txt for reasons and if you wish to use fpdb with different licensing.

Preferred File Formats
======================
Preferred: Where possible simple text-based formats, e.g. plain text (with Unix end of line char) or (X)HTML. Preferred picture format is PNG. IE-compability for HTML files is optional as IE was never meant to be a real web browser, if it were they would've implemented web standards.

Also good: Other free and open formats, e.g. ODF. 

Not good: Any format that doesn't have full documentation freely and publicly available with a proper license for anyone to implement it. Sadly, Microsoft has chosen not fulfil these requirements for ISO MS OOXML to become a truly open standard.

License (of this file)
=======
Trademarks of third parties have been used under Fair Use or similar laws.

Copyright 2008 Steffen Jobbagy-Felso
Permission is granted to copy, distribute and/or modify this
document under the terms of the GNU Free Documentation License,
Version 1.2 as published by the Free Software Foundation; with
no Invariant Sections, no Front-Cover Texts, and with no Back-Cover
Texts. A copy of the license can be found in fdl-1.2.txt

The program itself is licensed under AGPLv3, see agpl-3.0.txt
