# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2015, 2021-2022 Mike FABIAN <mfabian@redhat.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from typing import Any
from typing import Union
import os
import re
import sys
import argparse
from signal import signal, SIGTERM, SIGINT
import logging
import logging.handlers

from gi import require_version # type: ignore
require_version('IBus', '1.0')
from gi.repository import IBus # type: ignore
from gi.repository import GLib

import tabsqlitedb
import ibus_table_location

LOGGER = logging.getLogger('ibus-table')

DEBUG_LEVEL = int(0)
try:
    DEBUG_LEVEL = int(str(os.getenv('IBUS_TABLE_DEBUG_LEVEL')))
except (TypeError, ValueError):
    DEBUG_LEVEL = int(0)

DB_DIR = os.path.join(ibus_table_location.data(), 'tables')
BYO_DB_DIR = os.path.join(ibus_table_location.data_home(), "byo-tables")
ICON_DIR = os.path.join(ibus_table_location.data(), 'icons')
SETUP_CMD = os.path.join(ibus_table_location.lib(), "ibus-setup-table")
LOGFILE = os.path.join(ibus_table_location.cache_home(), 'debug.log')

def parse_args() -> Any:
    '''Parse the command line arguments'''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--table', '-t',
        action='store',
        type=str,
        dest='db',
        default='',
        help='Set the IME table file, default: %(default)s')
    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        dest='daemon',
        default=False,
        help='Run as daemon, default: %(default)s')
    parser.add_argument(
        '--ibus', '-i',
        action='store_true',
        dest='ibus',
        default=False,
        help='Set the IME icon file, default: %(default)s')
    parser.add_argument(
        '--xml', '-x',
        action='store_true',
        dest='xml',
        default=False,
        help='output the engines xml part, default: %(default)s')
    parser.add_argument(
        '--no-debug', '-n',
        action='store_false',
        dest='debug',
        default=True,
        help='Write log file to ' + LOGFILE + ', default: %(default)s')
    parser.add_argument(
        '--profile', '-p',
        action='store_true',
        dest='profile',
        default=False,
        help=('Print profiling information into the debug log. '
              'Works only when --no-debug is not used. '
              'default: %(default)s'))
    return parser.parse_args()

_ARGS = parse_args()

if _ARGS.profile:
    import cProfile
    import pstats
    import io
    _PROFILE = cProfile.Profile()

if  _ARGS.xml:
    from locale import getdefaultlocale
    from xml.etree.ElementTree import Element, SubElement, tostring
else:
    # Avoid importing factory when the --xml option is used because
    # factory imports other stuff which imports Gtk and that needs a
    # display.
    #
    # But by moving the import of factory here, it is possible to
    # use the --xml option in an environment where there is no
    # display without getting an error message like this:
    #
    #    $ env -u DISPLAY python3 main.py --xml
    #    Unable to init server: Could not connect: Connection refused
    #
    # The --xml option is used by “ibus write-cache” which is used
    # during rpm updates and then there is often no display and
    # the above error message appears.
    #
    # See: https://bugzilla.redhat.com/show_bug.cgi?id=1955283
    import factory

class IMApp:
    def __init__(self, dbfile: str, exec_by_ibus: bool) -> None:
        if DEBUG_LEVEL > 1:
            LOGGER.debug('IMApp.__init__(exec_by_ibus=%s)\n', exec_by_ibus)
        self.__mainloop = GLib.MainLoop()
        self.__bus: IBus.Bus = IBus.Bus()
        self.__bus.connect("disconnected", self.__bus_destroy_cb)
        self.__factory = factory.EngineFactory(self.__bus, dbfile)
        self.destroyed = False
        if exec_by_ibus:
            self.__bus.request_name("org.freedesktop.IBus.Table", 0)
        else:
            self.__component = IBus.Component(
                name='org.freedesktop.IBus.Table',
                description='Table Component',
                version='0.1.0',
                license='GPL',
                author='Yuwei Yu <acevery@gmail.com>',
                homepage='http://code.google.com/p/ibus/',
                textdomain='ibus-table')
            # now we get IME info from self.__factory.db
            engine_name = ''
            name = ''
            longname = ''
            description = ''
            language = 'en'
            credit = ''
            author = ''
            icon = ''
            layout = 'us'
            symbol = ''
            if self.__factory.db:
                engine_name = os.path.basename(
                    self.__factory.db.filename).replace('.db', '')
                name = 'table:'+engine_name
                longname = self.__factory.db.ime_properties.get("name")
                description = self.__factory.db.ime_properties.get(
                    "description")
                language = self.__factory.db.ime_properties.get("languages")
                credit = self.__factory.db.ime_properties.get("credit")
                author = self.__factory.db.ime_properties.get("author")
                icon = self.__factory.db.ime_properties.get("icon")
                layout = self.__factory.db.ime_properties.get("layout")
                symbol = self.__factory.db.ime_properties.get("symbol")
            if icon:
                icon = os.path.join(ICON_DIR, icon)
                if not os.access(icon, os.F_OK):
                    icon = ''
            setup_arg = "{} --engine-name {}".format(SETUP_CMD, name)
            engine = IBus.EngineDesc(name=name,
                                     longname=longname,
                                     description=description,
                                     language=language,
                                     license=credit,
                                     author=author,
                                     icon=icon,
                                     layout=layout,
                                     symbol=symbol,
                                     setupdsis=setup_arg)
            self.__component.add_engine(engine)
            self.__bus.register_component(self.__component)


    def run(self) -> None:
        if DEBUG_LEVEL > 1:
            LOGGER.debug('IMApp.run()\n')
        if _ARGS.profile:
            _PROFILE.enable()
        self.__mainloop.run()
        self.__bus_destroy_cb()

    def quit(self) -> None:
        if DEBUG_LEVEL > 1:
            LOGGER.debug('IMApp.quit()\n')
        self.__bus_destroy_cb()

    def __bus_destroy_cb(self, bus: Any = None) -> None:
        if DEBUG_LEVEL > 1:
            LOGGER.debug('IMApp.__bus_destroy_cb(bus=%s)\n', bus)
        if self.destroyed:
            return
        LOGGER.info('finalizing:)')
        self.__factory.do_destroy()
        self.destroyed = True
        self.__mainloop.quit()
        if _ARGS.profile:
            _PROFILE.disable()
            stats_stream = io.StringIO()
            stats = pstats.Stats(_PROFILE, stream=stats_stream)
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats('main', 25)
            stats.print_stats('factory', 25)
            stats.print_stats('tabsqlite', 25)
            stats.print_stats('table', 25)
            LOGGER.info('Profiling info:\n%s', stats_stream.getvalue())

def cleanup(ima_ins: IMApp) -> None:
    ima_ins.quit()
    sys.exit()

def indent(element: Any, level: int = 0) -> None:
    '''Use to format xml Element pretty :)'''
    i = "\n" + level*"    "
    if element:
        if not element.text or not element.text.strip():
            element.text = i + "    "
        for subelement in element:
            indent(subelement, level+1)
            if not subelement.tail or not subelement.tail.strip():
                subelement.tail = i + "    "
        if not subelement.tail or not subelement.tail.strip():
            subelement.tail = i
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = i

def write_xml() -> None:
    '''
    Writes the XML to describe the engine(s) to standard output.
    '''
    # 1. we find all dbs in DB_DIR and extract the infos into
    #    Elements
    dbs = os.listdir(DB_DIR)
    dbs = list(filter(lambda x: x.endswith('.db'), dbs))

    _all_dbs = []
    for _db in dbs:
        _all_dbs.append(os.path.join(DB_DIR, _db))
    try:
        byo_dbs = os.listdir(BYO_DB_DIR)
        byo_dbs = list(filter(lambda x: x.endswith('.db'), byo_dbs))
        for _db in byo_dbs:
            _all_dbs.append(os.path.join(BYO_DB_DIR, _db))
    except OSError:
        # BYO_DB_DIR does not exist or is not accessible
        pass

    egs = Element('engines')
    for _db in _all_dbs:
        _sq_db = tabsqlitedb.TabSqliteDb(_db, user_db='')
        _engine = SubElement(egs, 'engine')

        _name = SubElement(_engine, 'name')
        engine_name = os.path.basename(_db).replace('.db', '')
        _name.text = 'table:'+engine_name
        setup_arg = "{} --engine-name {}".format(SETUP_CMD, _name.text)

        _longname = SubElement(_engine, 'longname')
        _longname.text = ''
        # getdefaultlocale() returns something like ('ja_JP', 'UTF-8').
        # In case of C/POSIX locale it returns (None, None)
        _locale = getdefaultlocale()[0]
        if _locale:
            _locale = _locale.lower()
        else:
            _locale = 'en'
        _longname.text = _sq_db.ime_properties.get(
            '.'.join(['name', _locale]))
        if not _longname.text:
            _longname.text = _sq_db.ime_properties.get(
                '.'.join(['name', _locale.split('_')[0]]))
        if not _longname.text:
            _longname.text = _sq_db.ime_properties.get('name')
        if not _longname.text:
            _longname.text = engine_name

        _language = SubElement(_engine, 'language')
        _languages = _sq_db.ime_properties.get('languages')
        if _languages:
            _langs = _languages.split(',')
            if len(_langs) == 1:
                _language.text = _langs[0].strip()
            else:
                # we ignore the place
                _language.text = _langs[0].strip().split('_')[0]

        _license = SubElement(_engine, 'license')
        _license.text = _sq_db.ime_properties.get('license')

        _author = SubElement(_engine, 'author')
        _author.text = _sq_db.ime_properties.get('author')

        _icon = SubElement(_engine, 'icon')
        _icon_basename = _sq_db.ime_properties.get('icon')
        if _icon_basename:
            _icon.text = os.path.join(ICON_DIR, _icon_basename)

        _layout = SubElement(_engine, 'layout')
        _layout.text = _sq_db.ime_properties.get('layout')

        _symbol = SubElement(_engine, 'symbol')
        _symbol.text = _sq_db.ime_properties.get('symbol')

        _desc = SubElement(_engine, 'description')
        _desc.text = _sq_db.ime_properties.get('description')

        _setup = SubElement(_engine, 'setup')
        _setup.text = setup_arg

        _icon_prop_key = SubElement(_engine, 'icon_prop_key')
        _icon_prop_key.text = 'InputMode'

    # now format the xmlout pretty
    indent(egs)
    egsout = tostring(egs, encoding='utf8').decode('utf-8')
    patt = re.compile(r'<\?.*\?>\n')
    egsout = patt.sub('', egsout)
    # Always write xml output in UTF-8 encoding, not in the
    # encoding of the current locale, otherwise it might fail
    # if conversion into the encoding of the current locale is
    # not possible:
    sys.stdout.buffer.write((egsout+'\n').encode('utf-8'))

def main() -> None:
    '''Main program'''
    if _ARGS.xml:
        write_xml()
        return

    log_handler: Union[
        logging.NullHandler, logging.handlers.TimedRotatingFileHandler] = (
            logging.NullHandler())
    if _ARGS.debug:
        log_handler = logging.handlers.TimedRotatingFileHandler(
            LOGFILE,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='UTF-8',
            delay=False,
            utc=False,
            atTime=None)
    log_formatter = logging.Formatter(
        '%(asctime)s %(filename)s '
        'line %(lineno)d %(funcName)s %(levelname)s: '
        '%(message)s')
    log_handler.setFormatter(log_formatter)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(log_handler)
    LOGGER.info('********** STARTING **********')

    if _ARGS.daemon:
        if os.fork():
            sys.exit()
    if _ARGS.db:
        if os.access(_ARGS.db, os.F_OK):
            db = _ARGS.db
        else:
            db = '%s%s%s' % (DB_DIR,
                             os.path.sep,
                             os.path.basename(_ARGS.db))
    else:
        db = ""
    ima = IMApp(db, _ARGS.ibus)
    signal(SIGTERM, lambda signum, stack_frame: cleanup(ima))
    signal(SIGINT, lambda signum, stack_frame: cleanup(ima))
    try:
        ima.run()
    except KeyboardInterrupt:
        ima.quit()

if __name__ == "__main__":
    main()
