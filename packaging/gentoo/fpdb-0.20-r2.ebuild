# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# created by Steffen Schaumburg, steffen@schaumburger.info

EAPI="2"
NEED_PYTHON=2.5

DESCRIPTION="Fpdb is a free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${PV}/${P}.tar.gz"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: this should work on other architectures too, please send me your experiences

IUSE="graphing mysql postgres sqlite"
RDEPEND="
    mysql? ( virtual/mysql
        dev-python/mysql-python )
    postgres? ( dev-db/postgresql-server
        dev-python/psycopg )
    sqlite? ( dev-lang/python[sqlite]
        dev-python/numpy )
    >=x11-libs/gtk+-2.10
    dev-python/pygtk
    graphing? ( dev-python/numpy
        dev-python/matplotlib[gtk] )
    dev-python/python-xlib"
DEPEND="${RDEPEND}"

src_install() {
	dodir /usr/share/games/fpdb
	
	exeinto /usr/share/games/fpdb
	doexe run_fpdb.py
	dosym /usr/share/games/fpdb/run_fpdb.py /usr/bin/fpdb

	insinto /usr/share/games/fpdb
	doins readme.txt

	insinto /usr/share/games/fpdb/files
	doins files/*

	insinto /usr/share/games/fpdb/gfx
	doins gfx/*

	insinto /usr/share/games/fpdb/pyfpdb
	doins pyfpdb/*

# pyfpdb/regression-test-files dir is missing for now; cp -r ??

}

pkg_postinst() {
    elog "Note that if you really want to use mysql or postgresql you will have to create"
    elog "the database and user yourself and enter it into the fpdb config."
	elog "You can find the instructions on the project's website."
}
