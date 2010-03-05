# Variable definitions
VERSION = 0.20
DATE = $(shell date +%Y%m%d)

all:
	@echo "Usage:"
	@echo "    make snapshot - Tags the repository with $(VERSION)-$(DATE) and creates a tarball from that"

snapshot:
	git tag $(VERSION)-$(DATE)
	git archive --prefix=fpdb-$(VERSION)-$(DATE)/ $(VERSION)-$(DATE) | gzip -9 > ../fpdb-$(VERSION)-$(DATE).tar.gz
