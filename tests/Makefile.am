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

TESTS = run_tests

run_tests: run_tests.in
	sed -e 's&@PYTHON_BIN@&$(PYTHON)&g' \
	    -e 's&@SRCDIR@&$(srcdir)&g' $< > $@
	chmod +x $@

EXTRA_DIST = \
	run_tests.in \
	test_it.py \
	__init__.py \
	$(NULL)

CLEANFILES = \
	run_tests \
	$(NULL)

MAINTAINERCLEANFILES = \
	Makefile.in \
	$(NULL)
