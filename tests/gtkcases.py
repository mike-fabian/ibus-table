#!/usr/bin/python3

# 'init' has one array which is [keysym, keycode, modifier] and to be run
# before the main tests. E.g.
# Ctrl-space to enable Hiragana mode
#
# 'tests' cases are the main test cases.
# 'preedit' case runs to create a preedit text.
# 'lookup' case runs to update a lookup table.
# 'commit' case runs to commit the preedit text.
# 'result' case is the expected output.
# 'preedit', 'lookup', 'commit' can choose the type of either 'string' or 'keys'
# 'string' type is a string sequence which does not need modifiers

from gi import require_version as gi_require_version # type: ignore
gi_require_version('IBus', '1.0')
from gi.repository import IBus # type: ignore

TestCases = {
    #'init': [IBus.KEY_j, 0, IBus.ModifierType.CONTROL_MASK],
    'tests': [
                {'preedit': {'string': 'a'},
                 'lookup': {'keys': [[IBus.KEY_Down, 0, 0]]},
                 'commit': {'keys': [[IBus.KEY_space, 0, 0]]},
                 'result': {'string': '区'}
                },
                {'preedit': {'string': 'ijgl'},
                 'commit': {'keys': [[IBus.KEY_space, 0, 0]]},
                 'result': {'string': '漫画'}
                },
                {'preedit': {'string': 'wgl'},
                 'lookup': {'keys': [[IBus.KEY_Down, 0, 0]]},
                 'commit': {'keys': [[IBus.KEY_space, 0, 0]]},
                 'result': {'string': '全国'}
                },
            ]
}
