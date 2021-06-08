#!/usr/bin/python3
# vim:fileencoding=utf-8:sw=4:et

# generate-chinese-variants
#
# Copyright (c) 2013-2018 Mike FABIAN <mfabian@redhat.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any
import re
import logging
import sys

# Unihan_Variants.txt contains the following 2 lines:
#
# U+50DE  kSimplifiedVariant      U+4F2A
# U+50DE  kTraditionalVariant     U+507D U+50DE
#
# This seems to be currently the only case in Unihan_Variants.txt where
# a character which has entries for kTraditionalVariant and
# the same character is listed again among the traditional variants
# is *not* simplified Chinese.
#
# U+50DE 僞 is traditional Chinese.
# U+507D 偽 is also traditional Chinese.
# U+4F2A 伪 is simplified Chinese
#
# This does not cause a problem with the current parsing code
# of Unihan_Variants.txt because the line
#
# U+50DE  kSimplifiedVariant      U+4F2A
#
# is read first and thus the character is already inserted in the
# “VARIANTS_TABLE_ORIG” dictionary as traditional Chinese, which is correct.
# If a character is already in the dictionary and more lines for the
# same character are read from Unihan_Variants.txt, these extra lines
# are ignored.
#
# But maybe for some corner cases more tweaking of the code is
# necessary. One can also add overrides manually to the
# initial content of “VARIANTS_TABLE_ORIG”.

VARIANTS_TABLE_ORIG = {
    # Meaning of the bits in the values:
    # 1 = 1 << 0       simplified Chinese
    # 2 = 1 << 1       traditional Chinese
    # 3 = (1 | 1 << 1) used both in simplified *and* traditional Chinese
    # 4 = 1 << 2       mixture of simplified and traditional Chinese
    #
    # overrides can be added manually here. For example the following
    # line marks the 〇 character as used in both
    # simplified and traditional Chinese:
    u'〇': 3 # simplified *and* traditional Chinese
    }

# keep the lines from Unihan_Variants.txt which were used for debugging
VARIANTS_TABLE_ORIG_UNIHAN_VARIANTS_ENTRY_USED = {}

def read_unihan_variants(unihan_variants_file) -> None:
    '''
    Read the Unihan_Variants.txt file downloaded  from Unicode.org.
    '''
    for line in unihan_variants_file:
        line = line.strip()
        if not re.match('^#', line):
            if re.search('(kTraditionalVariant|kSimplifiedVariant)', line):
                match = re.match(r'^U\+([0-9A-F]{4,5})', line)
                if match:
                    char = chr(int(match.group(1), 16))
                    category = 0 # should never  stay at this value
                    if re.match(re.escape(match.group(0))
                                + r'.*'
                                + re.escape(match.group(0)), line):
                        # is both simplified and traditional
                        category = 1 | 1 << 1
                    elif re.search('kTraditionalVariant', line):
                        category = 1 # simplified only
                    elif re.search('kSimplifiedVariant', line):
                        category = 1 << 1 # traditional only
                    logging.debug(
                        'char=%s category=%d line=%s',
                        char, category, line)
                    if not char in VARIANTS_TABLE_ORIG:
                        VARIANTS_TABLE_ORIG[char] = category
                    if (not char
                            in VARIANTS_TABLE_ORIG_UNIHAN_VARIANTS_ENTRY_USED):
                        VARIANTS_TABLE_ORIG_UNIHAN_VARIANTS_ENTRY_USED[
                            char] = line

def detect_chinese_category_old(phrase: str) -> int:
    '''
    Old function using encoding conversion to guess whether
    a text is simplified Chinese, traditional Chinese, both,
    or unknown. Does not work well, is included here for reference
    and for comparing with the results of the new, improved function
    using the data from the Unihan database.
    '''
    # this is the bitmask we will use,
    # from low to high, 1st bit is simplified Chinese,
    # 2nd bit is traditional Chinese,
    # 3rd bit means out of gbk
    category = 0
    # make sure that we got a unicode string
    tmp_phrase = ''.join(re.findall(u'['
                                    + u'\u4E00-\u9FCB'
                                    + u'\u3400-\u4DB5'
                                    + u'\uF900-\uFaFF'
                                    + u'\U00020000-\U0002A6D6'
                                    + u'\U0002A700-\U0002B734'
                                    + u'\U0002B740-\U0002B81D'
                                    + u'\U0002F800-\U0002FA1D'
                                    + u']+',
                                    phrase))
    # first whether in gb2312
    try:
        tmp_phrase.encode('gb2312')
        category |= 1
    except:
        if u'〇' in tmp_phrase:
            # we add '〇' into SC as well
            category |= 1
    # second check big5-hkscs
    try:
        tmp_phrase.encode('big5hkscs')
        category |= 1 << 1
    except:
        # then check whether in gbk,
        if category & 1:
            # already know in SC
            pass
        else:
            # need to check
            try:
                tmp_phrase.encode('gbk')
                category |= 1
            except:
                # not in gbk
                pass
    # then set for 3rd bit, if not in SC and TC
    if not category & (1 | 1 << 1):
        category |= (1 << 2)
    return category

def write_variants_script(script_file) -> None:
    '''
    Write the generated Python script.
    '''
    script_file.write('''#!/usr/bin/python
# vim:fileencoding=utf-8:sw=4:et

# auto-generated by “generate-chinese-variants.py”, do not edit here!
#
# Copyright (c) 2013 Mike FABIAN <mfabian@redhat.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
''')

    script_file.write('''
import sys
''')

    script_file.write('''
VARIANTS_TABLE = {
    # Meaning of the bits in the values:
    # 1 = 1 << 0       simplified Chinese
    # 2 = 1 << 1       traditional Chinese
    # 3 = (1 | 1 << 1) used both in simplified *and* traditional Chinese
    # 4 = 1 << 2       mixture of simplified and traditional Chinese
''')

    for phrase in sorted(VARIANTS_TABLE_ORIG):
        script_file.write(
            "    u'" + phrase + "': "
            + "%s" %VARIANTS_TABLE_ORIG[phrase] + ",\n")

    script_file.write('''    }
''')

    script_file.write('''
def detect_chinese_category(phrase):
    \'\'\'
    New function using Unihan data to guess whether a text is
    simplified Chinese, traditional Chinese, both, or something rare
    like a mixture of exclusively simplified with exclusively traditional
    characters.

    Meaning of the bits in the category value returned by this function:
    1 = 1 << 0       simplified Chinese
    2 = 1 << 1       traditional Chinese
    3 = (1 | 1 << 1) used both in simplified *and* traditional Chinese
    4 = 1 << 2       mixture of simplified and traditional Chinese
    \'\'\'
    # make sure that we got a unicode string
    if phrase in VARIANTS_TABLE:
        # the complete phrase is in VARIANTS_TABLE, just return the
        # value found:
        return VARIANTS_TABLE[phrase]
    category = 0xFF
    for char in phrase:
        if char in VARIANTS_TABLE:
            category &= VARIANTS_TABLE[char]
        else:
            # If it is not listed in VARIANTS_TABLE, assume it is
            # both simplified and traditional Chinese.
            # It could be something non-Chinese as well then, but
            # if it is non-Chinese, it should also be allowed to
            # occur in any Chinese text and thus classified as
            # both simplified *and* traditional Chinese (the emoji
            # table for example uses many non-Chinese characters)
            category &= (1 | 1 << 1)
    if category == 0:
        # If category is 0 after binary & of the categories of all the
        # characters in the phrase, it means that the phrase contained
        # exclusively simplified *and* exclusively traditional
        # characters at the same time.  For example if the phrase is
        # “乌烏” then “乌” gets category 1 (simplified Chinese)
        # and “烏” gets category 2 (traditional Chinese), the result
        # of the binary & is thus 0. In that case, classify it as
        # category 4 which is for weird, excentric, rare stuff. If the
        # user selects one of the modes “all characters but
        # simplified Chinese first” or “all characters but
        # traditional Chinese first”, phrases with category 4 will be
        # shown but filtered to be shown only at the end of the
        # candidate list.
        category = 1 << 2
    return category
''')

TEST_DATA = {
    # Meaning of the bits in the values:
    # 1 = 1 << 0       simplified Chinese
    # 2 = 1 << 1       traditional Chinese
    # 3 = (1 | 1 << 1) used both in simplified *and* traditional Chinese
    # 4 = 1 << 2       mixture of simplified and traditional Chinese
    u'乌': 1,
    u'烏': 2,
    u'晞': 3,
    u'䖷': 3,
    u'乌烏': 4,
    u'a☺α乌': 1,
    u'a☺α烏': 2,
    u'台': 3,
    u'同': 3,
    # Characters below this comments probably have buggy entries
    # in Unihan_Variants.txt:
    u'覆': 3, # U+8986
    u'表': 3, # U+8868
    u'杰': 3, # U+6770
    u'面': 3, # U+9762
    u'系': 3, # U+7CFB
    u'乾': 3, # U+4E7E
    u'著': 3, # U+8457 Patch by Heiher <r@hev.cc>
    u'只': 3, # U+53EA, see: https://github.com/kaio/ibus-table/issues/74
    }

def test_detection(generated_script) -> int:
    '''
    Test whether the generated script does the detection correctly.

    Returns the number of errors found.
    '''
    logging.info('Testing detection ...')
    error_count = 0
    for phrase in TEST_DATA:
        if (generated_script.detect_chinese_category(phrase)
                != TEST_DATA[phrase]):
            print('phrase', phrase, repr(phrase),
                  'detected as',
                  generated_script.detect_chinese_category(phrase),
                  'should have been', TEST_DATA[phrase],
                  'FAIL.')
            error_count += 1
        else:
            logging.info('phrase=%s %s detected as %d PASS.',
                         phrase,
                         repr(phrase),
                         TEST_DATA[phrase])
    return error_count

def compare_old_new_detection(phrase, generated_script) -> None:
    '''
    Only for debugging.

    Compares results of the Chinese category detection using the
    old and the new function.
    '''
    if (detect_chinese_category_old(phrase)
            != generated_script.detect_chinese_category(phrase)):
        logging.debug(
            '%s %s old=%d new=%d',
            phrase.encode('utf-8'),
            repr(phrase),
            detect_chinese_category_old(phrase),
            generated_script.detect_chinese_category(phrase))
        if phrase in VARIANTS_TABLE_ORIG_UNIHAN_VARIANTS_ENTRY_USED:
            logging.debug(
                VARIANTS_TABLE_ORIG_UNIHAN_VARIANTS_ENTRY_USED[phrase])

def parse_args() -> Any:
    '''Parse the command line arguments'''
    import argparse
    parser = argparse.ArgumentParser(
        description=(
            'Generate a script containing a table and a function '
            + 'to check whether a string of Chinese characters '
            + 'is simplified or traditional'))
    parser.add_argument('-i', '--inputfilename',
                        nargs='?',
                        type=str,
                        default='./Unihan_Variants.txt',
                        help='input file, default is ./Unihan_Variants.txt')
    parser.add_argument('-o', '--outputfilename',
                        nargs='?',
                        type=str,
                        default='./chinese_variants.py',
                        help='output file, default is ./chinese_variants.py')
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='print debugging output')
    return parser.parse_args()

def main() -> None:
    '''Main program'''
    args = parse_args()
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
    with open(args.inputfilename, 'r') as inputfile:
        logging.info("input file=%s", inputfile)
        read_unihan_variants(inputfile)
    with open(args.outputfilename, 'w') as outputfile:
        logging.info("output file=%s", outputfile)
        write_variants_script(outputfile)

    import imp
    generated_script = imp.load_source('dummy', args.outputfilename)

    logging.info('Testing detection ...')
    error_count = test_detection(generated_script)
    if error_count:
        logging.info('FAIL: %s tests failed, exiting ...', error_count)
        exit(1)
    else:
        logging.info('PASS: All tests passed.')

    for phrase in generated_script.VARIANTS_TABLE: # type: ignore
        compare_old_new_detection(phrase, generated_script)

if __name__ == '__main__':
    main()
