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
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
Get locations where ibus-table stores stuff.

The directories used are according to the
“XDG Base Directory Specification”,
see: http://standards.freedesktop.org/basedir-spec/latest/index.html
'''

from typing import Dict
import os

IBUS_TABLE_LOCATION: Dict[str, str] = {
    'data': '',
    'lib': '',
    'data_home': '',
    'cache_home': '',
}

def data() -> str:
    return IBUS_TABLE_LOCATION['data']

def lib() -> str:
    return IBUS_TABLE_LOCATION['lib']

def data_home() -> str:
    return IBUS_TABLE_LOCATION['data_home']

def cache_home() -> str:
    return IBUS_TABLE_LOCATION['cache_home']

def _init() -> None:
    if os.getenv('IBUS_TABLE_LOCATION'):
        IBUS_TABLE_LOCATION['data'] = str(os.getenv('IBUS_TABLE_LOCATION'))
    if (not IBUS_TABLE_LOCATION['data']
            or not os.path.exists(IBUS_TABLE_LOCATION['data'])):
        IBUS_TABLE_LOCATION['data'] = "/usr/share/ibus-table/"

    if os.getenv('IBUS_TABLE_LIB_LOCATION'):
        IBUS_TABLE_LOCATION['lib'] = str(os.getenv('IBUS_TABLE_LIB_LOCATION'))
    if (not IBUS_TABLE_LOCATION['lib']
            or not os.path.exists(IBUS_TABLE_LOCATION['lib'])):
        IBUS_TABLE_LOCATION['lib'] = "/usr/libexec"

    # $XDG_DATA_HOME defines the base directory relative to which user
    # specific data files should be stored. If $XDG_DATA_HOME is either
    # not set or empty, a default equal to $HOME/.local/share should be
    # used.
    if os.getenv('IBUS_TABLE_DATA_HOME'):
        IBUS_TABLE_LOCATION['data_home'] = str(
            os.getenv('IBUS_TABLE_DATA_HOME'))
    if (not IBUS_TABLE_LOCATION['data_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['data_home'])):
        if os.getenv('XDG_DATA_HOME'):
            IBUS_TABLE_LOCATION['data_home'] = str(os.getenv('XDG_DATA_HOME'))
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
    if os.getenv('IBUS_TABLE_CACHE_HOME'):
        IBUS_TABLE_LOCATION['cache_home'] = str(
            os.getenv('IBUS_TABLE_CACHE_HOME'))
    if (not IBUS_TABLE_LOCATION['cache_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['cache_home'])):
        if os.getenv('XDG_CACHE_HOME'):
            IBUS_TABLE_LOCATION['cache_home'] = str(
                os.getenv('XDG_CACHE_HOME'))
    if (not IBUS_TABLE_LOCATION['cache_home']
            or not os.path.exists(IBUS_TABLE_LOCATION['cache_home'])):
        IBUS_TABLE_LOCATION['cache_home'] = os.path.expanduser('~/.cache')
    IBUS_TABLE_LOCATION['cache_home'] = os.path.join(
        IBUS_TABLE_LOCATION['cache_home'], 'ibus-table')
    if not os.access(IBUS_TABLE_LOCATION['cache_home'], os.F_OK):
        os.makedirs(IBUS_TABLE_LOCATION['cache_home'], exist_ok=True)

class __ModuleInitializer:
    def __init__(self) -> None:
        _init()

    def __del__(self) -> None:
        return

__module_init = __ModuleInitializer()
