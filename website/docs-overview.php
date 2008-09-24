<?php

$PAGE_TITLE = 'Overview';

require 'header.php';
require 'sidebar.php';

?>

            <div id="main">

                <h1>Overview</h1>
<p>
Summary<br>
=======<br>
A database program to track your online poker games, the behaviour of the other players and your winnings/losses. Supports Holdem, Omaha, Stud and Razz for cash games as well as SnG and MTT tournaments with more possibly coming in the future. Some of this is not yet working though, please see status.txt and known-bugs-and-planned-features.txt<br>
<br>
But you could send all my hand histories to yourself!<br>
=====================================================<br>
At the end of the day this comes down to a question of trust, but unlike Windows and the poker client software you don't have to trust fpdb blindly. You can:<br>
- Verify the source code yourself.<br>
- Convince or pay someone to verify the source code for you.<br>
- Use a personal firewall to completely block fpdb from the Internet<br>
- (for the uber-paranoid) Get yourself the free virtualisation software VirtualBox, set up a VM (virtual machine) to run fpdb but run the poker software on your real PC. Then cut the VM off the Internet, fpdb doesn't need it. If you have a PC made in the last few years this should run fast enough as well. Note that most Windows licenses do NOT permit you to use two Windows installations at once, even if they are on the same PC.<br>
<br>
Requirements<br>
============<br>
Software requirements are listed in requirements.txt<br>
As for hardware, my main test machine is a Pentium 3-M 800 with 256 RAM and Gentoo GNU/Linux<br>
(running the poker client through what most people will call emulation). So this<br>
program will have to work on that. If you run an even more ancient machine and<br>
its too slow let me know and I'll see what I can do :)<br>
<br>
Why Free Software?<br>
==================<br>
This program is released under the terms of the free/libre software license AGPL3 as released by the FSF. The AGPL3 protects your rights and those of the wider community. As Richard Stallman, one of the founders of the free software movement, put it: "Free software is a matter of liberty, not price. To understand the concept, you should think of free as in free speech, not as in free beer." (well, it is both really, like the right to vote used to be free)<br>
<br>
For example, a "pirated" copy of proprietary software X is free of charge, but you don't actually have a legal right to use it, you don't have any possibility to fix its bugs and you certainly don't have any legal right to share it with your friends. You also won't be able to get support, often not even security fixes. Actually, even if you pay hundreds of pounds for your program they deny your right to fix their errors for them. Imagine buying a car where you're not permitted (under threat of jail) to replace broken parts..<br>
<br>
With free/libre software (also known as open source software, or short FOSS or FLOSS) on the other hand you get all these freedoms:<br>
(note: the legally binding terms are in the license text, this is merely an amateur summary so normal people don't have to read pages of legalese)<br>
<br>
Freedom 0: The freedom to use: To run the program, for any purpose. Free of Charge.<br>
Freedom 1: The freedom to study and help yourself. This freedom guarantees your right to study and learn from the source code of the program, and to fix it if it is broken. If you're not a programmer yourself the developers will generally be happy to fix it for you, often even for free. Failing that you can always pay someone from the money you saved on not having to pay for it.<br>
Freedom 2: The freedom to be a decent human being and help your neighbour: I don't threaten you with lawsuits or jail time if you share with your friends and neighbours, subject to the very modest restrictions of the AGPL3.<br>
Freedom 3: The freedom to improve the program and release your improvements to the public (or parts thereof) so that the whole community benefits. Note that you are PERMITTED, but not REQUIRED to distribute your changes. If you do distribute your changes you must do so under the terms of the AGPL3 however.<br>
<br>
Note that this is the license - I retain full copyright over my code, including the right to change the license for future versions. I do not intend to do this however. In any case, any version I released under AGPL3 remains available under that license forever, or more accurately until my copyright expires at which point it goes into the public domain.<br>
<br>
I reject the concept of software patents as a crime and under the European Patent Agreement software patents - even if you mislabel them as "computer-implemented inventions" or whatever - are explicitly prohibited.<br>
<br>
Can I get/use this under a different license?<br>
=============================================<br>
The short answer: Maybe.<br>
The long one: As detailed, I fully support what the FSF does and aims to achieve with the GPL. However, I realise that many free software developers don't object to closed source, some don't even object to closed source profiteering of their charity, and I don't think I have any right to go and tell them they're wrong.<br>
So if anyone wishes to use all or part of my code in another free software/open source project with an AGPL3-incompatible license such as BSD then let me know and we'll figure out a solution that makes everyone happy.<br>
If you wish to use all or part of this in closed source let me know how much if anything that is worth to you and I'm sure we'll be able to reach an agreement. Note that you are NOT permitted to just use fpdb code in closed source development whether in-house or by an independent software developer, you will NEED an additionally agreement with me to get fpdb under different licensing conditions.<br>
<br>
<br>
License of this Document<br>
========================<br>
The views expressed in this document are those of Steffen Jobbagy-Felso, other members of the fpdb team and external contributors may or may not agree.<br>
<br>
Trademarks of third parties have been used under Fair Use or similar laws.<br>
<br>
Copyright 2008 Steffen Jobbagy-Felso<br>
Permission is granted to copy, distribute and/or modify this<br>
document under the terms of the GNU Free Documentation License,<br>
Version 1.2 as published by the Free Software Foundation; with<br>
no Invariant Sections, no Front-Cover Texts, and with no Back-Cover<br>
Texts. A copy of the license can be found in fdl-1.2.txt<br>
<br>
The program itself is licensed under AGPLv3, see agpl-3.0.txt<br>
</p>



            </div>

<?php

require 'footer.php';

?>
