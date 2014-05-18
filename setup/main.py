# vim:fileencoding=utf-8:sw=4:et
#
# ibus-table-setup - Setup UI for ibus-table
#
# Copyright (c) 2008-2010 Peng Huang <shawn.p.huang@gmail.com>
# Copyright (c) 2010 BYVoid <byvoid1@gmail.com>
# Copyright (c) 2012 Ma Xiaojun <damage3025@gmail.com>
# Copyright (c) 2012 mozbugbox <mozbugbox@yahoo.com.au>
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

import gettext
import locale
import os
import sys
import signal
import optparse
from time import strftime
import re

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import IBus

import version

sys.path = [sys.path[0]+'/../engine'] + sys.path
import tabsqlitedb

_ = lambda a : gettext.dgettext("ibus-table", a)

OPTION_DEFAULTS = {
    "inputmode": 1,
    "chinesemode": 0,
    "tabdeffullwidthletter": False,
    "tabdeffullwidthpunct": False,
    "endeffullwidthletter": False,
    "endeffullwidthpunct": False,
    "lookuptableorientation": True,
    "lookuptablepagesize": 6,
    "onechar": False,
    "autoselect": False,
    "autocommit": False,
    "spacekeybehavior": False,
}

SCALE_WIDGETS = {
    "lookuptablepagesize",
}

ibus_dir = os.getenv('IBUS_TABLE_LOCATION')
ibus_lib_dir = os.getenv('IBUS_TABLE_LIB_LOCATION')

if not ibus_dir or not os.path.exists(ibus_dir):
    ibus_dir = "/usr/share/ibus-table/"
if not ibus_lib_dir or not os.path.exists(ibus_lib_dir):
    ibus_lib_dir = "/usr/libexec"

db_dir = os.path.join (ibus_dir, 'tables')
icon_dir = os.path.join (ibus_dir, 'icons')
setup_cmd = os.path.join(ibus_lib_dir, "ibus-setup-table")

opt = optparse.OptionParser()
opt.set_usage ('%prog [options]')
opt.add_option('-n', '--engine-name',
        action = 'store',type = 'string', dest = 'engine_name', default = '',
        help = 'Set the name of the engine, for example "table:cangjie3". Default: "%default"')
opt.add_option( '-q', '--no-debug',
        action = 'store_false', dest = 'debug', default = True,
        help = 'redirect stdout and stderr to ~/.ibus/tables/setup-debug.log, default: %default')

(options, args) = opt.parse_args()

if options.debug:
    if not os.access ( os.path.expanduser('~/.ibus/tables/'), os.F_OK):
        os.system ('mkdir -p ~/.ibus/tables')
    logfile = os.path.expanduser('~/.ibus/tables/setup-debug.log')
    sys.stdout = open(logfile, mode='a', buffering=1)
    sys.stderr = open(logfile, mode='a', buffering=1)
    print('--- %s ---' %strftime('%Y-%m-%d: %H:%M:%S'))

class PreferencesDialog:
    def __init__(self):
        locale.setlocale(locale.LC_ALL, "")
        localedir = os.getenv("IBUS_LOCALEDIR")
        gettext.bindtextdomain("ibus-table", localedir)
        gettext.bind_textdomain_codeset("ibus-table", "UTF-8")

        self.__bus = IBus.Bus()
        self.__engine_name = None
        if options.engine_name:
            # If the engine name is specified on the command line, use that:
            self.__engine_name = options.engine_name
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
        if self.__engine_name == None:
            self.__run_message_dialog(
                _("Cannot determine the engine name. Please use the --engine-name option."),
                Gtk.MessageType.ERROR)
            sys.exit(1)

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

    def get_default_options_from_database(self):
        self.tabsqlitedb = tabsqlitedb.tabsqlitedb(
            filename = os.path.join(
                db_dir,
                re.sub(r'^table:', '', self.__engine_name)+'.db'),
            user_db = None,
            create_database = False)
        language_filter = self.tabsqlitedb.ime_properties.get('language_filter')
        if language_filter in ['cm0', 'cm1', 'cm2', 'cm3', 'cm4']:
            OPTION_DEFAULTS['chinesemode'] = int(language_filter[-1])
        def_full_width_punct = self.tabsqlitedb.ime_properties.get('def_full_width_punct')
        if (def_full_width_punct
            and type(def_full_width_punct) == type(u'')
            and def_full_width_punct.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['tabdeffullwidthpunct'] = def_full_width_punct.lower() == u'true'
            OPTION_DEFAULTS['endeffullwidthpunct'] = def_full_width_punct.lower() == u'true'
        def_full_width_letter = self.tabsqlitedb.ime_properties.get('def_full_width_letter')
        if (def_full_width_letter
            and type(def_full_width_letter) == type(u'')
            and def_full_width_letter.lower() in [u'true', u'false']):
            OPTION_DEFAULTS['tabdeffullwidthletter'] = def_full_width_letter.lower() == u'true'
            OPTION_DEFAULTS['endeffullwidthletter'] = def_full_width_letter.lower() == u'true'
        select_keys_csv = self.tabsqlitedb.ime_properties.get('select_keys')
        if select_keys_csv: # select_keys_csv is something like: "1,2,3,4,5,6,7,8,9,0"
            OPTION_DEFAULTS['lookuptablepagesize'] = len(select_keys_csv.split(","))
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
        # if space is a page down key, set the option
        # “spacekeybehavior” to “True”:
        page_down_keys_csv = self.tabsqlitedb.ime_properties.get('page_down_keys')
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

    def _build_combobox_renderer(self, name):
        """setup cell renderer for combobox"""
        __combobox = self.__builder.get_object("combobox%s" % name)
        __cell = Gtk.CellRendererText()
        __combobox.pack_start(__cell, True)
        __combobox.add_attribute(__cell, 'text', 0)

    def load_builder(self):
        """Load builder and __dialog attribute"""
        self.__builder = Gtk.Builder()
        self.__builder.set_translation_domain("ibus-table")
        self.__builder.add_from_file("ibus-table-preferences.ui")
        self.__dialog = self.__builder.get_object("dialog")

        for name in list(OPTION_DEFAULTS.keys()):
            if name not in SCALE_WIDGETS:
                self._build_combobox_renderer(name)

    def do_init(self):
        self.__config = self.__bus.get_config()
        self.__config_section = ("engine/Table/%s" %
                re.sub(r'^table:', '', self.__engine_name).replace(" ", "_"))

        self.__init_general()
        self.__init_about()

    def __init_general(self):
        """Initialize the general notebook page"""
        self.__dialog.set_title(_("IBus Table %s Preferences")
                                %re.sub(r'^table:', '', self.__engine_name))
        self.__values = self.__config.get_values(self.__config_section).unpack()
        self.__config.connect ("value-changed", self.__config_value_changed_cb)

        for name in list(OPTION_DEFAULTS.keys()):
            #self.__config.unset(self.__config_section, name); continue
            if name in SCALE_WIDGETS:
                self._init_hscale(name)
            else:
                self._init_combobox(name)
        return

    def __init_about(self):
        """Initialize the About notebook page"""
        # page About
        self.__name_version = self.__builder.get_object("NameVersion")
        self.__name_version.set_markup(
                "<big><b>IBus Table %s</b></big>" %version.get_version())

        img_fname = os.path.join(icon_dir, "ibus-table.svg")
        if os.path.exists(img_fname):
            img = self.__builder.get_object("image_about")
            img.set_from_file(img_fname)

        # setup table info
        engines = self.__bus.list_engines()
        engine = None
        for e in engines:
            if e.get_name() == self.__engine_name:
                engine = e
                break
        if engine:
            longname = engine.get_longname()
            if not longname:
                longname = engine.get_name()
            w = self.__builder.get_object("TableNameVersion")
            w.set_markup("<b>%s</b>" %longname)
            icon_path = engine.get_icon()
            if icon_path and os.path.exists(icon_path):
                from gi.repository import GdkPixbuf
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path,
                        -1, 32)
                w = self.__builder.get_object("TableNameImage")
                w.set_from_pixbuf(pixbuf)

    def _init_combobox(self, name):
        """Set combobox from the __config engine"""
        __combobox = self.__builder.get_object("combobox%s" % name)
        val = 0
        if name in self.__values:
            init_val = self.__values[name]
        else:
            init_val = OPTION_DEFAULTS[name]
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
        __combobox.connect("changed", self.__changed_cb, name)

    def _init_hscale(self, name):
        """Set scale widget from the __config engine"""
        __hscale = self.__builder.get_object("hscale%s" % name)
        if name in self.__values:
            val = self.__values[name]
        else:
            val = OPTION_DEFAULTS[name]
        __hscale.set_value(val)
        __hscale.connect("value-changed", self.__value_changed_cb, name)

    def __changed_cb(self, widget, name):
        """Combobox changed handler"""
        val = widget.get_active()
        vtype = type(OPTION_DEFAULTS[name])
        if vtype == bool:
            val = False if val == 0 else True
        self.__set_value(name, val)

    def __value_changed_cb(self, widget, name):
        """scale widget value changed handler"""
        val = widget.get_value()
        vtype = type(OPTION_DEFAULTS[name])
        if vtype == int:
            val = int(val)
        self.__set_value(name, val)

    def __config_value_changed_cb(self, config, section, name, val):
        """__config engine value changed handler"""
        val = val.unpack()
        if name in SCALE_WIDGETS:
            __hscale = self.__builder.get_object("hscale%s" % name)
            __hscale.set_value(val)
        else:
            __combobox = self.__builder.get_object("combobox%s" % name)
            if isinstance(val, bool):
                val = 1 if val else 0
            elif isinstance(val, str):
                val = val.get_string()
                model = __combobox.get_model()
                for i, row in enumerate(model):
                    if row[0] == val:
                        val = i
                        break
            __combobox.set_active(val)
        self.__values[name] = val

    def __toggled_cb(self, widget, name):
        """toggle button toggled signal handler"""
        self.__set_value(name, widget.get_active ())

    def __get_value(self, name, defval):
        """Get the __config value if available"""
        if name in self.__values:
            var = self.__values[name]
            if isinstance(defval, type(var)):
                return var
        self.__set_value(name, defval)
        return defval

    def __set_value(self, name, val):
        """Set the config value to __config"""
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

        self.__values[name] = val
        self.__config.set_value(self.__config_section, name, var)

    def __run_message_dialog(self, message, type=Gtk.MessageType.INFO):
        dlg = Gtk.MessageDialog(parent=None,
                                flags=Gtk.DialogFlags.MODAL,
                                message_type=type,
                                buttons=Gtk.ButtonsType.OK,
                                message_format=message)
        dlg.run()
        dlg.destroy()

    def run(self):
        ret = self.check_table_available()
        if not ret:
            return 0
        self.get_default_options_from_database()
        GLib.idle_add(self.do_init)
        self.load_builder()
        return self.__dialog.run()


def main():
    PreferencesDialog().run()

if __name__ == "__main__":
    # Workaround for
    # https://bugzilla.gnome.org/show_bug.cgi?id=622084
    # Bug 622084 - Ctrl+C does not exit gtk app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
