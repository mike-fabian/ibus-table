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
import logging
from gi import require_version
require_version('GLib', '2.0')
from gi.repository import GLib
require_version('IBus', '1.0')
from gi.repository import IBus

LOGGER = logging.getLogger('ibus-table')

# When matching keybindings, only the bits in the following mask are
# considered for key.state:
KEYBINDING_STATE_MASK = (
    IBus.ModifierType.MODIFIER_MASK
    & ~IBus.ModifierType.LOCK_MASK # Caps Lock
    & ~IBus.ModifierType.MOD2_MASK # Num Lock
)

def variant_to_value(variant):
    '''
    Convert a GLib variant to a value
    '''
    # pylint: disable=unidiomatic-typecheck
    if type(variant) != GLib.Variant:
        LOGGER.info('not a GLib.Variant')
        return variant
    type_string = variant.get_type_string()
    if type_string == 's':
        return variant.get_string()
    elif type_string == 'i':
        return variant.get_int32()
    elif type_string == 'b':
        return variant.get_boolean()
    if type_string == 'v':
        return variant.unpack()
    if type_string and type_string[0] == 'a':
        return variant.unpack()
    LOGGER.error('unknown variant type: %s', type_string)
    return variant

def dict_update_existing_keys(pdict, other_pdict):
    '''Update values of existing keys in a Python dict from another Python dict

    Using pdict.update(other_pdict) would add keys and values from other_pdict
    to pdict even for keys which do not exist in pdict. Sometimes I want
    to update only existing keys and ignore new keys.

    :param pdict: The Python dict to update
    :type pdict: Python dict
    :param other_pdict: The Python dict to get the updates from
    :type other_pdict: Python dict

    Examples:

    >>> old_pdict = {'a': 1, 'b': 2}
    >>> new_pdict = {'b': 3, 'c': 4}
    >>> dict_update_existing_keys(old_pdict, new_pdict)
    >>> old_pdict
    {'a': 1, 'b': 3}
    >>> old_pdict.update(new_pdict)
    >>> old_pdict
    {'a': 1, 'b': 3, 'c': 4}
    '''
    for key in other_pdict:
        if key in pdict:
            pdict[key] = other_pdict[key]

class KeyEvent:
    '''Key event class used to make the checking of details of the key
    event easy
    '''
    def __init__(self, keyval, keycode, state):
        self.val = keyval
        self.code = keycode
        self.state = state
        self.name = IBus.keyval_name(self.val)
        self.unicode = IBus.keyval_to_unicode(self.val)
        self.shift = self.state & IBus.ModifierType.SHIFT_MASK != 0
        self.lock = self.state & IBus.ModifierType.LOCK_MASK != 0
        self.control = self.state & IBus.ModifierType.CONTROL_MASK != 0
        self.super = self.state & IBus.ModifierType.SUPER_MASK != 0
        self.hyper = self.state & IBus.ModifierType.HYPER_MASK != 0
        self.meta = self.state & IBus.ModifierType.META_MASK != 0
        # mod1: Usually Alt_L (0x40),  Alt_R (0x6c),  Meta_L (0xcd)
        self.mod1 = self.state & IBus.ModifierType.MOD1_MASK != 0
        # mod2: Usually Num_Lock (0x4d)
        self.mod2 = self.state & IBus.ModifierType.MOD2_MASK != 0
        self.mod3 = self.state & IBus.ModifierType.MOD3_MASK != 0
        # mod4: Usually Super_L (0xce),  Hyper_L (0xcf)
        self.mod4 = self.state & IBus.ModifierType.MOD4_MASK != 0
        # mod5: ISO_Level3_Shift (0x5c),  Mode_switch (0xcb)
        self.mod5 = self.state & IBus.ModifierType.MOD5_MASK != 0
        self.button1 = self.state & IBus.ModifierType.BUTTON1_MASK != 0
        self.button2 = self.state & IBus.ModifierType.BUTTON2_MASK != 0
        self.button3 = self.state & IBus.ModifierType.BUTTON3_MASK != 0
        self.button4 = self.state & IBus.ModifierType.BUTTON4_MASK != 0
        self.button5 = self.state & IBus.ModifierType.BUTTON5_MASK != 0
        self.release = self.state & IBus.ModifierType.RELEASE_MASK != 0
        # MODIFIER_MASK: Modifier mask for the all the masks above
        self.modifier = self.state & IBus.ModifierType.MODIFIER_MASK != 0

    def __eq__(self, other):
        if (self.val == other.val
                and self.code == other.code
                and self.state == other.state):
            return True
        return False

    def __ne__(self, other):
        if (self.val != other.val
                or self.code != other.code
                or self.state != other.state):
            return True
        return False

    def __str__(self):
        return (
            "val=%s code=%s state=0x%08x name='%s' unicode='%s' "
            % (self.val,
               self.code,
               self.state,
               self.name,
               self.unicode)
            + "shift=%s lock=%s control=%s super=%s hyper=%s meta=%s "
            % (self.shift,
               self.lock,
               self.control,
               self.super,
               self.hyper,
               self.meta)
            + "mod1=%s mod5=%s release=%s\n"
            % (self.mod1,
               self.mod5,
               self.release))

def keyevent_to_keybinding(keyevent):
    keybinding=''
    if keyevent.shift:
        keybinding += 'Shift+'
    if keyevent.lock:
        keybinding += 'Lock+'
    if keyevent.control:
        keybinding += 'Control+'
    if keyevent.super:
        keybinding += 'Super+'
    if keyevent.hyper:
        keybinding += 'Hyper+'
    if keyevent.meta:
        keybinding += 'Meta+'
    if keyevent.mod1:
        keybinding += 'Mod1+'
    if keyevent.mod2:
        keybinding += 'Mod2+'
    if keyevent.mod3:
        keybinding += 'Mod3+'
    if keyevent.mod4:
        keybinding += 'Mod4+'
    if keyevent.mod5:
        keybinding += 'Mod5+'
    keybinding += keyevent.name
    return keybinding

def keybinding_to_keyevent(keybinding):
    name = keybinding.split('+')[-1]
    keyval = IBus.keyval_from_name(name)
    state = 0
    if 'Shift+' in keybinding:
        state |= IBus.ModifierType.SHIFT_MASK
    if 'Lock+' in keybinding:
        state |= IBus.ModifierType.LOCK_MASK
    if 'Control+' in keybinding:
        state |= IBus.ModifierType.CONTROL_MASK
    if 'Super+' in keybinding:
        state |= IBus.ModifierType.SUPER_MASK
    if 'Hyper+' in keybinding:
        state |= IBus.ModifierType.HYPER_MASK
    if 'Meta+' in keybinding:
        state |= IBus.ModifierType.META_MASK
    if 'Mod1+' in keybinding:
        state |= IBus.ModifierType.MOD1_MASK
    if 'Mod2+' in keybinding:
        state |= IBus.ModifierType.MOD2_MASK
    if 'Mod3+' in keybinding:
        state |= IBus.ModifierType.MOD3_MASK
    if 'Mod4+' in keybinding:
        state |= IBus.ModifierType.MOD4_MASK
    if 'Mod5+' in keybinding:
        state |= IBus.ModifierType.MOD5_MASK
    return KeyEvent(keyval, 0, state)

class HotKeys:
    '''Class to make checking whether a key matches a hotkey for a certain
    command easy
    '''
    def __init__(self, keybindings):
        self._hotkeys = {}
        for command in keybindings:
            for keybinding in keybindings[command]:
                key = keybinding_to_keyevent(keybinding)
                val = key.val
                state = key.state & KEYBINDING_STATE_MASK
                if command in self._hotkeys:
                    self._hotkeys[command].append((val, state))
                else:
                    self._hotkeys[command] = [(val, state)]

    def __contains__(self, command_key_tuple):
        if not isinstance(command_key_tuple, tuple):
            return False
        command = command_key_tuple[2]
        key = command_key_tuple[1]
        prev_key = command_key_tuple[0]
        if prev_key is None:
            # When ibus-table has just started and the very first key is pressed
            # prev_key is not yet set. In that case, assume that it is the same
            # as the current key:
            prev_key = key
        val = key.val
        state = key.state # Do not change key.state, only the copy!
        if key.name in ('Shift_L', 'Shift_R',
                        'Control_L', 'Control_R',
                        'Alt_L', 'Alt_R',
                        'Meta_L', 'Meta_R',
                        'Super_L', 'Super_R',
                        'ISO_Level3_Shift'):
            # For these modifier keys, match on the release event
            # *and* make sure that the previous key pressed was
            # exactly the same key. Then we know that for example only
            # Shift_L was pressed and then released with nothing in
            # between.  For example it could not have been something
            # like “Shift_L” then “a” followed by releasing the “a”
            # and the “Shift_L”.
            if (prev_key.val != val
                or not state & IBus.ModifierType.RELEASE_MASK):
                return False
            state &= ~IBus.ModifierType.RELEASE_MASK
            if key.name in ('Shift_L', 'Shift_R'):
                state &= ~IBus.ModifierType.SHIFT_MASK
            elif key.name in ('Control_L', 'Control_R'):
                state &= ~IBus.ModifierType.CONTROL_MASK
            elif key.name in ('Alt_L', 'Alt_R'):
                state &= ~IBus.ModifierType.MOD1_MASK
            elif key.name in ('Super_L', 'Super_R'):
                state &= ~IBus.ModifierType.SUPER_MASK
                state &= ~IBus.ModifierType.MOD4_MASK
            elif key.name in ('Meta_L', 'Meta_R'):
                state &= ~IBus.ModifierType.META_MASK
                state &= ~IBus.ModifierType.MOD1_MASK
            elif key.name in ('ISO_Level3_Shift',):
                state &= ~IBus.ModifierType.MOD5_MASK
        state = state & KEYBINDING_STATE_MASK
        if command in self._hotkeys:
            if (val, state) in self._hotkeys[command]:
                return True
        return False

    def __str__(self):
        return repr(self._hotkeys)

if __name__ == "__main__":
    LOG_HANDLER = logging.StreamHandler(stream=sys.stderr)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(LOG_HANDLER)
    import doctest
    (FAILED, ATTEMPTED) = doctest.testmod()
    if FAILED:
        sys.exit(1)
    else:
        sys.exit(0)
