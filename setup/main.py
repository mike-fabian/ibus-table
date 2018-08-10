# vim:fileencoding=utf-8:sw=4:et
#
# ibus-table-setup - Setup UI for ibus-table
#
# Copyright (c) 2008-2010 Peng Huang <shawn.p.huang@gmail.com>
# Copyright (c) 2010 BYVoid <byvoid1@gmail.com>
# Copyright (c) 2012 Ma Xiaojun <damage3025@gmail.com>
# Copyright (c) 2012 mozbugbox <mozbugbox@yahoo.com.au>
# Copyright (c) 2014-2018 Mike FABIAN <mfabian@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

'''
The setup tool for ibus-table.
'''

import gettext
import locale
import os
import sys
import signal
import optparse
from time import strftime
import re

from gi import require_version
require_version('Gio', '2.0')
from gi.repository import Gio
require_version('GLib', '2.0')
from gi.repository import GLib

# set_prgname before importing other modules to show the name in warning
# messages when import modules are failed. E.g. Gtk.
GLib.set_application_name('IBus Table Preferences')
# This makes gnome-shell load the .desktop file when running under Wayland:
GLib.set_prgname('ibus-setup-table')

require_version('Gtk', '3.0')
from gi.repository import Gtk
require_version('IBus', '1.0')
from gi.repository import IBus

import version

sys.path = [sys.path[0]+'/../engine'] + sys.path
import tabsqlitedb
import ibus_table_location
import it_util

_ = lambda a: gettext.dgettext("ibus-table", a)

# The contents this OPTION_DEFAULTS dict are first overwritten
# with the defaults from the Gsettings schema file and then again with
# the defaults from the tables.

OPTION_DEFAULTS = {
    "inputmode": 1,
    "chinesemode": 4,
    "tabdeffullwidthletter": False,
    "tabdeffullwidthpunct": False,
    "endeffullwidthletter": False,
    "endeffullwidthpunct": False,
    "alwaysshowlookup": True,
    "lookuptableorientation": 1, # 0 = horizontal, 1 = vertical, 2 = system
    "lookuptablepagesize": 6,
    "onechar": False,
    "autoselect": False,
    "autocommit": False,
    "spacekeybehavior": False,
    "autowildcard": True,
    "singlewildcardchar": u'',
    "multiwildcardchar": u'',
}

SCALE_WIDGETS = {
    "lookuptablepagesize",
}

ENTRY_WIDGETS = {
    "singlewildcardchar",
    "multiwildcardchar",
}

DB_DIR = os.path.join(ibus_table_location.data(), 'tables')
ICON_DIR = os.path.join(ibus_table_location.data(), 'icons')
LOGFILE = os.path.join(ibus_table_location.cache_home(), 'setup-debug.log')

_OPTION_PARSER = optparse.OptionParser()
_OPTION_PARSER.set_usage('%prog [options]')
_OPTION_PARSER.add_option(
    '-n', '--engine-name',
    action='store',
    type='string',
    dest='engine_name',
    default='',
    help=('Set the name of the engine, for example "table:cangjie3". '
          + 'Default: "%default"'))
_OPTION_PARSER.add_option(
    '-q', '--no-debug',
    action='store_false',
    dest='debug',
    default=True,
    help=('redirect stdout and stderr to '
          + LOGFILE + ', default: %default'))

(_OPTIONS, _ARGS) = _OPTION_PARSER.parse_args()

if _OPTIONS.debug:
    sys.stdout = open(LOGFILE, mode='a', buffering=1)
    sys.stderr = open(LOGFILE, mode='a', buffering=1)
    print('--- %s ---' %strftime('%Y-%m-%d: %H:%M:%S'))

class PreferencesDialog:
    '''
    The setup dialog of ibus-table.
    '''
    def __init__(self):
        locale.setlocale(locale.LC_ALL, "")
        localedir = os.getenv("IBUS_LOCALEDIR")
        gettext.bindtextdomain("ibus-table", localedir)
        gettext.bind_textdomain_codeset("ibus-table", "UTF-8")

        self.__bus = IBus.Bus()
        self.__engine_name = None
        if _OPTIONS.engine_name:
            # If the engine name is specified on the command line, use that:
            self.__engine_name = _OPTIONS.engine_name
        else:
            # If the engine name is not specified on the command line,
            # try to get it from the environment. This is necessary
            # in gnome-shell on Fedora 18,19,20,... because the setup tool is
            # called without command line options there but the
            # environment variable IBUS_ENGINE_NAME is set:
            if 'IBUS_ENGINE_NAME' in os.environ:
                self.__engine_name = os.environ['IBUS_ENGINE_NAME']
            else:
                self.__run_message_dialog(
                    _("IBUS_ENGINE_NAME environment variable is not set."),
                    Gtk.MessageType.WARNING)
        if self.__engine_name is None:
            self.__run_message_dialog(
                _("Cannot determine the engine name. Please use the --engine-name option."),
                Gtk.MessageType.ERROR)
            sys.exit(1)
        short_engine_name = re.sub(
            r'^table:', '', self.__engine_name).replace(" ", "_")
        self.__gsettings = Gio.Settings(
            schema='org.freedesktop.ibus.engine.table',
            path='/org/freedesktop/ibus/engine/table/%s/' %short_engine_name)
        self.__gsettings.connect('changed', self.on_gsettings_value_changed)

    def check_table_available(self):
        """Check if the current engine_name is available.
        Return bool"""
        names = self.__bus.list_engines()
        names = [x.get_name() for x in names]
        ret = True

        if self.__engine_name not in names:
            ret = False
            self.__run_message_dialog(
                _('IBus Table engine %s is not available') %self.__engine_name,
                Gtk.MessageType.ERROR)
        return ret

    def get_default_options_from_gsettings(self):
        '''
        Get the default options from the Gsettings schema file.
        '''
        for key in OPTION_DEFAULTS:
            OPTION_DEFAULTS[key] = it_util.variant_to_value(
                self.__gsettings.get_value(key))

    def get_default_options_from_database(self):
        '''
        If there are default options in the database,
        they override the defaults from Gsettings.
        '''
        self.tabsqlitedb = tabsqlitedb.TabSqliteDb(
            filename=os.path.join(
                DB_DIR,
                re.sub(r'^table:', '', self.__engine_name)+'.db'),
            user_db=None,
            create_database=False)
        self.__is_chinese = False
        self.__is_cjk = False
        languages = self.tabsqlitedb.ime_properties.get('languages')
        if languages:
            languages = languages.split(',')
            for language in languages:
                if language.strip().startswith('zh'):
                    self.__is_chinese = True
                for lang in ['zh', 'ja', 'ko']:
                    if language.strip().startswith(lang):
                        self.__is_cjk = True
        self.__user_can_define_phrase = False
        user_can_define_phrase = self.tabsqlitedb.ime_properties.get(
            'user_can-define_phrase')
        if user_can_define_phrase:
            self.__user_can_define_phrase = (
                user_can_define_phrase.lower() == u'true')
        self.__rules = self.tabsqlitedb.ime_properties.get('rules')
        language_filter = self.tabsqlitedb.ime_properties.get(
            'language_filter')
        if language_filter in ('cm0', 'cm1', 'cm2', 'cm3', 'cm4'):
            OPTION_DEFAULTS['chinesemode'] = int(language_filter[-1])
        def_full_width_punct = self.tabsqlitedb.ime_properties.get(
            'def_full_width_punct')
        if (def_full_width_punct
                and type(def_full_width_punct) == type(u'')
                and def_full_width_punct.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['tabdeffullwidthpunct'] = (
                def_full_width_punct.lower() == u'true')
            OPTION_DEFAULTS['endeffullwidthpunct'] = (
                def_full_width_punct.lower() == u'true')
        def_full_width_letter = self.tabsqlitedb.ime_properties.get(
            'def_full_width_letter')
        if (def_full_width_letter
                and type(def_full_width_letter) == type(u'')
                and def_full_width_letter.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['tabdeffullwidthletter'] = (
                def_full_width_letter.lower() == u'true')
            OPTION_DEFAULTS['endeffullwidthletter'] = (
                def_full_width_letter.lower() == u'true')
        always_show_lookup = self.tabsqlitedb.ime_properties.get(
            'always_show_lookup')
        if (always_show_lookup
                and type(always_show_lookup) == type(u'')
                and always_show_lookup.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['alwaysshowlookup'] = (
                always_show_lookup.lower() == u'true')
        select_keys_csv = self.tabsqlitedb.ime_properties.get('select_keys')
        if select_keys_csv:
            # select_keys_csv is something like: "1,2,3,4,5,6,7,8,9,0"
            OPTION_DEFAULTS['lookuptablepagesize'] = len(
                select_keys_csv.split(","))
        auto_select = self.tabsqlitedb.ime_properties.get('auto_select')
        if (auto_select
                and type(auto_select) == type(u'')
                and auto_select.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['autoselect'] = auto_select.lower() == u'true'
        auto_commit = self.tabsqlitedb.ime_properties.get('auto_commit')
        if (auto_commit
                and type(auto_commit) == type(u'')
                and auto_commit.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['autocommit'] = auto_commit.lower() == u'true'
        orientation = self.tabsqlitedb.get_orientation()
        OPTION_DEFAULTS['lookuptableorientation'] = orientation
        # if space is a page down key, set the option
        # “spacekeybehavior” to “True”:
        page_down_keys_csv = self.tabsqlitedb.ime_properties.get(
            'page_down_keys')
        if page_down_keys_csv:
            self._page_down_keys = [
                IBus.keyval_from_name(x)
                for x in page_down_keys_csv.split(',')]
        if IBus.KEY_space in self._page_down_keys:
            OPTION_DEFAULTS['spacekeybehavior'] = True
        # if space is a commit key, set the option
        # “spacekeybehavior” to “False” (overrides if space is
        # also a page down key):
        commit_keys_csv = self.tabsqlitedb.ime_properties.get('commit_keys')
        if commit_keys_csv:
            self._commit_keys = [
                IBus.keyval_from_name(x)
                for x in commit_keys_csv.split(',')]
        if IBus.KEY_space in self._commit_keys:
            OPTION_DEFAULTS['spacekeybehavior'] = False
        auto_wildcard = self.tabsqlitedb.ime_properties.get('auto_wildcard')
        if (auto_wildcard
                and type(auto_wildcard) == type(u'')
                and auto_wildcard.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['autowildcard'] = auto_wildcard.lower() == u'true'
        single_wildcard_char = self.tabsqlitedb.ime_properties.get(
            'single_wildcard_char')
        if (single_wildcard_char
                and type(single_wildcard_char) == type(u'')):
            if len(single_wildcard_char) > 1:
                single_wildcard_char = single_wildcard_char[0]
            OPTION_DEFAULTS['singlewildcardchar'] = single_wildcard_char
        multi_wildcard_char = self.tabsqlitedb.ime_properties.get(
            'multi_wildcard_char')
        if (multi_wildcard_char
                and type(multi_wildcard_char) == type(u'')):
            if len(multi_wildcard_char) > 1:
                multi_wildcard_char = multi_wildcard_char[0]
            OPTION_DEFAULTS['multiwildcardchar'] = multi_wildcard_char

    def __restore_defaults(self):
        '''
        Restore defaults as specified in the database for this engine.
        '''
        for key in OPTION_DEFAULTS:
            value = OPTION_DEFAULTS[key]
            self.__set_value(key, value)

    def _build_combobox_renderer(self, key):
        """setup cell renderer for combobox"""
        __combobox = self.__builder.get_object("combobox%s" % key)
        __cell = Gtk.CellRendererText()
        __combobox.pack_start(__cell, True)
        __combobox.add_attribute(__cell, 'text', 0)

    def load_builder(self):
        """Load builder and __dialog attribute"""
        self.__builder = Gtk.Builder()
        self.__builder.set_translation_domain("ibus-table")
        self.__builder.add_from_file("ibus-table-preferences.ui")
        self.__dialog = self.__builder.get_object("dialog")

        for key in list(OPTION_DEFAULTS.keys()):
            if key not in SCALE_WIDGETS and key not in ENTRY_WIDGETS:
                self._build_combobox_renderer(key)

    def do_init(self):
        '''
        Initialize the setup dialog.
        '''
        self.__init_general()
        self.__init_about()

    def __init_general(self):
        """Initialize the general notebook page"""
        self.__dialog.set_title(_("IBus Table %s Preferences")
                                %re.sub(r'^table:', '', self.__engine_name))
        # https://tronche.com/gui/x/icccm/sec-4.html#WM_CLASS
        # gnome-shell seems to use the first argument of set_wmclass()
        # to find the .desktop file.  If the .desktop file can be
        # found, the name shown by gnome-shell in the top bar comes
        # from that .desktop file and the icon to show is also read
        # from that .desktop file. If the .desktop file cannot be
        # found, the second argument of set_wmclass() is shown by
        # gnome-shell in the top bar.
        self.__dialog.set_wmclass('ibus-setup-table', 'IBus Table Setup')

        self.__user_values = {}
        for key in OPTION_DEFAULTS:
            if self.__gsettings.get_user_value(key) != None:
                self.__user_values[key] = it_util.variant_to_value(
                    self.__gsettings.get_user_value(key))
                sys.stderr.write(
                    'self.__user_values[%s]=%s\n'
                    %(key, self.__user_values[key]))
            if key in SCALE_WIDGETS:
                self._init_hscale(key)
            elif key in ENTRY_WIDGETS:
                self._init_entry(key)
            else:
                self._init_combobox(key)
        self._init_button('restoredefaults')
        return

    def __init_about(self):
        '''
        Initialize the About notebook page
        '''
        self.__name_version = self.__builder.get_object("NameVersion")
        self.__name_version.set_markup(
            "<big><b>IBus Table %s</b></big>" %version.get_version())

        img_fname = os.path.join(ICON_DIR, "ibus-table.svg")
        if os.path.exists(img_fname):
            img = self.__builder.get_object("image_about")
            img.set_from_file(img_fname)

        # setup table info
        our_engine = None
        for engine in self.__bus.list_engines():
            if engine.get_name() == self.__engine_name:
                our_engine = engine
                break
        if our_engine:
            longname = our_engine.get_longname()
            if not longname:
                longname = our_engine.get_name()
            label = self.__builder.get_object("TableNameVersion")
            label.set_markup("<b>%s</b>" %longname)
            icon_path = our_engine.get_icon()
            if icon_path and os.path.exists(icon_path):
                from gi.repository import GdkPixbuf
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                    icon_path, -1, 32)
                image = self.__builder.get_object("TableNameImage")
                image.set_from_pixbuf(pixbuf)

    def _init_combobox(self, key):
        """Set combobox from the Gsettings"""
        __combobox = self.__builder.get_object("combobox%s" % key)
        val = 0
        if key in self.__user_values:
            init_val = self.__user_values[key]
        else:
            init_val = OPTION_DEFAULTS[key]
        if isinstance(init_val, bool):
            val = 1 if init_val else 0
        elif isinstance(init_val, int):
            val = init_val
        elif isinstance(init_val, str):
            model = __combobox.get_model()
            for i, row in enumerate(model):
                if row[0] == init_val:
                    val = i
                    break
        __combobox.set_active(val)
        __combobox.connect("changed", self.__changed_cb, key)
        if ((key in ['chinesemode']
             and not self.__is_chinese)
                or
                (key in ['tabdeffullwidthletter',
                         'tabdeffullwidthpunct',
                         'endeffullwidthletter',
                         'endeffullwidthpunct']
                 and not self.__is_cjk)
                or
                (key in ['onechar']
                 and not  self.__is_cjk)
                or
                (key in ['autocommit']
                 and (not self.__user_can_define_phrase or not self.__rules))):
            __combobox.set_button_sensitivity(Gtk.SensitivityType.OFF)

    def _init_entry(self, key):
        """Set entry widget from the Gsettings engine"""
        __entry = self.__builder.get_object("entry%s" % key)
        if key in self.__user_values:
            val = self.__user_values[key]
        else:
            val = OPTION_DEFAULTS[key]
        __entry.set_text(val)
        __entry.connect("notify::text", self.__entry_changed_cb, key)

    def _init_hscale(self, key):
        """Set scale widget from Gsettings"""
        __hscale = self.__builder.get_object("hscale%s" % key)
        if key in self.__user_values:
            val = self.__user_values[key]
        else:
            val = OPTION_DEFAULTS[key]
        __hscale.set_value(val)
        __hscale.connect("value-changed", self.__value_changed_cb, key)

    def _init_button(self, key):
        """Initialize the button to restore the default settings"""
        __button = self.__builder.get_object("button%s" %key)
        __button.connect("clicked", self.__button_clicked_cb, key)

    def __button_clicked_cb(self, widget, key):
        """Button clicked handler"""
        if key == 'restoredefaults':
            self.__restore_defaults()

    def __changed_cb(self, widget, key):
        """Combobox changed handler"""
        val = widget.get_active()
        vtype = type(OPTION_DEFAULTS[key])
        if vtype == bool:
            val = False if val == 0 else True
        self.__set_value(key, val)

    def __value_changed_cb(self, widget, key):
        """scale widget value changed handler"""
        val = widget.get_value()
        vtype = type(OPTION_DEFAULTS[key])
        if vtype == int:
            val = int(val)
        self.__set_value(key, val)

    def __entry_changed_cb(self, widget, property_spec, key):
        """entry widget text changed handler"""
        val = widget.get_text()
        vtype = type(OPTION_DEFAULTS[key])
        if vtype != type(u''):
            val = val.decode('UTF-8')
        self.__set_value(key, val)

    def on_gsettings_value_changed(self, _settings, key):
        """
        Called when a value in the settings has been changed.
        """
        value = it_util.variant_to_value(self.__gsettings.get_value(key))
        sys.stderr.write('Settings changed: key=%s value=%s\n' %(key, value))
        if key in SCALE_WIDGETS:
            __hscale = self.__builder.get_object("hscale%s" % key)
            __hscale.set_value(value)
        elif key in ENTRY_WIDGETS:
            __entry = self.__builder.get_object("entry%s" % key)
            __entry.set_text(value)
        else:
            __combobox = self.__builder.get_object("combobox%s" % key)
            if isinstance(value, bool):
                value = 1 if value else 0
            elif isinstance(value, str):
                model = __combobox.get_model()
                for i, row in enumerate(model):
                    if row[0] == value:
                        value = i
                        break
            __combobox.set_active(value)
        self.__user_values[key] = value

    def __toggled_cb(self, widget, key):
        """toggle button toggled signal handler"""
        self.__set_value(key, widget.get_active())

    def __set_value(self, key, val):
        """Set the _gsettings value"""
        var = None
        if isinstance(val, bool):
            var = GLib.Variant.new_boolean(val)
        elif isinstance(val, int):
            var = GLib.Variant.new_int32(val)
        elif isinstance(val, str):
            var = GLib.Variant.new_string(val)
        else:
            sys.stderr.write("val(%s) is not in support type." %repr(val))
            return

        self.__user_values[key] = val
        self.__gsettings.set_value(key, var)

    def __run_message_dialog(self, message, message_type=Gtk.MessageType.INFO):
        '''
        Pop up a message dialog.
        '''
        dlg = Gtk.MessageDialog(parent=None,
                                flags=Gtk.DialogFlags.MODAL,
                                message_type=message_type,
                                buttons=Gtk.ButtonsType.OK,
                                message_format=message)
        dlg.run()
        dlg.destroy()

    def run(self):
        '''
        Run the setup dialog.
        '''
        ret = self.check_table_available()
        if not ret:
            return 0
        self.load_builder()
        self.get_default_options_from_gsettings()
        self.get_default_options_from_database()
        self.do_init()
        return self.__dialog.run()


def main():
    '''
    Main function to run  the setup dialog.
    '''
    PreferencesDialog().run()

if __name__ == "__main__":
    # Workaround for
    # https://bugzilla.gnome.org/show_bug.cgi?id=622084
    # Bug 622084 - Ctrl+C does not exit gtk app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
