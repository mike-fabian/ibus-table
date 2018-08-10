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
from gi import require_version
require_version('GLib', '2.0')
from gi.repository import GLib

def variant_to_value(variant):
    '''
    Convert a GLib variant to a value
    '''
    # pylint: disable=unidiomatic-typecheck
    if type(variant) != GLib.Variant:
        return variant
    type_string = variant.get_type_string()
    if type_string == 's':
        return variant.get_string()
    elif type_string == 'i':
        return variant.get_int32()
    elif type_string == 'b':
        return variant.get_boolean()
    elif type_string == 'as':
        # In the latest pygobject3 3.3.4 or later, g_variant_dup_strv
        # returns the allocated strv but in the previous release,
        # it returned the tuple of (strv, length)
        if type(GLib.Variant.new_strv([]).dup_strv()) == tuple:
            return variant.dup_strv()[0]
        return variant.dup_strv()
    else:
        print('error: unknown variant type: %s' %type_string)
    return variant

if __name__ == "__main__":
    import doctest
    (FAILED, ATTEMPTED) = doctest.testmod()
    if FAILED:
        sys.exit(1)
    else:
        sys.exit(0)
