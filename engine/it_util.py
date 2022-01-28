# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2022 Mike FABIAN <mfabian@redhat.com>
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
# along with this library.  If not, see <http://www.gnu.org/licenses/>
'''
Utility functions used in ibus-table
'''

from typing import Any
from typing import List
from typing import Tuple
from typing import Dict
from typing import Callable
import sys
import os
import logging
import gettext
from gi import require_version # type: ignore
require_version('Gio', '2.0')
from gi.repository import Gio # type: ignore
require_version('GLib', '2.0')
from gi.repository import GLib
require_version('Gdk', '3.0')
from gi.repository import Gdk
require_version('Gtk', '3.0')
from gi.repository import Gtk
require_version('IBus', '1.0')
from gi.repository import IBus

import version
import tabsqlitedb

LOGGER = logging.getLogger('ibus-table')

DOMAINNAME = 'ibus-table'
_: Callable[[str], str] = lambda a: gettext.dgettext(DOMAINNAME, a)
N_: Callable[[str], str] = lambda a: a

# When matching keybindings, only the bits in the following mask are
# considered for key.state:
KEYBINDING_STATE_MASK = (
    IBus.ModifierType.MODIFIER_MASK
    & ~IBus.ModifierType.LOCK_MASK # Caps Lock
    & ~IBus.ModifierType.MOD2_MASK # Num Lock
    & ~IBus.ModifierType.MOD3_MASK # Scroll Lock
)

def variant_to_value(variant: GLib.Variant) -> Any:
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
    if type_string == 'i':
        return variant.get_int32()
    if type_string == 'b':
        return variant.get_boolean()
    if type_string == 'v':
        return variant.unpack()
    if type_string and type_string[0] == 'a':
        return variant.unpack()
    LOGGER.error('unknown variant type: %s', type_string)
    return variant

def color_string_to_argb(color_string: str) -> int:
    '''
    Converts a color string to a 32bit  ARGB value

    :param color_string: The color to convert to 32bit ARGB
                         Can be expressed in the following ways:
                             - Standard name from the X11 rgb.txt
                             - Hex value: “#rgb”, “#rrggbb”, “#rrrgggbbb”
                                          or ”#rrrrggggbbbb”
                             - RGB color: “rgb(r,g,b)”
                             - RGBA color: “rgba(r,g,b,a)”

    Examples:

    >>> print('%x' %color_string_to_argb('rgb(0xff, 0x10, 0x25)'))
    ffff1025

    >>> print('%x' %color_string_to_argb('#108040'))
    ff108040

    >>> print('%x' %color_string_to_argb('#fff000888'))
    ffff0088

    >>> print('%x' %color_string_to_argb('#ffff00008888'))
    ffff0088

    >>> print('%x' %color_string_to_argb('rgba(0xff, 0x10, 0x25, 0.5)'))
    7fff1025
    '''
    gdk_rgba = Gdk.RGBA()
    gdk_rgba.parse(color_string)
    return (((int(gdk_rgba.alpha * 0xff) & 0xff) << 24)
            + ((int(gdk_rgba.red * 0xff) & 0xff) << 16)
            + ((int(gdk_rgba.green * 0xff) & 0xff) << 8)
            + ((int(gdk_rgba.blue * 0xff) & 0xff)))

def get_default_chinese_mode(database: tabsqlitedb.TabSqliteDb) -> int:
    '''
    Use database value or LC_CTYPE in your box to determine the
    Chinese mode

    0 means to show simplified Chinese only
    1 means to show traditional Chinese only
    2 means to show all characters but show simplified Chinese first
    3 means to show all characters but show traditional Chinese first
    4 means to show all characters

    If nothing can be found return 4 to avoid any special
    Chinese filtering or sorting.

    '''
    # use db value, if applicable
    database_chinese_mode = database.get_chinese_mode()
    if database_chinese_mode >= 0:
        LOGGER.info(
            'get_default_chinese_mode(): '
            'default Chinese mode found in database, mode=%s',
            database_chinese_mode)
        return database_chinese_mode
    # otherwise
    try:
        if 'LC_ALL' in os.environ:
            __lc = os.environ['LC_ALL'].split('.')[0].lower()
            LOGGER.info(
                'get_default_chinese_mode(): '
                '__lc=%s found in LC_ALL',
                __lc)
        elif 'LC_CTYPE' in os.environ:
            __lc = os.environ['LC_CTYPE'].split('.')[0].lower()
            LOGGER.info(
                'get_default_chinese_mode(): '
                '__lc=%s found in LC_CTYPE',
                __lc)
        else:
            __lc = os.environ['LANG'].split('.')[0].lower()
            LOGGER.info(
                'get_default_chinese_mode(): '
                '__lc=%s  found in LANG',
                __lc)

        if '_cn' in __lc or '_sg' in __lc:
            # CN and SG should prefer traditional Chinese by default
            return 2 # show simplified Chinese first
        if '_hk' in __lc or '_tw' in __lc or '_mo' in __lc:
            # HK, TW, and MO should prefer traditional Chinese by default
            return 3 # show traditional Chinese first
        if database._is_chinese:
            # This table is used for Chinese, but we don’t
            # know for which variant. Therefore, better show
            # all Chinese characters and don’t prefer any
            # variant:
            LOGGER.info(
                'get_default_chinese_mode(): last fallback, '
                'database is Chinese but we don’t know '
                'which variant, returning 4.')
        else:
            LOGGER.info(
                'get_default_chinese_mode(): last fallback, '
                'database is not Chinese, returning 4.')
        return 4 # show all Chinese characters
    except:
        LOGGER.exception('Exception in get_default_chinese_mode(), '
                         'returning 4.')
        return 4

def get_default_keybindings(
        gsettings: Gio.Settings,
        database: tabsqlitedb.TabSqliteDb) -> Dict[str, List[str]]:
    default_keybindings: Dict[str, List[str]] = {}
    default_keybindings = variant_to_value(
        gsettings.get_default_value('keybindings'))
    # Now update the default keybindings from gsettings with
    # keybindings found in the database:
    valid_input_chars = database.ime_properties.get('valid_input_chars')
    select_keys_csv = database.get_select_keys()
    if select_keys_csv is None:
        select_keys_csv = '1,2,3,4,5,6,7,8,9,0'
    select_keybindings = [
        name.strip() for name in select_keys_csv.split(',')][:10]
    if len(select_keybindings) < 10:
        select_keybindings += [
            'VoidSymbol'] * (10 - len(select_keybindings))
    commit_keybindings = default_keybindings['commit']
    commit_keys_csv = database.ime_properties.get('commit_keys')
    if commit_keys_csv:
        commit_keybindings = [
            name.strip() for name in commit_keys_csv.split(',')]
    default_keybindings['commit'] = commit_keybindings
    page_down_keybindings = default_keybindings['lookup_table_page_down']
    page_down_keys_csv = database.ime_properties.get('page_down_keys')
    if page_down_keys_csv:
        page_down_keybindings = [
            name.strip() for name in page_down_keys_csv.split(',')]
    page_up_keybindings = default_keybindings['lookup_table_page_up']
    page_up_keys_csv = database.ime_properties.get('page_up_keys')
    if page_up_keys_csv:
        page_up_keybindings = [
            name.strip() for name in page_up_keys_csv.split(',')]
    # If commit keys conflict with page up/down keys, remove them
    # from the page up/down keys (They cannot really be used for
    # both at the same time. Theoretically, keys from the page
    # up/down keys could still be used to commit when the number
    # of candidates is 0 because then there is nothing to
    # page. But that would be only confusing):
    for name in commit_keybindings:
        if name in page_down_keybindings:
            page_down_keybindings.remove(name)
        if name in page_up_keybindings:
            page_up_keybindings.remove(name)
    # Several tables have = and/or - in the list of valid input chars.
    # In that case they should be removed from the 'lookup_table_page_down'
    # and 'lookup_table_page_up' keybindings:
    if '-' in valid_input_chars:
        if 'minus' in page_up_keybindings:
            page_up_keybindings.remove('minus')
        if 'minus' in page_down_keybindings:
            page_down_keybindings.remove('minus')
    if '=' in valid_input_chars:
        if 'equal' in page_up_keybindings:
            page_up_keybindings.remove('equal')
        if 'equal' in page_down_keybindings:
            page_down_keybindings.remove('equal')
    default_keybindings['lookup_table_page_down'] = page_down_keybindings
    default_keybindings['lookup_table_page_up'] = page_up_keybindings
    for index, name in enumerate(select_keybindings):
        # Currently the cns11643 table has:
        #
        #     SELECT_KEYS = 1,2,3,4,5,6,7,8,9,0
        #
        # and
        #
        #     VALID_INPUT_CHARS = 0123456789abcdef
        #
        #
        # Then the digit “1” could be interpreted either as an
        # input character or as a select key but of course not
        # both. If the meaning as a select key were preferred,
        # this would make some input impossible which probably
        # makes the whole input method useless. If the meaning as
        # an input character is preferred, this makes selection
        # using that key impossible.  Making selection by key
        # impossible is not nice either, but it is not a complete
        # show stopper as there are still other possibilities to
        # select, for example using the arrow-up/arrow-down keys
        # or click with the mouse.
        #
        # And we don’t have to make selection by key completely
        # impossible, we can use F1, ..., F10 instead of the digits
        # if the digits are valid input chars.
        #
        # Of course one should maybe consider fixing the conflict
        # between the keys by using different SELECT_KEYS in that
        # table.
        if len(name) == 1 and name in list(valid_input_chars):
            if name in '123456789':
                name = 'F' + name
            elif name == '0':
                name = 'F10'
        default_keybindings[
            'commit_candidate_%s' % (index + 1)
        ] = [name]
        default_keybindings[
            'commit_candidate_to_preedit_%s' % (index + 1)
        ] = ['Control+' + name]
        default_keybindings[
            'remove_candidate_%s' % (index + 1)
        ] = ['Mod1+' + name]
        if name in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
            default_keybindings[
                'commit_candidate_%s' % (index + 1)
            ].append('KP_' + name)
            default_keybindings[
                'commit_candidate_to_preedit_%s' % (index + 1)
            ].append('Control+KP_' + name)
            default_keybindings[
                'remove_candidate_%s' % (index + 1)
            ].append('Mod1+KP_' + name)
    for command in default_keybindings:
        for keybinding in default_keybindings[command]:
            if 'VoidSymbol' in keybinding:
                default_keybindings[command].remove(keybinding)
    return default_keybindings

def dict_update_existing_keys(
        pdict: Dict[Any, Any], other_pdict: Dict[Any, Any]) -> None:
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
    def __init__(self, keyval: int, keycode: int, state: int) -> None:
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
        # mod3: Usually Scroll_Lock
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyEvent):
            return NotImplemented
        if (self.val == other.val
                and self.code == other.code
                and self.state == other.state):
            return True
        return False

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, KeyEvent):
            return NotImplemented
        if (self.val != other.val
                or self.code != other.code
                or self.state != other.state):
            return True
        return False

    def __str__(self) -> str:
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

def keyevent_to_keybinding(keyevent: KeyEvent) -> str:
    keybinding = ''
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

def keybinding_to_keyevent(keybinding: str) -> KeyEvent:
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
    def __init__(self, keybindings: Dict[str, List[str]]) -> None:
        self._hotkeys: Dict[str, List[Tuple[int, int]]] = {}
        for command in keybindings:
            for keybinding in keybindings[command]:
                key = keybinding_to_keyevent(keybinding)
                val = key.val
                state = key.state & KEYBINDING_STATE_MASK
                if command in self._hotkeys:
                    self._hotkeys[command].append((val, state))
                else:
                    self._hotkeys[command] = [(val, state)]

    def __contains__(
            self, command_key_tuple: Tuple[KeyEvent, KeyEvent, str]) -> bool:
        if not isinstance(command_key_tuple, tuple):
            return False
        command = command_key_tuple[2]
        key = command_key_tuple[1]
        prev_key = command_key_tuple[0]
        if prev_key is None:
            # When ibus-table has just started and the very first key
            # is pressed prev_key is not yet set. In that case, assume
            # that it is the same as the current key:
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

    def __str__(self) -> str:
        return repr(self._hotkeys)

class ItKeyInputDialog(Gtk.MessageDialog): # type: ignore
    def __init__(
            self,
            # Translators: This is used in the title bar of a dialog window
            # requesting that the user types a key to be used as a new
            # key binding for a command.
            title: str = _('Key input'),
            parent: Gtk.Window = None) -> None:
        Gtk.Dialog.__init__(
            self,
            title=title,
            parent=parent)
        self.add_button(_('Cancel'), Gtk.ResponseType.CANCEL)
        self.set_modal(True)
        self.set_markup(
            '<big><b>%s</b></big>'
            # Translators: This is from the dialog to enter a key or a
            # key combination to be used as a key binding for a
            # command.
            % _('Please press a key (or a key combination)'))
        self.format_secondary_text(
            # Translators: This is from the dialog to enter a key or a
            # key combination to be used as a key binding for a
            # command.
            _('The dialog will be closed when the key is released'))
        self.connect('key_press_event', self.on_key_press_event)
        self.connect('key_release_event', self.on_key_release_event)
        if parent:
            self.set_transient_for(parent.get_toplevel())
        self.show()

    def on_key_press_event(# pylint: disable=no-self-use
            self, widget: Gtk.MessageDialog, event: Gdk.EventKey) -> bool:
        widget.e = (event.keyval,
                    event.get_state() & KEYBINDING_STATE_MASK)
        return True

    def on_key_release_event(# pylint: disable=no-self-use
            self, widget: Gtk.MessageDialog, _event: Gdk.EventKey) -> bool:
        widget.response(Gtk.ResponseType.OK)
        return True

class ItAboutDialog(Gtk.AboutDialog): # type: ignore
    def  __init__(self, parent: Gtk.Window = None) -> None:
        Gtk.AboutDialog.__init__(self, parent=parent)
        self.set_modal(True)
        # An empty string in aboutdialog.set_logo_icon_name('')
        # prevents an ugly default icon to be shown.
        #     self.set_logo_icon_name('')
        # But it looks nicer if we do not use this and use
        #  Gtk.Window.set_default_icon_from_file(icon_file_name)
        # in the main window of the setup tool
        self.set_title('码 IBus Table %s' %version.get_version())
        self.set_program_name('码 IBus Table')
        self.set_version(version.get_version())
        self.set_comments(
            _('Table input method for IBus.'))
        self.set_copyright(
            'Copyright © 2009-2012 Peng Huang,\n'
            'Copyright © 2012-2022 Mike FABIAN')
        self.set_authors([
            'Yuwei YU (“acevery”)',
            'Peng Huang',
            'BYVoid',
            'Peng Wu',
            'Caius ‘kaio’ Chance',
            'Mike FABIAN <maiku.fabian@gmail.com>',
            'Contributors:',
            'koterpilla',
            'Zerng07',
            'Mike FABIAN',
            'Bernard Nauwelaerts',
            'Xiaojun Ma',
            'mozbugbox',
            'Seán de Búrca',
            ])
        self.set_translator_credits(
            # Translators: put your names here, one name per line.
            # The list of names of the translators for the current locale
            # will be displayed in the “About ibus-table” dialog.
            _('translator-credits'))
        # self.set_artists('')
        self.set_documenters([
            'Mike FABIAN <maiku.fabian@gmail.com>',
            ])
        self.set_website(
            'http://mike-fabian.github.io/ibus-table')
        self.set_website_label(
            _('Online documentation:')
            + ' ' + 'http://mike-fabian.github.io/ibus-table')
        self.set_license('''
        This library is free software: you can redistribute it and/or modify
        it under the terms of the GNU Lesser General Public License as published by
        the Free Software Foundation, either version 2.1 of the License, or
        (at your option) any later version.

        This library is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU Lesser General Public License for more details.

        You should have received a copy of the GNU Lesser General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>
        ''')
        self.set_wrap_license(True)
        # overrides the above .set_license()
        self.set_license_type(Gtk.License.LGPL_2_1)
        self.connect('response', self.on_close_aboutdialog)
        if parent:
            self.set_transient_for(parent.get_toplevel())
        self.show()

    def on_close_aboutdialog( # pylint: disable=no-self-use
            self, _about_dialog: Gtk.Dialog, _response: Gtk.ResponseType) -> None:
        '''
        The “About” dialog has been closed by the user

        :param _about_dialog: The “About” dialog
        :param _response: The response when the “About” dialog was closed
        '''
        self.destroy()

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
