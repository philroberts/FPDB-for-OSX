# Copyright 1999-2008 Gentoo Foundation
# Gentoo had nothing to do with the production of this ebuild, but I'm pre-emptively transferring all copyrights (as far as legally possible under my local jurisdiction) to them.
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/games-util/fpdb/fpdb-1.0_alpha7_p136.ebuild,v 1.0 2008/10/15 steffen@sycamoretest.info Exp $

NEED_PYTHON=2.3

#inherit distutils

MY_P="fpdb-${PV}"
DESCRIPTION="A database program to track your online poker games"
HOMEPAGE="https://sourceforge.net/projects/fpdb/"
SRC_URI="mirror://sourceforge/fpdb/${MY_P}.tar.bz2"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: this should work on other architectures too, please send me your experiences
IUSE=""

RDEPEND="virtual/mysql
	dev-python/mysql-python
	>=x11-libs/gtk+-2.10
	dev-python/pygtk
	dev-python/numpy
	dev-python/matplotlib"

DEPEND="${RDEPEND}"

src_install() {
	DIRINST="${D}usr/share/games/fpdb/"
	mkdir -p "${DIRINST}"
	cp -R * "${DIRINST}" || die
	
	DIRBIN="${D}usr/games/bin/"
	mkdir -p "${DIRBIN}"
	#echo "pathes"
	#echo "${DIRINST}pyfpdb/fpdb.py"
	#echo "${DIRBIN}fpdb.py"
	#echo 
	echo "cd /usr/share/games/fpdb/pyfpdb/ && python fpdb.py" > "${DIRBIN}fpdb" || die
	chmod 755 "${DIRBIN}fpdb" || die
}

#src_test() {
#}

pkg_postinst() {
	elog "Fpdb has been installed and can be called by executing /usr/games/bin/fpdb"
	elog "You need to perform a couple more steps manually."
	elog "Please also make sure you followed instructions from previous emerges, in particular make sure you configured mysql and set a root pw for it"
	elog "Now run this command to connect to MySQL: mysql --user=root --password=yourPassword"
	elog "In the mysql command line interface you need to type these two lines (make sure you get the ; at the end)"
	elog "In the second line replace \"newPassword\" with a password of your choice"
	elog "CREATE DATABASE fpdb;"
	elog "GRANT ALL PRIVILEGES ON fpdb.* TO 'fpdb'@'localhost' IDENTIFIED BY 'newPassword' WITH GRANT OPTION;"
	elog "Finally copy the default config file from ${DIRINST}docs/default.conf to ~/.fpdb/ for every user that is to use fpdb."
	elog "You will need to edit the default.conf, in particular you need to replace the password with what you entered in the \"GRANT ALL...\""
	elog "Finally run the GUI and click the menu database -> recreate tables"
	elog "That's it! See our webpage at http://fpdb.sourceforge.net for more documentation"
	elog " "
}
