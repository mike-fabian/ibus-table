# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2015 Mike FABIAN <mfabian@redhat.com>
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
'''
Utility functions used in ibus-table
'''

import sys
import re
import string

def config_section_normalize(section):
    '''Replaces “_:” with “-” in the dconf section and converts to lower case

    :param section: The name of the dconf section
    :type section: string
    :rtype: string

    To make the comparison of the dconf sections work correctly.

    I avoid using .lower() here because it is locale dependent, when
    using .lower() this would not achieve the desired effect of
    comparing the dconf sections case insentively in some locales, it
    would fail for example if Turkish locale (tr_TR.UTF-8) is set.

    Examples:

    >>> config_section_normalize('Foo_bAr:Baz')
    'foo-bar-baz'
    '''
    return re.sub(r'[_:]', r'-', section).translate(
        bytes.maketrans(
            bytes(string.ascii_uppercase.encode('ascii')),
            bytes(string.ascii_lowercase.encode('ascii'))))


if __name__ == "__main__":
    import doctest
    (FAILED, ATTEMPTED) = doctest.testmod()
    if FAILED:
        sys.exit(1)
    else:
        sys.exit(0)
