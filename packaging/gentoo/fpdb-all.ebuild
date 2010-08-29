# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="2"

inherit eutils
inherit games
if [[ ${PV} = 9999* ]]; then
    inherit git
fi

NEED_PYTHON=2.6

DESCRIPTION="A free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
if [[ ${PV} = 9999* ]]; then
	EGIT_REPO_URI="git://git.assembla.com/fpdb.git"
	KEYWORDS=""
	IUSE="graph mysql postgres sqlite linguas_hu linguas_it"
elif [[ ${PV} = 0.20.90* ]]; then
	SRC_URI="mirror://sourceforge/${PN}/Snapshots/${P}.tar.bz2"
	KEYWORDS="~amd64 ~x86"
	IUSE="graph mysql postgres sqlite linguas_hu linguas_it"
else; then
	SRC_URI="mirror://sourceforge/${PN}/${PV}/${P}.tar.bz2"
	KEYWORDS="~amd64 ~x86"
	IUSE="graph mysql postgres sqlite"
fi

LICENSE="AGPL-3"
SLOT="0"

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

if [[ ${PV} = 9999* ]]; then
	src_unpack() {
		git_src_unpack
	}
fi

src_install() {
	insinto "${GAMES_DATADIR}"/${PN}
	doins -r gfx
	doins -r pyfpdb

	if [[ ${PV} >= 0.20.901 ]]; then
		if use linguas_hu; then
			dosym "${GAMES_DATADIR}"/${PN}/pyfpdb/locale/hu/LC_MESSAGES/${PN}.mo /usr/share/locale/hu/LC_MESSAGES/${PN}.mo
		fi

		if use linguas_it; then
			dosym "${GAMES_DATADIR}"/${PN}/pyfpdb/locale/it/LC_MESSAGES/${PN}.mo /usr/share/locale/it/LC_MESSAGES/${PN}.mo
		fi
	fi

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
