# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# created by Steffen Schaumburg, steffen@schaumburger.info
EAPI="2"

inherit eutils
inherit games
inherit git

NEED_PYTHON=2.5

DESCRIPTION="A free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
EGIT_REPO_URI="git://git.assembla.com/fpdb.git"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: this should work on other architectures too, please send me your experiences

IUSE="graph mysql postgres sqlite"
RDEPEND="
	mysql? ( virtual/mysql
		dev-python/mysql-python )
	postgres? ( dev-db/postgresql-server
		dev-python/psycopg )
	sqlite? ( dev-lang/python[sqlite]
		dev-python/numpy )
	>=x11-libs/gtk+-2.10
	dev-python/pygtk
	graph? ( dev-python/numpy
		dev-python/matplotlib[gtk] )
	dev-python/python-xlib
	dev-python/pytz"
DEPEND="${RDEPEND}"

src_unpack() {
	git_src_unpack
}

src_install() {
	insinto "${GAMES_DATADIR}"/${PN}
	doins -r gfx
	doins -r pyfpdb
	doins readme.txt

	exeinto "${GAMES_DATADIR}"/${PN}
	doexe run_fpdb.py

	dodir "${GAMES_BINDIR}"
	dosym "${GAMES_DATADIR}"/${PN}/run_fpdb.py "${GAMES_BINDIR}"/${PN}

	newicon gfx/fpdb-icon.png ${PN}.png
	make_desktop_entry ${PN}

	chmod +x "${D}/${GAMES_DATADIR}"/${PN}/pyfpdb/*.pyw
	prepgamesdirs
}

pkg_postinst() {
	games_pkg_postinst
	elog "Note that if you really want to use mysql or postgresql you will have to create"
	elog "the database and user yourself and enter it into the fpdb config."
	elog "You can find the instructions on the project's website."
}
