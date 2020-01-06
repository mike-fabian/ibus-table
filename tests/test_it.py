#!/usr/bin/python3

# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2018 Mike FABIAN <mfabian@redhat.com>
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
This file implements the test cases for the unit tests of ibus-table
'''

import sys
import os
import unittest

from gi import require_version
require_version('IBus', '1.0')
from gi.repository import IBus

# Get more verbose output in the test log:
os.environ['IBUS_TABLE_DEBUG_LEVEL'] = '255'

# Monkey patch the environment with the mock classes:
from mock_engine import MockEngine
from mock_engine import MockLookupTable
from mock_engine import MockProperty
from mock_engine import MockPropList
sys.modules["gi.repository.IBus"].Engine = MockEngine
sys.modules["gi.repository.IBus"].LookupTable = MockLookupTable
sys.modules["gi.repository.IBus"].Property = MockProperty
sys.modules["gi.repository.IBus"].PropList = MockPropList

sys.path.insert(0, "../engine")
from table import *
import tabsqlitedb

ENGINE = None
TABSQLITEDB = None
ORIG_INPUT_MODE = None
ORIG_CHINESE_MODE = None
ORIG_LETTER_WIDTH = None
ORIG_PUNCTUATION_WIDTH = None
ORIG_ALWAYS_SHOW_LOOKUP = None
ORIG_LOOKUP_TABLE_ORIENTATION = None
ORIG_PAGE_SIZE = None
ORIG_ONECHAR_MODE = None
ORIG_AUTOSELECT_MODE = None
ORIG_AUTOCOMMIT_MODE = None
ORIG_SPACE_KEY_BEHAVIOR_MODE = None
ORIG_AUTOWILDCARD_MODE = None
ORIG_SINGLE_WILDCARD_CHAR = None
ORIG_MULTI_WILDCARD_CHAR = None

def backup_original_settings():
    global ENGINE
    global ORIG_INPUT_MODE
    global ORIG_CHINESE_MODE
    global ORIG_LETTER_WIDTH
    global ORIG_PUNCTUATION_WIDTH
    global ORIG_ALWAYS_SHOW_LOOKUP
    global ORIG_LOOKUP_TABLE_ORIENTATION
    global ORIG_PAGE_SIZE
    global ORIG_ONECHAR_MODE
    global ORIG_AUTOSELECT_MODE
    global ORIG_AUTOCOMMIT_MODE
    global ORIG_SPACE_KEY_BEHAVIOR_MODE
    global ORIG_AUTOWILDCARD_MODE
    global ORIG_SINGLE_WILDCARD_CHAR
    global ORIG_MULTI_WILDCARD_CHAR
    ORIG_INPUT_MODE = ENGINE.get_input_mode()
    ORIG_CHINESE_MODE = ENGINE.get_chinese_mode()
    ORIG_LETTER_WIDTH = ENGINE.get_letter_width()
    ORIG_PUNCTUATION_WIDTH = ENGINE.get_punctuation_width()
    ORIG_ALWAYS_SHOW_LOOKUP = ENGINE.get_always_show_lookup()
    ORIG_LOOKUP_TABLE_ORIENTATION = ENGINE.get_lookup_table_orientation()
    ORIG_PAGE_SIZE = ENGINE.get_page_size()
    ORIG_ONECHAR_MODE = ENGINE.get_onechar_mode()
    ORIG_AUTOSELECT_MODE = ENGINE.get_autoselect_mode()
    ORIG_AUTOCOMMIT_MODE = ENGINE.get_autocommit_mode()
    ORIG_SPACE_KEY_BEHAVIOR_MODE = ENGINE.get_space_key_behavior_mode()
    ORIG_AUTOWILDCARD_MODE = ENGINE.get_autowildcard_mode()
    ORIG_SINGLE_WILDCARD_CHAR = ENGINE.get_single_wildcard_char()
    ORIG_MULTI_WILDCARD_CHAR = ENGINE.get_multi_wildcard_char()

def restore_original_settings():
    global ENGINE
    global ORIG_INPUT_MODE
    global ORIG_CHINESE_MODE
    global ORIG_LETTER_WIDTH
    global ORIG_PUNCTUATION_WIDTH
    global ORIG_ALWAYS_SHOW_LOOKUP
    global ORIG_LOOKUP_TABLE_ORIENTATION
    global ORIG_PAGE_SIZE
    global ORIG_ONECHAR_MODE
    global ORIG_AUTOSELECT_MODE
    global ORIG_AUTOCOMMIT_MODE
    global ORIG_SPACE_KEY_BEHAVIOR_MODE
    global ORIG_AUTOWILDCARD_MODE
    global ORIG_SINGLE_WILDCARD_CHAR
    global ORIG_MULTI_WILDCARD_CHAR
    ENGINE.set_input_mode(ORIG_INPUT_MODE)
    ENGINE.set_chinese_mode(ORIG_CHINESE_MODE)
    ENGINE.set_letter_width(ORIG_LETTER_WIDTH[0], input_mode=0)
    ENGINE.set_letter_width(ORIG_LETTER_WIDTH[1], input_mode=1)
    ENGINE.set_punctuation_width(ORIG_PUNCTUATION_WIDTH[0], input_mode=0)
    ENGINE.set_punctuation_width(ORIG_PUNCTUATION_WIDTH[1], input_mode=1)
    ENGINE.set_always_show_lookup(ORIG_ALWAYS_SHOW_LOOKUP)
    ENGINE.set_lookup_table_orientation(ORIG_LOOKUP_TABLE_ORIENTATION)
    ENGINE.set_page_size(ORIG_PAGE_SIZE)
    ENGINE.set_onechar_mode(ORIG_ONECHAR_MODE)
    ENGINE.set_autoselect_mode(ORIG_AUTOSELECT_MODE)
    ENGINE.set_autocommit_mode(ORIG_AUTOCOMMIT_MODE)
    ENGINE.set_space_key_behavior_mode(ORIG_SPACE_KEY_BEHAVIOR_MODE)
    ENGINE.set_autowildcard_mode(ORIG_AUTOWILDCARD_MODE)
    ENGINE.set_single_wildcard_char(ORIG_SINGLE_WILDCARD_CHAR)
    ENGINE.set_multi_wildcard_char(ORIG_MULTI_WILDCARD_CHAR)

def set_default_settings():
    global ENGINE
    global TABSQLITEDB
    ENGINE.set_input_mode(mode=1)
    chinese_mode = 4
    language_filter = TABSQLITEDB.ime_properties.get('language_filter')
    if language_filter in ('cm0', 'cm1', 'cm2', 'cm3', 'cm4'):
        chinese_mode = int(language_filter[-1])
    ENGINE.set_chinese_mode(mode=chinese_mode)

    letter_width_mode = False
    def_full_width_letter = TABSQLITEDB.ime_properties.get(
        'def_full_width_letter')
    if def_full_width_letter:
        letter_width_mode = (def_full_width_letter.lower() == u'true')
    ENGINE.set_letter_width(mode=False, input_mode=0)
    ENGINE.set_letter_width(mode=letter_width_mode, input_mode=1)

    punctuation_width_mode = False
    def_full_width_punct = TABSQLITEDB.ime_properties.get(
        'def_full_width_punct')
    if def_full_width_punct:
        punctuation_width_mode = (def_full_width_punct.lower() == u'true')
    ENGINE.set_punctuation_width(mode=False, input_mode=0)
    ENGINE.set_punctuation_width(mode=punctuation_width_mode, input_mode=1)

    always_show_lookup_mode = True
    always_show_lookup = TABSQLITEDB.ime_properties.get(
        'always_show_lookup')
    if always_show_lookup:
        always_show_lookup_mode = (always_show_lookup.lower() == u'true')
    ENGINE.set_always_show_lookup(always_show_lookup_mode)

    orientation = TABSQLITEDB.get_orientation()
    ENGINE.set_lookup_table_orientation(orientation)

    page_size = 6
    select_keys_csv = TABSQLITEDB.ime_properties.get('select_keys')
    # select_keys_csv is something like: "1,2,3,4,5,6,7,8,9,0"
    if select_keys_csv:
        page_size = len(select_keys_csv.split(","))
    ENGINE.set_page_size(page_size)

    onechar = False
    ENGINE.set_onechar_mode(onechar)

    auto_select_mode = False
    auto_select = TABSQLITEDB.ime_properties.get('auto_select')
    if auto_select:
        auto_select_mode = (auto_select.lower() == u'true')
    ENGINE.set_autoselect_mode(auto_select_mode)

    auto_commit_mode = False
    auto_commit = TABSQLITEDB.ime_properties.get('auto_commit')
    if auto_commit:
        auto_commit_mode = (auto_commit.lower() == u'true')
    ENGINE.set_autocommit_mode(auto_commit_mode)

    space_key_behavior_mode = False
    # if space is a page down key, set the option
    # “spacekeybehavior” to “True”:
    page_down_keys_csv = TABSQLITEDB.ime_properties.get(
        'page_down_keys')
    if page_down_keys_csv:
        page_down_keys = [
            IBus.keyval_from_name(x)
            for x in page_down_keys_csv.split(',')]
    if IBus.KEY_space in page_down_keys:
        space_key_behavior_mode = True
    # if space is a commit key, set the option
    # “spacekeybehavior” to “False” (overrides if space is
    # also a page down key):
    commit_keys_csv = TABSQLITEDB.ime_properties.get('commit_keys')
    if commit_keys_csv:
        commit_keys = [
            IBus.keyval_from_name(x)
            for x in commit_keys_csv.split(',')]
    if IBus.KEY_space in commit_keys:
        space_key_behavior_mode = False
    ENGINE.set_space_key_behavior_mode(space_key_behavior_mode)

    auto_wildcard_mode = True
    auto_wildcard = TABSQLITEDB.ime_properties.get('auto_wildcard')
    if auto_wildcard:
        auto_wildcard_mode = (auto_wildcard.lower() == u'true')
    ENGINE.set_autowildcard_mode(auto_wildcard_mode)

    single_wildcard_char = TABSQLITEDB.ime_properties.get(
        'single_wildcard_char')
    if not single_wildcard_char:
        single_wildcard_char = u''
    if len(single_wildcard_char) > 1:
        single_wildcard_char = single_wildcard_char[0]
    ENGINE.set_single_wildcard_char(single_wildcard_char)

    multi_wildcard_char = TABSQLITEDB.ime_properties.get(
        'multi_wildcard_char')
    if not multi_wildcard_char:
        multi_wildcard_char = u''
    if len(multi_wildcard_char) > 1:
        multi_wildcard_char = multi_wildcard_char[0]
    ENGINE.set_multi_wildcard_char(multi_wildcard_char)

def set_up(engine_name):
    global TABSQLITEDB
    global ENGINE
    bus = IBus.Bus()
    db_dir = '/usr/share/ibus-table/tables'
    db_file = os.path.join(db_dir, engine_name + '.db')
    TABSQLITEDB = tabsqlitedb.TabSqliteDb(
        filename=db_file, user_db=':memory:')
    ENGINE = TabEngine(
        bus,
        '/com/redhat/IBus/engines/table/%s/engine/0' %engine_name,
        TABSQLITEDB,
        unit_test=True)
    backup_original_settings()
    set_default_settings()

def tear_down():
    restore_original_settings()

class WubiJidian86TestCase(unittest.TestCase):
    def setUp(self):
        set_up('wubi-jidian86')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工')

    def test_commit_to_preedit_switching_to_pinyin_defining_a_phrase(self):
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        # commit to preëdit needs a press and release of either
        # the left or the right shift key:
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE.do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了')
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以')
        ENGINE.do_process_key_event(IBus.KEY_d, 0, 0)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以在')
        # Move left two characters in the preëdit:
        ENGINE.do_process_key_event(IBus.KEY_Left, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Left, 0, 0)
        # Switch to pinyin mode by pressing and releasing the right
        # shift key:
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        ENGINE.do_process_key_event(IBus.KEY_n, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_i, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_numbersign, 0, 0)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你以在')
        ENGINE.do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_o, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_numbersign, 0, 0)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        # Move right two characters in the preëdit
        # (triggers a commit to preëdit):
        ENGINE.do_process_key_event(IBus.KEY_Right, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Right, 0, 0)
        self.assertEqual(ENGINE.mock_auxiliary_text, 'd dhf dhfd\t#: abwd')
        # commit the preëdit:
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工了你好以在')
        # Switch out of pinyin mode:
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE.do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        # “abwd” shown on the right of the auxiliary text above shows the
        # newly defined shortcut for this phrase. Let’s  try to type
        # the same phrase again using the new shortcut:
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE.do_process_key_event(IBus.KEY_b, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '节')
        ENGINE.do_process_key_event(IBus.KEY_w, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        ENGINE.do_process_key_event(IBus.KEY_d, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        # commit the preëdit:
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工了你好以在工了你好以在')

    def test_chinese_mode(self):
        ENGINE.set_chinese_mode(mode=0) # show simplified Chinese only
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['以  418261033 0',
                          '能 ex 1820000000 0',
                          '能 exx 1820000000 0',
                          '对 fy 1200000000 0',
                          '又 cc 729000000 0',
                          '又 ccc 729000000 0',
                          '通 ep 521000000 0',
                          '通 epk 521000000 0',
                          '台 kf 486000000 0',
                          '难忘 wyn 404000000 0'])
        ENGINE.do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(mode=1) # show traditional Chinese only
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['以  418261033 0',
                          '能 ex 1820000000 0',
                          '能 exx 1820000000 0',
                          '又 cc 729000000 0',
                          '又 ccc 729000000 0',
                          '通 ep 521000000 0',
                          '通 epk 521000000 0',
                          '台 kf 486000000 0',
                          '能 e 306980312 0',
                          '能力 elt 274000000 0'])
        ENGINE.do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(mode=2) # show simplified Chinese first
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['以  418261033 0',
                          '能 ex 1820000000 0',
                          '能 exx 1820000000 0',
                          '对 fy 1200000000 0',
                          '又 cc 729000000 0',
                          '又 ccc 729000000 0',
                          '通 ep 521000000 0',
                          '通 epk 521000000 0',
                          '台 kf 486000000 0',
                          '难忘 wyn 404000000 0'])
        ENGINE.do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(mode=3) # show traditional Chinese first
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['以  418261033 0',
                          '能 ex 1820000000 0',
                          '能 exx 1820000000 0',
                          '又 cc 729000000 0',
                          '又 ccc 729000000 0',
                          '通 ep 521000000 0',
                          '通 epk 521000000 0',
                          '台 kf 486000000 0',
                          '能 e 306980312 0',
                          '能力 elt 274000000 0'])
        ENGINE.do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(mode=4) # show all characters
        ENGINE.do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['以  418261033 0',
                          '能 ex 1820000000 0',
                          '能 exx 1820000000 0',
                          '对 fy 1200000000 0',
                          '又 cc 729000000 0',
                          '又 ccc 729000000 0',
                          '通 ep 521000000 0',
                          '通 epk 521000000 0',
                          '台 kf 486000000 0',
                          '难忘 wyn 404000000 0'])
        ENGINE.do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates, [])

class Stroke5TestCase(unittest.TestCase):
    def setUp(self):
        set_up('stroke5')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE.do_process_key_event(IBus.KEY_comma, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_slash, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_n, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '的')

class TranslitTestCase(unittest.TestCase):
    def setUp(self):
        set_up('translit')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_sh_multiple_match(self):
        ENGINE.do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE.do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        ENGINE.do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ш')
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE.do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ш')
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        ENGINE.do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщ')
        self.assertEqual(ENGINE.mock_preedit_text, '')
        ENGINE.do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщ')
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщс ')

class Cangjie5TestCase(unittest.TestCase):
    def setUp(self):
        set_up('cangjie5')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '日')

    def test_type_one_char_and_check_auxiliary(self):
        ENGINE.do_process_key_event(IBus.KEY_d, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '木')
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates[8],
                         '林 木 1000 0')
        ENGINE.do_process_key_event(IBus.KEY_v, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_i, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_i, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '機')
        self.assertEqual(ENGINE.mock_auxiliary_text, '木女戈戈 (1 / 1)')
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['機  1000 0'])
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '機')

class IpaXSampaTestCase(unittest.TestCase):
    def setUp(self):
        set_up('ipa-x-sampa')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE.do_process_key_event(IBus.KEY_at, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ə ')

    def test_single_char_commit_with_f3(self):
        ENGINE.do_process_key_event(IBus.KEY_at, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['ə  0 0', 'ɘ \\ 0 0', 'ɚ ` 0 0'])
        ENGINE.do_process_key_event(IBus.KEY_F3, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ɚ')

class LatexTestCase(unittest.TestCase):
    def setUp(self):
        set_up('latex')

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE.do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_l, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_p, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'α')

    def test_single_char_commit_with_f3(self):
        ENGINE.do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_b, 0, 0)
        # Lookup table shows only the first page, subsequent
        # pages are added on demand as a speed optimization:
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['¯ ar 0 0',
                          '⊥ ot 0 0',
                          'β eta 0 0',
                          'ℶ eth 0 0',
                          '⋂ igcap 0 0',
                          '⋃ igcup 0 0',
                          '⋁ igvee 0 0',
                          '⋈ owtie 0 0',
                          '⊡ oxdot 0 0'])
        ENGINE.do_process_key_event(IBus.KEY_F3, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β')
        ENGINE.do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Page_Down, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['β eta 0 1', # user freq for β increased to 1
                          '¯ ar 0 0',
                          '⊥ ot 0 0',
                          'ℶ eth 0 0',
                          '⋂ igcap 0 0',
                          '⋃ igcup 0 0',
                          '⋁ igvee 0 0',
                          '⋈ owtie 0 0',
                          '⊡ oxdot 0 0',
                          '• ullet 0 0',
                          '∙ ullet 0 0',
                          '≏ umpeq 0 0',
                          '∽ acksim 0 0',
                          '∵ ecause 0 0',
                          '≬ etween 0 0',
                          '⊞ oxplus 0 0',
                          '⊼ arwedge 0 0',
                          '⋀ igwedge 0 0'])
        self.assertEqual(ENGINE._editor._lookup_table.get_cursor_pos(), 9)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.get_cursor_pos(), 15)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates[0:18],
                         ['β eta 0 1', # user freq for β increased to 1
                          '¯ ar 0 0',
                          '⊥ ot 0 0',
                          'ℶ eth 0 0',
                          '⋂ igcap 0 0',
                          '⋃ igcup 0 0',
                          '⋁ igvee 0 0',
                          '⋈ owtie 0 0',
                          '⊡ oxdot 0 0',
                          '• ullet 0 0',
                          '∙ ullet 0 0',
                          '≏ umpeq 0 0',
                          '∽ acksim 0 0',
                          '∵ ecause 0 0',
                          '≬ etween 0 0',
                          '⊞ oxplus 0 0',
                          '⊼ arwedge 0 0',
                          '⋀ igwedge 0 0'])
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β⊞')
        ENGINE.do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Page_Down, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.mock_candidates,
                         ['β eta 0 1', # user freq for β increased to 1
                          '⊞ oxplus 0 1', # user freq for ⊞ increased to 1
                          '¯ ar 0 0',
                          '⊥ ot 0 0',
                          'ℶ eth 0 0',
                          '⋂ igcap 0 0',
                          '⋃ igcup 0 0',
                          '⋁ igvee 0 0',
                          '⋈ owtie 0 0',
                          '⊡ oxdot 0 0',
                          '• ullet 0 0',
                          '∙ ullet 0 0',
                          '≏ umpeq 0 0',
                          '∽ acksim 0 0',
                          '∵ ecause 0 0',
                          '≬ etween 0 0',
                          '⊼ arwedge 0 0',
                          '⋀ igwedge 0 0'])
        self.assertEqual(ENGINE._editor._lookup_table.get_cursor_pos(), 9)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE.do_process_key_event(IBus.KEY_Down, 0, 0)
        self.assertEqual(ENGINE._editor._lookup_table.get_cursor_pos(), 15)
        ENGINE.do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β⊞≬')

if __name__ == '__main__':
    unittest.main()
