# vim:set noet ts=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2018 Mike FABIAN <mfabian@redhat.com>
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

TESTS = \
	test_it.py \
	test_0_gtk.py \
	$(NULL)

check_SCRIPTS = run_tests

LOG_COMPILER = $(builddir)/run_tests

TESTS_ENVIRONMENT = \
	IBUS_TABLE_LOCATION=../

test_meta_in = meta.test.in
test_metas =

if ENABLE_INSTALLED_TESTS
test_metas += $(patsubst %.py, %.test, $(TESTS))
test_source_DATA = $(test_metas)
test_sourcedir = $(datadir)/installed-tests/ibus-table
test_exec_SCRIPTS = \
	$(TESTS) \
	gtkcases.py \
	mock_engine.py \
	run_tests \
	$(NULL)
test_execdir = $(libexecdir)/installed-tests/ibus-table

$(test_metas): $(test_meta_in)
	@TEST_EXEC=`echo $@ | sed -e 's&\.test&\.py&'`; \
	sed -e "s&@TEST_EXECDIR@&$(test_execdir)&g" \
	    -e "s&@TEST_EXEC@&$$TEST_EXEC&g" $< > $@.tmp; \
	mv $@.tmp $@; \
	$(NULL)
endif

run_tests: run_tests.in
	sed -e 's&@PYTHON_BIN@&$(PYTHON)&g' \
	    -e 's&@PKGDATADIR@&$(pkgdatadir)&g' \
	    -e 's&@SRCDIR@&$(srcdir)&g' $< > $@
	chmod +x $@

EXTRA_DIST = \
	$(test_meta_in) \
	__init__.py \
	gtkcases.py \
	mock_engine.py \
	run_tests.in \
	$(TESTS) \
	$(NULL)

CLEANFILES = \
	$(test_metas) \
	run_tests \
	$(NULL)

MAINTAINERCLEANFILES = \
	Makefile.in \
	$(NULL)
