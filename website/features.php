<?php

$PAGE_TITLE = 'Features';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Features</h1>

<p>Backend, Distribution<br>
=====================<br>
- Choice of MySQL/InnoDB or PostgreSQL. (not tested on PostgreSQL)<br>
- It is possible to run the database on one PC, the importer on another, and then access the database with the table viewer or HUD from a third PC. (note: do NOT do this unencrypted over an untrusted network like your employer's LAN or the Internet!)<br>
<br>
Site/Game Support<br>
=================<br>
- Initially only full support for PS, FTP coming soon<br>
- Supports Holdem, Omaha Hi and Omaha Hi/Lo. Stud and Razz coming soon.<br>

- Supports No Limit, Pot Limit, Fixed Limit NL, Cap NL and Cap PL<br>
	Note that currently it does not display extra stats for NL/PL so usefulness is limited for these limit types. Suggestions welcome, I don't play these.<br>
- Supports ring/cash games, SnG/MTT coming soon<br>
<br>
Tableviewer (tv)<br>
===========<br>
Tv takes a history filename and loads the appropriate players' stats and displays them in a tabular format. These stats currently are:<br>
	- VPIP, PFR and Preflop 3B/4B (3B/4B is not quite correct I think)<br>

	- Raise and Fold % on flop, turn and river. Fold only counts hands when someone raised. This can be displayed per street or as one combined value each for aggression and folding.<br>
	- Number of hands this is based on.<br>
	- SD/F (aka WtSD, proportion of hands where player went to showdown after seeing flop)<br>
	- W$wSF (Won $ when seen Flop)<br>
	- W$@SD (Won $ at showdown)<br>
	For all stats it also displays how many hands this particular is based on</p>


            </div>

<?php

require 'footer.php';

?>
