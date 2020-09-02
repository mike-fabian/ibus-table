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
import logging
import unittest
import importlib
import mock

from gi import require_version
require_version('IBus', '1.0')
from gi.repository import IBus

LOGGER = logging.getLogger('ibus-table')

# Get more verbose output in the test log:
os.environ['IBUS_TABLE_DEBUG_LEVEL'] = '255'

# Monkey patch the environment with the mock classes:
from mock_engine import MockEngine
from mock_engine import MockLookupTable
from mock_engine import MockProperty
from mock_engine import MockPropList

sys.path.insert(0, "../engine")
import table
import tabsqlitedb
import ibus_table_location
sys.path.pop(0)

ENGINE_PATCHER = mock.patch.object(
    IBus, 'Engine', new=MockEngine)
ENGINE_SIMPLE_PATCHER = mock.patch.object(
    IBus, 'EngineSimple', new=MockEngine)
LOOKUP_TABLE_PATCHER = mock.patch.object(
    IBus, 'LookupTable', new=MockLookupTable)
PROPERTY_PATCHER = mock.patch.object(
    IBus, 'Property', new=MockProperty)
PROP_LIST_PATCHER = mock.patch.object(
    IBus, 'PropList', new=MockPropList)
IBUS_ENGINE = IBus.Engine
IBUS_ENGINE_SIMPLE = IBus.EngineSimple
IBUS_LOOKUP_TABLE = IBus.LookupTable
IBUS_PROPERTY = IBus.Property
IBUS_PROP_LIST = IBus.PropList

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
ORIG_AUTOWILDCARD_MODE = None
ORIG_SINGLE_WILDCARD_CHAR = None
ORIG_MULTI_WILDCARD_CHAR = None
ORIG_PINYIN_MODE = None
ORIG_SUGGESTION_MODE = None
ORIG_KEYBINDINGS = None
ORIG_DEBUG_LEVEL = None

def backup_original_settings():
    global ENGINE
    global ORIG_KEYBINDINGS
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
    global ORIG_AUTOWILDCARD_MODE
    global ORIG_SINGLE_WILDCARD_CHAR
    global ORIG_MULTI_WILDCARD_CHAR
    global ORIG_PINYIN_MODE
    global ORIG_SUGGESTION_MODE
    global ORIG_DEBUG_LEVEL
    ORIG_KEYBINDINGS = ENGINE.get_keybindings()
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
    ORIG_AUTOWILDCARD_MODE = ENGINE.get_autowildcard_mode()
    ORIG_SINGLE_WILDCARD_CHAR = ENGINE.get_single_wildcard_char()
    ORIG_MULTI_WILDCARD_CHAR = ENGINE.get_multi_wildcard_char()
    ORIG_PINYIN_MODE = ENGINE.get_pinyin_mode()
    ORIG_SUGGESTION_MODE = ENGINE.get_suggestion_mode()
    ORIG_DEBUG_LEVEL = ENGINE.get_debug_level()

def restore_original_settings():
    global ENGINE
    global ORIG_KEYBINDINGS
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
    global ORIG_AUTOWILDCARD_MODE
    global ORIG_SINGLE_WILDCARD_CHAR
    global ORIG_MULTI_WILDCARD_CHAR
    global ORIG_PINYIN_MODE
    global ORIG_SUGGESTION_MODE
    global ORIG_DEBUG_LEVEL
    ENGINE.set_keybindings(
        ORIG_KEYBINDINGS, update_gsettings=False)
    ENGINE.set_input_mode(ORIG_INPUT_MODE)
    ENGINE.set_chinese_mode(
        ORIG_CHINESE_MODE, update_gsettings=False)
    ENGINE.set_letter_width(
        ORIG_LETTER_WIDTH[0], input_mode=0, update_gsettings=False)
    ENGINE.set_letter_width(
        ORIG_LETTER_WIDTH[1], input_mode=1, update_gsettings=False)
    ENGINE.set_punctuation_width(
        ORIG_PUNCTUATION_WIDTH[0], input_mode=0, update_gsettings=False)
    ENGINE.set_punctuation_width(
        ORIG_PUNCTUATION_WIDTH[1], input_mode=1, update_gsettings=False)
    ENGINE.set_always_show_lookup(
        ORIG_ALWAYS_SHOW_LOOKUP, update_gsettings=False)
    ENGINE.set_lookup_table_orientation(
        ORIG_LOOKUP_TABLE_ORIENTATION, update_gsettings=False)
    ENGINE.set_page_size(
        ORIG_PAGE_SIZE, update_gsettings=False)
    ENGINE.set_onechar_mode(ORIG_ONECHAR_MODE, update_gsettings=False)
    ENGINE.set_autoselect_mode(
        ORIG_AUTOSELECT_MODE, update_gsettings=False)
    ENGINE.set_autocommit_mode(
        ORIG_AUTOCOMMIT_MODE, update_gsettings=False)
    ENGINE.set_autowildcard_mode(
        ORIG_AUTOWILDCARD_MODE, update_gsettings=False)
    ENGINE.set_single_wildcard_char(
        ORIG_SINGLE_WILDCARD_CHAR, update_gsettings=False)
    ENGINE.set_multi_wildcard_char(
        ORIG_MULTI_WILDCARD_CHAR, update_gsettings=False)
    ENGINE.set_pinyin_mode(ORIG_PINYIN_MODE)
    ENGINE.set_suggestion_mode(ORIG_SUGGESTION_MODE)
    ENGINE.set_debug_level(ORIG_DEBUG_LEVEL, update_gsettings=False)

def set_default_settings():
    global ENGINE
    global TABSQLITEDB
    ENGINE.set_input_mode(mode=1)
    chinese_mode = 4
    language_filter = TABSQLITEDB.ime_properties.get('language_filter')
    if language_filter in ('cm0', 'cm1', 'cm2', 'cm3', 'cm4'):
        chinese_mode = int(language_filter[-1])
    ENGINE.set_chinese_mode(
        mode=chinese_mode, update_gsettings=False)

    letter_width_mode = False
    def_full_width_letter = TABSQLITEDB.ime_properties.get(
        'def_full_width_letter')
    if def_full_width_letter:
        letter_width_mode = (def_full_width_letter.lower() == u'true')
    ENGINE.set_letter_width(
        mode=False, input_mode=0, update_gsettings=False)
    ENGINE.set_letter_width(
        mode=letter_width_mode, input_mode=1, update_gsettings=False)

    punctuation_width_mode = False
    def_full_width_punct = TABSQLITEDB.ime_properties.get(
        'def_full_width_punct')
    if def_full_width_punct:
        punctuation_width_mode = (def_full_width_punct.lower() == u'true')
    ENGINE.set_punctuation_width(
        mode=False, input_mode=0, update_gsettings=False)
    ENGINE.set_punctuation_width(
        mode=punctuation_width_mode, input_mode=1, update_gsettings=False)

    always_show_lookup_mode = True
    always_show_lookup = TABSQLITEDB.ime_properties.get(
        'always_show_lookup')
    if always_show_lookup:
        always_show_lookup_mode = (always_show_lookup.lower() == u'true')
    ENGINE.set_always_show_lookup(
        always_show_lookup_mode, update_gsettings=False)

    orientation = TABSQLITEDB.get_orientation()
    ENGINE.set_lookup_table_orientation(
        orientation, update_gsettings=False)

    page_size = 6
    select_keys_csv = TABSQLITEDB.ime_properties.get('select_keys')
    # select_keys_csv is something like: "1,2,3,4,5,6,7,8,9,0"
    if select_keys_csv:
        page_size = len(select_keys_csv.split(","))
    ENGINE.set_page_size(
        page_size, update_gsettings=False)

    onechar = False
    ENGINE.set_onechar_mode(
        onechar, update_gsettings=False)

    auto_select_mode = False
    auto_select = TABSQLITEDB.ime_properties.get('auto_select')
    if auto_select:
        auto_select_mode = (auto_select.lower() == u'true')
    ENGINE.set_autoselect_mode(
        auto_select_mode, update_gsettings=False)

    auto_commit_mode = False
    auto_commit = TABSQLITEDB.ime_properties.get('auto_commit')
    if auto_commit:
        auto_commit_mode = (auto_commit.lower() == u'true')
    ENGINE.set_autocommit_mode(
        auto_commit_mode, update_gsettings=False)

    page_down_keys_csv = TABSQLITEDB.ime_properties.get(
        'page_down_keys')
    if page_down_keys_csv:
        page_down_keys = [
            IBus.keyval_from_name(x)
            for x in page_down_keys_csv.split(',')]
    commit_keys_csv = TABSQLITEDB.ime_properties.get('commit_keys')
    if commit_keys_csv:
        commit_keys = [
            IBus.keyval_from_name(x)
            for x in commit_keys_csv.split(',')]

    auto_wildcard_mode = True
    auto_wildcard = TABSQLITEDB.ime_properties.get('auto_wildcard')
    if auto_wildcard:
        auto_wildcard_mode = (auto_wildcard.lower() == u'true')
    ENGINE.set_autowildcard_mode(
        auto_wildcard_mode, update_gsettings=False)

    single_wildcard_char = TABSQLITEDB.ime_properties.get(
        'single_wildcard_char')
    if not single_wildcard_char:
        single_wildcard_char = u''
    if len(single_wildcard_char) > 1:
        single_wildcard_char = single_wildcard_char[0]
    ENGINE.set_single_wildcard_char(
        single_wildcard_char, update_gsettings=False)

    multi_wildcard_char = TABSQLITEDB.ime_properties.get(
        'multi_wildcard_char')
    if not multi_wildcard_char:
        multi_wildcard_char = u''
    if len(multi_wildcard_char) > 1:
        multi_wildcard_char = multi_wildcard_char[0]
    ENGINE.set_multi_wildcard_char(
        multi_wildcard_char, update_gsettings=False)

    ENGINE.set_pinyin_mode(False)
    ENGINE.set_suggestion_mode(False)

    page_up_keys_csv = TABSQLITEDB.ime_properties.get(
        'page_up_keys')
    if page_up_keys_csv:
        page_up_keys = [
            IBus.keyval_from_name(x)
            for x in page_up_keys_csv.split(',')]
    ENGINE._commit_key_names = [
        IBus.keyval_name(keyval) for keyval in commit_keys]
    ENGINE._page_down_key_names = [
        IBus.keyval_name(keyval) for keyval in page_down_keys]
    ENGINE._page_up_key_names = [
        IBus.keyval_name(keyval) for keyval in page_up_keys]
    user_keybindings={}
    ENGINE.set_keybindings(user_keybindings, update_gsettings=False)

    # Get more verbose output in the test log:
    ENGINE.set_debug_level(255)

def set_up(engine_name):
    '''
    Setup an ibus table engine

    :param engine_name: The name of the engine to setup
    :type engine_name: String
    :return: True if the engine could be setup successfully, False if not.
    :rtype: Boolean
    '''
    global ENGINE_PATCHER
    global ENGINE_SIMPLE_PATCHER
    global LOOKUP_TABLE_PATCHER
    global PROPERTY_PATCHER
    global PROP_LIST_PATCHER
    global IBUS_ENGINE
    global IBUS_ENGINE_SIMPLE
    global IBUS_LOOKUP_TABLE
    global IBUS_PROPERTY
    global IBUS_PROP_LIST
    global TABSQLITEDB
    global ENGINE
    ENGINE_PATCHER.start()
    ENGINE_SIMPLE_PATCHER.start()
    LOOKUP_TABLE_PATCHER.start()
    PROPERTY_PATCHER.start()
    PROP_LIST_PATCHER.start()
    assert IBus.Engine is not IBUS_ENGINE
    assert IBus.Engine is MockEngine
    assert IBus.EngineSimple is not IBUS_ENGINE_SIMPLE
    assert IBus.EngineSimple is MockEngine
    assert IBus.LookupTable is not IBUS_LOOKUP_TABLE
    assert IBus.LookupTable is MockLookupTable
    assert IBus.Property is not IBUS_PROPERTY
    assert IBus.Property is MockProperty
    assert IBus.PropList is not IBUS_PROP_LIST
    assert IBus.PropList is MockPropList
    # Reload the table module so that the patches
    # are applied to TabEngine:
    sys.path.insert(0, '../engine')
    importlib.reload(table)
    sys.path.pop(0)
    bus = IBus.Bus()
    db_dir = '/usr/share/ibus-table/tables'
    db_file = os.path.join(db_dir, engine_name + '.db')
    if not os.path.isfile(db_file):
        TABSQLITEDB = None
        ENGINE = None
        tear_down()
        return False
    TABSQLITEDB = tabsqlitedb.TabSqliteDb(
        filename=db_file, user_db=':memory:', unit_test=True)
    ENGINE = table.TabEngine(
        bus,
        '/com/redhat/IBus/engines/table/%s/engine/0' %engine_name,
        TABSQLITEDB,
        unit_test=True)
    backup_original_settings()
    set_default_settings()
    return True

def tear_down():
    global ENGINE_PATCHER
    global ENGINE_SIMPLE_PATCHER
    global LOOKUP_TABLE_PATCHER
    global PROPERTY_PATCHER
    global PROP_LIST_PATCHER
    global IBUS_ENGINE
    global IBUS_LOOKUP_TABLE
    global IBUS_PROPERTY
    global IBUS_PROP_LIST
    global TABSQLITEDB
    global ENGINE
    if ENGINE:
        restore_original_settings()
        TABSQLITEDB = None
        ENGINE = None
    # Remove the patches from the IBus stuff:
    ENGINE_PATCHER.stop()
    ENGINE_SIMPLE_PATCHER.stop()
    LOOKUP_TABLE_PATCHER.stop()
    PROPERTY_PATCHER.stop()
    PROP_LIST_PATCHER.stop()
    assert IBus.Engine is IBUS_ENGINE
    assert IBus.Engine is not MockEngine
    assert IBus.EngineSimple is IBUS_ENGINE_SIMPLE
    assert IBus.EngineSimple is not MockEngine
    assert IBus.LookupTable is IBUS_LOOKUP_TABLE
    assert IBus.LookupTable is not MockLookupTable
    assert IBus.Property is IBUS_PROPERTY
    assert IBus.Property is not MockProperty
    assert IBus.PropList is IBUS_PROP_LIST
    assert IBus.PropList is not MockPropList

class WubiJidian86TestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'wubi-jidian86'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工')

    def test_toggle_suggestion_mode_with_keybinding(self):
        if not ENGINE._ime_sg:
            self.skipTest("This engine does not have a suggestion mode.")
        self.assertEqual(ENGINE.get_suggestion_mode(), False)
        ENGINE._do_process_key_event(
            IBus.KEY_F6, 0,
            IBus.ModifierType.SUPER_MASK | IBus.ModifierType.MOD4_MASK)
        self.assertEqual(ENGINE.get_suggestion_mode(), True)
        ENGINE._do_process_key_event(
            IBus.KEY_F6, 0,
            IBus.ModifierType.SUPER_MASK | IBus.ModifierType.MOD4_MASK)
        self.assertEqual(ENGINE.get_suggestion_mode(), False)

    def test_toggle_input_mode_with_keybinding(self):
        self.assertEqual(ENGINE.get_input_mode(), 1)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        # This should have successfully switched, although there was
        # only a key release, no key press. Matching on modifiers keys
        # like Shift_L matches only on key release and checks whether
        # the previous key pressed was exactly the same key (To avoid
        # matching on something like “Shift_L” + “a”).  But when this
        # is very first key event after the startup of ibus-table, the
        # previous key is still empty. The it_util.HotKey class then
        # assumes that the previous key was the same automatically.
        self.assertEqual(ENGINE.get_input_mode(), 0)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Control_L, 0,
            IBus.ModifierType.CONTROL_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        # This should have failed to switch because the key before the
        # release of “Shift_L” was not a “Shift_L” key.
        self.assertEqual(ENGINE.get_input_mode(), 0)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        # This switch should succeed because the previous key was
        # also a “Shift_L” (also a key release, but this doesn’t matter
        # I don’t check for this case as it cannot happen in reality).
        self.assertEqual(ENGINE.get_input_mode(), 1)

    def test_switch_to_next_chinese_mode_with_keybinding(self):
        self.assertEqual(ENGINE.get_chinese_mode(), 2)
        # Now change with the keybinding:
        ENGINE._do_process_key_event(IBus.KEY_semicolon, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_chinese_mode(), 3)

    def test_toggle_onechar_mode_with_keybinding(self):
        self.assertEqual(ENGINE.get_onechar_mode(), False)
        ENGINE.set_onechar_mode(True, update_gsettings=False)
        self.assertEqual(ENGINE.get_onechar_mode(), True)
        ENGINE.set_onechar_mode(False, update_gsettings=False)
        self.assertEqual(ENGINE.get_onechar_mode(), False)
        # Now change with the keybinding:
        ENGINE._do_process_key_event(IBus.KEY_comma, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_onechar_mode(), True)
        ENGINE._do_process_key_event(IBus.KEY_comma, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_onechar_mode(), False)

    def test_toggle_autocommit_mode_with_keybinding(self):
        self.assertEqual(ENGINE.get_autocommit_mode(), False)
        ENGINE.set_autocommit_mode(True, update_gsettings=False)
        self.assertEqual(ENGINE.get_autocommit_mode(), True)
        ENGINE.set_autocommit_mode(False, update_gsettings=False)
        self.assertEqual(ENGINE.get_autocommit_mode(), False)
        # Now change with the keybinding:
        ENGINE._do_process_key_event(IBus.KEY_slash, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_autocommit_mode(), True)
        ENGINE._do_process_key_event(IBus.KEY_slash, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_autocommit_mode(), False)

    def test_change_letter_width(self):
        # The defaults come from the wubi-jidian86.txt source:
        # DEF_FULL_WIDTH_LETTER = FALSE
        self.assertEqual(ENGINE.get_letter_width(), [False, False])
        ENGINE.set_letter_width(mode=True, input_mode=0, update_gsettings=False)
        self.assertEqual(ENGINE.get_letter_width(), [True, False])
        ENGINE.set_letter_width(mode=True, input_mode=1, update_gsettings=False)
        self.assertEqual(ENGINE.get_letter_width(), [True, True])
        # Restore the default:
        ENGINE.set_letter_width(mode=False, input_mode=0, update_gsettings=False)
        ENGINE.set_letter_width(mode=False, input_mode=1, update_gsettings=False)
        self.assertEqual(ENGINE.get_letter_width(), [False, False])
        # Now change it for input mode 1 with the default keybinding:
        self.assertEqual(ENGINE.get_input_mode(), 1)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, IBus.ModifierType.SHIFT_MASK)
        self.assertEqual(ENGINE.get_letter_width(), [False, True])
        # Restore it for input mode 1 with the default keybinding:
        ENGINE._do_process_key_event(IBus.KEY_space, 0, IBus.ModifierType.SHIFT_MASK)
        self.assertEqual(ENGINE.get_letter_width(), [False, False])
        # Now change it for input mode 0 with the default keybinding:
        ENGINE.set_input_mode(0)
        self.assertEqual(ENGINE.get_input_mode(), 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, IBus.ModifierType.SHIFT_MASK)
        self.assertEqual(ENGINE.get_letter_width(), [True, False])
        # Restore it for input mode 0 with the default keybinding:
        ENGINE._do_process_key_event(IBus.KEY_space, 0, IBus.ModifierType.SHIFT_MASK)
        self.assertEqual(ENGINE.get_letter_width(), [False, False])

    def test_change_punctuation_width(self):
        # The defaults come from the wubi-jidian86.txt source:
        # DEF_FULL_WIDTH_PUNCT = TRUE
        self.assertEqual(ENGINE.get_punctuation_width(), [False, True])
        ENGINE.set_punctuation_width(mode=True, input_mode=0, update_gsettings=False)
        self.assertEqual(ENGINE.get_punctuation_width(), [True, True])
        ENGINE.set_punctuation_width(mode=False, input_mode=1, update_gsettings=False)
        self.assertEqual(ENGINE.get_punctuation_width(), [True, False])
        # Restore the default:
        ENGINE.set_punctuation_width(mode=False, input_mode=0, update_gsettings=False)
        ENGINE.set_punctuation_width(mode=False, input_mode=1, update_gsettings=False)
        self.assertEqual(ENGINE.get_punctuation_width(), [False, False])
        # Now change it for input mode 1 with the default keybinding:
        self.assertEqual(ENGINE.get_input_mode(), 1)
        ENGINE._do_process_key_event(IBus.KEY_period, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_punctuation_width(), [False, True])
        # Restore it for input mode 1 with the default keybinding:
        ENGINE._do_process_key_event(IBus.KEY_period, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_punctuation_width(), [False, False])
        # Now change it for input mode 0 with the default keybinding:
        ENGINE.set_input_mode(0)
        self.assertEqual(ENGINE.get_input_mode(), 0)
        ENGINE._do_process_key_event(IBus.KEY_period, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_punctuation_width(), [True, False])
        # Restore it for input mode 0 with the default keybinding:
        ENGINE._do_process_key_event(IBus.KEY_period, 0, IBus.ModifierType.CONTROL_MASK)
        self.assertEqual(ENGINE.get_punctuation_width(), [False, False])

    def test_next_and_previous_candidates_in_page(self):
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        print(ENGINE._lookup_table.mock_candidates)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['工  99454797 0',
                          '区 qi 1730000000 0',
                          '或 kg 1250000000 0',
                          '或 kgd 1250000000 0',
                          '其 dw 1150000000 0',
                          '其 dwu 1150000000 0',
                          '其他 dwb 685000000 0',
                          '世界 nlw 684000000 0',
                          '花 wx 598000000 0',
                          '花 wxb 598000000 0'])
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # Go one candidate down in the candidate list:
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '区')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # Go one candidate up in the candidate list:
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK
            | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # Go three candidates up in the candidate list
        # (should wrap around in the current page):
        #
        # 1
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK
            | IBus.ModifierType.RELEASE_MASK)
        # 2
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK
            | IBus.ModifierType.RELEASE_MASK)
        # 3
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Alt_L, 0,
            IBus.ModifierType.MOD1_MASK
            | IBus.ModifierType.CONTROL_MASK
            | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '世界')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '世界')

    def test_cancel_key_binding_changed(self):
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # This 'Insert' does not 'cancel' because the default key for
        # 'cancel' is 'Escape':
        ENGINE._do_process_key_event(IBus.KEY_Insert, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工')
        # Changing the key binding for 'cancel':
        ENGINE.set_keybindings({
            'cancel': ['Insert'],
            }, update_gsettings=False)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '工')
        # Now this 'Insert' should cancel, i.e. empty the preedit:
        ENGINE._do_process_key_event(IBus.KEY_Insert, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工')
        # And as the preedit is empty now, there is nothing to commit
        # and the 'space' key just adds a space:
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工 ')

    def test_pinyin_mode(self):
        # Pinyin mode is False by default:
        self.assertEqual(ENGINE.get_pinyin_mode(), False)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工')
        ENGINE.set_pinyin_mode(True)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '啊')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['啊 ↑5   kbsk 464000000 0',
                          '阿 ↑1   bskg 319000000 0',
                          '阿 ↑3   bskg 319000000 0',
                          '阿 ↑4   bskg 319000000 0',
                          '阿 ↑5   bskg 319000000 0',
                          '吖 ↑1   kuhh 9910000 0',
                          '腌 ↑1   edjn 4100000 0',
                          '锕 ↑1   qbsk 1690000 0',
                          '嗄 ↑2   kdht 1510000 0',
                          '錒 ↑1   qbsk 503000 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工啊')
        ENGINE.set_pinyin_mode(False)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工啊工')

    def test_pinyin_mode_chinese_mode(self):
        # Pinyin mode is False by default:
        self.assertEqual(ENGINE.get_pinyin_mode(), False)
        ENGINE.set_pinyin_mode(True)
        ENGINE.set_chinese_mode(0) # simplified only
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '吗')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['吗    kcg 959000000 0',
                          '码    dcg 274000000 0',
                          '马    cnng 236000000 0',
                          '玛    gcg 51300000 0',
                          '蚂    jcg 3110000 0',
                          '杩    scg 1280000 0',
                          '犸    qtcg 120000 0',
                          '溤    icy 38700 0',
                          '鰢    qocy 36500 0',
                          '鷌    wvgc 25500 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '吗')
        ENGINE.set_chinese_mode(1) # traditional only
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '嗎')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['嗎    kcy 148000000 0',
                          '馬    cghy 99400000 0',
                          '碼    dcy 38600000 0',
                          '瑪    gcy 15900000 0',
                          '鎷    qcy 1650000 0',
                          '螞    jcy 662000 0',
                          '榪    scy 142000 0',
                          '獁    qtcy 41200 0',
                          '溤    icy 38700 0',
                          '鰢    qocy 36500 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '吗嗎')
        ENGINE.set_chinese_mode(2) # simplified first
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '吗')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['吗    kcg 959000000 0',
                          '码    dcg 274000000 0',
                          '马    cnng 236000000 0',
                          '玛    gcg 51300000 0',
                          '蚂    jcg 3110000 0',
                          '杩    scg 1280000 0',
                          '犸    qtcg 120000 0',
                          '溤    icy 38700 0',
                          '鰢    qocy 36500 0',
                          '鷌    wvgc 25500 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '吗嗎吗')
        ENGINE.set_chinese_mode(3) # traditional first
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '嗎')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['嗎    kcy 148000000 0',
                          '馬    cghy 99400000 0',
                          '碼    dcy 38600000 0',
                          '瑪    gcy 15900000 0',
                          '鎷    qcy 1650000 0',
                          '螞    jcy 662000 0',
                          '榪    scy 142000 0',
                          '獁    qtcy 41200 0',
                          '溤    icy 38700 0',
                          '鰢    qocy 36500 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '吗嗎吗嗎')
        ENGINE.set_chinese_mode(4) # all characters
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '吗')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['吗    kcg 959000000 0',
                          '码    dcg 274000000 0',
                          '马    cnng 236000000 0',
                          '嗎    kcy 148000000 0',
                          '馬    cghy 99400000 0',
                          '玛    gcg 51300000 0',
                          '碼    dcy 38600000 0',
                          '瑪    gcy 15900000 0',
                          '蚂    jcg 3110000 0',
                          '鎷    qcy 1650000 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '吗嗎吗嗎吗')

    def test_suggestion_mode(self):
        if not ENGINE._ime_sg:
            self.skipTest("This engine does not have a suggestion mode.")
        # Suggestion mode is False by default:
        self.assertEqual(ENGINE.get_suggestion_mode(), False)
        self.assertEqual(ENGINE.get_pinyin_mode(), False)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工')
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])
        ENGINE.set_suggestion_mode(True)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['工作人员 673 0',
                          '工作会议 310 0',
                          '工作报告 267 0',
                          '工人阶级 146 0',
                          '工作重点 78 0',
                          '工作小组 73 0',
                          '工业企业 71 0',
                          '工业大学 69 0',
                          '工作单位 61 0',
                          '工业生产 58 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工作人员')
        ENGINE.set_pinyin_mode(True)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '啊')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工作人员啊')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['啊呀 145 0',
                          '啊哈 103 0',
                          '啊哟 23 0',
                          '啊唷 7 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工作人员啊呀')
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_i, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '爱')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工作人员啊呀爱')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['爱因斯坦 1109 0',
                          '爱情故事 519 0',
                          '爱国主义 191 0',
                          '爱尔兰语 91 0',
                          '爱好和平 62 0',
                          '爱情小说 58 0',
                          '爱不释手 39 0',
                          '爱国热情 35 0',
                          '爱莫能助 34 0',
                          '爱理不理 32 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工工作人员啊呀爱因斯坦')

    def test_commit_to_preedit_switching_to_pinyin_defining_a_phrase(self):
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        # commit to preëdit needs a press and release of either
        # the left or the right shift key:
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_d, 0, 0)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # Move left two characters in the preëdit:
        ENGINE._do_process_key_event(IBus.KEY_Left, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Left, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        self.assertEqual(ENGINE._chars_valid, '')
        self.assertEqual(ENGINE._chars_invalid, '')
        # Switch to pinyin mode by pressing and releasing the right
        # shift key:
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.get_pinyin_mode(), True)
        self.assertEqual(ENGINE.mock_preedit_text, '工了以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_n, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_i, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '')
        self.assertEqual(ENGINE.mock_preedit_text, '工了你以在')
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_numbersign, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_L, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        # Move right two characters in the preëdit
        # (triggers a commit to preëdit):
        ENGINE._do_process_key_event(IBus.KEY_Right, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Right, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        self.assertEqual(ENGINE.mock_committed_text, '')
        self.assertEqual(ENGINE.mock_auxiliary_text, 'd dhf dhfd\t#: abwd')
        # commit the preëdit:
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, '工了你好以在')
        # Switch out of pinyin mode:
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK)
        ENGINE._do_process_key_event(
            IBus.KEY_Shift_R, 0,
            IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)
        self.assertEqual(ENGINE.get_pinyin_mode(), False)
        # “abwd” shown on the right of the auxiliary text above shows the
        # newly defined shortcut for this phrase. Let’s  try to type
        # the same phrase again using the new shortcut:
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工')
        ENGINE._do_process_key_event(IBus.KEY_b, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '节')
        ENGINE._do_process_key_event(IBus.KEY_w, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        ENGINE._do_process_key_event(IBus.KEY_d, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '工了你好以在')
        # commit the preëdit:
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '工了你好以在工了你好以在')

    def test_chinese_mode(self):
        ENGINE.set_chinese_mode(
            mode=0, update_gsettings=False) # show simplified Chinese only
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        ENGINE._do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(
            mode=1, update_gsettings=False) # show traditional Chinese only
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        ENGINE._do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(
            mode=2, update_gsettings=False) # show simplified Chinese first
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        ENGINE._do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(
            mode=3, update_gsettings=False) # show traditional Chinese first
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        ENGINE._do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])
        ENGINE.set_chinese_mode(
            mode=4, update_gsettings=False) # show all characters
        ENGINE._do_process_key_event(IBus.KEY_c, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        ENGINE._do_process_key_event(IBus.KEY_BackSpace, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates, [])

class Stroke5TestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'stroke5'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE._do_process_key_event(IBus.KEY_comma, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_slash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_n, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '的')

class TelexTestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'telex'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_telex(self):
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'o')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'o')
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_f, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'oò')
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ô')
        self.assertEqual(ENGINE.mock_committed_text, 'oò')
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'oòô')
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ô')
        self.assertEqual(ENGINE.mock_committed_text, 'oòô')
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'oòôô')
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_o, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ô')
        self.assertEqual(ENGINE.mock_committed_text, 'oòôô')
        ENGINE._do_process_key_event(IBus.KEY_j, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'oòôôộ')

class TranslitTestCase(unittest.TestCase):
    def setUp(self):
        engine_name ='translit'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_sh_multiple_match(self):
        ENGINE._do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        ENGINE._do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ш')
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ш')
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщ')
        self.assertEqual(ENGINE.mock_preedit_text, '')
        ENGINE._do_process_key_event(IBus.KEY_s, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщ')
        self.assertEqual(ENGINE.mock_preedit_text, 'с')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'шщс ')

    def test_sh_multiple_match_slavic(self):
        ENGINE._do_process_key_event(IBus.KEY_scaron, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'щ')
        ENGINE._do_process_key_event(IBus.KEY_scaron, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'ш')
        self.assertEqual(ENGINE.mock_committed_text, 'щ')
        ENGINE._do_process_key_event(IBus.KEY_ccaron, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'щщ')

class Cangjie5TestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'cangjie5'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '日')

    def test_type_one_char_and_check_auxiliary(self):
        ENGINE._do_process_key_event(IBus.KEY_d, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '木')
        self.assertEqual(ENGINE._lookup_table.mock_candidates[8],
                         '林 木 1000 0')
        ENGINE._do_process_key_event(IBus.KEY_v, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_i, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_i, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '機')
        self.assertEqual(ENGINE.mock_auxiliary_text, '木女戈戈 (1 / 1)')
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['機  1000 0'])
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '機')

class IpaXSampaTestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'ipa-x-sampa'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE._do_process_key_event(IBus.KEY_at, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ə ')

    def test_single_char_commit_with_f3(self):
        ENGINE._do_process_key_event(IBus.KEY_at, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['ə  0 0', 'ɘ \\ 0 0', 'ɚ ` 0 0'])
        ENGINE._do_process_key_event(IBus.KEY_F3, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'ɚ')

class LatexTestCase(unittest.TestCase):
    def setUp(self):
        engine_name = 'latex'
        if not set_up(engine_name):
            self.skipTest('Could not setup “%s”, skipping test.' % engine_name)

    def tearDown(self):
        tear_down()

    def test_dummy(self):
        self.assertEqual(True, True)

    def test_single_char_commit_with_space(self):
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_l, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_p, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'α')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'α')

    def test_single_char_commit_with_space_fraktur(self):
        # needs ibus-table-others-1.3.10 which adds
        # most of Unicode 9.0 block Mathematical Alphanumeric Symbols
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_m, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_t, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_f, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_r, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_k, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_F, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, '𝔉')

    def test_toggle_input_mode_on_off(self):
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_l, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_p, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, 'α')
        self.assertEqual(ENGINE.mock_committed_text, '')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'α')
        ENGINE._do_process_key_event(IBus.KEY_Shift_L, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Shift_L, 0, IBus.ModifierType.RELEASE_MASK)
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_l, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_p, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_h, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_a, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'α\\alpha')
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_preedit_text, '')
        self.assertEqual(ENGINE.mock_committed_text, 'α\\alpha ')

    def test_single_char_commit_with_f3(self):
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_b, 0, 0)
        # Lookup table shows only the first page, subsequent
        # pages are added on demand as a speed optimization:
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
                         ['¯ ar 0 0',
                          '⊥ ot 0 0',
                          'β eta 0 0',
                          'ℶ eth 0 0',
                          '⋂ igcap 0 0',
                          '⋃ igcup 0 0',
                          '⋁ igvee 0 0',
                          '⋈ owtie 0 0',
                          '⊡ oxdot 0 0'])
        ENGINE._do_process_key_event(IBus.KEY_F3, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β')
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Page_Down, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        self.assertEqual(ENGINE._lookup_table.get_cursor_pos(), 9)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        self.assertEqual(ENGINE._lookup_table.get_cursor_pos(), 15)
        self.assertEqual(ENGINE._lookup_table.mock_candidates[0:18],
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
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β⊞')
        ENGINE._do_process_key_event(IBus.KEY_backslash, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_b, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Page_Down, 0, 0)
        self.assertEqual(ENGINE._lookup_table.mock_candidates,
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
        self.assertEqual(ENGINE._lookup_table.get_cursor_pos(), 9)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        ENGINE._do_process_key_event(IBus.KEY_Down, 0, 0)
        self.assertEqual(ENGINE._lookup_table.get_cursor_pos(), 15)
        ENGINE._do_process_key_event(IBus.KEY_space, 0, 0)
        self.assertEqual(ENGINE.mock_committed_text, 'β⊞≬')

if __name__ == '__main__':
    LOG_HANDLER = logging.StreamHandler(stream=sys.stderr)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(LOG_HANDLER)
    unittest.main()
