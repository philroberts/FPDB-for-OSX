#Copyright 2009-2011 Carl Gherardi
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

# Variable definitions
VERSION = 0.40.4
DATE = $(shell date +%Y%m%d)

all:
	@echo "Usage:"
	@echo "    make snapshot - Tags the repository with $(VERSION)-$(DATE) and creates a tarball from that"

snapshot:
	git tag $(VERSION)-$(DATE)
	git archive --prefix=fpdb-$(VERSION)-$(DATE)/ $(VERSION)-$(DATE) | gzip -9 > ../fpdb-$(VERSION)-$(DATE).tar.gz

release:
	git tag $(VERSION)
	git archive --prefix=fpdb-$(VERSION)/ $(VERSION) | gzip -9 > ../fpdb-$(VERSION).tar.gz
