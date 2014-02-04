# vim:set noet ts=4:
#
# ibus-table - The Chinese Table engine for IBus
#
# Copyright (c) 2008-2010 Peng Huang <shawn.p.huang@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

setup_table_PYTHON = \
	main.py \
	version.py \
	ibus-table-preferences.ui \
	$(NULL)
setup_tabledir = $(datadir)/ibus-table/setup

libexec_SCRIPTS = ibus-setup-table

CLEANFILES = \
	*.pyc \
	$(NULL)

EXTRA_DIST = \
	version.py.in \
	ibus-setup-table.in \
	$(NULL)

test-table:
	$(ENV) DBUS_DEBUG=true \
		   IBUS_LOCALEDIR=@localedir@ \
		   PYTHONPATH=$(abs_top_srcdir):$(pyexecdir) \
		   $(PYTHON) $(srcdir)/main.py ziranma4

