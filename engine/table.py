# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2014 Mike FABIAN <mfabian@redhat.com>
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

__all__ = (
    "tabengine",
)

import sys
import os
import string
from gi.repository import IBus
from gi.repository import GLib
#import tabsqlitedb
import re
from gi.repository import GObject
import time
import chinese_variants

debug_level = int(0)

from gettext import dgettext
_  = lambda a : dgettext ("ibus-table", a)
N_ = lambda a : a


def ascii_ispunct(character):
    '''
    Use our own function instead of ascii.ispunct()
    from “from curses import ascii” because the behaviour
    of the latter is kind of weird. In Python 3.3.2 it does
    for example:

        >>> from curses import ascii
        >>> ascii.ispunct('.')
        True
        >>> ascii.ispunct(u'.')
        True
        >>> ascii.ispunct('a')
        False
        >>> ascii.ispunct(u'a')
        False
        >>>
        >>> ascii.ispunct(u'あ')
        True
        >>> ascii.ispunct('あ')
        True
        >>>

    あ isn’t punctuation. ascii.ispunct() only really works
    in the ascii range, it returns weird results when used
    over the whole unicode range. Maybe we should better use
    unicodedata.category(), which works fine to figure out
    what is punctuation for all of unicode. But at the moment
    I am only porting from Python2 to Python3 and just want to
    preserve the original behaviour for the moment.
    '''
    if character in '''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~''':
        return True
    else:
        return False

def variant_to_value(variant):
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
        else:
            return variant.dup_strv()
    else:
        print('error: unknown variant type: %s' %type_string)
    return variant

def argb(a, r, g, b):
    return ((a & 0xff)<<24) + ((r & 0xff) << 16) + ((g & 0xff) << 8) + (b & 0xff)

def rgb(r, g, b):
    return argb(255, r, g, b)

__half_full_table = [
    (0x0020, 0x3000, 1),
    (0x0021, 0xFF01, 0x5E),
    (0x00A2, 0xFFE0, 2),
    (0x00A5, 0xFFE5, 1),
    (0x00A6, 0xFFE4, 1),
    (0x00AC, 0xFFE2, 1),
    (0x00AF, 0xFFE3, 1),
    (0x20A9, 0xFFE6, 1),
    (0xFF61, 0x3002, 1),
    (0xFF62, 0x300C, 2),
    (0xFF64, 0x3001, 1),
    (0xFF65, 0x30FB, 1),
    (0xFF66, 0x30F2, 1),
    (0xFF67, 0x30A1, 1),
    (0xFF68, 0x30A3, 1),
    (0xFF69, 0x30A5, 1),
    (0xFF6A, 0x30A7, 1),
    (0xFF6B, 0x30A9, 1),
    (0xFF6C, 0x30E3, 1),
    (0xFF6D, 0x30E5, 1),
    (0xFF6E, 0x30E7, 1),
    (0xFF6F, 0x30C3, 1),
    (0xFF70, 0x30FC, 1),
    (0xFF71, 0x30A2, 1),
    (0xFF72, 0x30A4, 1),
    (0xFF73, 0x30A6, 1),
    (0xFF74, 0x30A8, 1),
    (0xFF75, 0x30AA, 2),
    (0xFF77, 0x30AD, 1),
    (0xFF78, 0x30AF, 1),
    (0xFF79, 0x30B1, 1),
    (0xFF7A, 0x30B3, 1),
    (0xFF7B, 0x30B5, 1),
    (0xFF7C, 0x30B7, 1),
    (0xFF7D, 0x30B9, 1),
    (0xFF7E, 0x30BB, 1),
    (0xFF7F, 0x30BD, 1),
    (0xFF80, 0x30BF, 1),
    (0xFF81, 0x30C1, 1),
    (0xFF82, 0x30C4, 1),
    (0xFF83, 0x30C6, 1),
    (0xFF84, 0x30C8, 1),
    (0xFF85, 0x30CA, 6),
    (0xFF8B, 0x30D2, 1),
    (0xFF8C, 0x30D5, 1),
    (0xFF8D, 0x30D8, 1),
    (0xFF8E, 0x30DB, 1),
    (0xFF8F, 0x30DE, 5),
    (0xFF94, 0x30E4, 1),
    (0xFF95, 0x30E6, 1),
    (0xFF96, 0x30E8, 6),
    (0xFF9C, 0x30EF, 1),
    (0xFF9D, 0x30F3, 1),
    (0xFFA0, 0x3164, 1),
    (0xFFA1, 0x3131, 30),
    (0xFFC2, 0x314F, 6),
    (0xFFCA, 0x3155, 6),
    (0xFFD2, 0x315B, 9),
    (0xFFE9, 0x2190, 4),
    (0xFFED, 0x25A0, 1),
    (0xFFEE, 0x25CB, 1)]

def unichar_half_to_full (c):
    code = ord (c)
    for half, full, size in __half_full_table:
        if code >= half and code < half + size:
            if sys.version_info >= (3,0,0):
                return chr (full + code - half)
            else:
                return unichr (full + code - half)
    return c

def unichar_full_to_half (c):
    code = ord (c)
    for half, full, size in __half_full_table:
        if code >= full and code < full + size:
            if sys.version_info >= (3,0,0):
                return chr (half + code - full)
            else:
                return unichr (half + code - full)
    return c

SAVE_USER_COUNT_MAX = 16
SAVE_USER_TIMEOUT = 30 # in seconds

class KeyEvent:
    def __init__(self, keyval, is_press, state):
        self.code = keyval
        self.mask = state
        if not is_press:
            self.mask |= IBus.ModifierType.RELEASE_MASK
    def __str__(self):
        return "%s 0x%08x" % (IBus.keyval_name(self.code), self.mask)


class editor(object):
    '''Hold user inputs chars and preedit string'''
    def __init__ (self, config, phrase_table_index,valid_input_chars, max_key_length, database):
        self.db = database
        self._config = config
        engine_name = os.path.basename(self.db.filename).replace('.db', '')
        self._config_section = "engine/Table/%s" %engine_name.replace(' ','_')
        self._pt = phrase_table_index
        self._max_key_len = int(max_key_length)
        self._valid_input_chars = valid_input_chars
        #
        # The values below will be reset in self.clear()
        self._chars_valid = u''    # valid user input in table mode
        self._chars_invalid = u''  # invalid user input in table mode
        self._chars_valid_when_update_candidates_was_last_called = u''
        self._tabkeys = u'' # the input characters typed by the user
        # self._u_chars: holds the user input of the phrases which
        # have been automatically committed to preedit (but not yet
        # “really” committed).
        self._u_chars = []
        # self._strings: holds the phrases which have been
        # automatically committed to preedit (but not yet “really”
        # committed).
        #
        # self._u_chars and self._strings should always have the same
        # length, if I understand it correctly.
        #
        # Example when using the wubi-jidian86 table:
        #
        # self._u_chars = ['gaaa', 'gggg', 'ihty']
        # self._strings = ['形式', '王', '小']
        #
        # I.e. after typing 'gaaa', '形式' is in the preedit and
        # both self._u_chars and self._strings are empty. When typing
        # another 'g', the maximum key length of the wubi table (which is 4)
        # is exceeded and '形式' is automatically committed to the preedit
        # (but not yet “really” committed, i.e. not yet committed into
        # the application). The key 'gaaa' and the matching phrase '形式'
        # are stored in self._u_chars and self._strings respectively
        # and 'gaaa' is removed from self._chars_valid. Now self._chars_valid
        # contains only the 'g' which starts a new search for candidates ...
        # When removing the 'g' with backspace, the 'gaaa' is moved
        # back from self._u_chars into self._chars_valid again and
        # the same candidate list is shown as before the last 'g' had
        # been entered.
        self._strings = []
        # self._cursor_precommit: The cursor
        # position inthe array of strings which have already been
        # committed to preëdit but not yet “really” committed.
        self._cursor_precommit = 0
        # self._candidates holds the “best” candidates matching the user input
        # [(tabkeys, phrase, freq, user_freq), ...]
        self._candidates = []
        self._candidate_previous = []
        # __orientation: lookup table orientation
        __orientation = variant_to_value(self._config.get_value(
                self._config_section,
                "LookupTableOrientation"))
        if __orientation == None:
                __orientation = self.db.get_orientation()
        # __page_size: lookup table page size
        # this is computed from the select_keys, so should be done after it
        __page_size = self.db.get_page_size()
        self._lookup_table = IBus.LookupTable.new(
            page_size=__page_size,
            cursor_pos=0,
            cursor_visible=True,
            round=True)
        self._lookup_table.set_orientation (__orientation)
        # self._select_keys: a list of chars for select keys
        self.init_select_keys()
        # self._py_mode: whether in pinyin mode
        self._py_mode = False
        # self._zi: the last Zi commit to preedit
        self._zi = u''
        # self._onechar: whether we only select single character
        self._onechar = variant_to_value(self._config.get_value(
                self._config_section,
                "OneChar"))
        if self._onechar == None:
            self_onechar = False
        # self._chinese_mode: the candidate filter mode,
        #   0 means to show simplified Chinese only
        #   1 means to show traditional Chinese only
        #   2 means to show all characters but show simplified Chinese first
        #   3 means to show all characters but show traditional Chinese first
        #   4 means to show all characters
        # we use LC_CTYPE or LANG to determine which one to use
        self._chinese_mode = variant_to_value(self._config.get_value(
                self._config_section,
                "ChineseMode"))
        if self._chinese_mode == None:
            self._chinese_mode = self.get_chinese_mode()

        # If auto select is true, then the first candidate phrase will
        # be selected automatically during typing. Auto select is true
        # by default for the stroke5 table for example.
        self._auto_select = variant_to_value(self._config.get_value(
                self._config_section,
                "AutoSelect"))
        if self._auto_select == None:
            if self.db.get_ime_property('auto_select') != None:
                self._auto_select = self.db.get_ime_property('auto_select').lower() == u'true'
            else:
                self._auto_select = False

    def init_select_keys(self):
        # __select_keys: lookup table select keys/labels
        __select_keys = variant_to_value(self._config.get_value(
                self._config_section,
                "LookupTableSelectKeys"))
        if __select_keys == None:
            __select_keys = self.db.get_select_keys()
        if __select_keys:
            self.set_select_keys(__select_keys)

    def set_select_keys(self, astring):
        """astring: select keys setting. e.g. 1,2,3,4,5,6,7,8,9"""
        self._select_keys = [x.strip() for x in astring.split(",")]
        for x in self._select_keys:
            self._lookup_table.append_label(IBus.Text.new_from_string("{}.".format(x)))

    def get_select_keys(self):
        """@return: a list of chars as select keys: ["1", "2", ...]"""
        return self._select_keys

    def get_chinese_mode (self):
        '''Use db value or LC_CTYPE in your box to determine the _chinese_mode'''
        # use db value, if applicable
        __db_chinese_mode = self.db.get_chinese_mode()
        if __db_chinese_mode >= 0:
            return __db_chinese_mode
        # otherwise
        try:
            if 'LC_ALL' in os.environ:
                __lc = os.environ['LC_ALL'].split('.')[0].lower()
            elif 'LC_CTYPE' in os.environ:
                __lc = os.environ['LC_CTYPE'].split('.')[0].lower()
            else:
                __lc = os.environ['LANG'].split('.')[0].lower()

            if __lc.find('_cn') != -1:
                return 0
            # HK and TW should use traditional Chinese by default
            elif __lc.find('_hk') != -1 or __lc.find('_tw') != -1\
                    or __lc.find('_mo') != -1:
                return 1
            else:
                if self.db._is_chinese:
                    # if IME declare as Chinese IME
                    return 0
                else:
                    return -1
        except:
            import traceback
            traceback.print_exc()
            return -1

    def change_chinese_mode (self):
        if self._chinese_mode != -1:
            self._chinese_mode = (self._chinese_mode +1 ) % 5
        self._config.set_value (
                self._config_section,
                "ChineseMode",
                GLib.Variant.new_int32(self._chinese_mode))

    def clear (self):
        '''Remove data holded'''
        self.clear_input()
        self._u_chars = []
        self._strings = []
        self._cursor_precommit = 0
        self._zi = u''
        self.update_candidates()

    def is_empty(self):
        return u'' == self._chars_valid + self._chars_invalid

    def clear_input (self):
        '''
        Remove input characters held for Table mode,
        '''
        self._chars_valid = u''
        self._chars_invalid = u''
        self._chars_valid_when_update_candidates_was_last_called = u''
        self._tabkeys = u''
        self._lookup_table.clear()
        self._lookup_table.set_cursor_visible(True)
        self._candidates = []
        self._candidates_previous = []

    def add_input(self,c):
        '''add input character'''
        self._zi = u''
        if (len(self._chars_valid) == self._max_key_len and (not self._py_mode)) or (len(self._chars_valid) == 7 and self._py_mode ) :
            self.auto_commit_to_preedit()
            res = self.add_input (c)
            return res
        elif self._chars_invalid:
            self._chars_invalid += c
        else:
            if (not self._py_mode and ( c in self._valid_input_chars)) or\
                (self._py_mode and (c in u'abcdefghijklmnopqrstuvwxyz!@#$%')):
                self._tabkeys += c
                self._chars_valid += c
            else:
                self._chars_invalid += c
        res = self.update_candidates ()
        return res

    def pop_input(self):
        '''remove and display last input char held'''
        _c =''
        if self._chars_invalid:
            _c = self._chars_invalid[-1]
            self._chars_invalid = self._chars_invalid[:-1]
        elif self._chars_valid:
            _c = self._chars_valid[-1]
            self._chars_valid = self._chars_valid[:-1]
            self._tabkeys = self._tabkeys[:-1]
            if (not self._chars_valid) and self._u_chars:
                self._chars_valid = self._u_chars.pop(self._cursor_precommit - 1)
                self._tabkeys = self._chars_valid
                self._strings.pop(self._cursor_precommit - 1)
                self._cursor_precommit -= 1
        self.update_candidates ()
        return _c

    def get_input_chars (self):
        '''get characters held, valid and invalid'''
        return self._chars_valid + self._chars_invalid

    def get_all_input_strings (self):
        '''Get all uncommitted input characters, used in English mode or direct commit'''
        (left_tabkeys,
         current_tabkeys,
         right_tabkeys) = self.get_preedit_tabkeys_parts()
        return  u''.join(left_tabkeys) + current_tabkeys + u''.join(right_tabkeys)

    def split_strings_committed_to_preedit(self, index, index_in_phrase):
        head = self._strings[index][:index_in_phrase]
        tail = self._strings[index][index_in_phrase:]
        self._u_chars.pop(index)
        self._strings.pop(index)
        self._u_chars.insert(index, self.db.parse_phrase(head))
        self._strings.insert(index, head)
        self._u_chars.insert(index+1, self.db.parse_phrase(tail))
        self._strings.insert(index+1, tail)

    def remove_preedit_before_cursor(self):
        '''Remove preëdit left of cursor'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit <= 0:
            return
        self._u_chars = self._u_chars[self._cursor_precommit:]
        self._strings = self._strings[self._cursor_precommit:]
        self._cursor_precommit = 0

    def remove_preedit_after_cursor(self):
        '''Remove preëdit right of cursor'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit >= len(self._strings):
            return
        self._u_chars = self._u_chars[:self._cursor_precommit]
        self._strings = self._strings[:self._cursor_precommit]
        self._cursor_precommit = len(self._strings)

    def remove_preedit_character_before_cursor(self):
        '''Remove character before cursor in strings comitted to preëdit'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit < 1:
            return
        self._cursor_precommit -= 1
        self._chars_valid = self._u_chars.pop(self._cursor_precommit)
        self._strings.pop(self._cursor_precommit)
        self.update_candidates()

    def remove_preedit_character_after_cursor (self):
        '''Remove character after cursor in strings committed to preëdit'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit > len(self._strings) - 1:
            return
        self._u_chars.pop(self._cursor_precommit)
        self._strings.pop(self._cursor_precommit)

    def get_preedit_tabkeys_parts(self):
        '''Returns the tabkeys which were used to type the parts
        of the preëdit string.

        Such as “(left_of_current_edit, current_edit, right_of_current_edit)”

        “left_of_current_edit” and “right_of_current_edit” are
        strings of tabkeys which have been typed to get the phrases
        which have already been committed to preëdit, but not
        “really” committed yet. “current_edit” is the string of
        tabkeys of the part of the preëdit string which is not
        committed at all.

        For example, the return value could look like:

        (('gggg', 'aahw'), 'adwu', ('ijgl', 'jbus'))

        See also get_preedit_string_parts() which might return something
        like

        (('王', '工具'), '其', ('漫画', '最新'))

        when the wubi-jidian86 table is used.
        '''
        left_of_current_edit = ()
        current_edit = u''
        right_of_current_edit = ()
        if self.get_input_chars():
            current_edit = self.get_input_chars()
        if self._u_chars:
            left_of_current_edit = tuple(self._u_chars[:self._cursor_precommit])
            right_of_current_edit = tuple(self._u_chars[self._cursor_precommit:])
        return (left_of_current_edit, current_edit, right_of_current_edit)

    def get_preedit_string_parts(self):
        '''Returns the phrases which are parts of the preëdit string.

        Such as “(left_of_current_edit, current_edit, right_of_current_edit)”

        “left_of_current_edit” and “right_of_current_edit” are
        tuples of strings which have already been committed to preëdit, but not
        “really” committed yet. “current_edit” is the phrase in the part of the
        preëdit string which is not yet committed at all.

        For example, the return value could look like:

        (('王', '工具'), '其', ('漫画', '最新'))

        See also get_preedit_tabkeys_parts() which might return something
        like

        (('gggg', 'aahw'), 'adwu', ('ijgl', 'jbus'))

        when the wubi-jidian86 table is used.
        '''
        left_of_current_edit = ()
        current_edit = u''
        right_of_current_edit = ()
        if self._candidates:
            current_edit = self._candidates[
                int(self._lookup_table.get_cursor_pos())][1]
        elif self.get_input_chars():
                current_edit = self.get_input_chars()
        if self._strings:
            left_of_current_edit = tuple(self._strings[:self._cursor_precommit])
            right_of_current_edit = tuple(self._strings[self._cursor_precommit:])
        return (left_of_current_edit, current_edit, right_of_current_edit)

    def get_preedit_string_complete(self):
        (left_strings,
         current_string,
         right_strings) = self.get_preedit_string_parts()
        return u''.join(left_strings) + current_string + u''.join(right_strings)

    def get_caret (self):
        '''Get caret position in preëdit string'''
        caret = 0
        if self._cursor_precommit and self._strings:
            for x in self._strings[:self._cursor_precommit]:
                caret += len(x)
        if self._candidates:
            caret += len(
                self._candidates[int(self._lookup_table.get_cursor_pos())][1])
        else:
            caret += len(self.get_input_chars())
        return caret

    def arrow_left(self):
        '''Move cursor left in the preëdit string.'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit <= 0:
            return
        if len(self._strings[self._cursor_precommit-1]) <= 1:
            self._cursor_precommit -= 1
        else:
            self.split_strings_committed_to_preedit(self._cursor_precommit-1, -1)
        self.update_candidates()

    def arrow_right(self):
        '''Move cursor right in the preëdit string.'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        if self._cursor_precommit >= len(self._strings):
            return
        self._cursor_precommit += 1
        if len(self._strings[self._cursor_precommit-1]) > 1:
            self.split_strings_committed_to_preedit(self._cursor_precommit-1, 1)
        self.update_candidates()

    def control_arrow_left(self):
        '''Move cursor to the beginning of the preëdit string.'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        self._cursor_precommit = 0
        self.update_candidates ()

    def control_arrow_right(self):
        '''Move cursor to the end of the preëdit string'''
        if self._chars_invalid:
            return
        if self.get_input_chars():
            self.commit_to_preedit()
        if not self._strings:
            return
        self._cursor_precommit = len(self._strings)
        self.update_candidates ()

    def append_candidate_to_lookup_table(self, tabkeys=u'', phrase=u'', freq=0, user_freq=0):
        '''append candidate to lookup_table'''
        if not tabkeys or not phrase:
            return
        remaining_tabkeys = tabkeys[len(self._tabkeys):]
        if self.db._is_chinese and self._py_mode:
            # restore tune symbol
            remaining_tabkeys = remaining_tabkeys.replace('!','↑1').replace('@','↑2').replace('#','↑3').replace('$','↑4').replace('%','↑5')
        candidate_text = phrase + u' ' + remaining_tabkeys
        attrs = IBus.AttrList ()
        attrs.append(IBus.attr_foreground_new(
            rgb(0x19,0x73,0xa2), 0, len(candidate_text)))
        if not self._py_mode and freq < 0:
            # this is a user defined phrase:
            attrs.append(IBus.attr_foreground_new(rgb(0x77,0x00,0xc3), 0, len(phrase)))
        elif not self._py_mode and user_freq > 0:
            # this is a system phrase which has already been used by the user:
            attrs.append(IBus.attr_foreground_new(rgb(0x00,0x00,0x00), 0, len(phrase)))
        else:
            # this is a system phrase that has not been used yet:
            attrs.append(IBus.attr_foreground_new(rgb(0x00,0x00,0x00), 0, len(phrase)))
        if debug_level > 0:
            debug_text = u' ' + str(freq) + u' ' + str(user_freq)
            candidate_text += debug_text
            attrs.append(IBus.attr_foreground_new(
                rgb(0x00,0xff,0x00), len(candidate_text) - len(debug_text), len(candidate_text)))
        text = IBus.Text.new_from_string(candidate_text)
        i = 0
        while attrs.get(i) != None:
            attr = attrs.get(i)
            text.append_attribute(attr.get_attr_type(),
                                  attr.get_value(),
                                  attr.get_start_index(),
                                  attr.get_end_index())
            i += 1
        self._lookup_table.append_candidate (text)
        self._lookup_table.set_cursor_visible(True)

    def filter_candidates (self, candidates):
        '''Filter candidates if IME is Chinese'''
        if not self._chinese_mode in(2,3) or self._py_mode:
            return candidates[:]
        candidates_used_in_simplified_chinese = []
        candidates_used_in_traditional_chinese = []
        candidates_used_only_in_simplified_chinese = []
        candidates_used_only_in_traditional_chinese = []
        candidates_containing_mixture_of_simplified_and_traditional_chinese = []
        for x in candidates:
            if (1 << 0) & chinese_variants.detect_chinese_category(x[1]):
                candidates_used_in_simplified_chinese.append(x)
            if (1 << 1) & chinese_variants.detect_chinese_category(x[1]):
                candidates_used_in_traditional_chinese.append(x)
            if (1 << 0) & chinese_variants.detect_chinese_category(x[1]) and (not (1 << 1) & chinese_variants.detect_chinese_category(x[1])):
                candidates_used_only_in_simplified_chinese.append(x)
            if (1 << 1) & chinese_variants.detect_chinese_category(x[1]) and (not (1 << 0) & chinese_variants.detect_chinese_category(x[1])):
                candidates_used_only_in_traditional_chinese.append(x)
            if (1 << 2) & chinese_variants.detect_chinese_category(x[1]):
                candidates_containing_mixture_of_simplified_and_traditional_chinese.append(x)
        if self._chinese_mode == 2:
            # All characters with simplified Chinese first
            return candidates_used_in_simplified_chinese + candidates_used_only_in_traditional_chinese + candidates_containing_mixture_of_simplified_and_traditional_chinese
        else: # (self._chinese_mode == 3)
            # All characters with traditional Chinese first
            return candidates_used_only_in_traditional_chinese + candidates_used_in_simplified_chinese + candidates_containing_mixture_of_simplified_and_traditional_chinese

    def update_candidates (self):
        '''Update lookuptable'''
        if self._chars_valid == self._chars_valid_when_update_candidates_was_last_called:
            # The input did not change since we came here last, do nothing and leave
            # candidates and lookup table unchanged:
            return True
        # first check whether the IME have defined start_chars
        if self.db.startchars and (len(self._chars_valid) == 1)\
                and (len(self._chars_invalid) == 0) \
                and (self._chars_valid[0] not in self.db.startchars):
            self._u_chars.append(self._chars_valid[0])
            self._strings.insert(self._cursor[0], self._chars_valid[0])
            self._cursor [0] += 1
            self.clear_input()
        else:
            if (self._chars_valid == self._chars_valid_when_update_candidates_was_last_called and self._candidates) \
                    or self._chars_invalid:
                # if no change in valid input char or we have invalid input,
                # we do not do sql query
                pass
            else:
                # check whether last time we have only one candidate
                only_one_last = self.one_candidate()
                # do enquiry
                self._lookup_table.clear()
                self._lookup_table.set_cursor_visible(True)
                if self._tabkeys:
                    # here we need to consider two parts, table and pinyin
                    # first table
                    if not self._py_mode:
                        if self.db._is_chinese and self._chinese_mode == 0: # simplified
                            self._candidates = self.db.select_words(self._tabkeys, self._onechar, 1)
                        elif self.db._is_chinese and self._chinese_mode == 1: #traditional
                            self._candidates = self.db.select_words(self._tabkeys, self._onechar, 2)
                        else:
                            self._candidates = self.db.select_words(self._tabkeys, self._onechar)
                    else:
                        self._candidates = self.db.select_zi(self._tabkeys)
                    self._chars_valid_when_update_candidates_was_last_called = self._chars_valid
                else:
                    self._candidates =[]
                if self._candidates:
                    self._candidates = self.filter_candidates (self._candidates)
                if self._candidates:
                    self.fill_lookup_table()
                else:
                    if self._chars_valid:
                        ## old manner:
                        #if self._candidates_previous:
                        #    #print self._candidates_previous
                        #    self._candidates = self._candidates_previous
                        #    self._candidates_previous = []
                        #    last_input = self.pop_input ()
                        #    self.auto_commit_to_preedit ()
                        #    res = self.add_input( last_input )
                        #    print res
                        #    return res
                        #else:
                        #    self.pop_input ()
                        #    self._lookup_table.clear()
                        #    self._lookup_table.set_cursor_visible(True)
                        #    return False
                        ###################
                        ## new manner, we add new char to invalid input
                        ## chars
                        if not self._chars_invalid:
                            # we don't have invalid input chars
                            # here we need to check whether the last input char
                            # is a punctuation character or not,
                            # if is a punctuation char, then we use old manner
                            # to submit the former valid candidate
                            if ascii_ispunct(self._chars_valid[-1]) \
                                    or len (self._chars_valid[:-1]) \
                                    in self.db.possible_tabkeys_lengths \
                                    or only_one_last \
                                    or self._auto_select:
                                # because we use [!@#$%] to denote [12345]
                                # in py_mode, so we need to distinguish them
                                ## old manner:
                                if self._py_mode:
                                    if self._chars_valid[-1] in "!@#$%":
                                        self._chars_valid = self._chars_valid[:-1]
                                        self._tabkeys = self._tabkeys[:-1]
                                        return True

                                if self._candidates_previous:
                                    # If there are no candidates but there were
                                    # for previous input, we process that case
                                    # in tabengine, (auto-select mode)
                                    if self._auto_select:
                                        res=False
                                    else:
                                        self._candidates = self._candidates_previous
                                        self._candidates_previous = []
                                        last_input = self.pop_input ()
                                        self.auto_commit_to_preedit ()
                                        res = self.add_input( last_input )
                                    return res
                                else:
                                    self.pop_input ()
                                    self._lookup_table.clear()
                                    self._lookup_table.set_cursor_visible(True)
                                    return False
                            else:
                                # this is not a punct or not a valid phrase
                                # last time
                                self._chars_invalid += self._chars_valid[-1]
                                self._chars_valid = self._chars_valid[:-1]
                                self._tabkeys = self._tabkeys[:-1]
                        else:
                            pass
                        self._candidates =[]
                    else:
                        self._lookup_table.clear()
                        self._lookup_table.set_cursor_visible(True)
                self._candidates_previous = self._candidates

        return True

    def commit_to_preedit (self):
        '''Add selected phrase in lookup table to preedit string'''
        if self._chars_valid:
            try:
                if self._candidates:
                    self._u_chars.insert(self._cursor_precommit, self._candidates[self.get_cursor_pos()][0])
                    self._strings.insert(self._cursor_precommit, self._candidates[self.get_cursor_pos()][1])
                    self._cursor_precommit += 1
                    if self._py_mode:
                        self._zi = self._candidates[self.get_cursor_pos()][1]
                self.clear_input ()
                self.update_candidates()
            except:
                import traceback
                traceback.print_exc()
            return True
        else:
            return False

    def auto_commit_to_preedit (self):
        '''Add selected phrase in lookup table to preedit string'''
        try:
            self._u_chars.insert(self._cursor_precommit, self._candidates[self.get_cursor_pos()][0])
            self._strings.insert(self._cursor_precommit, self._candidates[self.get_cursor_pos()][1])
            self._cursor_precommit += 1
            self.clear_input()
            self.update_candidates()
        except:
            import traceback
            traceback.print_exc()

    def get_aux_strings (self):
        '''Get aux strings'''
        input_chars = self.get_input_chars ()
        if input_chars:
            aux_string = input_chars
            if debug_level > 0 and self._u_chars:
                (tabkeys_left,
                 tabkeys_current,
                 tabkeys_right) = self.get_preedit_tabkeys_parts()
                (strings_left,
                 string_current,
                 strings_right) = self.get_preedit_string_parts()
                aux_string = u''
                for i in range(0, len(strings_left)):
                    aux_string += u'('+tabkeys_left[i]+u' '+strings_left[i]+u') '
                aux_string += input_chars
                for i in range(0, len(strings_right)):
                    aux_string += u' ('+tabkeys_right[i]+u' '+strings_right[i]+u')'

            if self._py_mode:
                aux_string = aux_string.replace('!','1').replace('@','2').replace('#','3').replace('$','4').replace('%','5')
            return aux_string

        aux_string = u''
        if self._zi:
            # we have pinyin result
            aux_string = u' '.join(self.db.find_zi_code(self._zi))
        cstr = u''.join(self._strings)
        if self.db.user_can_define_phrase:
            if len (cstr ) > 1:
                aux_string += (u'\t#: ' + self.db.parse_phrase(cstr))
        return aux_string

    def fill_lookup_table(self):
        '''Fill more entries to self._lookup_table if needed.

        If the cursor in _lookup_table moved beyond current length,
        add more entries from _candidiate[0] to _lookup_table.'''

        looklen = self._lookup_table.get_number_of_candidates()
        psize = self._lookup_table.get_page_size()
        if (self._lookup_table.get_cursor_pos() + psize >= looklen and
                looklen < len(self._candidates)):
            endpos = looklen + psize
            batch = self._candidates[looklen:endpos]
            for x in batch:
                self.append_candidate_to_lookup_table(
                    tabkeys=x[0], phrase=x[1], freq=x[2], user_freq=x[3])

    def cursor_down(self):
        '''Process Arrow Down Key Event
        Move Lookup Table cursor down'''
        self.fill_lookup_table()

        res = self._lookup_table.cursor_down()
        self.update_candidates ()
        if not res and self._candidates:
            return True
        return res

    def cursor_up(self):
        '''Process Arrow Up Key Event
        Move Lookup Table cursor up'''
        res = self._lookup_table.cursor_up()
        self.update_candidates ()
        if not res and self._candidates:
            return True
        return res

    def page_down(self):
        '''Process Page Down Key Event
        Move Lookup Table page down'''
        self.fill_lookup_table()
        res = self._lookup_table.page_down()
        self.update_candidates ()
        if not res and self._candidates:
            return True
        return res

    def page_up(self):
        '''Process Page Up Key Event
        move Lookup Table page up'''
        res = self._lookup_table.page_up()
        self.update_candidates ()
        if not res and self._candidates:
            return True
        return res

    def select_key(self, char):
        '''
        Commit a candidate which was selected by typing a selection key
        from the lookup table to the preedit. Does not yet “really”
        commit the candidate, only to the preedit.
        '''
        if char not in self._select_keys:
            return False
        index = self._select_keys.index(char)
        cursor_pos = self._lookup_table.get_cursor_pos()
        cursor_in_page = self._lookup_table.get_cursor_in_page()
        current_page_start = cursor_pos - cursor_in_page
        real_index = current_page_start + index
        if real_index >= len (self._candidates):
            # the index given is out of range we do not commit anything
            return False
        self._lookup_table.set_cursor_pos(real_index)
        self.commit_to_preedit ()
        return True

    def remove_candidate_from_user_database(self, char):
        '''Remove a candidate displayed in the lookup table from the user database.

        The candidate indicated by the selection key “char” is
        removed, if possible.  If it is not in the user database at
        all, nothing happens.

        If this is a candidate which is also in the system database,
        removing it from the user database only means that its user
        frequency data is reset. It might still appear in subsequent
        matches but with much lower priority.

        If this is a candidate which is user defined and not in the system
        database, it will not match at all anymore after removing it.
        '''
        if char not in self._select_keys:
            return False
        index = self._select_keys.index(char)
        cursor_pos = self._lookup_table.get_cursor_pos()
        cursor_in_page = self._lookup_table.get_cursor_in_page()
        current_page_start = cursor_pos - cursor_in_page
        real_index = current_page_start + index
        if len(self._candidates) > real_index: # this index is valid
            candidate = self._candidates[real_index]
            self.db.remove_phrase(tabkeys=candidate[0], phrase=candidate[1], commit=True)
            # call update_candidates() to get a new SQL query.  The
            # input has not really changed, therefore we must clear
            # the remembered list of transliterated characters to
            # force update_candidates() to really do something and not
            # return immediately:
            self._chars_valid_when_update_candidates_was_last_called = u''
            self.update_candidates()
            return True
        else:
            return False

    def get_cursor_pos (self):
        '''get lookup table cursor position'''
        return self._lookup_table.get_cursor_pos()

    def get_lookup_table (self):
        '''Get lookup table'''
        return self._lookup_table

    def remove_char(self):
        '''Process remove_char Key Event'''
        self._zi = u''
        if self.get_input_chars():
            self.pop_input ()
            return
        self.remove_preedit_character_before_cursor()

    def delete(self):
        '''Process delete Key Event'''
        self._zi = u''
        if self.get_input_chars():
            return
        self.remove_preedit_character_after_cursor()

    def toggle_tab_py_mode (self):
        '''Toggle between Pinyin Mode and Table Mode'''
        self._zi = u''
        if self._chars_valid:
            self.commit_to_preedit ()
        self._py_mode = not (self._py_mode)
        return True

    def cycle_next_cand(self):
        '''Cycle cursor to next candidate in the page.'''
        total = len(self._candidates)

        if total > 0:
            page_size = self._lookup_table.get_page_size()
            pos = self._lookup_table.get_cursor_pos()
            page = int(pos/page_size)
            pos += 1
            if pos >= (page+1)*page_size or pos >= total:
                pos = page*page_size
            res = self._lookup_table.set_cursor_pos(pos)
            return True
        else:
            return False

    def space (self):
        '''Process space Key Event
        return (KeyProcessResult,whethercommit,commitstring)'''
        if self._chars_invalid:
            # we have invalid input, so do not commit
            return (False, u'', u'')
        if not self.is_empty():
            self.commit_to_preedit()
        istr = self.get_all_input_strings()
        pstr = self.get_preedit_string_complete()
        self.clear()
        if istr or pstr:
            return (True, pstr, istr)
        else:
            return (False, u'', u'')

    def one_candidate (self):
        '''Return true if there is only one candidate'''
        return len(self._candidates) == 1


########################
### Engine Class #####
####################
class tabengine (IBus.Engine):
    '''The IM Engine for Tables'''

    def __init__ (self, bus, obj_path, db ):
        super(tabengine,self).__init__ (connection=bus.get_connection(),
                                        object_path=obj_path)
        global debug_level
        try:
            debug_level = int(os.getenv('IBUS_TABLE_DEBUG_LEVEL'))
        except:
            debug_level = int(0)
        self._input_purpose = 0
        self._has_input_purpose = False
        if hasattr(IBus, 'InputPurpose'):
            self._has_input_purpose = True
        self._bus = bus
        # this is the backend sql db we need for our IME
        # we receive this db from IMEngineFactory
        #self.db = tabsqlitedb.tabsqlitedb( name = dbname )
        self.db = db

        self._icon_dir = '%s%s%s%s' % (os.getenv('IBUS_TABLE_LOCATION'),
                os.path.sep, 'icons', os.path.sep)
        # 0 = english input mode
        # 1 = table input mode
        self._mode = 1
        # self._ime_py: True / False this IME support pinyin mode
        self._ime_py = self.db.get_ime_property ('pinyin_mode')
        if self._ime_py:
            if self._ime_py.lower() == u'true':
                self._ime_py = True
            else:
                self._ime_py = False
        else:
            print('We could not find "pinyin_mode" entry in database, is it an outdated database?')
            self._ime_py = False

        self._status = self.db.get_ime_property('status_prompt')
        # now we check and update the valid input characters
        self._valid_input_chars = self.db.get_ime_property('valid_input_chars')

        # check whether we can use '=' and '-' for page_down/up
        self._page_down_keys = [IBus.KEY_Page_Down, IBus.KEY_KP_Page_Down]
        self._page_up_keys = [IBus.KEY_Page_Up, IBus.KEY_KP_Page_Up]
        if '=' not in self._valid_input_chars \
                and '-' not in self._valid_input_chars:
            self._page_down_keys.append (IBus.KEY_equal)
            self._page_up_keys.append (IBus.KEY_minus)

        pageup_prop = self.db.get_ime_property('page_up_keys')
        pagedown_prop = self.db.get_ime_property('page_down_keys')
        if pageup_prop is not None:
            self._page_up_keys = [IBus.keyval_from_name(x) for x in
                    pageup_prop.split(",")]
        if pagedown_prop is not None:
            self._page_down_keys = [IBus.keyval_from_name(x) for x in
                    pagedown_prop.split(",")]

        self._pt = self.db.get_phrase_table_index ()
        self._ml = int(self.db.get_ime_property ('max_key_length'))

        # name for config section
        self._engine_name = os.path.basename(self.db.filename).replace('.db', '')
        self._config_section = "engine/Table/%s" %self._engine_name.replace(' ','_')

        # config module
        self._config = self._bus.get_config ()
        self._config.connect ("value-changed", self.config_value_changed_cb)
        # Containers we used:
        self._editor = editor(self._config, self._pt, self._valid_input_chars, self._ml, self.db)

        # some other vals we used:
        # self._prev_key: hold the key event last time.
        self._prev_key = None
        self._prev_char = None
        self._double_quotation_state = False
        self._single_quotation_state = False

        # [EnMode,TabMode] we get TabMode properties from db
        self._full_width_letter = [
            variant_to_value(self._config.get_value(
                    self._config_section,
                    "EnDefFullWidthLetter")),
            variant_to_value(self._config.get_value(
                    self._config_section,
                    "TabDefFullWidthLetter"))
            ]
        if self._full_width_letter[0] == None:
            self._full_width_letter[0] = False
        if self._full_width_letter[1] == None:
            self._full_width_letter[1] = self.db.get_ime_property('def_full_width_letter').lower() == u'true'
        self._full_width_punct = [
            variant_to_value(self._config.get_value(
                    self._config_section,
                    "EnDefFullWidthPunct")),
            variant_to_value(self._config.get_value(
                    self._config_section,
                    "TabDefFullWidthPunct"))
            ]
        if self._full_width_punct[0] == None:
            self._full_width_punct[0] = False
        if self._full_width_punct[1] == None:
            self._full_width_punct[1] = self.db.get_ime_property('def_full_width_punct').lower() == u'true'
        #self._setup_property = Property ("setup", _("Setup"))

        self._auto_commit = variant_to_value(self._config.get_value(
                self._config_section,
                "AutoCommit"))
        if self._auto_commit == None:
            self._auto_commit = self.db.get_ime_property('auto_commit').lower() == u'true'

        # If auto select is true, then the first candidate phrase will
        # be selected automatically during typing. Auto select is true
        # by default for the stroke5 table for example.
        self._auto_select = variant_to_value(self._config.get_value(
                self._config_section,
                "AutoSelect"))
        if self._auto_select == None:
            if self.db.get_ime_property('auto_select') != None:
                self._auto_select = self.db.get_ime_property('auto_select').lower() == u'true'
            else:
                self._auto_select = False

        self._always_show_lookup = variant_to_value(self._config.get_value(
                self._config_section,
                "AlwaysShowLookup"))
        if self._always_show_lookup == None:
            if self.db.get_ime_property('always_show_lookup') != None:
                self._always_show_lookup = self.db.get_ime_property('always_show_lookup').lower() == u'true'
            else:
                self._always_show_lookup = True

        # the length of the commit phrases
        self._len_list = [0]
        self._on = False
        self._save_user_count = 0
        self._save_user_start = time.time()

        self._save_user_count_max = SAVE_USER_COUNT_MAX
        self._save_user_timeout = SAVE_USER_TIMEOUT
        self.reset ()

        self.sync_timeout_id = GObject.timeout_add_seconds(1,
                self._sync_user_db)

    def reset (self):
        self._editor.clear ()
        self._double_quotation_state = False
        self._single_quotation_state = False
        self._prev_key = None
        #self._editor._onechar = False
        self._init_properties ()
        self._update_ui ()

    def do_destroy(self):
        if self.sync_timeout_id > 0:
            GObject.source_remove(self.sync_timeout_id)
            self.sync_timeout_id = 0
        self.reset ()
        self.do_focus_out ()
        if self._save_user_count > 0:
            self.db.sync_usrdb()
            self._save_user_count = 0
        super(tabengine,self).destroy()

    def _init_properties (self):
        self.properties= IBus.PropList ()

        self._status_property = self._new_property(u'status')
        self.properties.append(self._status_property)

        if self.db._is_chinese:
            self._cmode_property = self._new_property(u'cmode')
            self.properties.append(self._cmode_property)

        self._letter_property = self._new_property(u'letter')
        self.properties.append(self._letter_property)

        self._punct_property = self._new_property(u'punct')
        self.properties.append(self._punct_property)

        self._py_property = self._new_property('py_mode')
        self.properties.append(self._py_property)

        self._onechar_property = self._new_property(u'onechar')
        self.properties.append(self._onechar_property)

        self._auto_commit_property = self._new_property(u'acommit')
        self.properties.append(self._auto_commit_property)

        self._always_show_lookup_property = self._new_property(u'always_show_lookup')
        self.properties.append(self._always_show_lookup_property)

        self.register_properties (self.properties)
        self._refresh_properties ()

    def _new_property (self, key):
        '''Creates new IBus.Property and returns'''
        return IBus.Property(key=key,
                             label=None,
                             icon=None,
                             tooltip=None,
                             sensitive=True,
                             visible=True)

    def _refresh_properties (self):
        '''Method used to update properties'''
        # taken and modified from PinYin.py :)
        if self._mode == 1: # refresh mode
            if self._status == u'CN':
                self._set_property(self._status_property, 'chinese.svg', _('Chinese Mode'), _('Switch to English mode - Right Shift'))
            else:
                self._set_property(self._status_property, 'ibus-table.svg', self._status, _('Switch to English mode - Right Shift'))
        else:
            self._set_property(self._status_property, 'english.svg', _('English Mode'), _('Switch to Table mode - Right Shift'))
        self.update_property(self._status_property)

        if self._full_width_letter[self._mode]:
            self._set_property(self._letter_property, 'full-letter.svg', _('Full Letter'), _('Switch to half-width letter - Ctrl-Space'))
        else:
            self._set_property(self._letter_property, 'half-letter.svg', _('Half Letter'), _('Switch to full-width letter - Ctrl-Space'))
        self.update_property(self._letter_property)

        if self._full_width_punct[self._mode]:
            self._set_property(self._punct_property, 'full-punct.svg', _('Full-width Punctuation'), _('Switch to half-width punctuation - Ctrl-.'))
        else:
            self._set_property(self._punct_property, 'half-punct.svg', _('Half-width Punctuation'), _('Switch to full-width punctuation - Ctrl-.'))
        self.update_property(self._punct_property)

        if self._editor._py_mode:
            self._set_property(self._py_property, 'py-mode.svg', _('PinYin Mode'), _('Switch to Table mode - Left Shift'))
        else:
            self._set_property(self._py_property, 'tab-mode.svg', _('Table Mode'), _('Switch to PinYin mode - Left Shift'))
        self.update_property(self._py_property)

        if self._editor._onechar:
            self._set_property(self._onechar_property, 'onechar.svg', _('Single Char Mode'), _('Switch to phrase mode - Ctrl-,'))
        else:
            self._set_property(self._onechar_property, 'phrase.svg', _('Phrase Mode'), _('Switch to single char mode - Ctrl-,'))
        self.update_property(self._onechar_property)

        if self._auto_commit:
            self._set_property(self._auto_commit_property, 'acommit.svg', _('Direct Commit Mode'), _('Switch to normal commit mode, which use space to commit - Ctrl-/'))
        else:
            self._set_property(self._auto_commit_property, 'ncommit.svg', _('Normal Commit Mode'), _('Switch to direct commit mode - Ctrl-/'))
        self.update_property(self._auto_commit_property)
        if self._always_show_lookup:
            self._set_property(self._always_show_lookup_property, 'always_show_lookup_y.svg', _('Display candidates'), _('Display the candidate list.'))
        else:
            self._set_property(self._always_show_lookup_property, 'always_show_lookup_n.svg', _('Hide candidates'), _('Do not display the candidates list.'))
        self.update_property(self._always_show_lookup_property)

        # the chinese_mode:
        if self.db._is_chinese:
            if self._editor._chinese_mode == 0:
                self._set_property(self._cmode_property, 'sc-mode.svg', _('Simplified Chinese Mode'), _('Switch to Traditional Chinese mode - Ctrl-;'))
            elif self._editor._chinese_mode == 1:
                self._set_property(self._cmode_property, 'tc-mode.svg', _('Traditional Chinese Mode'), _('Switch to Simplify Chinese first Big Charset Mode - Ctrl-;'))
            elif self._editor._chinese_mode == 2:
                self._set_property(self._cmode_property, 'scb-mode.svg', _('Simplified Chinese First Big Charset Mode'), _('Switch to Traditional Chinese first Big Charset Mode - Ctrl-;'))
            elif self._editor._chinese_mode == 3:
                self._set_property(self._cmode_property, 'tcb-mode.svg', _('Traditional Chinese First Big Charset Mode'), _('Switch to Big Charset Mode - Ctrl-;'))
            elif self._editor._chinese_mode == 4:
                self._set_property(self._cmode_property, 'cb-mode.svg', _('Big Chinese Mode'), _('Switch to Simplified Chinese Mode'))
            self.update_property(self._cmode_property)

    def _set_property (self, property, icon, label, tooltip):
        if type(label) != type(u''):
            label = label.decode('utf-8')
        if type(tooltip) != type(u''):
            tooltip = tooltip.decode('utf-8')
        property.set_icon ( u'%s%s' % (self._icon_dir, icon ) )
        property.set_label(IBus.Text.new_from_string(label))
        property.set_tooltip(IBus.Text.new_from_string(tooltip))

    def _change_mode (self):
        '''Shift input mode, TAB -> EN -> TAB
        '''
        self._mode = int (not self._mode)
        self.reset ()
        self._update_ui ()

    def do_property_activate (self, property, prop_state = IBus.PropState.UNCHECKED):
        '''Shift property'''
        if property == u"status":
            self._change_mode ()
        elif property == u'py_mode' and self._ime_py:
            self._editor.toggle_tab_py_mode ()
        elif property == u'onechar':
            self._editor._onechar = not self._editor._onechar
            self._config.set_value(self._config_section,
                    "OneChar",
                    GLib.Variant.new_boolean(self._editor._onechar))

        elif property == u'acommit':
            self._auto_commit = not self._auto_commit
            self._config.set_value( self._config_section,
                    "AutoCommit",
                    GLib.Variant.new_boolean(self._auto_commit))
        elif property == u'letter':
            self._full_width_letter [self._mode] = not self._full_width_letter [self._mode]
            if self._mode:
                self._config.set_value(self._config_section,
                        "TabDefFullWidthLetter",
                        GLib.Variant.new_boolean(self._full_width_letter [self._mode]))
            else:
                self._config.set_value(self._config_section,
                        "EnDefFullWidthLetter",
                        GLib.Variant.new_boolean(self._full_width_letter [self._mode]))

        elif property == u'punct':
            self._full_width_punct [self._mode] = not self._full_width_punct [self._mode]
            if self._mode:
                self._config.set_value(self._config_section,
                        "TabDefFullWidthPunct",
                        GLib.Variant.new_boolean(self._full_width_punct [self._mode]))
            else:
                self._config.set_value(self._config_section,
                        "EnDefFullWidthPunct",
                        GLib.Variant.new_boolean(self._full_width_punct [self._mode]))
        elif property == u'always_show_lookup':
            self._always_show_lookup = not self._always_show_lookup
            self._config.set_value( self._config_section,
                    "AlwaysShowLookup",
                    GLib.Variant.new_boolean(self._always_show_lookup))
        elif property == u'cmode':
            self._editor.change_chinese_mode()
            self.reset()
        self._refresh_properties ()
    #    elif property == "setup":
            # Need implementation
    #        self.start_helper ("96c07b6f-0c3d-4403-ab57-908dd9b8d513")
        # at last invoke default method

    def _update_preedit(self):
        '''Update Preedit String in UI'''
        preedit_string_parts = self._editor.get_preedit_string_parts()
        left_of_current_edit = u''.join(preedit_string_parts[0])
        current_edit = preedit_string_parts[1]
        right_of_current_edit = u''.join(preedit_string_parts[2])
        preedit_string_complete = (
            left_of_current_edit + current_edit + right_of_current_edit)
        if not preedit_string_complete:
            super(tabengine, self).update_preedit_text(IBus.Text.new_from_string(u''), 0, False)
            return
        color_left = rgb(0xf9, 0x0f, 0x0f) # bright red
        color_right = rgb(0x1e, 0xdc, 0x1a) # light green
        attrs = IBus.AttrList()
        attrs.append(
            IBus.attr_foreground_new(
                color_left,
                0,
                len(left_of_current_edit)))
        attrs.append(
            IBus.attr_foreground_new(
                color_right,
                len(left_of_current_edit) + len(current_edit),
                len(preedit_string_complete)))
        attrs.append(
            IBus.attr_underline_new(
                IBus.AttrUnderline.SINGLE,
                0,
                len(preedit_string_complete)))
        text = IBus.Text.new_from_string(preedit_string_complete)
        i = 0
        while attrs.get(i) != None:
            attr = attrs.get(i)
            text.append_attribute(attr.get_attr_type(),
                                  attr.get_value(),
                                  attr.get_start_index(),
                                  attr.get_end_index())
            i += 1
        super(tabengine, self).update_preedit_text(text, self._editor.get_caret(), True)

    def _update_aux (self):
        '''Update Aux String in UI'''
        _ic = self._editor.get_aux_strings ()
        if _ic:
            attrs = IBus.AttrList()
            attrs.append(IBus.attr_foreground_new(rgb(0x95,0x15,0xb5),0, len(_ic)))
            text = IBus.Text.new_from_string(_ic)
            i = 0
            while attrs.get(i) != None:
                attr = attrs.get(i)
                text.append_attribute(attr.get_attr_type(),
                                      attr.get_value(),
                                      attr.get_start_index(),
                                      attr.get_end_index())
                i += 1
            visible = True
            if self._editor._lookup_table.get_number_of_candidates() == 0 \
               or not self._always_show_lookup:
                visible = False
            super(tabengine, self).update_auxiliary_text(text, visible)
        else:
            self.hide_auxiliary_text()

    def _update_lookup_table (self):
        '''Update Lookup Table in UI'''
        if len(self._editor._candidates) == 0:
            # Also make sure to hide lookup table if there are
            # no candidates to display. On f17, this makes no
            # difference but gnome-shell in f18 will display
            # an empty suggestion popup if the number of candidates
            # is zero!
            self.hide_lookup_table()
            return
        if self._editor.is_empty ():
            self.hide_lookup_table()
            return
        if not self._always_show_lookup:
            self.hide_lookup_table()
            return
        self.update_lookup_table(self._editor.get_lookup_table(), True)

    def _update_ui (self):
        '''Update User Interface'''
        self._update_lookup_table ()
        self._update_preedit ()
        self._update_aux ()

    def _check_phrase (self, tabkeys=u'', phrase=u''):
        """Check the given phrase and update save user db info"""
        if not tabkeys or not phrase:
            return
        self.db.check_phrase(tabkeys=tabkeys, phrase=phrase)

        if self._save_user_count <= 0:
            self._save_user_start = time.time()
        self._save_user_count += 1

    def _sync_user_db(self):
        """Save user db to disk"""
        if self._save_user_count >= 0:
            now = time.time()
            time_delta = now - self._save_user_start
            if (self._save_user_count > self._save_user_count_max or
                    time_delta >= self._save_user_timeout):
                self.db.sync_usrdb()
                self._save_user_count = 0
                self._save_user_start = now
        return True

    def commit_string (self,string):
        self._editor.clear ()
        self._update_ui ()
        super(tabengine,self).commit_text(IBus.Text.new_from_string(string))
        if len(string) > 0:
            self._prev_char = string[-1]
        else:
            self._prev_char = None

    def _convert_to_full_width (self, c):
        '''convert half width character to full width'''

        # This function picks up punctuations that are not comply to the
        # unicode convesion formula in unichar_half_to_full (c).
        # For ".", "\"", "'"; there are even variations under specific
        # cases. This function should be more abstracted by extracting
        # that to another handling function later on.
        special_punct_dict = {u"<": u"\u300a",
                               u">": u"\u300b",
                               u"[": u"\u300c",
                               u"]": u"\u300d",
                               u"{": u"\u300e",
                               u"}": u"\u300f",
                               u"\\": u"\u3001",
                               u"^": u"\u2026\u2026",
                               u"_": u"\u2014\u2014",
                               u"$": u"\uffe5"
                               }

        # special puncts w/o further conditions
        if c in special_punct_dict.keys():
            if c in [u"\\", u"^", u"_", u"$"]:
                return special_punct_dict[c]
            elif self._mode:
                return special_punct_dict[c]

        # special puncts w/ further conditions
        if c == u".":
            if self._prev_char and self._prev_char.isdigit () \
                and self._prev_key and chr (self._prev_key.code) == self._prev_char:
                return u"."
            else:
                return u"\u3002"
        elif c == u"\"":
            self._double_quotation_state = not self._double_quotation_state
            if self._double_quotation_state:
                return u"\u201c"
            else:
                return u"\u201d"
        elif c == u"'":
            self._single_quotation_state = not self._single_quotation_state
            if self._single_quotation_state:
                return u"\u2018"
            else:
                return u"\u2019"

        return unichar_half_to_full (c)

    def _match_hotkey (self, key, code, mask):

        if key.code == code and key.mask == mask:
            if self._prev_key and key.code == self._prev_key.code and key.mask & IBus.ModifierType.RELEASE_MASK:
                return True
            if not key.mask & IBus.ModifierType.RELEASE_MASK:
                return True

        return False

    def do_process_key_event(self, keyval, keycode, state):
        '''Process Key Events
        Key Events include Key Press and Key Release,
        modifier means Key Pressed
        '''
        if self._has_input_purpose and self._input_purpose in [IBus.InputPurpose.PASSWORD, IBus.InputPurpose.PIN]:
            return False

        key = KeyEvent(keyval, state & IBus.ModifierType.RELEASE_MASK == 0, state)
        # ignore NumLock mask
        key.mask &= ~IBus.ModifierType.MOD2_MASK

        result = self._process_key_event (key)
        self._prev_key = key
        return result

    def _process_key_event (self, key):
        '''Internal method to process key event'''
        # Match mode switch hotkey
        if self._editor.is_empty() and (self._match_hotkey(key, IBus.KEY_Shift_L, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)):
            self._change_mode ()
            return True

        # Match full half letter mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_space, IBus.ModifierType.SHIFT_MASK):
            self.do_property_activate ("letter")
            return True

        # Match full half punct mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_period, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ("punct")
            return True

        if self._mode:
            return self._table_mode_process_key_event (key)
        else:
            return self._english_mode_process_key_event (key)

    def _english_mode_process_key_event (self, key):
        '''English Mode Process Key Event'''
        # Ignore key release event
        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True

        if key.code >= 128:
            return False
        # we ignore all hotkeys here
        if key.mask & (IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.MOD1_MASK):
            return False

        cond_letter_translate = lambda c: \
            self._convert_to_full_width (c) if self._full_width_letter [
                    self._mode] else c
        cond_punct_translate = lambda c: \
            self._convert_to_full_width (c) if self._full_width_punct [
                    self._mode] else c

        keychar = IBus.keyval_to_unicode(key.code)
        if ascii_ispunct(keychar):
            trans_char = cond_punct_translate (keychar)
        else:
            trans_char = cond_letter_translate (keychar)

        if trans_char == keychar:
            return False
        else:
            self.commit_string(trans_char)
            return True

        # should not reach there
        return False

    def _table_mode_process_key_event (self, key):
        '''Xingma Mode Process Key Event'''
        cond_letter_translate = lambda c: \
            self._convert_to_full_width (c) if self._full_width_letter [self._mode] else c
        cond_punct_translate = lambda c: \
            self._convert_to_full_width (c) if self._full_width_punct [self._mode] else c

        # We have to process the pinyin mode change key event here,
        # because we ignore all Release event below.
        if self._match_hotkey (key, IBus.KEY_Shift_R, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK) and self._ime_py:
            res = self._editor.toggle_tab_py_mode ()
            self._refresh_properties ()
            self._update_ui ()
            return res
        # process commit to preedit
        if self._match_hotkey (key, IBus.KEY_Shift_R, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK) or self._match_hotkey (key, IBus.KEY_Shift_L, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK):
            res = self._editor.commit_to_preedit()
            self._update_ui ()
            return res

        # Left ALT key to cycle candidates in the current page.
        if self._match_hotkey (key, IBus.KEY_Alt_L, IBus.ModifierType.MOD1_MASK | IBus.ModifierType.RELEASE_MASK):
            res = self._editor.cycle_next_cand ()
            self._update_ui ()
            return res

        # Match single char mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_comma, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"onechar" )
            return True
        # Match direct commit mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_slash, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"acommit" )
            return True

        # Match Chinese mode shift
        if self._match_hotkey (key, IBus.KEY_semicolon, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"cmode" )
            return True

        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True

        #
        keychar = IBus.keyval_to_unicode(key.code)

        if self._editor.is_empty() and not self._editor.get_preedit_string_complete():
            # This is the first character typed
            if (key.code >= 32
                and (keychar not in self._valid_input_chars
                     or (self.db.startchars and keychar not in self.db.startchars))
                and (not key.mask &
                            (IBus.ModifierType.MOD1_MASK |
                                IBus.ModifierType.CONTROL_MASK))):
                if ascii_ispunct(keychar):
                    trans_char = cond_punct_translate (keychar)
                else:
                    trans_char = cond_letter_translate (keychar)
                if trans_char == keychar:
                    return False
                else:
                    self.commit_string(trans_char)
                    return True

            elif (key.code < 32 or key.code > 127) and ( keychar not in self._valid_input_chars ) \
                    and(not self._editor._py_mode):
                return False

        if key.code == IBus.KEY_Escape:
            self.reset ()
            self._update_ui ()
            return True

        elif key.code in (IBus.KEY_Return, IBus.KEY_KP_Enter):
            if self._auto_select:
                self._editor.commit_to_preedit ()
                commit_string = self._editor.get_preedit_string_complete() + os.linesep
            else:
                commit_string = self._editor.get_all_input_strings ()
            self.commit_string (commit_string)
            return True

        elif key.code in (IBus.KEY_Tab, IBus.KEY_KP_Tab) and self._auto_select:
            self._editor.commit_to_preedit ()
            self.commit_string(self._editor.get_preedit_string_complete())

        elif key.code in (IBus.KEY_Down, IBus.KEY_KP_Down) :
            res = self._editor.cursor_down ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Up, IBus.KEY_KP_Up):
            res = self._editor.cursor_up ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Left, IBus.KEY_KP_Left) and key.mask & IBus.ModifierType.CONTROL_MASK:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.control_arrow_left()
                self._update_ui()
                return True

        elif key.code in (IBus.KEY_Right, IBus.KEY_KP_Right) and key.mask & IBus.ModifierType.CONTROL_MASK:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.control_arrow_right()
                self._update_ui()
                return True

        elif key.code in (IBus.KEY_Left, IBus.KEY_KP_Left):
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.arrow_left()
                self._update_ui()
                return True

        elif key.code in (IBus.KEY_Right, IBus.KEY_KP_Right):
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.arrow_right()
                self._update_ui()
                return True

        elif key.code == IBus.KEY_BackSpace and key.mask & IBus.ModifierType.CONTROL_MASK:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.remove_preedit_before_cursor()
                self._update_ui()
                return True

        elif key.code == IBus.KEY_BackSpace:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.remove_char()
                self._update_ui()
                return True

        elif key.code == IBus.KEY_Delete  and key.mask & IBus.ModifierType.CONTROL_MASK:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.remove_preedit_after_cursor()
                self._update_ui()
                return True

        elif key.code == IBus.KEY_Delete:
            if not self._editor.get_preedit_string_complete():
                return False
            else:
                self._editor.delete()
                self._update_ui()
                return True

        elif ( keychar in self._editor.get_select_keys() and
                self._editor._candidates and
                key.mask & IBus.ModifierType.CONTROL_MASK ):
            res = self._editor.select_key (keychar)
            self._update_ui ()
            return res

        elif ( keychar in self._editor.get_select_keys() and
                self._editor._candidates and
                key.mask & IBus.ModifierType.MOD1_MASK ):
            res = self._editor.remove_candidate_from_user_database(keychar)
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_space:
            # if space is one of "page_down_keys" change to next page
            #  on lookup page
            if IBus.KEY_space in self._page_down_keys:
                res = self._editor.page_down()
                self._update_ui ()
                return res
            else:
                o_py = self._editor._py_mode
                sp_res = self._editor.space ()
                #return (KeyProcessResult,whethercommit,commitstring)
                if sp_res[0]:
                    if self._editor._auto_select:
                        self.commit_string ("%s " %sp_res[1])
                    else:
                        self.commit_string (sp_res[1])
                    self._check_phrase(tabkeys=sp_res[2], phrase=sp_res[1])
                if o_py != self._editor._py_mode:
                    self._refresh_properties ()
                    self._update_ui ()
                return True
        # now we ignore all else hotkeys
        elif key.mask & (IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.MOD1_MASK):
            return False

        elif key.mask & IBus.ModifierType.MOD1_MASK:
            return False

        elif keychar and (keychar in self._valid_input_chars or (self._editor._py_mode and keychar in u'abcdefghijklmnopqrstuvwxyz!@#$%')):
            if self._auto_commit and (len(self._editor._chars_valid) == self._ml \
                or len(self._editor._chars_valid) in self.db.possible_tabkeys_lengths)\
                and not self._editor._py_mode:
                # it is time to direct commit
                sp_res = self._editor.space ()
                #return (whethercommit,commitstring)
                if sp_res[0]:
                    self.commit_string (sp_res[1])
                    self._check_phrase (tabkeys=sp_res[2], phrase=sp_res[1])

            res = self._editor.add_input ( keychar )
            if not res:
                # If this input has no candidate but the previous had,
                # we remove the last input, commit the previous candidate
                # and reprocess the last input (auto-select mode)
                reprocess_last_key=False
                if self._auto_select and self._editor._candidates_previous:
                    self._editor.pop_input ()
                    reprocess_last_key=True
                    key_char=''
                elif ascii_ispunct(keychar):
                    key_char = cond_punct_translate (keychar)
                else:
                    key_char = cond_letter_translate (keychar)
                sp_res = self._editor.space ()
                if sp_res[0]:
                    self.commit_string (sp_res[1] + key_char)
                    self._check_phrase (tabkeys=sp_res[2], phrase=sp_res[1])
                else:
                    self.commit_string ( key_char )
                if reprocess_last_key == True:
                    self._table_mode_process_key_event(key)
                return True
            else:
                if self._auto_commit and self._editor.one_candidate () and \
                        (len(self._editor._chars_valid) == self._ml \
                            or not self.db._is_chinese):
                    # it is time to direct commit
                    sp_res = self._editor.space ()
                    #return (whethercommit,commitstring)
                    if sp_res[0]:
                        self.commit_string (sp_res[1])
                        self._check_phrase (tabkeys=sp_res[2], phrase=sp_res[1])
                        return True
            self._update_ui ()
            return True

        elif key.code in self._page_down_keys \
                and self._editor._candidates:
            res = self._editor.page_down()
            self._update_ui ()
            return res

        elif key.code in self._page_up_keys \
                and self._editor._candidates:
            res = self._editor.page_up ()
            self._update_ui ()
            return res

        elif keychar in self._editor.get_select_keys() and self._editor._candidates:
            input_keys = self._editor.get_all_input_strings ()
            res = self._editor.select_key (keychar)
            if res:
                o_py = self._editor._py_mode
                commit_string = self._editor.get_preedit_string_complete()
                self.commit_string (commit_string)
                if o_py != self._editor._py_mode:
                    self._refresh_properties ()
                    self._update_ui ()
                # modify freq info
                self._check_phrase(tabkeys=input_keys, phrase=commit_string)
            return True

        elif key.code <= 127:
            if not self._editor._candidates:
                commit_string = self._editor.get_all_input_strings ()
            else:
                self._editor.commit_to_preedit ()
                commit_string = self._editor.get_preedit_string_complete()
            # we need to take care of the py_mode here :)
            py_mode = self._editor._py_mode
            self._editor.clear ()
            if py_mode:
                self._refresh_properties ()
            if ascii_ispunct(keychar):
                self.commit_string ( commit_string + cond_punct_translate(keychar))
            else:
                self.commit_string ( commit_string + cond_letter_translate(keychar))

            return True
        return False

    # below for initial test
    def do_focus_in (self):
        if self._on:
            self.register_properties (self.properties)
            self._refresh_properties ()
            self._update_ui ()

    def do_focus_out (self):
        if self._has_input_purpose:
            self._input_purpose = 0
        self._editor.clear()

    def do_set_content_type(self, purpose, hints):
        if self._has_input_purpose:
            self._input_purpose = purpose

    def do_enable (self):
        self._on = True
        self.do_focus_in()

    def do_disable (self):
        self._on = False


    def do_page_up (self):
        if self._editor.page_up ():
            self._update_ui ()
            return True
        return False

    def do_page_down (self):
        if self._editor.page_down ():
            self._update_ui ()
            return True
        return False

    def config_section_normalize(self, section):
        # This function replaces _: with - in the dconf
        # section and converts to lower case to make
        # the comparison of the dconf sections work correctly.
        # I avoid using .lower() here because it is locale dependent,
        # when using .lower() this would not achieve the desired
        # effect of comparing the dconf sections case insentively
        # in some locales, it would fail for example if Turkish
        # locale (tr_TR.UTF-8) is set.
        if sys.version_info >= (3,0,0): # Python3
            return re.sub(r'[_:]', r'-', section).translate(
                ''.maketrans(
                string.ascii_uppercase,
                string.ascii_lowercase))
        else: # Python2
            return re.sub(r'[_:]', r'-', section).translate(
                string.maketrans(
                string.ascii_uppercase,
                string.ascii_lowercase).decode('ISO-8859-1'))

    def config_value_changed_cb (self, config, section, name, value):
        if self.config_section_normalize(self._config_section) != self.config_section_normalize(section):
            return
        print("config value %(n)s for engine %(en)s changed" %{'n': name, 'en': self._engine_name})
        value = variant_to_value(value)
        if name == u'autoselect':
            self._editor._auto_select = value
            self._refresh_properties()
            return
        if name == u'autocommit':
            self._auto_commit = value
            self._refresh_properties()
            return
        elif name == u'chinesemode':
            self._editor._chinese_mode = value
            self._refresh_properties()
            return
        elif name == u'endeffullwidthletter':
            self._full_width_letter[0] = value
            self._refresh_properties()
            return
        elif name == u'endeffullwidthpunct':
            self._full_width_punct[0] = value
            self._refresh_properties()
            return
        elif name == u'lookuptableorientation':
            self._editor._lookup_table.set_orientation (value)
            return
        elif name == u'lookuptableselectkeys':
            self._editor.set_select_keys (value)
            return
        elif name == u'onechar':
            self._editor._onechar = value
            self._refresh_properties()
            return
        elif name == u'tabdeffullwidthletter':
            self._full_width_letter[1] = value
            self._refresh_properties()
            return
        elif name == u'tabdeffullwidthpunct':
            self._full_width_punct[1] = value
            self._refresh_properties()
            return
        elif name == u'alwaysshowlookup':
            self._always_show_lookup = value
            self._refresh_properties()
            return

    # for further implementation :)
    @classmethod
    def CONFIG_VALUE_CHANGED(cls, bus, section, name, value):
        config = bus.get_config()
        if section != self._config_section:
            return

    @classmethod
    def CONFIG_RELOADED(cls, bus):
        config = bus.get_config()
        if section != self._config_section:
            return
