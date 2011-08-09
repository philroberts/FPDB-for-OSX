# Copyright 1999-2011 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

#TODO: Header, add cdecimal

EAPI="2"

inherit eutils games

DESCRIPTION="A free/open source tracker/HUD for use with online poker"
HOMEPAGE="http://fpdb.wiki.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${PV}/${P}.tar.bz2"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: fpdb has only been tested on x86 and amd64, but should work on other arches, too

IUSE="graph mysql postgres sqlite linguas_ca linguas_de linguas_es linguas_fr linguas_hu linguas_it linguas_lt linguas_pl linguas_pt linguas_ro linguas_ru linguas_zh"
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

	if use linguas_ca; then
		msgfmt pyfpdb/locale/fpdb-ca_ES.po -o pyfpdb/locale/ca.mo || die "failed to create Catalan mo file"
	fi

	if use linguas_de; then
		msgfmt pyfpdb/locale/fpdb-de_DE.po -o pyfpdb/locale/de.mo || die "failed to create German mo file"
	fi

	if use linguas_es; then
		msgfmt pyfpdb/locale/fpdb-es_ES.po -o pyfpdb/locale/es.mo || die "failed to create Spanish mo file"
	fi

	if use linguas_fr; then
		msgfmt pyfpdb/locale/fpdb-fr_FR.po -o pyfpdb/locale/fr.mo || die "failed to create French mo file"
	fi

	if use linguas_hu; then
		msgfmt pyfpdb/locale/fpdb-hu_HU.po -o pyfpdb/locale/hu.mo || die "failed to create Hungarian mo file"
	fi

	if use linguas_it; then
		msgfmt pyfpdb/locale/fpdb-it_IT.po -o pyfpdb/locale/it.mo || die "failed to create Italian mo file"
	fi

	if use linguas_lt; then
		msgfmt pyfpdb/locale/fpdb-lt_IT.po -o pyfpdb/locale/lt.mo || die "failed to create Lithuanian mo file"
	fi

	if use linguas_pl; then
		msgfmt pyfpdb/locale/fpdb-pl_PL.po -o pyfpdb/locale/pl.mo || die "failed to create Polish mo file"
	fi

	if use linguas_pt; then
		msgfmt pyfpdb/locale/fpdb-pt_BR.po -o pyfpdb/locale/pt.mo || die "failed to create Portuguese mo file"
	fi

	if use linguas_ro; then
		msgfmt pyfpdb/locale/fpdb-ro_RO.po -o pyfpdb/locale/ro.mo || die "failed to create Romanian mo file"
	fi

	if use linguas_ru; then
		msgfmt pyfpdb/locale/fpdb-ru_RU.po -o pyfpdb/locale/ru.mo || die "failed to create Russian mo file"
	fi

	if use linguas_zh; then
		msgfmt pyfpdb/locale/fpdb-zh_CN.po -o pyfpdb/locale/zh.mo || die "failed to create Chinese mo file"
	fi

	if use linguas_ca || use linguas_de || use linguas_es || use linguas_fr || use linguas_hu || use linguas_it || use linguas_lt|| use linguas_pl || use linguas_pt || use linguas_ro || use	linguas_ru || use linguas_zh; then
		domo pyfpdb/locale/*.mo || die "failed to install mo files"
	fi

	doins readme.txt || die "failed to install readme.txt file"

	exeinto "${GAMES_DATADIR}"/${PN}
	doexe run_fpdb.py || die "failed to install executable run_fpdb.py"

	dodir "${GAMES_BINDIR}"
	dosym "${GAMES_DATADIR}"/${PN}/run_fpdb.py "${GAMES_BINDIR}"/${PN} || die "failed to create symlink for starting fpdb"

	newicon gfx/fpdb-icon.png ${PN}.png || die "failed to install fpdb icon"
	make_desktop_entry ${PN}  || die "failed to create desktop entry"

	fperms +x "${GAMES_DATADIR}"/${PN}/pyfpdb/fpdb.pyw
	fperms +x "${GAMES_DATADIR}"/${PN}/pyfpdb/HUD_main.pyw

	prepgamesdirs
}

pkg_postinst() {
	games_pkg_postinst
	elog "Note that if you really want to use mysql or postgresql you will have to create"
	elog "the database and user yourself and enter it into the fpdb config."
	elog "You can find the instructions on the project's website."
}
