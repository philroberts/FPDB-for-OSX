# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

#TODO: Header, add cdecimal

EAPI="2"

inherit eutils games

DESCRIPTION="A free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/Snapshots/${P}.tar.bz2"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: this should work on other architectures too, please send me your experiences

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
	dev-python/pytz
	x11-apps/xwininfo"
DEPEND="${RDEPEND}"

src_install() {
	insinto "${GAMES_DATADIR}"/${PN}
	doins -r gfx || die "failed to install gfx directory"
	doins -r pyfpdb || die "failed to install pyfpdb directory"

	if use linguas_hu; then
		msgfmt pyfpdb/locale/fpdb-hu_HU.po -o pyfpdb/locale/hu.mo || die "failed to create hungarian mo file"
	fi

	domo pyfpdb/locale/*.mo || die "failed to install mo files"

	doins readme.txt || die "failed to install readme.txt file"

	exeinto "${GAMES_DATADIR}"/${PN}
	doexe run_fpdb.py || die "failed to install executable run_fpdb.py"

	dodir "${GAMES_BINDIR}"
	dosym "${GAMES_DATADIR}"/${PN}/run_fpdb.py "${GAMES_BINDIR}"/${PN}  || die "failed to create symlink for starting fpdb"

	newicon gfx/fpdb-icon.png ${PN}.png || die "failed to install fpdb icon"
	make_desktop_entry ${PN}  || die "failed to create desktop entry"

	fperms +x "${GAMES_DATADIR}"/${PN}/pyfpdb/*.pyw
	prepgamesdirs
}

pkg_postinst() {
	games_pkg_postinst
	elog "Note that if you really want to use mysql or postgresql you will have to create"
	elog "the database and user yourself and enter it into the fpdb config."
	elog "You can find the instructions on the project's website."
}
