<?php

$PAGE_TITLE = 'Requirements';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Requirements</h1>
<p>
I recommend using a free/libre operating system, meaning a GNU/Linux distribution or a BSD variant (e.g. Gentoo GNU/Linux or OpenBSD) for ethical and practical reasons. Would you buy a car where you're prohibited from opening the bonnet under threat of jail? If the answer is no you should by the same logic not use closed source software for real money Poker :)<br>
<br>
Unfortunately you will always need one piece of unfree software: The poker client itself. Although not a direct dependency of fpdb you obviously will have a hard time putting this to productive use without running some poker client. As far as I know, only unfree clients are available. If you know better please let me know!<br>
<br>
If you can be bothered please do contact your poker site(s) and ask them to release free/libre clients, even if it is only for Windows. But lets be realistic, the chance of a positive answer is very low. Also, even unfree Linux client would of course be a great step forward<br>
<br>
In Windows use of the environment installer is recommended, pls see our sf download page. For Gentoo Linux we have an ebuild and for Ubuntu Linux we have (partial) instructions. If you use a different Linux or a BSD and have trouble please IM, email or post in the forums. Fpdb has been reported to work on MacOSX, but installation of the requirements is relatively painful. Any instructions for people to use would be much appreciated.<br>
<br>
Make new entries in this format:<br>
<b>Program Name</b><br>
a. Optional?<br>
b. Required Version and Why<br>
c. Project Webpage<br>
d. License</p>
<h2>Database backend - MySQL</h2>
<p>These two are required if you want to use MySQL as backend, which is the recommended choice due to lack of testing and polish of PostgreSQL support.</p>
<p><b>MySQL</b><br>
a. Optional?<br>
	Choose MySQL or PostgreSQL<br>
b. Required Version and Why<br>
	At least 3.23 required due to mysql-python.<br>
	I use 5.0.54 and 5.0.60-r1 (GNU/Linux) and 5.0.51b (Windows).<br>
c. Project Webpage<br>
	http://www.mysql.com<br>
d. License<br>
	GPL2<br>
<br>
<b>mysql-python</b><br>
a. Optional?<br>
	Required if you want to use MySQL backend<br>
b. Required Version and Why<br>
	I use 1.2.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://sourceforge.net/projects/mysql-python/<br>
d. License<br>
	SF lists GNU General Public License (GPL), Python License (CNRI Python License), Zope Public License.<br>
	Project states GPL without version in Pkg-info.</p>
	
<h2>Database backend - PostgreSQL</h2>
<p>These two are required if you want to use PostgreSQL as backend</p>
<p><b>PostgreSQL</b><br>
a. Optional?<br>
	Choose MySQL or PostgreSQL<br>
b. Required Version and Why<br>
	I use 8.0.15 (GNU/Linux) and 8.3.3 (Windows) but I am not aware of any incompatibilities<br>
	with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://www.postgresql.org<br>
d. License<br>
	BSD License<br>
<br>
<b>psycopg</b><br>
a. Optional?<br>
	Required if you want to use PostgreSQL backend<br>
b. Required Version and Why<br>
	I use 2.0.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://initd.org/projects/psycopg2<br>
d. License<br>
	GPL2 according to Gentoo's ebuilds<br>
<br>
<h2>Required for everyone</h2>
<p><b>Python</b><br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	I use 2.4.4 and 2.5.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://www.python.org<br>
d. License<br>
	Python License<br>
<br>
<p><b>GTK+ and dependencies</b><br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	I use 2.12.9 but it should run with 2.10 or higher. That is needed as I used MessageDialog updates<br>
c. Project Webpage<br>
	Main: http://www.gtk.org/<br>
	API spec: http://library.gnome.org/devel/gtk/2.12/<br>
	Windows DLs (get the bundle unless you know what you're doing): http://www.gtk.org/download-windows.html<br>
d. License<br>
	LGPL2<br>
<br>
<b>PyCairo</b><br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1<br>
<br>
<b>PyGObject</b><br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1<br>
<br>
<b>PyGTK</b><br>
a. Optional?<br>
	Required.<br>
b. Required Version and Why<br>
	?<br>
c. Project Webpage<br>
	main: http://www.pygtk.org<br>
d. License<br>
	LGPL2.1</p>
<h2>Requirements for the graphing function</h2>
<p>These are only required if you wish to use the graphing function, and fpdb will otherwise function without them</p>
<p><b>Numpy</b><br>
a. Optional?<br>
	Optional.<br>
b. Required Version and Why<br>
	I use 1.0.4 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://numeric.scipy.org/<br>
d. License<br>
	BSD according to Gentoo's ebuild<br>
	<br>
<b>matplotlib</b><br>
a. Optional?<br>
	Optional.<br>
b. Required Version and Why<br>
	I use 0.91.2 but I am not aware of any incompatibilities with older or newer versions, pls report success/failure.<br>
c. Project Webpage<br>
	http://matplotlib.sourceforge.net/<br>
d. License<br>
	BSD according to Gentoo's ebuild</p>

License (of this file)<br>
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

require 'footer.php';

?>
