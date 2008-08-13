# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/games-util/fpdb/fpdb-1.0_alpha1_p27.ebuild,v 1.0 2008/08/13 05:45:00 jer Exp $

NEED_PYTHON=2.3

#inherit distutils

MY_P="fpdb-${PV}"
DESCRIPTION="A database program to track your online poker games"
HOMEPAGE="https://sourceforge.net/projects/fpdb/"
SRC_URI="mirror://sourceforge/fpdb/fpdb-alpha1-git27.tar.bz2"

LICENSE="AGPL-3"
SLOT="0"
KEYWORDS="~amd64 ~x86"
#note: I would be very surprised if this doesnt work on other architectures, please send me your experiences
IUSE=""

RDEPEND="virtual/mysql
	dev-python/mysql-python
	>=x11-libs/gtk+-2.10
	dev-python/pygtk"
DEPEND="${RDEPEND}"

src_install() {
	DIRINST="${D}usr/share/games/fpdb/"
	mkdir -p "${DIRINST}"
	cp -R * "${DIRINST}" || die
	
	DIRBIN="${D}usr/bin/games/"
	mkdir -p "${DIRBIN}"
	#echo "dirs"
	#echo "${DIRINST}pyfpdb/fpdb.py"
	#echo 
	ln -s "${DIRINST}pyfpdb/fpdb.py" "${DIRBIN}/fpdb.py" || die
}
