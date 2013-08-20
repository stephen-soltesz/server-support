
SPECFILE=nodebase.spec
pkgname=$(shell rpm -q --qf "%{NAME}\n" --specfile $(SPECFILE) | head -1)
version=$(shell rpm -q --qf "%{VERSION}\n" --specfile $(SPECFILE) | head -1)

RPMBUILD=../build/nodebase-i386
TMPBUILD=../tmp

PKGNAME=$(pkgname)-$(version)
TARNAME=$(PKGNAME).tar.bz2
RPMNAME=$(PKGNAME).rpm

PKGDIR=$(TMPBUILD)/$(PKGNAME)
TARFILE=$(TMPBUILD)/$(TARNAME)
RPMFILE=$(RPMBUILD)/$(RPMNAME)

RPMDIRDEFS=--define "_sourcedir $(PWD)/$(TMPBUILD)" --define "_builddir $(PWD)/$(TMPBUILD)" 
RPMDIRDEFS+= --define "_srcrpmdir $(PWD)/$(TMPBUILD)" --define "_rpmdir $(PWD)/$(RPMBUILD)"

all: $(PKGDIR) $(TARFILE) $(RPMFILE)

$(PKGDIR):
	mkdir -p $(PKGDIR)

FILES=$(shell find . -type f -a -print | grep -v .tar.bz2 )

$(TARFILE): $(PKGDIR) $(FILES)
	rsync -ar --exclude "build" $(PWD)/ $(PKGDIR)/
	tar --exclude ".*.swp" --exclude "*.tar" \
		-jcvf $(TARFILE) -C $(TMPBUILD) $(PKGNAME)

$(RPMFILE): $(TARFILE)
	rpmbuild $(RPMDIRDEFS) -bb $(SPECFILE)

clean:
	rm -rf $(PKGDIR)
	rm -f $(TARFILE)
	rm -f $(RPMFILE)
