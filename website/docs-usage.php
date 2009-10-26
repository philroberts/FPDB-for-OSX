<?php

$PAGE_TITLE = 'Usage instructions';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Usage instructions</h1>

<p>Before you do this make sure you setup the dependencies, the database, user, tables and config file.<br>
<br>
Running it<br>
==========<br>
If you have python setup properly you can execute it by double clicking pyfpdb/fpdb.py.<br>
<br>
Note however that all error messages are currently only printed if you call it from a shell. It'll be much easier to diagnose possible problems (which are likely in alpha stage) if you run it from a shell. In Windows XP it seems to automatically open a shell window with the fpdb window where you can see the command line output.<br>
<br>
In Linux/MacOS/*BSD, e.g. if its in /home/sycamore/fpdb/, do this:<br>
cd /home/sycamore/fpdb/pyfpdb<br>
python fpdb.py<br>
<br>
That will start the main GUI.<br>
<br>
Have a look at the menus, the stuff that is marked todo is not yet implemented.<br>
<br>
The main things are the bulk importer and the table viewer. To use the importer open it from the menu (import files and directories). You can set a few options at the bottom, then select a folder or single file in the main are and click Import. Please report any errors by one of the contacts listed in readme-overview.txt.<br>
Currently this will block the interface, but you can open another instance of this program e.g. if you wanna play whilst a big import is running. <br>
<br>
Please check the output at the shell for errors, if there are any please get in touch by one of the methods listed in readme-overview.txt<br>
<br>
Table Viewer (tv)<br>
=================v
To use the table viewer open it from the menu, select the hand history file of the table you're at, and click the Import&Read&Refresh button. The abbreviations there are explained in abbreviations.txt, but feel free to ask. Note that most poker software will only create the file once the first hand you payed to play is finished.<br>
In each column there is either just the number (hand count for current stake, range of seats and type of game) or a percentage and the number of hands that this percentage is based on. For example, in W$@SD (won $ at shodown) the number in brackets is how many showdowns that player has seen.<br>
<br>
Reimporting<br>
===========<br>
Currently on most updates a reimport of the whole database is required. To do this open fpdb, click the menu Database and select Create/Recreate tables. Then import all your history files again.<br>
<br>
License<br>
=======
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

require 'footer.php';

?>
