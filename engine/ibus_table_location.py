# vim:et sts=4 sw=4 -*- coding: utf-8 -*-
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2015-2018 Mike FABIAN <mfabian@redhat.com>
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

u'''
Get locations where ibus-table stores stuff.

The directories used are according to the
“XDG Base Directory Specification”,
see: http://standards.freedesktop.org/basedir-spec/latest/index.html
'''

import os

IBUS_TABLE_LOCATION = {
    'data': '',
    'lib': '',
    'data_home': '',
    'cache_home': '',
}

def data():
    return IBUS_TABLE_LOCATION['data']

def lib():
    return IBUS_TABLE_LOCATION['lib']

def data_home():
    return IBUS_TABLE_LOCATION['data_home']

def cache_home():
    return IBUS_TABLE_LOCATION['cache_home']

def _init():
    IBUS_TABLE_LOCATION['data'] = os.getenv('IBUS_TABLE_LOCATION')
    if (not IBUS_TABLE_LOCATION['data']
            or not os.path.exists(IBUS_TABLE_LOCATION['data'])):
        IBUS_TABLE_LOCATION['data'] = "/usr/share/ibus-table/"

    IBUS_TABLE_LOCATION['lib'] = os.getenv('IBUS_TABLE_LIB_LOCATION')
    if (not IBUS_TABLE_LOCATION['lib']
            or not os.path.exists(IBUS_TABLE_LOCATION['lib'])):
        IBUS_TABLE_LOCATION['lib'] = "/usr/libexec"

    # $XDG_DATA_HOME defines the base directory relative to which user
    # specific data files should be stored. If $XDG_DATA_HOME is either
    # not set or empty, a default equal to $HOME/.local/share should be
    # used.
    IBUS_TABLE_LOCATION['data_home'] = os.getenv('IBUS_TABLE_DATA_HOME')
    if (not IBUS_TABLE_LOCATION['data_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['data_home'])):
        IBUS_TABLE_LOCATION['data_home'] = os.getenv('XDG_DATA_HOME')
    if (not IBUS_TABLE_LOCATION['data_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['data_home'])):
        IBUS_TABLE_LOCATION['data_home'] = os.path.expanduser('~/.local/share')
    IBUS_TABLE_LOCATION['data_home'] = os.path.join(
        IBUS_TABLE_LOCATION['data_home'], 'ibus-table')
    if not os.access(IBUS_TABLE_LOCATION['data_home'], os.F_OK):
        os.makedirs(IBUS_TABLE_LOCATION['data_home'], exist_ok=True)

    # $XDG_CACHE_HOME defines the base directory relative to which user
    # specific non-essential data files should be stored. If
    # $XDG_CACHE_HOME is either not set or empty, a default equal to
    # $HOME/.cache should be used.
    IBUS_TABLE_LOCATION['cache_home'] = os.getenv('IBUS_TABLE_CACHE_HOME')
    if (not IBUS_TABLE_LOCATION['cache_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['cache_home'])):
        IBUS_TABLE_LOCATION['cache_home'] = os.getenv('XDG_CACHE_HOME')
    if (not IBUS_TABLE_LOCATION['cache_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['cache_home'])):
        IBUS_TABLE_LOCATION['cache_home'] = os.path.expanduser('~/.cache')
    IBUS_TABLE_LOCATION['cache_home'] = os.path.join(
        IBUS_TABLE_LOCATION['cache_home'], 'ibus-table')
    if not os.access(IBUS_TABLE_LOCATION['cache_home'], os.F_OK):
        os.makedirs(IBUS_TABLE_LOCATION['cache_home'], exist_ok=True)

class __ModuleInitializer:
    def __init__(self):
        _init()
        return

    def __del__(self):
        return

__module_init = __ModuleInitializer()
