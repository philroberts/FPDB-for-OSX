# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# created by Steffen Schaumburg, steffen@schaumburger.info

EAPI="2"
NEED_PYTHON=2.5

#inherit distutils

DESCRIPTION="A database program to track your online poker games"
HOMEPAGE="http://fpdb.sourceforge.net/"
#SRC_URI="mirror://sourceforge/fpdb/${MY_P}.tar.bz2"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: this should work on other architectures too, please send me your experiences

IUSE="mysql postgres graphing"
RDEPEND="
	mysql? ( virtual/mysql
		dev-python/mysql-python )
	postgres? ( dev-db/postgresql-server
		dev-python/psycopg )
	>=x11-libs/gtk+-2.10
	dev-python/pygtk
	graphing? ( dev-python/numpy
		dev-python/matplotlib[gtk] )
	dev-python/python-xlib"
DEPEND="${RDEPEND}"

#src_install() {
#	DIRINST="${D}usr/share/games/fpdb/"
#	mkdir -p "${DIRINST}"
#	cp -R * "${DIRINST}" || die
#	
#	DIRBIN="${D}usr/games/bin/"
#	mkdir -p "${DIRBIN}"
#	#echo "pathes"
#	#echo "${DIRINST}pyfpdb/fpdb.py"
#	#echo "${DIRBIN}fpdb.py"
#	#echo 
#	echo "cd /usr/share/games/fpdb/pyfpdb/ && python fpdb.py" > "${DIRBIN}fpdb" || die
#	chmod 755 "${DIRBIN}fpdb" || die
#}

#src_test() {
#}

pkg_postinst() {
	elog "Fpdb's dependencies have been installed. Please visit fpdb.sourceforge.net and download and unpack the archive."
	elog "You can then start fpdb by running run_fpdb.py. Good luck!"
}
