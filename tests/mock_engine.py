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

from gi import require_version
require_version('IBus', '1.0')
from gi.repository import IBus

class MockEngine:
    def __init__(self, engine_name = '', connection = None, object_path = ''):
        self.mock_auxiliary_text = ''
        self.mock_preedit_text = ''
        self.mock_preedit_text_cursor_pos = 0
        self.mock_preedit_text_visible = True
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

    def update_auxiliary_text(self, text, visible):
        self.mock_auxiliary_text = text.text

    def hide_auxiliary_text(self):
        pass

    def hide_preedit_text(self):
        pass

    def commit_text(self, text):
        self.mock_committed_text = (
            self.mock_committed_text[
                :self.mock_committed_text_cursor_pos]
            + text.text
            + self.mock_committed_text[
                self.mock_committed_text_cursor_pos:])
        self.mock_committed_text_cursor_pos += len(text.text)

    def forward_key_event(self, val, code, state):
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

    def update_lookup_table(self, table, visible):
        pass

    def update_preedit_text(self, text, cursor_pos, visible):
        self.mock_preedit_text = text.get_text()
        self.mock_preedit_text_cursor_pos = cursor_pos
        self.mock_preedit_text_visible = visible

    def register_properties(self, property_list):
        pass

    def update_property(self, property):
        pass

    def hide_lookup_table(self):
        pass

    def connect(self, *args):
        pass

class MockLookupTable:
    def __init__(self, page_size = 9, cursor_pos = 0, cursor_visible = False, round = True):
        self.clear()
        self.mock_page_size = page_size
        self.mock_cursor_pos = cursor_pos
        self.mock_cursor_visible = cursor_visible
        self.cursor_visible = cursor_visible
        self.mock_round = round
        self.mock_candidates = []
        self.mock_labels = []
        self.mock_page_number = 0

    def clear(self):
        self.mock_candidates = []
        self.mock_cursor_pos = 0

    def set_page_size(self, size):
        self.mock_page_size = size

    def get_page_size(self):
        return self.mock_page_size

    def set_round(self, round):
        self.mock_round = round

    def set_cursor_pos(self, pos):
        self.mock_cursor_pos = pos

    def get_cursor_pos(self):
        return self.mock_cursor_pos

    def get_cursor_in_page(self):
        return (self.mock_cursor_pos
                - self.mock_page_size * self.mock_page_number)

    def set_cursor_visible(self, visible):
        self.mock_cursor_visible = visible
        self.cursor_visible = visible

    def cursor_down(self):
        if len(self.mock_candidates):
            self.mock_cursor_pos += 1
            self.mock_cursor_pos %= len(self.mock_candidates)

    def cursor_up(self):
        if len(self.mock_candidates):
            if self.mock_cursor_pos > 0:
                self.mock_cursor_pos -= 1
            else:
                self.mock_cursor_pos = len(self.mock_candidates) - 1

    def page_down(self):
        if len(self.mock_candidates):
            self.mock_page_number += 1
            self.mock_cursor_pos += self.mock_page_size

    def page_up(self):
        if len(self.mock_candidates):
            if self.mock_page_number > 0:
                self.mock_page_number -= 1
                self.mock_cursor_pos -= self.mock_page_size

    def set_orientation(self, orientation):
        self.mock_orientation = orientation

    def get_number_of_candidates(self):
        return len(self.mock_candidates)

    def append_candidate(self, candidate):
        self.mock_candidates.append(candidate.get_text())

    def get_candidate(self, index):
        return self.mock_candidates[index]

    def get_number_of_candidates(self):
        return len(self.mock_candidates)

    def append_label(self, label):
        self.mock_labels.append(label.get_text())

class MockPropList:
    def __init__(self, *args, **kwargs):
        self._mock_proplist = []

    def append(self, property):
        self._mock_proplist.append(property)

    def get(self, index):
        if index >= 0 and index < len(self._mock_proplist):
            return self._mock_proplist[index]
        else:
            return None

    def update_property(self, property):
        pass

class MockProperty:
    def __init__(self,
                 key='',
                 prop_type=IBus.PropType.RADIO,
                 label=IBus.Text.new_from_string(''),
                 symbol=IBus.Text.new_from_string(''),
                 icon='',
                 tooltip=IBus.Text.new_from_string(''),
                 sensitive=True,
                 visible=True,
                 state=IBus.PropState.UNCHECKED,
                 sub_props=None):
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

    def set_label(self, ibus_text):
        self.mock_property_label = ibus_text.get_text()

    def set_symbol(self, ibus_text):
        self.mock_property_symbol = ibus_text.get_text()

    def set_tooltip(self, ibus_text):
        self.mock_property_tooltip = ibus_text.get_text()

    def set_icon(self, icon_path):
        self.mock_property_icon = icon_path

    def set_sensitive(self, sensitive):
        self.mock_property_sensitive = sensitive

    def set_visible(self, visible):
        self.mock_property_visible = visible

    def set_state(self, state):
        self.mock_property_state = state

    def set_sub_props(self, proplist):
        self.mock_property_sub_props = proplist

    def get_key(self):
        return self.mock_property_key
