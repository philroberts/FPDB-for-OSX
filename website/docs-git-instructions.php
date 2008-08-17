<?php

require dirname(__FILE__).'/config.php';

$PAGE_TITLE = 'Git Instructions';

require SITE_PATH.'header.php';
require SITE_PATH.'sidebar.php';

?>

            <div id="main">

                <h1>Git Instructions</h1>

<p>Hi, welcome to my minimal git guide for fpdb devs!<br>
I'll expand this on request, if you have any questions just send me a mail at steffen(at)sycamoretest.info.<br><br>

How to make a local git commit<br>
==============================<br>
go to the root of your fpdb directory and type:<br>
git-add--interactive<br>
If you added any new files press a and Enter, then type the number of your new file and press Enter twice. If you made any changes to existing files press u and enter. If you want to commit all changes press * and Enter twice. Press q to leave git-add--interactive.<br>
Then create a file for your commit message (I call it since_last_commit.txt) but don't add this to the repository. In the first line of this file put a summary of your changes. If you wish to you can also add in a revision number. My tree (the "central" or "official" repository) uses the format gitX where X is a running number, e.g. git91 is followed by git92. Then give some details of your changes, try to mention anything non-trivial and definitely any user-visible bug fixes. If the table design has been changed that has to be mentioned in the first line.<br>
Then run this:<br>
git-commit -F since_last_commit.txt <br>
<br>
todo: how to pull/push changes to/from me<br>
todo: git-diff, git-rm, git-mv<br>
<br>
License<br>
=======<br>
Trademarks of third parties have been used under Fair Use or similar laws.<br>
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

require SITE_PATH.'footer.php';

?>
