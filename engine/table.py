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

def unichar_half_to_full(c):
    code = ord(c)
    for half, full, size in __half_full_table:
        if code >= half and code < half + size:
            if sys.version_info >= (3,0,0):
                return chr(full + code - half)
            else:
                return unichr(full + code - half)
    return c

def unichar_full_to_half(c):
    code = ord(c)
    for half, full, size in __half_full_table:
        if code >= full and code < full + size:
            if sys.version_info >= (3,0,0):
                return chr(half + code - full)
            else:
                return unichr(half + code - full)
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
    def __init__ (self, config, valid_input_chars, single_wildcard_char, multi_wildcard_char, auto_wildcard, max_key_length, database):
        self.db = database
        self._config = config
        engine_name = os.path.basename(self.db.filename).replace('.db', '')
        self._config_section = "engine/Table/%s" %engine_name.replace(' ','_')
        self._max_key_length = int(max_key_length)
        self._max_key_length_pinyin = 7
        self._valid_input_chars = valid_input_chars
        self._single_wildcard_char = single_wildcard_char
        self._multi_wildcard_char = multi_wildcard_char
        self._auto_wildcard = auto_wildcard
        #
        # The values below will be reset in self.clear_input_not_committed_to_preedit()
        self._chars_valid = u''    # valid user input in table mode
        self._chars_invalid = u''  # invalid user input in table mode
        self._chars_valid_update_candidates_last = u''
        self._chars_invalid_update_candidates_last = u''
        # self._candidates holds the “best” candidates matching the user input
        # [(tabkeys, phrase, freq, user_freq), ...]
        self._candidates = []
        self._candidates_previous = []

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

        self._prompt_characters = eval(self.db.ime_properties.get('char_prompts'))

        select_keys_csv = variant_to_value(self._config.get_value(
            self._config_section,
            "LookupTableSelectKeys"))
        if select_keys_csv == None:
            select_keys_csv = self.db.get_select_keys()
        self._select_keys = [x.strip() for x in select_keys_csv.split(",")]
        self._page_size = variant_to_value(self._config.get_value(
            self._config_section,
            "lookuptablepagesize"))
        if self._page_size == None or self._page_size > len(self._select_keys):
            self._page_size = len(self._select_keys)
        self._orientation = variant_to_value(self._config.get_value(
            self._config_section,
            "LookupTableOrientation"))
        if self._orientation == None:
            self._orientation = self.db.get_orientation()
        self._lookup_table = self.get_new_lookup_table(
            page_size = self._page_size,
            select_keys = self._select_keys,
            orientation = self._orientation)
        # self._py_mode: whether in pinyin mode
        self._py_mode = False
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
        # we use LC_CTYPE or LANG to determine which one to use if
        # no default comes from the config.
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
            if self.db.ime_properties.get('auto_select') != None:
                self._auto_select = self.db.ime_properties.get('auto_select').lower() == u'true'
            else:
                self._auto_select = False

    def get_new_lookup_table(self, page_size=10, select_keys='1234567890', orientation=True):
        if page_size < 1:
            page_size = 1
        if page_size > len(select_keys):
            page_size = len(select_keys)
        lookup_table = IBus.LookupTable.new(
            page_size=page_size,
            cursor_pos=0,
            cursor_visible=True,
            round=True)
        for key in select_keys:
            lookup_table.append_label(IBus.Text.new_from_string("%s." %key))
        lookup_table.set_orientation(orientation)
        return lookup_table

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

    def clear_all_input_and_preedit(self):
        '''
        Clear all input, whether committed to preëdit or not.
        '''
        self.clear_input_not_committed_to_preedit()
        self._u_chars = []
        self._strings = []
        self._cursor_precommit = 0
        self.update_candidates()

    def is_empty(self):
        return u'' == self._chars_valid + self._chars_invalid

    def clear_input_not_committed_to_preedit(self):
        '''
        Clear the input which has not yet been committed to preëdit.
        '''
        self._chars_valid = u''
        self._chars_invalid = u''
        self._chars_valid_update_candidates_last = u''
        self._chars_invalid_update_candidates_last = u''
        self._lookup_table.clear()
        self._lookup_table.set_cursor_visible(True)
        self._candidates = []
        self._candidates_previous = []

    def add_input(self,c):
        '''
        Add input character and update candidates.

        Returns “True” if candidates were found, “False” if not.
        '''
        if (self._chars_invalid
            or (not self._py_mode and (c not in self._valid_input_chars))
            or (self._py_mode and (c not in u'abcdefghijklmnopqrstuvwxyz!@#$%'))):
            self._chars_invalid += c
        else:
            self._chars_valid += c
        res = self.update_candidates()
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
            if (not self._chars_valid) and self._u_chars:
                self._chars_valid = self._u_chars.pop(self._cursor_precommit - 1)
                self._strings.pop(self._cursor_precommit - 1)
                self._cursor_precommit -= 1
        self.update_candidates ()
        return _c

    def get_input_chars (self):
        '''get characters held, valid and invalid'''
        return self._chars_valid + self._chars_invalid

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

    def get_preedit_tabkeys_complete(self):
        '''Returns the tabkeys which belong to the parts of the preëdit string as a single string'''
        (left_tabkeys,
         current_tabkeys,
         right_tabkeys) = self.get_preedit_tabkeys_parts()
        return  u''.join(left_tabkeys) + current_tabkeys + u''.join(right_tabkeys)

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
        '''Returns the phrases which are parts of the preëdit string as a single string'''
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
        regexp = self._chars_valid
        if self._multi_wildcard_char:
            regexp = regexp.replace(
                self._multi_wildcard_char, '_multi_wildchard_char_')
        if self._single_wildcard_char:
            regexp = regexp.replace(
                self._single_wildcard_char, '_single_wildchard_char_')
        regexp = re.escape(regexp)
        regexp = regexp.replace('_multi_wildchard_char_', '.*')
        regexp = regexp.replace('_single_wildchard_char_', '.?')
        match = re.match(r'^'+regexp, tabkeys)
        if match:
            remaining_tabkeys = tabkeys[match.end():]
        else:
             # This should never happen! For the candidates
             # added to the lookup table here, a match has
             # been found for self._chars_valid in the database.
             # In that case, the above regular expression should
             # match as well.
            remaining_tabkeys = tabkeys
        if self.db._is_chinese and self._py_mode:
            # restore tune symbol
            remaining_tabkeys = remaining_tabkeys.replace('!','↑1').replace('@','↑2').replace('#','↑3').replace('$','↑4').replace('%','↑5')
        for char in self._prompt_characters:
            remaining_tabkeys = remaining_tabkeys.replace(char, self._prompt_characters[char])
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
            return candidates_used_in_traditional_chinese + candidates_used_only_in_simplified_chinese + candidates_containing_mixture_of_simplified_and_traditional_chinese

    def update_candidates (self):
        '''
        Searches for candidates and updates the lookuptable.

        Returns “True” if candidates were found and “False” if not.
        '''
        if (self._chars_valid == self._chars_valid_update_candidates_last
            and
            self._chars_invalid == self._chars_invalid_update_candidates_last):
            # The input did not change since we came here last, do nothing and leave
            # candidates and lookup table unchanged:
            if self._candidates:
                return True
            else:
                return False
        self._chars_valid_update_candidates_last = self._chars_valid
        self._chars_invalid_update_candidates_last = self._chars_invalid
        self._lookup_table.clear()
        self._lookup_table.set_cursor_visible(True)
        if self._chars_invalid or not self._chars_valid:
            self._candidates = []
            self._candidates_previous = self._candidates
            return False
        if self.db._is_chinese and self._chinese_mode == 0:
            bitmask = (1 << 0) # simplified only
        elif self.db._is_chinese and self._chinese_mode == 1:
            bitmask = (1 << 1) # traditional only
        else:
            bitmask = 0xff     # everything
        if self._py_mode and self.db._is_chinese:
            self._candidates = self.db.select_chinese_characters_by_pinyin(
                tabkeys=self._chars_valid,
                bitmask=bitmask)
        else:
            self._candidates = self.db.select_words(
                tabkeys=self._chars_valid,
                onechar=self._onechar,
                bitmask=bitmask,
                single_wildcard_char=self._single_wildcard_char,
                multi_wildcard_char=self._multi_wildcard_char,
                auto_wildcard=self._auto_wildcard)
        if (self._candidates
            and self.db._is_chinese
            and self._chinese_mode in (2,3)
            and not self._py_mode):
            # In self._candidates, the candidates where the typed
            # characters matched the tabkeys in the database
            # *completely* are before all candidates where the typed
            # characters matched only the beginning of the tabkeys in
            # the database.  Do not destroy this property of
            # self._candidates when filtering for Chinese mode 2 (All
            # characters with simplified Chinese first) or Chinese
            # mode 3 (All characters with traditional Chinese first).
            # Having the exact matches first is more important than
            # the distinction between simplified and traditional.
            # Therefore, we do this filtering separately for the
            # exact matches and the completion matches and then
            # add the results together again:
            candidates_exact_match = []
            candidates_completion_match = []
            for candidate in self._candidates:
                if self._chars_valid == candidate[0]:
                    candidates_exact_match.append(candidate)
                else:
                    candidates_completion_match.append(candidate)
            self._candidates = (
                self.filter_candidates(candidates_exact_match)
                + self.filter_candidates(candidates_completion_match))
        if self._candidates:
            self.fill_lookup_table()
            self._candidates_previous = self._candidates
            return True
        # There are only valid and no invalid input characters but no
        # matching candidates could be found from the databases. The
        # last of self._chars_valid must have caused this.  That
        # character is valid in the sense that it is listed in
        # self._valid_input_chars, it is only invalid in the sense
        # that after adding this character, no candidates could be
        # found anymore.  Add this character to self._chars_invalid
        # and remove it from self._chars_valid.
        self._chars_invalid += self._chars_valid[-1]
        self._chars_valid = self._chars_valid[:-1]
        self._chars_valid_update_candidates_last = self._chars_valid
        self._chars_invalid_update_candidates_last = self._chars_invalid
        return False

    def commit_to_preedit(self):
        '''Add selected phrase in lookup table to preëdit string'''
        if not self._chars_valid:
            return False
        if self._candidates:
            self._u_chars.insert(self._cursor_precommit,
                                 self._candidates[self.get_cursor_pos()][0])
            self._strings.insert(self._cursor_precommit,
                                 self._candidates[self.get_cursor_pos()][1])
            self._cursor_precommit += 1
        self.clear_input_not_committed_to_preedit()
        self.update_candidates()
        return True

    def commit_to_preedit_current_page(self, index):
        '''
        Commits the candidate at position “index” in the current
        page of the lookup table to the preëdit. Does not yet “really”
        commit the candidate, only to the preëdit.
        '''
        cursor_pos = self._lookup_table.get_cursor_pos()
        cursor_in_page = self._lookup_table.get_cursor_in_page()
        current_page_start = cursor_pos - cursor_in_page
        real_index = current_page_start + index
        if real_index >= len(self._candidates):
            # the index given is out of range we do not commit anything
            return False
        self._lookup_table.set_cursor_pos(real_index)
        return self.commit_to_preedit()

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
            for char in self._prompt_characters:
                aux_string = aux_string.replace(char, self._prompt_characters[char])
            return aux_string

        # There are no input strings at the moment. But there could
        # be stuff committed to the preëdit. If there is something
        # committed to the preëdit, show some information in the
        # auxiliary text.
        #
        # For the character at the position of the cursor in the
        # preëdit, show a list of possible input key sequences which
        # could be used to type that character at the left side of the
        # auxiliary text.
        #
        # If the preëdit is longer than one character, show the input
        # key sequence which will be defined for the complete current
        # contents of the preëdit, if the preëdit is committed.
        aux_string = u''
        if self._strings:
            if self._cursor_precommit >= len(self._strings):
                char = self._strings[-1][0]
            else:
                char = self._strings[self._cursor_precommit][0]
            aux_string = u' '.join(self.db.find_zi_code(char))
        cstr = u''.join(self._strings)
        if self.db.user_can_define_phrase:
            if len(cstr) > 1:
                aux_string += (u'\t#: ' + self.db.parse_phrase(cstr))
        for char in self._prompt_characters:
            aux_string = aux_string.replace(char, self._prompt_characters[char])
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
        return self.commit_to_preedit_current_page(
            self._select_keys.index(char))

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
            # the remembered list of characters to
            # force update_candidates() to really do something and not
            # return immediately:
            self._chars_valid_update_candidates_last = u''
            self._chars_invalid_update_candidates_last = u''
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
        if self.get_input_chars():
            self.pop_input ()
            return
        self.remove_preedit_character_before_cursor()

    def delete(self):
        '''Process delete Key Event'''
        if self.get_input_chars():
            return
        self.remove_preedit_character_after_cursor()

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
        self._setup_pid = 0
        self._icon_dir = '%s%s%s%s' % (os.getenv('IBUS_TABLE_LOCATION'),
                os.path.sep, 'icons', os.path.sep)
        # self._ime_py: Indicates whether this table supports pinyin mode
        self._ime_py = self.db.ime_properties.get('pinyin_mode')
        if self._ime_py:
            if self._ime_py.lower() == u'true':
                self._ime_py = True
            else:
                self._ime_py = False
        else:
            print('We could not find "pinyin_mode" entry in database, is it an outdated database?')
            self._ime_py = False

        self._status = self.db.ime_properties.get('status_prompt')
        # now we check and update the valid input characters
        self._valid_input_chars = self.db.ime_properties.get('valid_input_chars')
        self._single_wildcard_char = self.db.ime_properties.get('single_wildcard_char')
        if not self._single_wildcard_char:
            self._single_wildcard_char = '?'
        self._multi_wildcard_char = self.db.ime_properties.get('multi_wildcard_char')
        if not self._multi_wildcard_char:
            self._multi_wildcard_char = '*'

        self._valid_input_chars += self._single_wildcard_char
        self._valid_input_chars += self._multi_wildcard_char
        self._auto_wildcard = self.db.ime_properties.get('auto_wildcard')
        if self._auto_wildcard and self._auto_wildcard.lower() == u'false':
            self._auto_wildcard = False
        else:
            self._auto_wildcard = True

        self._max_key_length = int(self.db.ime_properties.get('max_key_length'))
        self._max_key_length_pinyin = 7

        # name for config section
        self._engine_name = os.path.basename(self.db.filename).replace('.db', '')
        self._config_section = "engine/Table/%s" %self._engine_name.replace(' ','_')

        # config module
        self._config = self._bus.get_config ()
        self._config.connect ("value-changed", self.config_value_changed_cb)
        self._editor = editor(self._config, self._valid_input_chars,
                              self._single_wildcard_char,
                              self._multi_wildcard_char,
                              self._auto_wildcard,
                              self._max_key_length, self.db)

        self._page_up_keys = [
            IBus.KEY_Page_Up,
            IBus.KEY_KP_Page_Up,
            IBus.KEY_minus
        ]
        self._page_down_keys = [
            IBus.KEY_Page_Down,
            IBus.KEY_KP_Page_Down,
            IBus.KEY_equal
        ]
        # If page up or page down keys are defined in the database,
        # use the values from the database instead of the above
        # hardcoded defaults:
        page_up_keys_csv = self.db.ime_properties.get('page_up_keys')
        page_down_keys_csv = self.db.ime_properties.get('page_down_keys')
        if page_up_keys_csv:
            self._page_up_keys = [
                IBus.keyval_from_name(x)
                for x in page_up_keys_csv.split(',')]
        if page_down_keys_csv:
            self._page_down_keys = [
                IBus.keyval_from_name(x)
                for x in page_down_keys_csv.split(',')]
        # Remove keys from the page up/down keys if they are needed
        # for input (for example, '=' or '-' could well be needed for
        # input. Input is more important):
        for character in self._valid_input_chars:
            keyval = IBus.unicode_to_keyval(character)
            if keyval in self._page_up_keys:
                self._page_up_keys.remove(keyval)
            if keyval in self._page_down_keys:
                self._page_down_keys.remove(keyval)
        self._commit_keys = [IBus.KEY_space]
        # If commit keys are are defined in the database, use the
        # value from the database instead of the above hardcoded
        # default:
        commit_keys_csv = self.db.ime_properties.get('commit_keys')
        if commit_keys_csv:
            self._commit_keys = [
                IBus.keyval_from_name(x)
                for x in commit_keys_csv.split(',')]
        # If commit keys conflict with page up/down keys, remove them
        # from the page up/down keys (They cannot really be used for
        # both at the same time. Theoretically, keys from the page
        # up/down keys could still be used to commit when the number
        # of candidates is 0 because then there is nothing to
        # page. But that would be only confusing):
        for keyval in self._commit_keys:
            if keyval in self._page_up_keys:
                self._page_up_keys.remove(keyval)
            if keyval in self._page_down_keys:
                self._page_down_keys.remove(keyval)
        # Finally, check the user setting, i.e. the config value
        # “spacekeybehavior” and let the user have the last word
        # how to use the space key:
        spacekeybehavior = variant_to_value(self._config.get_value(
            self._config_section,
            "spacekeybehavior"))
        if spacekeybehavior == True:
            # space is used as a page down key and not as a commit key:
            if IBus.KEY_space not in self._page_down_keys:
                self._page_down_keys.append(IBus.KEY_space)
            if IBus.KEY_space in self._commit_keys:
                self._commit_keys.remove(IBus.KEY_space)
        if spacekeybehavior == False:
            # space is used as a commit key and not used as a page down key:
            if IBus.KEY_space in self._page_down_keys:
                self._page_down_keys.remove(IBus.KEY_space)
            if IBus.KEY_space not in self._commit_keys:
                self._commit_keys.append(IBus.KEY_space)

        # 0 = Direct input, i.e. table input OFF (aka “English input mode”),
        #     most characters are just passed through to the application
        #     (but some fullwidth ↔ halfwidth conversion may be done even
        #     in this mode, depending on the settings)
        # 1 = Table input ON (aka “Table input mode”, “Chinese mode”)
        self._input_mode = variant_to_value(self._config.get_value(
            self._config_section,
            "inputmode"))
        if self._input_mode == None:
            self._input_mode = 1

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
            self._full_width_letter[1] = self.db.ime_properties.get('def_full_width_letter').lower() == u'true'
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
            self._full_width_punct[1] = self.db.ime_properties.get('def_full_width_punct').lower() == u'true'

        self._auto_commit = variant_to_value(self._config.get_value(
                self._config_section,
                "AutoCommit"))
        if self._auto_commit == None:
            self._auto_commit = self.db.ime_properties.get('auto_commit').lower() == u'true'

        # If auto select is true, then the first candidate phrase will
        # be selected automatically during typing. Auto select is true
        # by default for the stroke5 table for example.
        self._auto_select = variant_to_value(self._config.get_value(
                self._config_section,
                "AutoSelect"))
        if self._auto_select == None:
            if self.db.ime_properties.get('auto_select') != None:
                self._auto_select = self.db.ime_properties.get('auto_select').lower() == u'true'
            else:
                self._auto_select = False

        self._always_show_lookup = variant_to_value(self._config.get_value(
                self._config_section,
                "AlwaysShowLookup"))
        if self._always_show_lookup == None:
            if self.db.ime_properties.get('always_show_lookup') != None:
                self._always_show_lookup = self.db.ime_properties.get('always_show_lookup').lower() == u'true'
            else:
                self._always_show_lookup = True

        self._on = False
        self._save_user_count = 0
        self._save_user_start = time.time()

        self._save_user_count_max = SAVE_USER_COUNT_MAX
        self._save_user_timeout = SAVE_USER_TIMEOUT
        self.reset()

        self.sync_timeout_id = GObject.timeout_add_seconds(1,
                self._sync_user_db)

    def reset(self):
        self._editor.clear_all_input_and_preedit()
        self._double_quotation_state = False
        self._single_quotation_state = False
        self._prev_key = None
        self._init_properties()
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

    def _init_properties(self):
        self.properties= IBus.PropList()

        self._status_property = self._new_property(u'status')
        self.properties.append(self._status_property)

        if self.db._is_chinese:
            self._cmode_property = self._new_property(u'cmode')
            self.properties.append(self._cmode_property)

        self._letter_property = self._new_property(u'letter')
        self.properties.append(self._letter_property)

        self._punct_property = self._new_property(u'punct')
        self.properties.append(self._punct_property)

        if self._ime_py:
            self._py_property = self._new_property('py_mode')
            self.properties.append(self._py_property)

        self._onechar_property = self._new_property(u'onechar')
        self.properties.append(self._onechar_property)

        self._auto_commit_property = self._new_property(u'acommit')
        self.properties.append(self._auto_commit_property)

        self._always_show_lookup_property = self._new_property(u'always_show_lookup')
        self.properties.append(self._always_show_lookup_property)

        self._setup_property = self._new_property(
            key = u'setup',
            label = _('Setup'),
            icon = 'gtk-preferences',
            tooltip = _('Configure ibus-table'))
        self.properties.append(self._setup_property)

        self.register_properties(self.properties)
        self._refresh_properties()

    def _new_property(self, key, label=None, icon=None, tooltip=None, sensitive=True, visible=True):
        '''Creates a new IBus.Property and returns it'''
        return IBus.Property(key=key,
                             label=label,
                             icon=icon,
                             tooltip=tooltip,
                             sensitive=sensitive,
                             visible=visible)

    def _refresh_properties (self):
        '''Method used to update properties'''
        # taken and modified from PinYin.py :)
        if self._input_mode == 1:
            if self.db._is_chinese:
                self._set_property(
                    self._status_property,
                    'chinese.svg',
                    _('Chinese input'),
                    _('Switch to “Direct input” (Left Shift)'))
            else:
                self._set_property(
                    self._status_property,
                    'ibus-table.svg',
                    self._status,
                    _('Switch to “Direct input” (Left Shift)'))
        else:
            if self.db.is_chinese:
                self._set_property(
                    self._status_property,
                    'english.svg',
                    _('Direct input'),
                    _('Switch to “Chinese input” (Left Shift)'))
            else:
                self._set_property(
                    self._status_property,
                    'english.svg',
                    _('Direct input'),
                    _('Switch to %s (“Table input”) (Left Shift)') %self._status)
        self.update_property(self._status_property)

        if self._full_width_letter[self._input_mode]:
            self._set_property(
                self._letter_property,
                'full-letter.svg',
                _('Fullwidth letters'),
                _('Switch to “Halfwidth letters” (Shift-Space)'))
        else:
            self._set_property(
                self._letter_property,
                'half-letter.svg',
                _('Halfwidth letters'),
                _('Switch to “Fullwidth letters” (Shift-Space)'))
        self.update_property(self._letter_property)

        if self._full_width_punct[self._input_mode]:
            self._set_property(
                self._punct_property,
                'full-punct.svg',
                _('Fullwidth punctuation'),
                _('Switch to “Halfwidth punctuation” (Ctrl-.)'))
        else:
            self._set_property(
                self._punct_property,
                'half-punct.svg',
                _('Halfwidth punctuation'),
                _('Switch to “Fullwidth punctuation” (Ctrl-.)'))
        self.update_property(self._punct_property)

        if self._ime_py:
            if self._editor._py_mode:
                self._set_property(
                    self._py_property,
                    'py-mode.svg',
                    _('Pinyin mode'),
                    _('Switch to “Table mode” (Right Shift)'))
            else:
                self._set_property(
                    self._py_property,
                    'tab-mode.svg',
                    _('Table mode'),
                    _('Switch to “Pinyin mode” (Right Shift)'))
            self.update_property(self._py_property)

        if self._editor._onechar:
            self._set_property(
                self._onechar_property,
                'onechar.svg',
                _('Single character mode'),
                _('Switch to “Phrase mode” (Ctrl-,)'))
        else:
            self._set_property(
                self._onechar_property,
                'phrase.svg',
                _('Phrase mode'),
                _('Switch to “Single character mode” (Ctrl-,)'))
        self.update_property(self._onechar_property)

        if self._auto_commit:
            self._set_property(
                self._auto_commit_property,
                'acommit.svg',
                _('Direct commit mode'),
                _('Switch to “Normal commit mode” (uses space to commit) (Ctrl-/)'))
        else:
            self._set_property(
                self._auto_commit_property,
                'ncommit.svg',
                _('Normal commit mode'),
                _('Switch to “Direct commit mode” (Ctrl-/)'))
        self.update_property(self._auto_commit_property)

        if self._always_show_lookup:
            self._set_property(
                self._always_show_lookup_property,
                'always_show_lookup_y.svg',
                _('Display candidates'),
                _('Switch to “Hide candidates”'))
        else:
            self._set_property(
                self._always_show_lookup_property,
                'always_show_lookup_n.svg',
                _('Hide candidates'),
                _('Switch to “Display candidates”'))
        self.update_property(self._always_show_lookup_property)

        # The Chinese_mode:
        #   0 means to show simplified Chinese only
        #   1 means to show traditional Chinese only
        #   2 means to show all characters but show simplified Chinese first
        #   3 means to show all characters but show traditional Chinese first
        #   4 means to show all characters
        if self.db._is_chinese:
            if self._editor._chinese_mode == 0:
                self._set_property(
                    self._cmode_property,
                    'sc-mode.svg',
                    _('Simplified Chinese'),
                    _('Switch to “Traditional Chinese” (Ctrl-;)'))
            elif self._editor._chinese_mode == 1:
                self._set_property(
                    self._cmode_property,
                    'tc-mode.svg',
                    _('Traditional Chinese'),
                    _('Switch to “Simplified Chinese before traditional” (Ctrl-;)'))
            elif self._editor._chinese_mode == 2:
                self._set_property(
                    self._cmode_property,
                    'scb-mode.svg',
                    _('Simplified Chinese before traditional'),
                    _('Switch to “Traditional Chinese before simplified” (Ctrl-;)'))
            elif self._editor._chinese_mode == 3:
                self._set_property(
                    self._cmode_property,
                    'tcb-mode.svg',
                    _('Traditional Chinese before simplified'),
                    _('Switch to “All Chinese characters” (Ctrl-;)'))
            elif self._editor._chinese_mode == 4:
                self._set_property(
                    self._cmode_property,
                    'cb-mode.svg',
                    _('All Chinese characters'),
                    _('Switch to “Simplified Chinese”'))
            self.update_property(self._cmode_property)

    def _set_property (self, property, icon, label, tooltip):
        if type(label) != type(u''):
            label = label.decode('utf-8')
        if type(tooltip) != type(u''):
            tooltip = tooltip.decode('utf-8')
        property.set_icon ( u'%s%s' % (self._icon_dir, icon ) )
        property.set_label(IBus.Text.new_from_string(label))
        property.set_tooltip(IBus.Text.new_from_string(tooltip))

    def do_property_activate(self, property, prop_state = IBus.PropState.UNCHECKED):
        '''Shift property'''
        if property == u"status":
            self._input_mode = int(not self._input_mode)
            self.reset()
            # Not saved to config on purpose. In the setup tool one
            # can select whether “Table input” or “Direct input” should
            # be the default when the input method starts. But when
            # changing this input mode using the property menu, the change
            # is not remembered.
        elif property == u'py_mode' and self._ime_py:
            self._editor.commit_to_preedit()
            self._editor._py_mode = not self._editor._py_mode
            self._update_ui()
            # Not saved to config on purpose.
        elif property == u'onechar':
            self._editor._onechar = not self._editor._onechar
            self._config.set_value(
                self._config_section,
                "OneChar",
                GLib.Variant.new_boolean(self._editor._onechar))
        elif property == u'acommit':
            self._auto_commit = not self._auto_commit
            self._config.set_value(
                self._config_section,
                "AutoCommit",
                GLib.Variant.new_boolean(self._auto_commit))
        elif property == u'letter':
            self._full_width_letter[self._input_mode] = not self._full_width_letter[self._input_mode]
            if self._input_mode:
                self._config.set_value(
                    self._config_section,
                    "TabDefFullWidthLetter",
                    GLib.Variant.new_boolean(
                        self._full_width_letter[self._input_mode]))
            else:
                self._config.set_value(
                    self._config_section,
                    "EnDefFullWidthLetter",
                    GLib.Variant.new_boolean(
                        self._full_width_letter[self._input_mode]))
        elif property == u'punct':
            self._full_width_punct[self._input_mode] = not self._full_width_punct[self._input_mode]
            if self._input_mode:
                self._config.set_value(
                    self._config_section,
                    "TabDefFullWidthPunct",
                    GLib.Variant.new_boolean(
                        self._full_width_punct[self._input_mode]))
            else:
                self._config.set_value(
                    self._config_section,
                    "EnDefFullWidthPunct",
                    GLib.Variant.new_boolean(
                        self._full_width_punct[self._input_mode]))
        elif property == u'always_show_lookup':
            self._always_show_lookup = not self._always_show_lookup
            self._config.set_value(
                self._config_section,
                "AlwaysShowLookup",
                GLib.Variant.new_boolean(self._always_show_lookup))
        elif property == u'cmode':
            if self._editor._chinese_mode != -1:
                self._editor._chinese_mode = (self._editor._chinese_mode+1) % 5
                self._config.set_value(
                    self._config_section,
                    "ChineseMode",
                    GLib.Variant.new_int32(self._editor._chinese_mode))
                self.reset()
        elif property == "setup":
                self._start_setup()
        self._refresh_properties()

    def _start_setup(self):
        if self._setup_pid != 0:
            pid, state = os.waitpid(self._setup_pid, os.P_NOWAIT)
            if pid != self._setup_pid:
                # If the last setup tool started from here is still
                # running the pid returned by the above os.waitpid()
                # is 0. In that case just return, don’t start a
                # second setup tool.
                return
            self._setup_pid = 0
        setup_cmd = os.path.join(
            os.getenv('IBUS_TABLE_LIB_LOCATION'),
            'ibus-setup-table')
        self._setup_pid = os.spawnl(
            os.P_NOWAIT,
            setup_cmd,
            'ibus-setup-table',
            '--engine-name table:%s' %self._engine_name)

    def _update_preedit(self):
        '''Update Preedit String in UI'''
        preedit_string_parts = self._editor.get_preedit_string_parts()
        left_of_current_edit = u''.join(preedit_string_parts[0])
        current_edit = preedit_string_parts[1]
        right_of_current_edit = u''.join(preedit_string_parts[2])
        for char in self._editor._prompt_characters:
            current_edit = current_edit.replace(char, self._editor._prompt_characters[char])
        preedit_string_complete = (
            left_of_current_edit + current_edit + right_of_current_edit)
        if not preedit_string_complete:
            super(tabengine, self).update_preedit_text(IBus.Text.new_from_string(u''), 0, False)
            return
        color_left = rgb(0xf9, 0x0f, 0x0f) # bright red
        color_right = rgb(0x1e, 0xdc, 0x1a) # light green
        color_invalid = rgb(0xff, 0x00, 0xff) # magenta
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
        if self._editor._chars_invalid:
            attrs.append(
                IBus.attr_foreground_new(
                    color_invalid,
                    len(left_of_current_edit) + len(current_edit)
                    - len(self._editor._chars_invalid),
                    len(left_of_current_edit) + len(current_edit)
                    ))
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
        aux_string = self._editor.get_aux_strings()
        if len(self._editor._candidates) > 0:
            aux_string += u' (%d / %d)' %(
                self._editor._lookup_table.get_cursor_pos() +1,
                self._editor._lookup_table.get_number_of_candidates())
        if aux_string:
            attrs = IBus.AttrList()
            attrs.append(IBus.attr_foreground_new(rgb(0x95,0x15,0xb5),0, len(aux_string)))
            text = IBus.Text.new_from_string(aux_string)
            i = 0
            while attrs.get(i) != None:
                attr = attrs.get(i)
                text.append_attribute(attr.get_attr_type(),
                                      attr.get_value(),
                                      attr.get_start_index(),
                                      attr.get_end_index())
                i += 1
            visible = True
            if not aux_string or not self._always_show_lookup:
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

    def commit_string (self, phrase, tabkeys=u''):
        self._editor.clear_all_input_and_preedit()
        self._update_ui()
        super(tabengine,self).commit_text(IBus.Text.new_from_string(phrase))
        if len(phrase) > 0:
            self._prev_char = phrase[-1]
        else:
            self._prev_char = None
        self._check_phrase(tabkeys=tabkeys, phrase=phrase)

    def commit_everything_unless_invalid(self):
        '''
        Commits the current input to the preëdit and then
        commits the preëdit to the application unless there are
        invalid input characters.

        Returns “True” if something was committed, “False” if not.
        '''
        if self._editor._chars_invalid:
            return False
        if not self._editor.is_empty():
            self._editor.commit_to_preedit()
        self.commit_string(self._editor.get_preedit_string_complete(),
                           tabkeys=self._editor.get_preedit_tabkeys_complete())
        return True

    def _convert_to_full_width(self, c):
        '''Convert half width character to full width'''

        # This function handles punctuation that does not comply to the
        # Unicode convesion formula in unichar_half_to_full(c).
        # For ".", "\"", "'"; there are even variations under specific
        # cases. This function should be more abstracted by extracting
        # that to another handling function later on.
        special_punct_dict = {u"<": u"《", # 《 U+300A LEFT DOUBLE ANGLE BRACKET
                               u">": u"》", # 》 U+300B RIGHT DOUBLE ANGLE BRACKET
                               u"[": u"「", # 「 U+300C LEFT CORNER BRACKET
                               u"]": u"」", # 」U+300D RIGHT CORNER BRACKET
                               u"{": u"『", # 『 U+300E LEFT WHITE CORNER BRACKET
                               u"}": u"』", # 』U+300F RIGHT WHITE CORNER BRACKET
                               u"\\": u"、", # 、 U+3001 IDEOGRAPHIC COMMA
                               u"^": u"……", # … U+2026 HORIZONTAL ELLIPSIS
                               u"_": u"——", # — U+2014 EM DASH
                               u"$": u"￥" # ￥ U+FFE5 FULLWIDTH YEN SIGN
                               }

        # special puncts w/o further conditions
        if c in special_punct_dict.keys():
            if c in [u"\\", u"^", u"_", u"$"]:
                return special_punct_dict[c]
            elif self._input_mode:
                return special_punct_dict[c]

        # special puncts w/ further conditions
        if c == u".":
            if self._prev_char and self._prev_char.isdigit() \
                and self._prev_key and chr(self._prev_key.code) == self._prev_char:
                return u"."
            else:
                return u"。" # 。U+3002 IDEOGRAPHIC FULL STOP
        elif c == u"\"":
            self._double_quotation_state = not self._double_quotation_state
            if self._double_quotation_state:
                return u"“" # “ U+201C LEFT DOUBLE QUOTATION MARK
            else:
                return u"”" # ” U+201D RIGHT DOUBLE QUOTATION MARK
        elif c == u"'":
            self._single_quotation_state = not self._single_quotation_state
            if self._single_quotation_state:
                return u"‘" # ‘ U+2018 LEFT SINGLE QUOTATION MARK
            else:
                return u"’" # ’ U+2019 RIGHT SINGLE QUOTATION MARK

        return unichar_half_to_full(c)

    def _match_hotkey (self, key, code, mask):

        if key.code == code and key.mask == mask:
            if self._prev_key and key.code == self._prev_key.code and key.mask & IBus.ModifierType.RELEASE_MASK:
                return True
            if not key.mask & IBus.ModifierType.RELEASE_MASK:
                return True

        return False

    def do_candidate_clicked(self, index, button, state):
        if self._editor.commit_to_preedit_current_page(index): # commits to preëdit
            self.commit_string(self._editor.get_preedit_string_complete(),
                               tabkeys=self._editor.get_preedit_tabkeys_complete())
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
            self.do_property_activate("status")
            return True

        # Match full half letter mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_space, IBus.ModifierType.SHIFT_MASK):
            self.do_property_activate ("letter")
            return True

        # Match full half punct mode switch hotkey
        if self._match_hotkey (key, IBus.KEY_period, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ("punct")
            return True

        if self._input_mode:
            return self._table_mode_process_key_event (key)
        else:
            return self._english_mode_process_key_event (key)

    def cond_letter_translate(self, char):
        if self._full_width_letter[self._input_mode]:
            return self._convert_to_full_width(char)
        else:
            return char

    def cond_punct_translate(self, char):
        if self._full_width_punct[self._input_mode]:
            return self._convert_to_full_width(char)
        else:
            return char

    def _english_mode_process_key_event(self, key):
        # Ignore key release event
        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True
        if key.code >= 128:
            return False
        # we ignore all hotkeys here
        if key.mask & (IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.MOD1_MASK):
            return False
        keychar = IBus.keyval_to_unicode(key.code)
        if type(keychar) != type(u''):
            keychar = keychar.decode('UTF-8')
        if ascii_ispunct(keychar):
            trans_char = self.cond_punct_translate(keychar)
        else:
            trans_char = self.cond_letter_translate(keychar)
        if trans_char == keychar:
            return False
        self.commit_string(trans_char)
        return True

    def _table_mode_process_key_event(self, key):
        if debug_level > 0:
            sys.stderr.write('_table_mode_process_key_event() ')
            sys.stderr.write('repr(key)=%(key)s\n' %{'key': key})
        # We have to process the pinyin mode change key event here,
        # because we ignore all Release event below.
        if (self._ime_py
            and self._match_hotkey(
                key, IBus.KEY_Shift_R,
                IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)):
            self.do_property_activate(u"py_mode")
            return True
        # process commit to preedit
        if (self._match_hotkey(
                key, IBus.KEY_Shift_R,
                IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
            or self._match_hotkey(
                key, IBus.KEY_Shift_L,
                IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)):
            res = self._editor.commit_to_preedit()
            self._update_ui()
            return res

        # Left ALT key to cycle candidates in the current page.
        if self._match_hotkey(
                key, IBus.KEY_Alt_L,
                IBus.ModifierType.MOD1_MASK | IBus.ModifierType.RELEASE_MASK):
            res = self._editor.cycle_next_cand()
            self._update_ui()
            return res

        # Match single char mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_comma, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate (u"onechar")
            return True

        # Match direct commit mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_slash, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate(u"acommit")
            return True

        # Match Chinese mode shift
        if self._match_hotkey(key, IBus.KEY_semicolon, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate(u"cmode")
            return True

        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True

        keychar = IBus.keyval_to_unicode(key.code)
        if type(keychar) != type(u''):
            keychar = keychar.decode('UTF-8')

        # Section to handle leading invalid input:
        #
        # This is the first character typed, if it is invalid
        # input, handle it immediately here, if it is valid, continue.
        if self._editor.is_empty() and not self._editor.get_preedit_string_complete():
            if ((keychar not in self._valid_input_chars
                 or (self.db.startchars and keychar not in self.db.startchars))
                and (not key.mask &
                     (IBus.ModifierType.MOD1_MASK |
                      IBus.ModifierType.CONTROL_MASK))):
                if debug_level > 0:
                    sys.stderr.write('_table_mode_process_key_event() leading invalid input: ')
                    sys.stderr.write('repr(keychar)=%(keychar)s\n' %{'keychar': keychar})
                if ascii_ispunct(keychar):
                    trans_char = self.cond_punct_translate(keychar)
                else:
                    trans_char = self.cond_letter_translate(keychar)
                if trans_char == keychar:
                    return False
                else:
                    self.commit_string(trans_char)
                    return True

        if key.code == IBus.KEY_Escape:
            self.reset()
            self._update_ui()
            return True

        if key.code in (IBus.KEY_Return, IBus.KEY_KP_Enter):
            if self._auto_select:
                self._editor.commit_to_preedit()
                commit_string = self._editor.get_preedit_string_complete() + os.linesep
            else:
                commit_string = self._editor.get_preedit_tabkeys_complete ()
            self.commit_string(commit_string)
            return True

        if key.code in (IBus.KEY_Tab, IBus.KEY_KP_Tab) and self._auto_select:
            # Used for example for the Russian transliteration method
            # “translit”, which uses “auto select”. If for example
            # a file with the name “шшш” exists and one types in
            # a bash shell:
            #
            #     “ls sh”
            #
            # the “sh” is converted to “ш” and one sees
            #
            #     “ls ш”
            #
            # in the shell where the “ш” is still in preëdit
            # because “shh” would be converted to “щ”, i.e. there
            # is more than one candidate and the input method is still
            # waiting whether one more “h” will be typed or not. But
            # if the next character typed is a Tab, the preëdit is
            # committed here and “False” is returned to pass the Tab
            # character through to the bash to complete the file name
            # to “шшш”.
            self._editor.commit_to_preedit()
            self.commit_string(self._editor.get_preedit_string_complete())
            return False

        if key.code in (IBus.KEY_Down, IBus.KEY_KP_Down) :
            if not self._editor.get_preedit_string_complete():
                return False
            res = self._editor.cursor_down()
            self._update_ui()
            return res

        if key.code in (IBus.KEY_Up, IBus.KEY_KP_Up):
            if not self._editor.get_preedit_string_complete():
                return False
            res = self._editor.cursor_up()
            self._update_ui()
            return res

        if (key.code in (IBus.KEY_Left, IBus.KEY_KP_Left)
            and key.mask & IBus.ModifierType.CONTROL_MASK):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.control_arrow_left()
            self._update_ui()
            return True

        if (key.code in (IBus.KEY_Right, IBus.KEY_KP_Right)
            and key.mask & IBus.ModifierType.CONTROL_MASK):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.control_arrow_right()
            self._update_ui()
            return True

        if key.code in (IBus.KEY_Left, IBus.KEY_KP_Left):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.arrow_left()
            self._update_ui()
            return True

        if key.code in (IBus.KEY_Right, IBus.KEY_KP_Right):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.arrow_right()
            self._update_ui()
            return True

        if (key.code == IBus.KEY_BackSpace
            and key.mask & IBus.ModifierType.CONTROL_MASK):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.remove_preedit_before_cursor()
            self._update_ui()
            return True

        if key.code == IBus.KEY_BackSpace:
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.remove_char()
            self._update_ui()
            return True

        if (key.code == IBus.KEY_Delete
            and key.mask & IBus.ModifierType.CONTROL_MASK):
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.remove_preedit_after_cursor()
            self._update_ui()
            return True

        if key.code == IBus.KEY_Delete:
            if not self._editor.get_preedit_string_complete():
                return False
            self._editor.delete()
            self._update_ui()
            return True

        if (keychar in self._editor.get_select_keys()
            and self._editor._candidates
            and key.mask & IBus.ModifierType.CONTROL_MASK):
            res = self._editor.select_key(keychar)
            self._update_ui()
            return res

        if (keychar in self._editor.get_select_keys()
            and self._editor._candidates
            and key.mask & IBus.ModifierType.MOD1_MASK):
            res = self._editor.remove_candidate_from_user_database(keychar)
            self._update_ui()
            return res

        # now we ignore all other hotkeys
        if key.mask & (IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.MOD1_MASK):
            return False

        if key.mask & IBus.ModifierType.MOD1_MASK:
            return False

        # Section to handle valid input characters:
        #
        # All keys which could possibly conflict with the valid input
        # characters should be checked below this section. These are
        # SELECT_KEYS, PAGE_UP_KEYS, PAGE_DOWN_KEYS, and COMMIT_KEYS.
        #
        # For example, consider a table has
        #
        #     SELECT_KEYS = 1,2,3,4,5,6,7,8,9,0
        #
        # and
        #
        #     VALID_INPUT_CHARS = 0123456789abcdef
        #
        # (Currently the cns11643 table has this, for example)
        #
        # Then the digit “1” could be interpreted either as an input
        # character or as a select key but of course not both. If the
        # meaning as a select key or page down key were preferred,
        # this would make some input impossible which probably makes
        # the whole input method useless. If the meaning as an input
        # character is preferred, this makes selection using that key
        # impossible.  Making selection by key impossible is not nice
        # either, but it is not a complete show stopper as there are
        # still other possibilities to select, for example using the
        # arrow-up/arrow-down keys or click with the mouse.
        #
        # Of course one should maybe consider fixing the conflict
        # between the keys by using different SELECT_KEYS and/or
        # PAGE_UP_KEYS/PAGE_DOWN_KEYS in that table ...
        if (keychar
            and (keychar in self._valid_input_chars
                 or (self._editor._py_mode
                     and keychar in u'abcdefghijklmnopqrstuvwxyz!@#$%'))):
            if debug_level > 0:
                sys.stderr.write('_table_mode_process_key_event() valid input: ')
                sys.stderr.write('repr(keychar)=%(keychar)s\n' %{'keychar': keychar})
            if self._editor._py_mode:
                if ((len(self._editor._chars_valid)
                     == self._max_key_length_pinyin)
                    or (len(self._editor._chars_valid) > 1
                        and self._editor._chars_valid[-1] in '!@#$%')):
                    if self._auto_commit:
                        self.commit_everything_unless_invalid()
                    else:
                        self._editor.commit_to_preedit()
            else:
                if ((len(self._editor._chars_valid)
                     == self._max_key_length)
                    or (len(self._editor._chars_valid)
                        in self.db.possible_tabkeys_lengths)):
                    if self._auto_commit:
                        self.commit_everything_unless_invalid()
                    else:
                        self._editor.commit_to_preedit()
            res = self._editor.add_input(keychar)
            if not res:
                if self._auto_select and self._editor._candidates_previous:
                    # Used for example for the Russian transliteration method
                    # “translit”, which uses “auto select”.
                    # The “translit” table contains:
                    #
                    #     sh ш
                    #     shh щ
                    #
                    # so typing “sh” matches “ш” and “щ”. The
                    # candidate with the shortest key sequence comes
                    # first in the lookup table, therefore “sh ш”
                    # is shown in the preëdit (The other candidate,
                    # “shh щ” comes second in the lookup table and
                    # could be selected using arrow-down. But
                    # “translit” hides the lookup table by default).
                    #
                    # Now, when after typing “sh” one types “s”,
                    # the key “shs” has no match, so add_input('s')
                    # returns “False” and we end up here. We pop the
                    # last character “s” which caused the match to
                    # fail, commit first of the previous candidates,
                    # i.e. “sh ш” and feed the “s” into the
                    # key event handler again.
                    self._editor.pop_input()
                    self.commit_everything_unless_invalid()
                    return self._table_mode_process_key_event(key)
                self.commit_everything_unless_invalid()
                self._update_ui()
                return True
            else:
                if (self._auto_commit and self._editor.one_candidate()
                    and
                    (self._editor._chars_valid
                     == self._editor._candidates[0][0])):
                    self.commit_everything_unless_invalid()
                self._update_ui()
                return True

        if key.code in self._commit_keys:
            if self.commit_everything_unless_invalid():
                if self._editor._auto_select:
                    self.commit_string(u' ')
            return True

        if key.code in self._page_down_keys and self._editor._candidates:
            res = self._editor.page_down()
            self._update_ui()
            return res

        if key.code in self._page_up_keys and self._editor._candidates:
            res = self._editor.page_up()
            self._update_ui()
            return res

        if keychar in self._editor.get_select_keys() and self._editor._candidates:
            if self._editor.select_key(keychar): # commits to preëdit
                self.commit_string(self._editor.get_preedit_string_complete(),
                                   tabkeys=self._editor.get_preedit_tabkeys_complete())
            return True

        # Section to handle trailing invalid input:
        #
        # If the key has still not been handled when this point is
        # reached, it cannot be a valid input character. Neither can
        # it be a select key nor a page-up/page-down key. Adding this
        # key to the tabkeys and search for matching candidates in the
        # table would thus be pointless.
        #
        # So we commit all pending input immediately and then commit
        # this invalid input character as well, possibly converted to
        # fullwidth or halfwidth.
        if keychar:
            if debug_level > 0:
                sys.stderr.write('_table_mode_process_key_event() trailing invalid input: ')
                sys.stderr.write('repr(keychar)=%(keychar)s\n' %{'keychar': keychar})
            if not self._editor._candidates:
                self.commit_string(self._editor.get_preedit_tabkeys_complete())
            else:
                self._editor.commit_to_preedit()
                self.commit_string(self._editor.get_preedit_string_complete())
            if ascii_ispunct(keychar):
                self.commit_string(self.cond_punct_translate(keychar))
            else:
                self.commit_string(self.cond_letter_translate(keychar))
            return True

        # What kind of key was this??
        #
        #     keychar = IBus.keyval_to_unicode(key.code)
        #
        # returned no result. So whatever this was, we cannot handle it,
        # just pass it through to the application by returning “False”.
        return False

    def do_focus_in (self):
        if self._on:
            self.register_properties (self.properties)
            self._refresh_properties ()
            self._update_ui ()

    def do_focus_out (self):
        if self._has_input_purpose:
            self._input_purpose = 0
        self._editor.clear_all_input_and_preedit()

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

    def config_value_changed_cb(self, config, section, name, value):
        if self.config_section_normalize(self._config_section) != self.config_section_normalize(section):
            return
        print("config value %(n)s for engine %(en)s changed" %{'n': name, 'en': self._engine_name})
        value = variant_to_value(value)
        if name == u'inputmode':
            self._input_mode = value
            self._refresh_properties()
            return
        if name == u'autoselect':
            self._editor._auto_select = value
            self._auto_select = value
            self._refresh_properties()
            return
        if name == u'autocommit':
            self._auto_commit = value
            self._refresh_properties()
            return
        if name == u'chinesemode':
            self._editor._chinese_mode = value
            self._refresh_properties()
            return
        if name == u'endeffullwidthletter':
            self._full_width_letter[0] = value
            self._refresh_properties()
            return
        if name == u'endeffullwidthpunct':
            self._full_width_punct[0] = value
            self._refresh_properties()
            return
        if name == u'lookuptableorientation':
            self._editor._orientation = value
            self._editor._lookup_table.set_orientation(value)
            return
        if name == u'lookuptablepagesize':
            if value > len(self._editor._select_keys):
                value = len(self._editor._select_keys)
                self._config.set_value(
                    self._config_section,
                    'lookuptablepagesize',
                    GLib.Variant.new_int32(value))
            if value < 1:
                value = 1
                self._config.set_value(
                    self._config_section,
                    'lookuptablepagesize',
                    GLib.Variant.new_int32(value))
            self._editor._page_size = value
            self._editor._lookup_table = self._editor.get_new_lookup_table(
                page_size = self._editor._page_size,
                select_keys = self._editor._select_keys,
                orientation = self._editor._orientation)
            self.reset()
            return
        if name == u'lookuptableselectkeys':
            self._editor.set_select_keys(value)
            return
        if name == u'onechar':
            self._editor._onechar = value
            self._refresh_properties()
            return
        if name == u'tabdeffullwidthletter':
            self._full_width_letter[1] = value
            self._refresh_properties()
            return
        if name == u'tabdeffullwidthpunct':
            self._full_width_punct[1] = value
            self._refresh_properties()
            return
        if name == u'alwaysshowlookup':
            self._always_show_lookup = value
            self._refresh_properties()
            return
        if name == u'spacekeybehavior':
            if value == True:
                # space is used as a page down key and not as a commit key:
                if IBus.KEY_space not in self._page_down_keys:
                    self._page_down_keys.append(IBus.KEY_space)
                if IBus.KEY_space in self._commit_keys:
                    self._commit_keys.remove(IBus.KEY_space)
            if value == False:
                # space is used as a commit key and not used as a page down key:
                if IBus.KEY_space in self._page_down_keys:
                    self._page_down_keys.remove(IBus.KEY_space)
                if IBus.KEY_space not in self._commit_keys:
                    self._commit_keys.append(IBus.KEY_space)
            return

