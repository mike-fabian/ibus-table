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
	i18n.py \
	$(NULL)
setup_tabledir = $(datadir)/ibus-table/setup

libexec_SCRIPTS = ibus-setup-table

desktop_in_in_files = ibus-setup-table.desktop.in.in
desktop_in_files = $(desktop_in_in_files:.in.in=.in)

$(desktop_in_files): %.desktop.in: %.desktop.in.in Makefile
	( \
		PKGDATADIR=$(pkgdatadir); \
		LIBEXECDIR=$(libexecdir); \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@

desktopdir=$(datadir)/applications
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
$(desktop_DATA): $(desktop_in_files) Makefile
	$(AM_V_GEN)$(MSGFMT) --desktop --template $< -d $(top_srcdir)/po -o $@

CLEANFILES = \
	$(desktop_DATA) \
	$(desktop_in_files) \
	*.pyc \
	$(NULL)

EXTRA_DIST = \
	version.py.in \
	ibus-setup-table.in \
	$(desktop_in_in_files) \
	$(desktop_in_files) \
	$(desktop_DATA) \
	$(NULL)

test-table:
	$(ENV) DBUS_DEBUG=true \
		   IBUS_LOCALEDIR=@localedir@ \
		   PYTHONPATH=$(abs_top_srcdir):$(pyexecdir) \
		   $(PYTHON) $(srcdir)/main.py ziranma4

