<?php

$PAGE_TITLE = 'Git Instructions';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Git Instructions</h1>

<p>Hi, welcome to my minimal git guide for fpdb devs!<br>
You can use a git version just as user as well of course, but as there are generally hardly tested it is not advised.<br>
I'll expand this on request, if you have any questions just send me a mail at steffen(at)sycamoretest.info. There's also a bunch of instructions at http://www.assembla.com/spaces/fpdb/trac_git_tool</p>

<h2>0. Getting it</h2>
<p>To get git for gentoo just do emerge git -av<br>
To get it for Windows go to http://code.google.com/p/msysgit/downloads/list and install it. 
<h2>1. Cloning the fpdb git tree</h2>
<p>Just create a new directory (lets say ~/fpdb/ ), go into it and type:<br>
git clone git://git.assembla.com/fpdb.git</p>
<h2>2. Making your changes</h2>
<p>You can use whatever you want to do edit the files. I personally use nedit and occassionally Eclipse.</p>
<h2>3. Making a (local) commit</h2>
<p>Unlike in svn you don't need to be online to make your commits. First we need to tell git what to commit, so go to the root of your fpdb directory and type:<br>
git-add--interactive<br>
Now press u and enter. It will display a list of all changed files. If you want to commit all files just press * and enter twice to return to the main menu. If you want to commit only certain ones press the number of the file and enter and repeat until you have all the files. Then press enter again to return to the main menu.<br>
If you added any new files press a and Enter, then type the number of your new file and press Enter twice. Press q to leave git-add--interactive.<br>
Now create a file for your commit message (I call it since_last_commit.txt) but don't add this to the repository. In the first line of this file put a summary of your changes. Then give some details of your changes, try to mention anything non-trivial and definitely any user-visible bug fixes.<br>
Then run this:<br>
git-commit -F since_last_commit.txt <br>
<h2>4a. Pushing the changes to your own public git tree</h2>
<p>Do this OR 4b, not both.<br>
todo</p>
<h2>4b. Preparing changeset for emailing/uploading</h2>
<p>Do this OR 4a, not both.<br>
todo</p>
<h2>5. Pulling updates from the main tree</h2>
<p>todo</p>
<h2>License</h2>
<p>Trademarks of third parties have been used under Fair Use or similar laws.<br>
<br>
Copyright 2008 Steffen Jobbagy-Felso<br>
Permission is granted to copy, distribute and/or modify this<br>
document under the terms of the GNU Free Documentation License,<br>
Version 1.2 as published by the Free Software Foundation; with<br>
no Invariant Sections, no Front-Cover Texts, and with no Back-Cover<br>
Texts. A copy of the license can be found in fdl-1.2.txt<br>
<br>
The program itself is licensed under AGPLv3, see agpl-3.0.txt</p>


            </div>

<?php

require 'footer.php';

?>
