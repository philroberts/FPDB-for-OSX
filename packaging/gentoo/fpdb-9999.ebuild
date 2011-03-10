# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

#TODO: Header, add cdecimal

EAPI="2"

inherit eutils games git

DESCRIPTION="A free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
EGIT_REPO_URI="git://git.assembla.com/fpdb.git"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS=""

IUSE="graph mysql postgres sqlite linguas_de linguas_hu linguas_fr"
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

	if use linguas_de; then
		msgfmt pyfpdb/locale/fpdb-de_DE.po -o pyfpdb/locale/de.mo
	fi

	if use linguas_hu; then
		msgfmt pyfpdb/locale/fpdb-hu_HU.po -o pyfpdb/locale/hu.mo
	fi

	domo pyfpdb/locale/*.mo

	doins readme.txt

	exeinto "${GAMES_DATADIR}"/${PN}
	doexe run_fpdb.py

	dodir "${GAMES_BINDIR}"
	dosym "${GAMES_DATADIR}"/${PN}/run_fpdb.py "${GAMES_BINDIR}"/${PN}

	newicon gfx/fpdb-icon.png ${PN}.png
	make_desktop_entry ${PN}

	fperms +x "${GAMES_DATADIR}"/${PN}/pyfpdb/*.pyw
	prepgamesdirs
}

pkg_postinst() {
	games_pkg_postinst
	elog "Note that if you really want to use mysql or postgresql you will have to create"
	elog "the database and user yourself and enter it into the fpdb config."
	elog "You can find the instructions on the project's website."
}
