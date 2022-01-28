# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2022 Mike FABIAN <mfabian@redhat.com>
# Copyright (c) 2019      Peng Wu <alexepico@gmail.com>
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
Module for ibus-table to access the sqlite3 databases
'''
from typing import List
from typing import Tuple
from typing import Iterable
from typing import Dict
from typing import Union
from typing import Optional
from typing import Callable
import os
import os.path as path
import shutil
import sqlite3
import uuid
import time
import re
import logging
import json
import chinese_variants
import ibus_table_location

LOGGER = logging.getLogger('ibus-table')

DEBUG_LEVEL = int(0)

DATABASE_VERSION = '1.00'

CHINESE_NOCHECK_CHARS = u"“”‘’《》〈〉〔〕「」『』【】〖〗（）［］｛｝"\
    u"．。，、；：？！…—·ˉˇ¨々～‖∶＂＇｀｜"\
    u"⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛"\
    u"АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЁ"\
    u"ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"\
    u"⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛"\
    u"㎎㎏㎜㎝㎞㎡㏄㏎㏑㏒㏕"\
    u"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"\
    u"⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇"\
    u"€＄￠￡￥"\
    u"¤→↑←↓↖↗↘↙"\
    u"ァアィイゥウェエォオカガキギクグケゲコゴサザシジ"\
    u"スズセゼソゾタダチヂッツヅテデトドナニヌネノハバパ"\
    u"ヒビピフブプヘベペホボポマミムメモャヤュユョヨラ"\
    u"リルレロヮワヰヱヲンヴヵヶーヽヾ"\
    u"ぁあぃいぅうぇえぉおかがきぎぱくぐけげこごさざしじ"\
    u"すずせぜそぞただちぢっつづてでとどなにぬねのはば"\
    u"ひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらり"\
    u"るれろゎわゐゑをん゛゜ゝゞ"\
    u"勹灬冫艹屮辶刂匚阝廾丨虍彐卩钅冂冖宀疒肀丿攵凵犭"\
    u"亻彡饣礻扌氵纟亠囗忄讠衤廴尢夂丶"\
    u"āáǎàōóǒòêēéěèīíǐìǖǘǚǜüūúǔù"\
    u"＋－＜＝＞±×÷∈∏∑∕√∝∞∟∠∣∥∧∨∩∪∫∮"\
    u"∴∵∶∷∽≈≌≒≠≡≤≥≦≧≮≯⊕⊙⊥⊿℃°‰"\
    u"♂♀§№☆★○●◎◇◆□■△▲※〓＃＆＠＼＾＿￣"\
    u"абвгдежзийклмнопрстуфхцчшщъыьэюяё"\
    u"ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹβγδεζηαικλμνξοπρστυφθψω"\
    u"①②③④⑤⑥⑦⑧⑨⑩①②③④⑤⑥⑦⑧⑨⑩"\
    u"㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩"\
    u"ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩ"\
    u"ㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ"

class ImeProperties:
    '''
    A class to cache the properties of an input method.
    '''
    def __init__(
            self,
            db: Optional[sqlite3.dbapi2.Connection] = None,
            default_properties: Optional[Dict[str, str]] = None) -> None:
        '''
        “db” is the handle of the sqlite3 database file obtained by
        sqlite3.connect().
        '''
        if default_properties is None:
            default_properties = {}
        if not db:
            return
        self.ime_property_cache = default_properties
        sqlstr = 'SELECT attr, val FROM main.ime;'
        try:
            results = db.execute(sqlstr).fetchall()
        except:
            LOGGER.exception('Cannot get ime properties from database')
        for result in results:
            self.ime_property_cache[result[0]] = result[1]

    def get(self, key: str) -> str:
        '''
        Return the value for a key from the property cache

        :param key: The key to lookup in the property cache
        '''
        if key in self.ime_property_cache:
            return self.ime_property_cache[key]
        return ''

    def __str__(self) -> str:
        return 'ime_property_cache = %s' %repr(self.ime_property_cache)

class TabSqliteDb:
    '''Phrase database for tables

    The phrases table in the database has columns with the names:

    “id”, “tabkeys”, “phrase”, “freq”, “user_freq”

    There are 2 databases, sysdb, userdb.

    sysdb: System database for the input method, for example something
           like /usr/share/ibus-table/tables/wubi-jidian86.db
           “user_freq” is always 0 in a system database.  “freq”
           is some number in a system database indicating a frequency
           of use of that phrase relative to the other phrases in that
           database.

    user_db: Database on disk where the phrases used or defined by the
           user are stored. “user_freq” is a counter which counts how
           many times that combination of “tabkeys” and “phrase” has
           been used. “freq” is equal to 0 for all combinations of
           “tabkeys” and “phrase” where an entry for that phrase is
           already in the system database which starts with the same
           “tabkeys”.
           For combinations of “tabkeys” and “phrase” which do not exist
           at all in the system database, “freq” is equal to -1 to
           indidated that this is a user defined phrase.
    '''
    def __init__(
            self,
            filename: str = '',
            user_db: str = '',
            create_database: bool = False,
            unit_test: bool = False) -> None:
        global DEBUG_LEVEL
        try:
            DEBUG_LEVEL = int(str(os.getenv('IBUS_TABLE_DEBUG_LEVEL')))
        except (TypeError, ValueError):
            DEBUG_LEVEL = int(0)
        self.old_phrases: List[Tuple[str, str, int, int]] = []
        self.filename = filename
        self._user_db = user_db
        self.reset_phrases_cache()

        if create_database or os.path.isfile(self.filename):
            self.db: sqlite3.dbapi2.Connection = sqlite3.connect(self.filename)
        else:
            print('Cannot open database file %s' %self.filename)
        try:
            self.db.execute('PRAGMA encoding = "UTF-8";')
            self.db.execute('PRAGMA case_sensitive_like = true;')
            self.db.execute('PRAGMA page_size = 4096;')
            # 20000 pages should be enough to cache the whole database
            self.db.execute('PRAGMA cache_size = 20000;')
            self.db.execute('PRAGMA temp_store = MEMORY;')
            self.db.execute('PRAGMA journal_size_limit = 1000000;')
            self.db.execute('PRAGMA synchronous = NORMAL;')
        except:
            LOGGER.exception('Error while initializing database')
        # create IME property table
        self.db.executescript(
            'CREATE TABLE IF NOT EXISTS main.ime (attr TEXT, val TEXT);')
        # Initalize missing attributes in the ime table with some
        # default values, they should be updated using the attributes
        # found in the source when creating a system database with
        # tabcreatedb.py
        self._default_ime_attributes = {
            'name':'',
            'name.zh_cn':'',
            'name.zh_hk':'',
            'name.zh_tw':'',
            'author':'somebody',
            'uuid':'%s' % uuid.uuid4(),
            'serial_number':'%s' % time.strftime('%Y%m%d'),
            'icon':'ibus-table.svg',
            'license':'LGPL',
            'languages':'',
            'language_filter':'',
            'valid_input_chars':'abcdefghijklmnopqrstuvwxyz',
            'max_key_length':'4',
            'commit_keys':'space',
            # 'forward_keys':'Return',
            'select_keys':'1,2,3,4,5,6,7,8,9,0',
            'page_up_keys':'Page_Up,KP_Page_Up,KP_Prior,minus',
            'page_down_keys':'Page_Down,KP_Page_Down,KP_Next,equal',
            'status_prompt':'',
            'def_full_width_punct':'true',
            'def_full_width_letter':'false',
            'user_can_define_phrase':'false',
            'pinyin_mode':'false',
            'suggestion_mode':'false',
            'dynamic_adjust':'false',
            'auto_select':'false',
            'auto_commit':'false',
            'auto_wildcard': 'true',
            # 'no_check_chars': '',
            'description':'A IME under IBus Table',
            'layout':'us',
            'symbol':'',
            'rules':'',
            'least_commit_length':'0',
            'start_chars':'',
            'orientation':'true',
            'always_show_lookup':'true',
            'char_prompts':'{}',
            # we use this entry for those IME, which don't
            # have rules to build up phrase, but still need
            # auto commit to preedit
        }
        if create_database:
            select_sqlstr = '''
            SELECT val FROM main.ime WHERE attr = :attr;'''
            insert_sqlstr = '''
            INSERT INTO main.ime (attr, val) VALUES (:attr, :val);'''
            for attr in sorted(self._default_ime_attributes):
                sqlargs = {
                    'attr': attr,
                    'val': self._default_ime_attributes[attr]
                }
                if not self.db.execute(select_sqlstr, sqlargs).fetchall():
                    self.db.execute(insert_sqlstr, sqlargs)
        self.ime_properties = ImeProperties(
            db=self.db,
            default_properties=self._default_ime_attributes)
        # shared variables in this class:
        self._mlen = int(self.ime_properties.get("max_key_length"))
        self._snum = self.ime_properties.get("serial_number")
        self._is_chinese = self.is_chinese()
        self._is_cjk = self.is_cjk()
        self.user_can_define_phrase = (self.ime_properties.get(
            'user_can_define_phrase').lower() == 'true')

        self.rules = self.get_rules()
        self.possible_tabkeys_lengths = self.get_possible_tabkeys_lengths()
        self.startchars = self.get_start_chars()

        tables_path = path.join(ibus_table_location.data_home(), 'tables')
        cache_name = os.path.basename(self.filename).replace('.db', '.cache')
        self.cache_path = path.join(tables_path, cache_name)
        if not unit_test:
            self.load_phrases_cache()

        if not user_db or create_database:
            # No user database requested or we are
            # just creating the system database and
            # we do not need a user database for that
            return

        if user_db != ":memory:":
            # Do not move this import to the beginning of this script!
            # If for example the home directory is not writeable,
            # ibus_table_location.py would fail because it cannot
            # create some directories.
            #
            # But for tabcreatedb.py, no such directories are needed,
            # tabcreatedb.py should not fail just because
            # ibus_table_location.py cannot create some directories.
            #
            # “HOME=/foobar ibus-table-createdb” should not fail if
            # “/foobar” is not writeable.
            if not path.isdir(tables_path):
                old_tables_path = os.path.expanduser('~/.ibus/tables')
                if path.isdir(old_tables_path):
                    if os.access(os.path.join(
                            old_tables_path, 'debug.log'), os.F_OK):
                        os.unlink(os.path.join(old_tables_path, 'debug.log'))
                    if os.access(os.path.join(
                            old_tables_path, 'setup-debug.log'), os.F_OK):
                        os.unlink(os.path.join(
                            old_tables_path, 'setup-debug.log'))
                    shutil.copytree(old_tables_path, tables_path)
                    shutil.rmtree(old_tables_path)
                    os.symlink(tables_path, old_tables_path)
                else:
                    os.makedirs(tables_path, exist_ok=True)
            user_db = path.join(tables_path, user_db)
            if not path.exists(user_db):
                LOGGER.debug(
                    'The user database %s does not exist yet.', user_db)
            else:
                try:
                    desc = self.get_database_desc(user_db)
                    phrase_table_column_names = [
                        'id', 'tabkeys', 'phrase', 'freq', 'user_freq']
                    if (desc is None
                            or desc["version"] != DATABASE_VERSION
                            or (self.get_number_of_columns_of_phrase_table(
                                user_db)
                                != len(phrase_table_column_names))):
                        LOGGER.debug(
                            'The user database %s seems to be incompatible.',
                            user_db)
                        if desc is None:
                            LOGGER.debug(
                                'There is no version information in '
                                'the database.')
                            self.old_phrases = self.extract_user_phrases(
                                user_db, old_database_version='0.0')
                        elif desc["version"] != DATABASE_VERSION:
                            LOGGER.debug(
                                'The version of the database does not match '
                                '(too old or too new?). '
                                'ibus-table wants version=%s '
                                'But the  database actually has version=%s',
                                DATABASE_VERSION, desc['version'])
                            self.old_phrases = self.extract_user_phrases(
                                user_db, old_database_version=desc['version'])
                        elif (self.get_number_of_columns_of_phrase_table(
                                user_db)
                              != len(phrase_table_column_names)):
                            LOGGER.debug(
                                'The number of columns of the database '
                                'does not match. '
                                'ibus-table expects %s columns. '
                                'But the database actually has %s columns. '
                                'But the versions of the databases are '
                                'identical. '
                                'This should never happen!',
                                len(phrase_table_column_names),
                                self.get_number_of_columns_of_phrase_table(
                                    user_db))
                            self.old_phrases = []
                        timestamp = time.strftime('-%Y-%m-%d_%H:%M:%S')
                        LOGGER.debug(
                            'Renaming the incompatible database to "%s".',
                            user_db+timestamp)
                        if os.path.exists(user_db):
                            os.rename(user_db, user_db+timestamp)
                        if os.path.exists(user_db+'-shm'):
                            os.rename(user_db+'-shm', user_db+'-shm'+timestamp)
                        if os.path.exists(user_db+'-wal'):
                            os.rename(user_db+'-wal', user_db+'-wal'+timestamp)
                        LOGGER.debug(
                            'Creating a new, empty database "%s".', user_db)
                        self.init_user_db(user_db)
                        LOGGER.debug(
                            'If user phrases were successfully recovered from '
                            'the old, '
                            'incompatible database, they will be used to '
                            'initialize the new database.')
                    else:
                        LOGGER.debug(
                            'Compatible database %s found.', user_db)
                except:
                    LOGGER.exception(
                        'Unexpected error trying to find user database')

        # open user phrase database
        try:
            LOGGER.debug(
                'Connect to the database %s.', user_db)
            self.db.executescript('''
                ATTACH DATABASE "%s" AS user_db;
                PRAGMA user_db.encoding = "UTF-8";
                PRAGMA user_db.case_sensitive_like = true;
                PRAGMA user_db.page_size = 4096;
                PRAGMA user_db.cache_size = 20000;
                PRAGMA user_db.temp_store = MEMORY;
                PRAGMA user_db.journal_mode = WAL;
                PRAGMA user_db.journal_size_limit = 1000000;
                PRAGMA user_db.synchronous = NORMAL;
            ''' % user_db)
        except:
            LOGGER.debug('Could not open the database %s.', user_db)
            timestamp = time.strftime('-%Y-%m-%d_%H:%M:%S')
            LOGGER.debug('Renaming the incompatible database to "%s".',
                         user_db+timestamp)
            if os.path.exists(user_db):
                os.rename(user_db, user_db+timestamp)
            if os.path.exists(user_db+'-shm'):
                os.rename(user_db+'-shm', user_db+'-shm'+timestamp)
            if os.path.exists(user_db+'-wal'):
                os.rename(user_db+'-wal', user_db+'-wal'+timestamp)
            LOGGER.debug('Creating a new, empty database "%s".', user_db)
            self.init_user_db(user_db)
            self.db.executescript('''
                ATTACH DATABASE "%s" AS user_db;
                PRAGMA user_db.encoding = "UTF-8";
                PRAGMA user_db.case_sensitive_like = true;
                PRAGMA user_db.page_size = 4096;
                PRAGMA user_db.cache_size = 20000;
                PRAGMA user_db.temp_store = MEMORY;
                PRAGMA user_db.journal_mode = WAL;
                PRAGMA user_db.journal_size_limit = 1000000;
                PRAGMA user_db.synchronous = NORMAL;
            ''' % user_db)
        self.create_tables("user_db")
        if self.old_phrases:
            sqlargs_old_phrases: List[Dict[str, Union[str, int]]] = []
            for phrase in self.old_phrases:
                sqlargs_old_phrases.append(
                    {'tabkeys': phrase[0],
                     'phrase': phrase[1],
                     'freq': phrase[2],
                     'user_freq': phrase[3]})
            sqlstr = '''
            INSERT INTO user_db.phrases (tabkeys, phrase, freq, user_freq)
            VALUES (:tabkeys, :phrase, :freq, :user_freq)
            '''
            try:
                self.db.executemany(sqlstr, sqlargs_old_phrases)
            except:
                LOGGER.exception('Error inserting old phrases')
            self.db.commit()
            self.db.execute('PRAGMA wal_checkpoint;')

        # try create all tables in user database
        self.create_indexes("user_db")
        self.generate_userdb_desc()

    def update_phrase(
            self,
            tabkeys: str = '',
            phrase: str = '',
            user_freq: int = 0,
            database: str = 'user_db',
            commit: bool = True) -> None:
        '''update phrase freqs'''
        if DEBUG_LEVEL > 1:
            LOGGER.debug(
                'tabkeys=%s phrase=%s user_freq=%s database=%s',
                tabkeys, phrase, user_freq, database)
        if not tabkeys or not phrase:
            return
        sqlstr = '''
        UPDATE %s.phrases SET user_freq = :user_freq
        WHERE tabkeys = :tabkeys AND phrase = :phrase
        ;''' % database
        sqlargs = {'user_freq': user_freq,
                   'tabkeys': tabkeys,
                   'phrase': phrase}
        try:
            self.db.execute(sqlstr, sqlargs)
            if commit:
                self.db.commit()
            self.invalidate_phrases_cache(tabkeys)
        except:
            LOGGER.exception('Unexpected error updating phrase in user_db.')

    def sync_usrdb(self) -> None:
        '''
        Trigger a checkpoint operation.
        '''
        self.save_phrases_cache()
        if self._user_db is None:
            return
        self.db.commit()
        self.db.execute('PRAGMA wal_checkpoint;')

    def reset_phrases_cache(self) -> None:
        '''
        Make the phrases cache empty
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('reset_phrases_cache()')
        self._phrases_cache: Dict[str, Union[str, Iterable[Tuple[str, str, int, int]]]]= {}

    def invalidate_phrases_cache(self, tabkeys: str = '') -> None:
        '''
        Delete all phrases starting with “tabkeys” from
        the phrases cache.

        :param tabkeys: The keys typed
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('invalidate_phrases_cache()')
        for i in range(1, self._mlen + 1):
            if self._phrases_cache.get(tabkeys[0:i]):
                self._phrases_cache.pop(tabkeys[0:i])

    def load_phrases_cache(self) -> None:
        '''
        Load phrases cache from disk
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('load_phrases_cache()')
        try:
            self._phrases_cache = json.load(open(self.cache_path, 'r'))
            snum = self._phrases_cache.get('serial_number')
            if not snum or (snum != self._snum):
                self._phrases_cache = {}
        except FileNotFoundError:
            if DEBUG_LEVEL > 1:
                LOGGER.debug(
                    'File %s not found', self.cache_path)
        except PermissionError:
            if DEBUG_LEVEL > 1:
                LOGGER.debug(
                    'Permission error reading %s', self.cache_path)
        except:
            LOGGER.debug('Unknown error reading %s', self.cache_path)

    def save_phrases_cache(self) -> None:
        '''
        Save phrases cache from disk
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('save_phrases_cache()')
        try:
            self._phrases_cache['serial_number'] = self._snum
            _cache_path = self.cache_path + '.tmp'
            # The system may be break stores on rebooting, so
            # dump to temporary file and then replace it.
            json.dump(self._phrases_cache, open(_cache_path, 'w'))
            os.replace(_cache_path, self.cache_path)
        except:
            LOGGER.exception('Unexpected error in save_phrases_cache().')

    def is_chinese(self) -> bool:
        '''
        Check whether this input method is classified as Chinese
        in the the database.
        '''
        languages = self.ime_properties.get('languages')
        if languages:
            langs = languages.split(',')
            for lang in langs:
                if lang.lower().find('zh') != -1:
                    return True
        return False

    def is_cjk(self) -> bool:
        '''
        Check whether this input method is classified as Chinese,
        Japanese, or Korean in the database.
        '''
        languages_str = self.ime_properties.get('languages')
        if languages_str:
            languages = languages_str.split(',')
            for language in languages:
                for lang in ['zh', 'ja', 'ko']:
                    if language.strip().startswith(lang):
                        return True
        return False

    def get_chinese_mode(self) -> int:
        '''
        Get the default Chinese mode from the database

        0 means to show simplified Chinese only
        1 means to show traditional Chinese only
        2 means to show all characters but show simplified Chinese first
        3 means to show all characters but show traditional Chinese first
        4 means to show all characters

        If no mode is specified in the database, return 4 to avoid all
        filtering of characters.
        '''
        language_filter = self.ime_properties.get('language_filter')
        if language_filter in ('cm0', 'cm1', 'cm2', 'cm3', 'cm4'):
            return int(language_filter[-1])
        return 4

    def get_select_keys(self) -> str:
        '''
        Get the keys used to select a candidate from the database
        '''
        ret = self.ime_properties.get("select_keys")
        if ret:
            return ret
        return "1,2,3,4,5,6,7,8,9,0"

    def get_orientation(self) -> int:
        '''Get the default orientation of the lookup table from the database'''
        try:
            return int(self.ime_properties.get('orientation'))
        except (TypeError, ValueError):
            return 1

    def create_tables(self, database: str) -> None:
        '''Create tables that contain all phrase'''
        if database == 'main':
            sqlstr = '''
            CREATE TABLE IF NOT EXISTS %s.goucima
            (zi TEXT PRIMARY KEY, goucima TEXT);
            ''' % database
            self.db.execute(sqlstr)
            sqlstr = '''
            CREATE TABLE IF NOT EXISTS %s.pinyin
            (pinyin TEXT, zi TEXT, freq INTEGER);
            ''' % database
            self.db.execute(sqlstr)
            sqlstr = '''
            CREATE TABLE IF NOT EXISTS %s.suggestion
            (phrase TEXT, freq INTEGER);
            ''' %database
            self.db.execute(sqlstr)

        sqlstr = '''
        CREATE TABLE IF NOT EXISTS %s.phrases
        (id INTEGER PRIMARY KEY, tabkeys TEXT, phrase TEXT,
        freq INTEGER, user_freq INTEGER);
        ''' % database
        self.db.execute(sqlstr)
        self.db.commit()

    def update_ime(self, attrs: Iterable[Tuple[str, str]]) -> None:
        '''Update or insert attributes in ime table, attrs is a iterable object
        Like [(attr,val), (attr,val), ...]

        This is called only by tabcreatedb.py.
        '''
        select_sqlstr = 'SELECT val from main.ime WHERE attr = :attr'
        update_sqlstr = 'UPDATE main.ime SET val = :val WHERE attr = :attr;'
        insert_sqlstr = (
            'INSERT INTO main.ime (attr, val) VALUES (:attr, :val);')
        for attr, val in attrs:
            sqlargs = {'attr': attr, 'val': val}
            if self.db.execute(select_sqlstr, sqlargs).fetchall():
                self.db.execute(update_sqlstr, sqlargs)
            else:
                self.db.execute(insert_sqlstr, sqlargs)
        self.db.commit()
        # update ime properties cache:
        self.ime_properties = ImeProperties(
            db=self.db,
            default_properties=self._default_ime_attributes)
        # The self variables used by tabcreatedb.py need to be updated now:
        self._mlen = int(self.ime_properties.get('max_key_length'))
        self._is_chinese = self.is_chinese()
        self.user_can_define_phrase = (self.ime_properties.get(
            'user_can_define_phrase').lower() == 'true')
        self.rules = self.get_rules()

    def get_rules(self) -> Dict[Union[str, int], Union[int, List[Tuple[int, int]]]]:
        '''Get phrase construct rules

        Example:

        The wubi-jidian86.txt table source contains:

        RULES = ce2:p11+p12+p21+p22;ce3:p11+p21+p31+p32;ca4:p11+p21+p31+p-11

        and the return value of this function becomes:

        {2: [(1, 1), (1, 2), (2, 1), (2, 2)],
         3: [(1, 1), (2, 1), (3, 1), (3, 2)],
         'above': 4,
         4: [(1, 1), (2, 1), (3, 1), (-1, 1)]}
        '''
        rules: Dict[Union[str, int], Union[int, List[Tuple[int, int]]]] = {}
        patt_r = re.compile(r'c([ea])(\d):(.*)')
        patt_p = re.compile(r'p(-{0,1}\d)(-{0,1}\d)')
        if not self.user_can_define_phrase:
            return {}
        try:
            _rules_str = self.ime_properties.get('rules')
            _rules: List[str] = []
            if _rules_str:
                _rules = _rules_str.strip().split(';')
            for rule in _rules:
                res = patt_r.match(rule)
                if res:
                    cms = []
                    if res.group(1) == 'a':
                        rules['above'] = int(res.group(2))
                    _cms = res.group(3).split('+')
                    if len(_cms) > self._mlen:
                        print('rule: "%s" over max key length' %rule)
                        break
                    for _cm in _cms:
                        cm_res = patt_p.match(_cm)
                        if cm_res:
                            cms.append((int(cm_res.group(1)),
                                        int(cm_res.group(2))))
                    rules[int(res.group(2))] = cms
                else:
                    print('not a legal rule: "%s"' %rule)
        except Exception:
            LOGGER.exception('Unexpected error in get_rules().')
        return rules

    def get_possible_tabkeys_lengths(self) -> List[int]:
        '''Return a list of the possible lengths for tabkeys in this table.

        Example:

        If the table source has rules like:

            RULES = ce2:p11+p12+p21+p22;ce3:p11+p21+p22+p31;ca4:p11+p21+p31+p41

        self._rules will be set to

            self._rules = {
                2: [(1, 1), (1, 2), (2, 1), (2, 2)],
                3: [(1, 1), (1, 2), (2, 1), (3, 1)],
                4: [(1, 1), (2, 1), (3, 1), (-1, 1)],
                'above': 4}

        and then this function returns “[4, 4, 4]”

        Or, if the table source has no RULES but LEAST_COMMIT_LENGTH=2
        and MAX_KEY_LENGTH = 4, then it returns “[2, 3, 4]”

        I cannot find any tables which use LEAST_COMMIT_LENGTH though.
        '''
        if self.rules:
            max_len = self.rules["above"]
            return [len(self.rules[x]) for x in range(2, max_len+1)][:] # type: ignore
        try:
            least_commit_len = int(
                self.ime_properties.get('least_commit_length'))
        except (TypeError, ValueError):
            least_commit_len = 0
        if least_commit_len > 0:
            return list(range(least_commit_len, self._mlen + 1))
        return []

    def get_start_chars(self) -> str:
        '''return possible start chars of IME'''
        return self.ime_properties.get('start_chars')

    def get_no_check_chars(self) -> str:
        '''Get the characters which engine should not change freq'''
        _chars = self.ime_properties.get('no_check_chars')
        return _chars

    def add_phrases(
            self,
            phrases: Iterable[Tuple[str, str, int, int]],
            database: str = 'main') -> None:
        '''Add many phrases to database fast. Used by tabcreatedb.py when
        creating the system database from scratch.

        “phrases” is a iterable object which looks like:

            [(tabkeys, phrase, freq ,user_freq),
             (tabkeys, phrase, freq, user_freq), ...]

        This function does not check whether phrases are already
        there.  As this function is only used while creating the
        system database, it is not really necessary to check whether
        phrases are already there because the database is initially
        empty anyway. And the caller should take care that the
        “phrases” argument does not contain duplicates.

        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('len(phrases)=%s', len(list(phrases)))
        insert_sqlstr = '''
        INSERT INTO %(database)s.phrases
        (tabkeys, phrase, freq, user_freq)
        VALUES (:tabkeys, :phrase, :freq, :user_freq);
        ''' % {'database': database}
        insert_sqlargs = []
        for (tabkeys, phrase, freq, user_freq) in phrases:
            insert_sqlargs.append({
                'tabkeys': tabkeys,
                'phrase': phrase,
                'freq': freq,
                'user_freq': user_freq})
            self.invalidate_phrases_cache(tabkeys)
        self.db.executemany(insert_sqlstr, insert_sqlargs)
        self.db.commit()
        self.db.execute('PRAGMA wal_checkpoint;')

    def add_phrase(
            self,
            tabkeys: str = '',
            phrase: str = '',
            freq: int = 0,
            user_freq: int = 0,
            database: str = 'main',
            commit: bool = True) -> None:
        '''Add phrase to database, phrase is a object of
        (tabkeys, phrase, freq ,user_freq)
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug(
                'add_phrase tabkeys=%s phrase=%s '
                'freq=%s user_freq=%s',
                tabkeys, phrase, freq, user_freq)
        if not tabkeys or not phrase:
            return
        select_sqlstr = '''
        SELECT * FROM %(database)s.phrases
        WHERE tabkeys = :tabkeys AND phrase = :phrase;
        ''' % {'database': database}
        select_sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        results = self.db.execute(select_sqlstr, select_sqlargs).fetchall()
        if results:
            # there is already such a phrase, i.e. add_phrase was called
            # in error, do nothing to avoid duplicate entries.
            if DEBUG_LEVEL > 1:
                LOGGER.debug(
                    'select_sqlstr=%(sql)s select_sqlargs=%(arg)s '
                    'already there!: results=%(r)s ',
                    select_sqlstr, select_sqlargs, results)
            return

        insert_sqlstr = '''
        INSERT INTO %(database)s.phrases
        (tabkeys, phrase, freq, user_freq)
        VALUES (:tabkeys, :phrase, :freq, :user_freq);
        ''' % {'database': database}
        insert_sqlargs = {
            'tabkeys': tabkeys,
            'phrase': phrase,
            'freq': freq,
            'user_freq': user_freq}
        if DEBUG_LEVEL > 1:
            LOGGER.debug(
                'insert_sqlstr=%s insert_sqlargs=%s',
                insert_sqlstr, insert_sqlargs)
        try:
            self.db.execute(insert_sqlstr, insert_sqlargs)
            if commit:
                self.db.commit()
            self.invalidate_phrases_cache(tabkeys)
        except:
            LOGGER.exception('Unexpected error in add_phrase()')

    def add_goucima(self, goucimas: Iterable[Tuple[str, str]]) -> None:
        '''Add goucima into database, goucimas is iterable object
        Like goucimas = [(zi,goucima), (zi,goucima), ...]
        '''
        sqlstr = '''
        INSERT INTO main.goucima (zi, goucima) VALUES (:zi, :goucima);
        '''
        sqlargs = []
        for zi, goucima in goucimas:
            sqlargs.append({'zi': zi, 'goucima': goucima})
        try:
            self.db.commit()
            self.db.executemany(sqlstr, sqlargs)
            self.db.commit()
            self.db.execute('PRAGMA wal_checkpoint;')
        except:
            LOGGER.exception('Unexpected error in add_goucima().')

    def add_pinyin(
            self,
            pinyins: Iterable[Tuple[str, str, int]],
            database: str = 'main') -> None:
        '''Add pinyin to database, pinyins is a iterable object
        Like: [(zi,pinyin, freq), (zi, pinyin, freq), ...]
        '''
        sqlstr = '''
        INSERT INTO %s.pinyin (pinyin, zi, freq) VALUES (:pinyin, :zi, :freq);
        ''' % database
        count = 0
        for pinyin, zi, freq in pinyins:
            count += 1
            pinyin = pinyin.replace(
                '1', '!').replace(
                    '2', '@').replace(
                        '3', '#').replace(
                            '4', '$').replace(
                                '5', '%')
            try:
                self.db.execute(
                    sqlstr, {'pinyin': pinyin, 'zi': zi, 'freq': freq})
            except Exception:
                LOGGER.exception(
                    'Error when inserting into pinyin table. '
                    'count=%s pinyin=%s zi=%s freq=%s',
                    count, pinyin, zi, freq)
        self.db.commit()

    def add_suggestion(
            self,
            suggestions: Iterable[Tuple[str, int]],
            database: str = 'main') -> None:
        '''Add suggestion phrase to database, suggestions is a iterable object
        Like: [(phrase, freq), (phrase, freq), ...]
        '''
        sqlstr = '''
        INSERT INTO %s.suggestion (phrase, freq) VALUES (:phrase, :freq);
        ''' % database
        count = 0
        for phrase, freq in suggestions:
            count += 1
            try:
                self.db.execute(
                    sqlstr, {'phrase': phrase, 'freq': freq})
            except Exception:
                LOGGER.exception(
                    'Error when inserting into suggestion table. '
                    'count=%s phrase=%s freq=%s',
                    count, phrase, freq)
        self.db.commit()

    def optimize_database(self) -> None:
        '''
        Optimize the database by copying the contents
        to temporary tables and back.
        '''
        sqlstr = '''
            CREATE TABLE tmp AS SELECT * FROM main.phrases;
            DELETE FROM main.phrases;
            INSERT INTO main.phrases SELECT * FROM tmp ORDER BY
            tabkeys ASC, phrase ASC, user_freq DESC, freq DESC, id ASC;
            DROP TABLE tmp;
            CREATE TABLE tmp AS SELECT * FROM main.goucima;
            DELETE FROM main.goucima;
            INSERT INTO main.goucima SELECT * FROM tmp ORDER BY zi, goucima;
            DROP TABLE tmp;
            CREATE TABLE tmp AS SELECT * FROM main.pinyin;
            DELETE FROM main.pinyin;
            INSERT INTO main.pinyin SELECT * FROM tmp ORDER BY pinyin ASC, freq DESC;
            DROP TABLE tmp;
            CREATE TABLE tmp as SELECT * FROM main.suggestion;
            DELETE FROM main.suggestion;
            INSERT INTO main.suggestion SELECT * FROM tmp ORDER by phrase ASC, freq DESC;
            DROP TABLE tmp;
            '''
        self.db.executescript(sqlstr)
        self.db.executescript("VACUUM;")
        self.db.commit()

    def drop_indexes(self, _database: str) -> None:
        '''Drop the indexes in the database to reduce its size

        We do not use any indexes at the moment, therefore this
        function does nothing.
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('drop_indexes()')

    def create_indexes(self, _database: str, _commit: bool = True) -> None:
        '''Create indexes for the database.

        We do not use any indexes at the moment, therefore
        this function does nothing. We used indexes before,
        but benchmarking showed that none of them was really
        speeding anything up, therefore we deleted all of them
        to get much smaller databases (about half the size).

        If some index turns out to be very useful in future, it could
        be created here (and dropped in “drop_indexes()”).
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('create_indexes()')

    def big5_code(self, phrase: str) -> bytes:
        '''
        Encode a string in Big5 or, if that is not possible,
        return something higher than any Big5 code.

        :param phrase: String to be encoded in Big5 encoding
        '''
        try:
            big5 = phrase.encode('Big5')
        except UnicodeEncodeError:
            big5 = b'\xff\xff' # higher than any Big5 code
        return big5

    def best_candidates(
            self,
            typed_tabkeys: str = '',
            candidates: Iterable[Tuple[str, str, int, int]] = (),
            chinese_mode: int = 4) -> Iterable[Tuple[str, str, int, int]]:
        '''
        “candidates” is an array containing something like:
        [(tabkeys, phrase, freq, user_freq), ...]

        “typed_tabkeys” is key sequence the user really typed, which
        maybe only the beginning part of the “tabkeys” in a matched
        candidate.
        '''
        maximum_number_of_candidates = 100
        engine_name = os.path.basename(self.filename).replace('.db', '')
        if engine_name in [
                'cangjie3', 'cangjie5', 'cangjie-big',
                'quick-classic', 'quick3', 'quick5']:
            code_point_function: Callable[[str], bytes] = self.big5_code
        else:
            code_point_function: Callable[[str], bytes] = lambda x: (b'\xff\xff')
        if self._is_chinese:
            pinyin_exact_match_function: Callable[[str], int] = lambda x: (
                - int(typed_tabkeys == x[:-1] and  x[-1] in '!@#$%')
            )
        else:
            pinyin_exact_match_function = lambda x: (1)
        if chinese_mode in (2, 3) and self._is_chinese:
            if chinese_mode == 2:
                bitmask = (1 << 0) # used in simplified Chinese
            else:
                bitmask = (1 << 1) # used in traditional Chinese
            return sorted(candidates,
                          key=lambda x: (
                              - int(
                                  typed_tabkeys == x[0]
                              ), # exact matches first!
                              pinyin_exact_match_function(x[0]),
                              -1*x[3],   # user_freq descending
                              # Prefer characters used in the
                              # desired Chinese variant:
                              -(bitmask
                                & chinese_variants.detect_chinese_category(
                                    x[1])),
                              -1*x[2],   # freq descending
                              len(x[0]), # len(tabkeys) ascending
                              x[0],      # tabkeys alphabetical
                              code_point_function(x[1][0]),
                              # Unicode codepoint of first character of phrase:
                              ord(x[1][0])
                          ))[:maximum_number_of_candidates]
        return sorted(candidates,
                      key=lambda x: (
                          - int(
                              typed_tabkeys == x[0]
                          ), # exact matches first!
                          pinyin_exact_match_function(x[0]),
                          -1*x[3],   # user_freq descending
                          -1*x[2],   # freq descending
                          len(x[0]), # len(tabkeys) ascending
                          x[0],      # tabkeys alphabetical
                          code_point_function(x[1][0]),
                          # Unicode codepoint of first character of phrase:
                          ord(x[1][0])
                      ))[:maximum_number_of_candidates]

    def select_words(
            self,
            tabkeys: str = '',
            onechar: bool = False,
            chinese_mode: int = 4,
            single_wildcard_char: str = '',
            multi_wildcard_char: str = '',
            auto_wildcard: bool = False,
            dynamic_adjust: bool = False) -> Iterable[Tuple[str, str, int, int]]:
        '''
        Get matching phrases for tabkeys from the database.
        '''
        if not tabkeys:
            return []
        # query phrases cache first
        best = self._phrases_cache.get(tabkeys)
        if best:
            return best # type: ignore
        one_char_condition = ''
        if onechar:
            # for some users really like to select only single characters
            one_char_condition = ' AND length(phrase)=1 '

        if self.user_can_define_phrase or dynamic_adjust:
            sqlstr = '''
            SELECT tabkeys, phrase, freq, user_freq FROM
            (
                SELECT tabkeys, phrase, freq, user_freq FROM main.phrases
                WHERE tabkeys LIKE :tabkeys ESCAPE :escapechar %(one_char_condition)s
                UNION ALL
                SELECT tabkeys, phrase, freq, user_freq FROM user_db.phrases
                WHERE tabkeys LIKE :tabkeys ESCAPE :escapechar %(one_char_condition)s
            )
            ''' % {'one_char_condition': one_char_condition}
        else:
            sqlstr = '''
            SELECT tabkeys, phrase, freq, user_freq FROM main.phrases
            WHERE tabkeys LIKE :tabkeys ESCAPE :escapechar %(one_char_condition)s
            ''' % {'one_char_condition': one_char_condition}
        escapechar = '☺'
        for char in '!@#':
            if char not in [single_wildcard_char, multi_wildcard_char]:
                escapechar = char
        tabkeys_for_like = tabkeys
        tabkeys_for_like = tabkeys_for_like.replace(
            escapechar, escapechar+escapechar)
        if '%' not in [single_wildcard_char, multi_wildcard_char]:
            tabkeys_for_like = tabkeys_for_like.replace('%', escapechar+'%')
        if '_' not in [single_wildcard_char, multi_wildcard_char]:
            tabkeys_for_like = tabkeys_for_like.replace('_', escapechar+'_')
        if single_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                single_wildcard_char, '_')
        if multi_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                multi_wildcard_char, '%%')
        if auto_wildcard:
            tabkeys_for_like += '%%'
        sqlargs = {'tabkeys': tabkeys_for_like, 'escapechar': escapechar}
        if DEBUG_LEVEL > 1:
            LOGGER.debug('sqlstr=%s sqlargs=%s', sqlstr, repr(sqlargs))
        unfiltered_results = self.db.execute(sqlstr, sqlargs).fetchall()
        bitmask = None
        if chinese_mode == 0:
            bitmask = (1 << 0) # simplified only
        elif chinese_mode == 1:
            bitmask = (1 << 1) # traditional only
        if not bitmask:
            results = unfiltered_results
        else:
            results = []
            for result in unfiltered_results:
                if (bitmask
                        & chinese_variants.detect_chinese_category(result[1])):
                    results.append(result)
        # merge matches from the system database and from the user
        # database to avoid duplicates in the candidate list for
        # example, if we have the result ('aaaa', '工', 551000000, 0)
        # from the system database and ('aaaa', '工', 0, 5) from the
        # user database, these should be merged into one match
        # ('aaaa', '工', 551000000, 5).
        phrase_frequencies = {}
        for result in results:
            key = (result[0], result[1])
            if key not in phrase_frequencies:
                phrase_frequencies[key] = result
            else:
                phrase_frequencies.update([(
                    key,
                    key +
                    (
                        max(result[2], phrase_frequencies[key][2]),
                        max(result[3], phrase_frequencies[key][3]))
                )])
        best = self.best_candidates(
            typed_tabkeys=tabkeys,
            candidates=phrase_frequencies.values(),
            chinese_mode=chinese_mode)
        if DEBUG_LEVEL > 1:
            LOGGER.debug('best=%s', repr(best))
        self._phrases_cache[tabkeys] = best
        return best

    def select_chinese_characters_by_pinyin(
            self,
            tabkeys: str = '',
            chinese_mode: int = 4,
            single_wildcard_char: str = '',
            multi_wildcard_char: str = '') -> Iterable[Tuple[str, str, int, int]]:
        '''
        Get Chinese characters matching the pinyin given by tabkeys
        from the database.
        '''
        if not tabkeys:
            return []
        sqlstr = '''
        SELECT pinyin, zi, freq FROM main.pinyin WHERE pinyin LIKE :tabkeys
        ORDER BY freq DESC, pinyin ASC;
        '''
        tabkeys_for_like = tabkeys
        if single_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                single_wildcard_char, '_')
        if multi_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                multi_wildcard_char, '%%')
        tabkeys_for_like += '%%'
        sqlargs = {'tabkeys': tabkeys_for_like}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        # now convert the results into a list of candidates in the format
        # which was returned before I simplified the pinyin database table.
        bitmask = None
        if chinese_mode == 0:
            bitmask = (1 << 0) # simplified only
        elif chinese_mode == 1:
            bitmask = (1 << 1) # traditional only
        phrase_frequencies: List[Tuple[str, str, int, int]] = []
        for (pinyin, zi, freq) in results:
            if not bitmask:
                phrase_frequencies.append((pinyin, zi, freq, 0))
            else:
                if bitmask & chinese_variants.detect_chinese_category(zi):
                    phrase_frequencies.append((pinyin, zi, freq, 0))
        return self.best_candidates(
            typed_tabkeys=tabkeys,
            candidates=phrase_frequencies,
            chinese_mode=chinese_mode)

    def select_suggestion_candidate(
            self, prefix: str = '') -> List[Tuple[str, int]]:
        '''
        Get Chinese phrase matching the prefix from the database.
        '''
        if not prefix:
            return []
        sqlstr = '''
        SELECT phrase, freq FROM main.suggestion WHERE phrase LIKE :prefix
        ORDER BY length(phrase) DESC, freq DESC, phrase ASC;
        '''
        prefix_for_like = prefix + '%%'
        sqlargs = {'prefix': prefix_for_like}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        phrase_frequencies = {}
        # merge the same phrase in suggestion candidates
        for phrase, freq in results:
            if phrase not in phrase_frequencies:
                phrase_frequencies[phrase] = (phrase, freq)
            else:
                phrase_frequencies.update(
                    [(phrase,
                      (phrase, max(freq, phrase_frequencies[phrase][1])))])
        candidates = phrase_frequencies.values()
        if DEBUG_LEVEL > 1:
            LOGGER.debug('candidates=%s', repr(candidates))
        maximum_number_of_candidates = 100
        engine_name = os.path.basename(self.filename).replace('.db', '')

        if engine_name in [
                'cangjie3', 'cangjie5', 'cangjie-big',
                'quick-classic', 'quick3', 'quick5']:
            code_point_function: Callable[[str], bytes] = self.big5_code
        else:
            code_point_function: Callable[[str], bytes] = lambda x: (b'\xff\xff')

        return sorted(candidates,
                      key=lambda x: (
                          - int(len(x[0])), # longest matches first!
                          -1*x[1],   # freq descending
                          code_point_function(x[0][0]),
                          code_point_function(x[0][1]),
                          # Unicode codepoint of first character of phrase:
                          ord(x[0][0]),
                          # Unicode codepoint of second character of phrase:
                          ord(x[0][1])
                      ))[:maximum_number_of_candidates]

    def generate_userdb_desc(self) -> None:
        '''
        Add a description table to the user database

        This adds the database version and  the create time
        '''
        try:
            sqlstring = (
                'CREATE TABLE IF NOT EXISTS user_db.desc '
                + '(name PRIMARY KEY, value);')
            self.db.executescript(sqlstring)
            sqlstring = 'INSERT OR IGNORE INTO user_db.desc  VALUES (?, ?);'
            self.db.execute(sqlstring, ('version', DATABASE_VERSION))
            sqlstring = (
                'INSERT OR IGNORE INTO user_db.desc  '
                + 'VALUES (?, DATETIME("now", "localtime"));')
            self.db.execute(sqlstring, ("create-time", ))
            self.db.commit()
        except:
            LOGGER.exception('Unexpected error in generate_userdb_desc().')

    def init_user_db(self, db_file: str) -> None:
        '''
        Initialize the user database unless it is an in-memory database

        :param db_file: Full path of the database file.
        :type db_file: String
        '''
        if db_file == ':memory:':
            return
        if not path.exists(db_file):
            db = sqlite3.connect(db_file)
            # 20000 pages should be enough to cache the whole database
            db.executescript('''
                PRAGMA encoding = "UTF-8";
                PRAGMA case_sensitive_like = true;
                PRAGMA page_size = 4096;
                PRAGMA cache_size = 20000;
                PRAGMA temp_store = MEMORY;
                PRAGMA journal_mode = WAL;
                PRAGMA journal_size_limit = 1000000;
                PRAGMA synchronous = NORMAL;
            ''')
            db.commit()

    def get_database_desc(self, db_file: str) -> Optional[Dict[str, str]]:
        '''
        Get the description table from the database

        :param db_file: Full path of the database file.
        :type db_file: String
        :rtype: Dictionary
        '''
        if not path.exists(db_file):
            return None
        try:
            db = sqlite3.connect(db_file)
            desc = {}
            for row in db.execute("SELECT * FROM desc;").fetchall():
                desc[row[0]] = row[1]
            db.close()
            return desc
        except:
            return None

    def get_number_of_columns_of_phrase_table(self, db_file: str) -> int:
        '''
        Get the number of columns in the 'phrases' table in
        the database in db_file.

        Determines the number of columns by parsing this:

        sqlite> select sql from sqlite_master where name='phrases';
        CREATE TABLE phrases
                (id INTEGER PRIMARY KEY, tabkeys TEXT, phrase TEXT,
                freq INTEGER, user_freq INTEGER)
        sqlite>

        This result could be on a single line, as above, or on multiple
        lines.

        :param db_file: Full path of the database file.
        :rtype: Integer
        '''
        if not path.exists(db_file):
            return 0
        try:
            db = sqlite3.connect(db_file)
            tp_res = db.execute(
                "select sql from sqlite_master where name='phrases';"
            ).fetchall()
            # Remove possible line breaks from the string where we
            # want to match:
            string = ' '.join(tp_res[0][0].splitlines())
            res = re.match(r'.*\((.*)\)', string)
            if res:
                tp = res.group(1).split(',')
                return len(tp)
            return 0
        except:
            return 0

    def get_goucima(self, zi: str) -> str:
        '''Get goucima of given character'''
        if not zi:
            return ''
        sqlstr = 'SELECT goucima FROM main.goucima WHERE zi = :zi;'
        results = self.db.execute(sqlstr, {'zi': zi}).fetchall()
        goucima = ''
        if results:
            goucima = results[0][0]
        if DEBUG_LEVEL > 1:
            LOGGER.debug('goucima=%s', goucima)
        return goucima

    def parse_phrase(self, phrase: str) -> str:
        '''Parse phrase to get its table code

        Example:

        Let’s assume we use wubi-jidian86. The rules in the source of
        that table are:

          RULES = ce2:p11+p12+p21+p22;ce3:p11+p21+p31+p32;ca4:p11+p21+p31+p-11

        “ce2” is a rule for phrases of length 2, “ce3” is a rule
        for phrases of length 3, “ca4” is a rule for phrases of
        length 4 *and* for all phrases with a length greater then
        4. “pnm” in such a rule means to use the n-th character of
        the phrase and take the m-th character of the table code of
        that character. I.e. “p-11” is the first character of the
        table code of the last character in the phrase.

        Let’s assume the phrase is “天下大事”. The goucima (構詞碼
        = “word formation keys”) for these 4 characters when
        using the wubi-jidian86 table are:

            character goucima
            天        gdi
            下        ghi
            大        dddd
            事        gkvh

        (If no special goucima are defined by the user, the longest
        encoding for a single character in a table is the goucima for
        that character).

        The length of the phrase “天下大事” is 4 characters,
        therefore the rule ca4:p11+p21+p31+p-11 applies, i.e. the
        table code for “天下大事” is calculated by using the first,
        second, third and last character of the phrase and taking the
        first character of the goucima for each of these. Therefore,
        the table code for “天下大事” is “ggdg”.

        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('phrase=%s rules%s', phrase, self.rules)
        # Shouldn’t this function try first whether the system database
        # already has an entry for this phrase and if yes return it
        # instead of constructing a new entry according to the rules?
        # And construct a new entry only when no entry already exists
        # in the system database??
        if not phrase:
            return ''
        if len(phrase) == 1:
            return self.get_goucima(phrase)
        if not self.rules:
            return ''
        if len(phrase) in self.rules:
            rule = self.rules[len(phrase)]
        elif (isinstance(self.rules['above'], int)
              and len(phrase) > self.rules['above']):
            rule = self.rules[self.rules['above']]
        else:
            LOGGER.debug(
                'No rule for this phrase length. phrase=%s rules=%s',
                phrase, self.rules)
            return ''
        if not isinstance(rule, int) and len(rule) > self._mlen:
            LOGGER.debug(
                'Rule exceeds maximum key length. '
                'rule=%s self._mlen=%s', rule, self._mlen)
            return ''
        tabkeys = ''
        if isinstance(rule, int):
            return '' # should never happen!
        for (zi, ma) in rule:
            if zi > 0:
                zi -= 1
            if ma > 0:
                ma -= 1
            tabkey = self.get_goucima(phrase[zi])[ma]
            if not tabkey:
                return ''
            tabkeys += tabkey
        if DEBUG_LEVEL > 1:
            LOGGER.debug('tabkeys=%s', tabkeys)
        return tabkeys

    def is_in_system_database(
            self, tabkeys: str = '', phrase: str = '') -> bool:
        '''
        Checks whether “phrase” can be matched in the system database
        with a key sequence *starting* with “tabkeys”.
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('tabkeys=%s phrase=%s', tabkeys, phrase)
        if not tabkeys or not phrase:
            return False
        sqlstr = '''
        SELECT * FROM main.phrases
        WHERE tabkeys LIKE :tabkeys AND phrase = :phrase;
        '''
        sqlargs = {'tabkeys': tabkeys+'%%', 'phrase': phrase}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        if DEBUG_LEVEL > 1:
            LOGGER.debug(
                'tabkeys=%s phrase=%s results=%s',
                tabkeys, phrase, results)
        return bool(results)

    def user_frequency(self, tabkeys: str = '', phrase: str = '') -> int:
        '''
        Return how often a conversion result “phrase” for the typed keys
        “tabkeys” has been happened by checking the user database.

        :param tabkeys: The keys typed
        :param phrase: A conversion result for these tabkeys
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('tabkeys=%s phrase=%s', tabkeys, phrase)
        if not tabkeys or not phrase:
            return 0
        sqlstr = '''
        SELECT sum(user_freq) FROM user_db.phrases
        WHERE tabkeys = :tabkeys AND phrase = :phrase GROUP BY tabkeys, phrase;
        '''
        sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        result = self.db.execute(sqlstr, sqlargs).fetchall()
        if DEBUG_LEVEL > 1:
            LOGGER.debug('result=%s', result)
        if result:
            return int(result[0][0])
        return 0

    def check_phrase(
            self,
            tabkeys: str = '',
            phrase: str = '',
            dynamic_adjust: bool = False) -> None:
        '''Adjust user_freq in user database if necessary.

        Also, if the phrase is not in the system database, and it is a
        Chinese table, and defining user phrases is allowed, add it as
        a user defined phrase to the user database if it is not yet
        there.
        '''
        if DEBUG_LEVEL > 1:
            LOGGER.debug('tabkey=%s phrase=%s', tabkeys, phrase)
        if not tabkeys or not phrase:
            return
        if self._is_chinese and phrase in CHINESE_NOCHECK_CHARS:
            return
        if not dynamic_adjust:
            if not self.user_can_define_phrase or not self.is_chinese:
                return
            tabkeys = self.parse_phrase(phrase)
            if not tabkeys:
                # no tabkeys could be constructed from the rules in the table
                return
            if self.is_in_system_database(tabkeys=tabkeys, phrase=phrase):
                # if it is in the system database, it does not need to
                # be defined
                return
            if self.user_frequency(tabkeys=tabkeys, phrase=phrase) > 0:
                # if it is in the user database, it has been defined before
                return
            # add this user defined phrase to the user database:
            self.add_phrase(
                tabkeys=tabkeys, phrase=phrase, freq=-1, user_freq=1,
                database='user_db')
        else:
            if self.is_in_system_database(tabkeys=tabkeys, phrase=phrase):
                user_freq = self.user_frequency(tabkeys=tabkeys, phrase=phrase)
                if user_freq > 0:
                    self.update_phrase(
                        tabkeys=tabkeys, phrase=phrase, user_freq=user_freq+1)
                else:
                    self.add_phrase(
                        tabkeys=tabkeys, phrase=phrase, freq=0, user_freq=1,
                        database='user_db')
            else:
                if not self.user_can_define_phrase or not self.is_chinese:
                    return
                tabkeys = self.parse_phrase(phrase)
                if not tabkeys:
                    # no tabkeys could be constructed from the rules
                    # in the table
                    return
                user_freq = self.user_frequency(tabkeys=tabkeys, phrase=phrase)
                if user_freq > 0:
                    self.update_phrase(
                        tabkeys=tabkeys, phrase=phrase, user_freq=user_freq+1)
                else:
                    self.add_phrase(
                        tabkeys=tabkeys, phrase=phrase, freq=-1, user_freq=1,
                        database='user_db')

    def find_zi_code(self, phrase: str) -> List[str]:
        '''
        Return the list of possible tabkeys for a phrase.

        For example, if “phrase” is “你” and the table is wubi-jidian.86.txt,
        the result will be ['wq', 'wqi', 'wqiy'] because that table
        contains the following 3 lines matching that phrase exactly:

        wq	你	597727619
        wqi	你	1490000000
        wqiy	你	1490000000
        '''
        sqlstr = '''
        SELECT tabkeys FROM main.phrases WHERE phrase = :phrase
        ORDER by length(tabkeys) ASC;
        '''
        sqlargs = {'phrase': phrase}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        list_of_possible_tabkeys = [x[0] for x in results]
        return list_of_possible_tabkeys

    def remove_phrase(
            self,
            tabkeys: str = '',
            phrase: str = '',
            database: str = 'user_db',
            commit: bool = True) -> None:
        '''Remove phrase from database
        '''
        LOGGER.info('Removing tabkeys=%s, phrase=%s, database=%s commit=%s',
                    tabkeys, phrase, database, commit)
        if not phrase:
            return
        if tabkeys:
            delete_sqlstr = '''
            DELETE FROM %(database)s.phrases
            WHERE tabkeys = :tabkeys AND phrase = :phrase;
            ''' % {'database': database}
        else:
            delete_sqlstr = '''
            DELETE FROM %(database)s.phrases
            WHERE phrase = :phrase;
            ''' % {'database': database}
        delete_sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        self.db.execute(delete_sqlstr, delete_sqlargs)
        if commit:
            self.db.commit()
        self.invalidate_phrases_cache(tabkeys)

    def remove_all_phrases_from_user_db(self) -> None:
        '''
        Remove all phrases from the user database, i.e. delete all the
        data learned from user input.
        '''
        LOGGER.info('Removing all phrases from the user database.')
        try:
            self.db.execute('DELETE FROM user_db.phrases;')
            self.db.commit()
            self.db.execute('PRAGMA wal_checkpoint;')
            self.reset_phrases_cache()
        except Exception:
            LOGGER.exception(
                'Unexpected error removing all phrases from database.')

    def extract_user_phrases(
            self,
            database_file: str = '',
            old_database_version: str = '0.0'
    ) -> List[Tuple[str, str, int, int]]:
        '''extract user phrases from database'''
        LOGGER.debug(
            'Trying to recover the phrases from the old, '
            'incompatible database.')
        try:
            db = sqlite3.connect(database_file)
            db.execute('PRAGMA wal_checkpoint;')
            if old_database_version >= '1.00':
                phrases = db.execute(
                    '''
                    SELECT tabkeys, phrase, freq, sum(user_freq) FROM phrases
                    GROUP BY tabkeys, phrase, freq;
                    '''
                ).fetchall()
                db.close()
                phrases = sorted(
                    phrases, key=lambda x: (x[0], x[1], x[2], x[3]))
                LOGGER.debug(
                    'Recovered phrases from the old database: phrases=%s',
                    repr(phrases))
                return phrases[:]
            # database is very old, it may still use many columns
            # of type INTEGER for the tabkeys. Therefore, ignore
            # the tabkeys in the database and try to get them
            # from the system database instead.
            phrases = []
            results = db.execute(
                'SELECT phrase, sum(user_freq) '
                + 'FROM phrases GROUP BY phrase;'
            ).fetchall()
            for result in results:
                sqlstr = '''
                SELECT tabkeys FROM main.phrases WHERE phrase = :phrase
                ORDER BY length(tabkeys) DESC;
                '''
                sqlargs = {'phrase': result[0]}
                tabkeys_results = self.db.execute(
                    sqlstr, sqlargs).fetchall()
                if tabkeys_results:
                    phrases.append(
                        (tabkeys_results[0][0], result[0], 0, result[1]))
                else:
                    # No tabkeys for that phrase could not be
                    # found in the system database.  Try to get
                    # tabkeys by calling self.parse_phrase(), that
                    # might return something if the table has
                    # rules to construct user defined phrases:
                    tabkeys = self.parse_phrase(result[0])
                    if tabkeys:
                        # for user defined phrases, the “freq”
                        # column is -1:
                        phrases.append((tabkeys, result[0], -1, result[1]))
            db.close()
            phrases = sorted(
                phrases, key=lambda x: (x[0], x[1], x[2], x[3]))
            LOGGER.debug(
                'Recovered phrases from the very old database: '
                'phrases=%s', repr(phrases))
            return phrases[:]
        except:
            LOGGER.exception('Unexpected error in extract_user_phrases()')
            return []
