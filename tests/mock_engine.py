# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2018-2020 Mike FABIAN <mfabian@redhat.com>
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
Define some mock classes for the unittests.
'''

from typing import Any
from typing import List
from typing import Optional
# pylint: disable=wrong-import-position
from gi import require_version # type: ignore
require_version('IBus', '1.0')
from gi.repository import IBus # type: ignore
# pylint: enable=wrong-import-position

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
class MockEngine:
    '''Mock engine class to simulate IBus.Engine for testing'''
    props = None
    def __init__(
            self,
            engine_name: str = '',
            connection: Any = None,
            object_path: str = ''):
        self.mock_engine_name = engine_name
        self.mock_connection = connection
        self.mock_object_path = object_path
        self.mock_auxiliary_text = ''
        self.mock_preedit_text = ''
        self.mock_preedit_text_cursor_pos = 0
        self.mock_preedit_text_visible = True
        self.mock_preedit_focus_mode = IBus.PreeditFocusMode.COMMIT
        self.mock_committed_text = ''
        self.mock_committed_text_cursor_pos = 0
        self.client_capabilities = (
            IBus.Capabilite.PREEDIT_TEXT
            | IBus.Capabilite.AUXILIARY_TEXT
            | IBus.Capabilite.LOOKUP_TABLE
            | IBus.Capabilite.FOCUS
            | IBus.Capabilite.PROPERTY)
        # There are lots of weird problems with surrounding text
        # which makes this hard to test. Therefore this mock
        # engine does not try to support surrounding text, i.e.
        # we omit “| IBus.Capabilite.SURROUNDING_TEXT” here.

    def update_auxiliary_text(self, text: IBus.Text, _visible: bool) -> None:
        self.mock_auxiliary_text = text.text

    def hide_auxiliary_text(self) -> None:
        pass

    def hide_preedit_text(self) -> None:
        pass

    def commit_text(self, text: IBus.Text) -> None:
        self.mock_committed_text = (
            self.mock_committed_text[
                :self.mock_committed_text_cursor_pos]
            + text.text
            + self.mock_committed_text[
                self.mock_committed_text_cursor_pos:])
        self.mock_committed_text_cursor_pos += len(text.text)

    def forward_key_event(self, val: int, _code: int, _state: int) -> None:
        if (val == IBus.KEY_Left
            and self.mock_committed_text_cursor_pos > 0):
            self.mock_committed_text_cursor_pos -= 1
            return
        unicode = IBus.keyval_to_unicode(val)
        if unicode:
            self.mock_committed_text = (
            self.mock_committed_text[
                :self.mock_committed_text_cursor_pos]
            + unicode
            + self.mock_committed_text[
                self.mock_committed_text_cursor_pos:])
            self.mock_committed_text_cursor_pos += len(unicode)

    def update_lookup_table(
            self, table: IBus.LookupTable, visible: bool) -> None:
        pass

    def update_preedit_text(
            self, text: IBus.Text, cursor_pos: int, visible: bool) -> None:
        self.mock_preedit_text = text.get_text()
        self.mock_preedit_text_cursor_pos = cursor_pos
        self.mock_preedit_text_visible = visible

    def update_preedit_text_with_mode(
            self,
            text: IBus.Text,
            cursor_pos: int,
            visible: bool,
            focus_mode: IBus.PreeditFocusMode) -> None:
        self.mock_preedit_focus_mode = focus_mode
        self.update_preedit_text(text, cursor_pos, visible)

    def register_properties(self, property_list: List[IBus.Property]) -> None:
        pass

    def update_property(self, _property: IBus.Property) -> None:
        pass

    def hide_lookup_table(self) -> None:
        pass

    def connect(self, signal: str, callback_function: Any) -> None:
        pass

    def add_table_by_locale(self, locale: str) -> None:
        pass

class MockLookupTable:
    def __init__(
            self,
            page_size: int = 9,
            cursor_pos: int = 0,
            cursor_visible: bool = False,
            wrap_around: bool = True):
        self.clear()
        self.mock_page_size = page_size
        self.mock_cursor_pos = cursor_pos
        self.mock_cursor_visible = cursor_visible
        self.cursor_visible = cursor_visible
        self.mock_wrap_around = wrap_around
        self.mock_candidates: List[str] = []
        self.mock_labels: List[str]  = []
        self.mock_page_number = 0
        self.mock_orientation = 0

    def clear(self) -> None:
        self.mock_candidates = []
        self.mock_cursor_pos = 0

    def set_page_size(self, size: int) -> None:
        self.mock_page_size = size

    def get_page_size(self) -> int:
        return self.mock_page_size

    def set_round(self, wrap_around: bool) -> None:
        self.mock_wrap_around = wrap_around

    def set_cursor_pos(self, pos: int) -> None:
        self.mock_cursor_pos = pos

    def get_cursor_pos(self) -> int:
        return self.mock_cursor_pos

    def get_cursor_in_page(self) -> int:
        return (self.mock_cursor_pos
                - self.mock_page_size * self.mock_page_number)

    def set_cursor_visible(self, visible: bool) -> None:
        self.mock_cursor_visible = visible
        self.cursor_visible = visible

    def cursor_down(self) -> None:
        if self.mock_candidates:
            self.mock_cursor_pos += 1
            self.mock_cursor_pos %= len(self.mock_candidates)

    def cursor_up(self) -> None:
        if self.mock_candidates:
            if self.mock_cursor_pos > 0:
                self.mock_cursor_pos -= 1
            else:
                self.mock_cursor_pos = len(self.mock_candidates) - 1

    def page_down(self) -> None:
        if self.mock_candidates:
            self.mock_page_number += 1
            self.mock_cursor_pos += self.mock_page_size

    def page_up(self) -> None:
        if self.mock_candidates:
            if self.mock_page_number > 0:
                self.mock_page_number -= 1
                self.mock_cursor_pos -= self.mock_page_size

    def set_orientation(self, orientation: int) -> None:
        self.mock_orientation = orientation

    def get_number_of_candidates(self) -> int:
        return len(self.mock_candidates)

    def append_candidate(self, candidate: IBus.Text) -> None:
        self.mock_candidates.append(candidate.get_text())

    def get_candidate(self, index: int) -> str:
        return self.mock_candidates[index]

    def append_label(self, label: IBus.Text) -> None:
        self.mock_labels.append(label.get_text())

class MockPropList:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._mock_proplist: List[IBus.Property] = []

    def append(self, new_property: IBus.Property) ->  None:
        self._mock_proplist.append(new_property)

    def get(self, index: int) -> Optional[IBus.Property]:
        if 0 <= index < len(self._mock_proplist):
            return self._mock_proplist[index]
        return None

    def update_property(self, _property: IBus.Property) -> None:
        pass

class MockProperty:
    def __init__(self,
                 key: str = '',
                 prop_type: IBus.PropType = IBus.PropType.RADIO,
                 label: IBus.Text = IBus.Text.new_from_string(''),
                 symbol: IBus.Text = IBus.Text.new_from_string(''),
                 icon: str = '',
                 tooltip: IBus.Text = IBus.Text.new_from_string(''),
                 sensitive: bool = True,
                 visible: bool = True,
                 state: IBus.PropState = IBus.PropState.UNCHECKED,
                 sub_props: Optional[List[IBus.Property]] = None) -> None:
        self.mock_property_key = key
        self.mock_property_prop_type = prop_type
        self.mock_property_label = label.get_text()
        self.mock_property_symbol = symbol.get_text()
        self.mock_property_icon = icon
        self.mock_property_tooltip = tooltip.get_text()
        self.mock_property_sensitive = sensitive
        self.mock_property_visible = visible
        self.mock_property_state = state
        self.mock_property_sub_props = sub_props

    def set_label(self, ibus_text: IBus.Text) -> None:
        self.mock_property_label = ibus_text.get_text()

    def set_symbol(self, ibus_text: IBus.Text) -> None:
        self.mock_property_symbol = ibus_text.get_text()

    def set_tooltip(self, ibus_text: IBus.Text) -> None:
        self.mock_property_tooltip = ibus_text.get_text()

    def set_icon(self, icon_path: str) -> None:
        self.mock_property_icon = icon_path

    def set_sensitive(self, sensitive: bool) -> None:
        self.mock_property_sensitive = sensitive

    def set_visible(self, visible: bool) -> None:
        self.mock_property_visible = visible

    def set_state(self, state: IBus.PropState) -> None:
        self.mock_property_state = state

    def set_sub_props(self, proplist: List[IBus.Property]) -> None:
        self.mock_property_sub_props = proplist

    def get_key(self) -> str:
        return self.mock_property_key
