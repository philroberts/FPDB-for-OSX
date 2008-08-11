Summary
=======
A database program to track your online poker games, the behaviour of the other players and your winnings/losses. Supports Holdem, Omaha, Stud and Razz for cash games as well as SnG and MTT tournaments with more possibly coming in the future. Some of this is not yet working though, please see status.txt and known-bugs-and-planned-features.txt

Contact
=======
Please note that this project has two hostings: one at assembla.com which holds are version control "central tree" (irrelevant for users) and everything else at http://sourceforge.net/projects/fpdb/.

The best means of contact are the sourceforge page: Use the bug, feature request or patch functions or just post in the forum.

Alternatively feel free to contact me directly:

mail: steffen(at)sycamoretest.info
jabber/xmpp/Google Talk: as above
ICQ: 7806355
MSN: steffenjf@gmx.de (don't email that)

But you could send all my hand histories to yourself!
=====================================================
At the end of the day this comes down to a question of trust, but unlike Windows and the poker client software you don't have to trust fpdb blindly. You can:
- Verify the source code yourself.
- Convince or pay someone to verify the source code for you.
- Use a personal firewall to completely block fpdb from the Internet
- (for the uber-paranoid) Get yourself the free virtualisation software VirtualBox, set up a VM (virtual machine) to run fpdb but run the poker software on your real PC. Then cut the VM off the Internet, fpdb doesn't need it. If you have a PC made in the last few years this should run fast enough as well. Note that most Windows licenses do NOT permit you to use two Windows installations at once, even if they are on the same PC.

Installing
==========
See the install-*.txt for your operating system. If your OS is missing or if you have problems let me know (contacts are further below). In particular I'd be happy to provide packages for GNU/Linux and *BSD distributions.

Using it
========
See readme-user.txt
If you have a problem, request or question see the contacts section below

Changing it
===========
See readme-dev.txt

Requirements
============
Software requirements are listed in requirements.txt
As for hardware, my main test machine is a Pentium 3-M 800 with 256 RAM and Gentoo GNU/Linux
(running the poker client through what most people will call emulation). So this
program will have to work on that. If you run an even more ancient machine and
its too slow let me know and I'll see what I can do :)

Why Free Software?
==================
This program is released under the terms of the free/libre software license AGPL3 as released by the FSF. The AGPL3 protects your rights and those of the wider community. As Richard Stallman, one of the founders of the free software movement, put it: "Free software is a matter of liberty, not price. To understand the concept, you should think of free as in free speech, not as in free beer." (well, it is both really, like the right to vote used to be free)

For example, a "pirated" copy of proprietary software X is free of charge, but you don't actually have a legal right to use it, you don't have any possibility to fix its bugs and you certainly don't have any legal right to share it with your friends. You also won't be able to get support, often not even security fixes. Actually, even if you pay hundreds of pounds for your program they deny your right to fix their errors for them. Imagine buying a car where you're not permitted (under threat of jail) to replace broken parts..

With free/libre software (also known as open source software, or short FOSS or FLOSS) on the other hand you get all these freedoms:
(note: the legally binding terms are in the license text, this is merely an amateur summary so normal people don't have to read pages of legalese)

Freedom 0: The freedom to use: To run the program, for any purpose. Free of Charge.
Freedom 1: The freedom to study and help yourself. This freedom guarantees your right to study and learn from the source code of the program, and to fix it if it is broken. If you're not a programmer yourself the developers will generally be happy to fix it for you, often even for free. Failing that you can always pay someone from the money you saved on not having to pay for it.
Freedom 2: The freedom to be a decent human being and help your neighbour: I don't threaten you with lawsuits or jail time if you share with your friends and neighbours, subject to the very modest restrictions of the AGPL3.
Freedom 3: The freedom to improve the program and release your improvements to the public (or parts thereof) so that the whole community benefits. Note that you are PERMITTED, but not REQUIRED to distribute your changes. If you do distribute your changes you must do so under the terms of the AGPL3 however.

Note that this is the license - I retain full copyright over my code, including the right to change the license for future versions. I do not intend to do this however. In any case, any version I released under AGPL3 remains available under that license forever, or more accurately until my copyright expires at which point it goes into the public domain.

I reject the concept of software patents as a crime and under the European Patent Agreement software patents - even if you mislabel them as "computer-implemented inventions" or whatever - are explicitly prohibited.

Can I get/use this under a different license?
=============================================
The short answer: Maybe.
The long one: As detailed, I fully support what the FSF does and aims to achieve with the GPL. However, I realise that many free software developers don't object to closed source, some don't even object to closed source profiteering of their charity, and I don't think I have any right to go and tell them they're wrong.
So if anyone wishes to use all or part of my code in another free software/open source project with an AGPL3-incompatible license such as BSD then let me know and we'll figure out a solution that makes everyone happy.
If you wish to use all or part of this in closed source let me know how much if anything that is worth to you and I'm sure we'll be able to reach an agreement. Note that you are NOT permitted to just use fpdb code in closed source development whether in-house or by an independent software developer, you will NEED an additionally agreement with me to get fpdb under different licensing conditions.


License of this Document
========================
The views expressed in this document are those of Steffen Jobbagy-Felso, other members of the fpdb team and external contributors may or may not agree.

Trademarks of third parties have been used under Fair Use or similar laws.

Copyright 2008 Steffen Jobbagy-Felso
Permission is granted to copy, distribute and/or modify this
document under the terms of the GNU Free Documentation License,
Version 1.2 as published by the Free Software Foundation; with
no Invariant Sections, no Front-Cover Texts, and with no Back-Cover
Texts. A copy of the license can be found in fdl-1.2.txt

The program itself is licensed under AGPLv3, see agpl-3.0.txt
