# vim:set noet ts=4
#
# ibus-table - The Table engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
DISTCHECK_CONFIGURE_FLAGS = \
	--enable-additional \
	$(NULL)

SUBDIRS = \
	engine \
	icons \
	m4 \
	tables \
	data \
	po \
	setup \
	tests \
	$(NULL)

ACLOCAL_AMFLAGS = -I m4

pkgconfig_DATA = \
	ibus-table.pc \
	$(NULL)

pkgconfigdir = $(libdir)/pkgconfig

# To register as an AppStream component to be visible in the software center
# (See http://www.freedesktop.org/software/appstream/docs/ for more details):
metainfodir = $(datadir)/metainfo
metainfo_in_files = \
	org.freedesktop.ibus.engine.table.metainfo.xml.in \
	$(NULL)
metainfo_DATA = $(metainfo_in_files:.in=)
%.metainfo.xml: %.metainfo.xml.in $(wildcard po/*.mo) Makefile
	$(AM_V_GEN)$(MSGFMT) --xml --template $< -d $(top_srcdir)/po --output-file $@

schemas_DATA = \
	org.freedesktop.ibus.engine.table.gschema.xml
	$(NULL)

schemasdir = $(datadir)/glib-2.0/schemas/

install-data-hook:
	if test -z "$(DESTDIR)"; then \
	    glib-compile-schemas $(schemasdir); \
	fi

uninstall-hook:
	SCHEMAS_FILES=`ls $(schemasdir)/*.gschema.xml` || true;         \
	if test -z "$$SCHEMAS_FILES" &&                                 \
	    test -f $(schemasdir)/gschemas.compiled; then               \
	    rm $(schemasdir)/gschemas.compiled;                         \
	fi

AUX_DIST = \
	config.guess \
	config.sub \
	install-sh \
	missing \
	py-compile \
	$(NULL)

MAINTAINERCLEANFILES = \
	Makefile.in \
	aclocal.m4 \
	configure \
	$(AUX_DIST) \
	$(NULL)


EXTRA_DIST = \
	config.rpath \
	autogen.sh \
	$(metainfo_in_files) \
	$(metainfo_DATA) \
	$(schemas_DATA) \
	@PACKAGE_NAME@.spec \
	$(NULL)

noinst_DIST = \
	$(NULL)


#DISTCLEANFILES = \
#	po/stamp-it \
#	$(NULL)

rpm: dist @PACKAGE_NAME@.spec
	rpmbuild -bb \
			--define "_sourcedir `pwd`" \
			--define "_builddir `pwd`" \
			--define "_specdir `pwd`" \
			--define "_rpmdir `pwd`" \
			--define "_srcrpmdir `pwd`" \
			@PACKAGE_NAME@.spec

srpm: dist @PACKAGE_NAME@.spec
	rpmbuild -bs \
			--define "_sourcedir `pwd`" \
			--define "_builddir `pwd`" \
			--define "_srcrpmdir `pwd`" \
			--define "_rpmdir `pwd`" \
			--define "_specdir `pwd`" \
			@PACKAGE_NAME@.spec

clean-rpm:
	$(RM) -r "`uname -i`"

clean-local: clean-rpm
