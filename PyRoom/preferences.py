# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# PyRoom - A clone of WriteRoom
# Copyright (c) 2007 Nicolas P. Rougier & NoWhereMan
# Copyright (c) 2008 The Pyroom Team - See AUTHORS file for more information
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

"""
allows for custom set preferences

Creates a preferences UI that allows the user to customise settings; allows for
the choice of a theme from $XDG_DATA_HOME/pyroom/themes as well as a custom
theme created via the dialog
"""

import gtk
import gtk.glade
import os

from gui import Theme
from pyroom_error import PyroomError
from globals import state, config
from utils import get_themes_list, FailsafeConfigParser

class Preferences(object):
    """our main preferences object, to be passed around where needed"""
    def __init__(self, gui):
        self.graphical = gui
        self.wTree = gtk.glade.XML(os.path.join(
            state['absolute_path'], "interface.glade"),
            "dialog-preferences")

        # Defining widgets needed
        self.window = self.wTree.get_widget("dialog-preferences")
        self.colorpreference = self.wTree.get_widget("colorbutton")
        self.textboxbgpreference = self.wTree.get_widget("textboxbgbutton")
        self.bgpreference = self.wTree.get_widget("bgbutton")
        self.borderpreference = self.wTree.get_widget("borderbutton")
        self.paddingpreference = self.wTree.get_widget("paddingtext")
        self.heightpreference = self.wTree.get_widget("heighttext")
        self.heightpreference.set_range(5, 95)
        self.widthpreference = self.wTree.get_widget("widthtext")
        self.widthpreference.set_range(5, 95)
        self.presetscombobox = self.wTree.get_widget("presetscombobox")
        self.showborderbutton = self.wTree.get_widget("showborder")
        self.autosave = self.wTree.get_widget("autosavetext")
        self.autosave_spinbutton = self.wTree.get_widget("autosavetime")
        self.linespacing_spinbutton = self.wTree.get_widget("linespacing")
        self.indent_check = self.wTree.get_widget("indent_check")
        if config.get('visual', 'indent') == '1':
            self.indent_check.set_active(True)
        self.save_custom_button = self.wTree.get_widget("save_custom_theme")
        self.custom_font_preference = self.wTree.get_widget("fontbutton1")
        if not config.get('visual', 'use_font_type') == 'custom':
            self.custom_font_preference.set_sensitive(False)
        self.font_radios = {
            'document':self.wTree.get_widget("radio_document_font"),
            'monospace':self.wTree.get_widget("radio_monospace_font"),
            'custom':self.wTree.get_widget("radio_custom_font")
        }
        for widget in self.font_radios.values():
            if not widget.get_name() == 'radio_custom_font':
                widget.set_sensitive(bool(state['gnome_fonts']))

        # Setting up config parser
        self.customfile = FailsafeConfigParser()
        self.customfile.read(os.path.join(
            state['themes_dir'], 'custom.theme')
        )
        if not self.customfile.has_section('theme'):
            self.customfile.add_section('theme')

        # Getting preferences from conf file
        active_style = config.get("visual", "theme")
        self.autosave.set_active(config.getint('editor', 'autosave'))

        # Set up pyroom from conf file
        self.linespacing_spinbutton.set_value(int(
            config.get('visual', 'linespacing')
        ))
        self.autosave_spinbutton.set_value(float(
            config.get('editor', 'autosavetime')))
        self.showborderbutton.set_active(
                config.getint('visual', 'showborder')
        )
        font_type = config.get('visual', 'use_font_type')
        self.font_radios[font_type].set_active(True)
        
        self.toggleautosave(self.autosave)

        self.window.set_transient_for(self.graphical.window)

        self.stylesvalues = {'custom': 0}
        startingvalue = 1

        self.graphical.theme = Theme(config.get('visual', 'theme'))
        # Add themes to combobox
        for i in get_themes_list():
            self.stylesvalues['%s' % (i)] = startingvalue
            startingvalue += 1
            current_loading_theme = Theme(i)
            theme_name = current_loading_theme['name']
            self.presetscombobox.append_text(theme_name)
        if active_style == 'custom':
            self.save_custom_button.set_sensitive(True)
        self.presetscombobox.set_active(self.stylesvalues[active_style])
        self.fill_pref_dialog()

        # Connecting interface's signals
        dic = {
                "on_MainWindow_destroy": self.QuitEvent,
                "on_button-ok_clicked": self.set_preferences,
                "on_button-close_clicked": self.kill_preferences,
                "on_close": self.kill_preferences
                }
        self.wTree.signal_autoconnect(dic)
        self.showborderbutton.connect('toggled', self.toggleborder)
        self.autosave.connect('toggled', self.toggleautosave)
        self.autosave_spinbutton.connect('value-changed', self.toggleautosave)
        self.linespacing_spinbutton.connect(
            'value-changed', self.changelinespacing
        )
        self.indent_check.connect(
            'toggled', self.toggle_indent
        )
        self.presetscombobox.connect('changed', self.presetchanged)
        self.colorpreference.connect('color-set', self.customchanged)
        self.textboxbgpreference.connect('color-set', self.customchanged)
        self.bgpreference.connect('color-set', self.customchanged)
        self.borderpreference.connect('color-set', self.customchanged)
        self.paddingpreference.connect('value-changed', self.customchanged)
        self.heightpreference.connect('value-changed', self.customchanged)
        self.widthpreference.connect('value-changed', self.customchanged)
        self.save_custom_button.connect('clicked', self.save_custom_theme)
        for widget in self.font_radios.values():
            widget.connect('toggled', self.change_font)
        self.custom_font_preference.connect('font-set', self.change_font)

    def change_font(self, widget):
        if widget.get_name() in ('fontbutton1', 'radio_custom_font'):
            self.custom_font_preference.set_sensitive(True)
            new_font = self.custom_font_preference.get_font_name()
            config.set('visual', 'use_font_type', 'custom')
            config.set('visual', 'custom_font', new_font)
        else:
            self.custom_font_preference.set_sensitive(False)
            font_type = widget.get_name().split('_')[1]
            config.set('visual', 'use_font_type', font_type)
        self.graphical.apply_theme()
    
    def get_custom_data(self):
        """reads custom themes"""
        custom_settings = dict(
            foreground = gtk.gdk.Color.to_string(
                                    self.colorpreference.get_color()),
            textboxbg = gtk.gdk.Color.to_string(
                                    self.textboxbgpreference.get_color()),
            background = gtk.gdk.Color.to_string(
                                   self.bgpreference.get_color()),
            border = gtk.gdk.Color.to_string(
                                   self.borderpreference.get_color()),
            padding = self.paddingpreference.get_value_as_int(),
            height = self.heightpreference.get_value() / 100.0,
            width = self.widthpreference.get_value() / 100.0,
        )
        return custom_settings

    def save_custom_theme(self, widget, data=None):
        chooser = gtk.FileChooserDialog('PyRoom', self.window, 
            gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        )
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_current_folder(state['themes_dir'])
        filter_pattern = gtk.FileFilter()
        filter_pattern.add_pattern('*.theme')
        filter_pattern.set_name(_('Theme Files'))
        chooser.add_filter(filter_pattern)
        res = chooser.run()
        if res == gtk.RESPONSE_OK:
            theme_filename = chooser.get_filename()
            self.graphical.theme.save(theme_filename)
            theme_name = os.path.basename(theme_filename)
            theme_id = max(self.stylesvalues.values()) + 1
            self.presetscombobox.append_text(theme_name)
            self.stylesvalues.update({theme_name: theme_id})
            self.presetscombobox.set_active(theme_id)
        chooser.destroy()

    def set_preferences(self, widget, data=None):
        """save preferences"""
        autosavepref = int(self.autosave.get_active())
        config.set("editor", "autosave", str(autosavepref))
        autosave_time = self.autosave_spinbutton.get_value_as_int()
        config.set("editor", "autosavetime", str(autosave_time))

        if self.presetscombobox.get_active_text().lower() == 'custom':
            custom_theme = open(os.path.join(
                state['themes_dir'], 'custom.theme'),
                "w"
            )
            self.customfile.write(custom_theme)
        self.dlg.hide()
        try:
            config_file = open(os.path.join(
                state['conf_dir'], "pyroom.conf"), "w"
            )
            config.write(config_file)
        except IOError:
            raise PyroomError(_("Could not save preferences file."))
            
    def customchanged(self, widget):
        """triggered when custom themes are changed, reloads style"""
        self.presetscombobox.set_active(0)
        for key, value in self.get_custom_data().iteritems():
            self.customfile.set('theme', key, str(value))
        self.presetchanged(widget)

    def fill_pref_dialog(self):
        """load config into the dialog"""
        self.custom_font_preference.set_font_name(
            config.get('visual', 'custom_font')
        )
        parse_color = lambda x: gtk.gdk.color_parse(
            self.graphical.theme[x]
        )
        self.colorpreference.set_color(parse_color('foreground'))
        self.textboxbgpreference.set_color(parse_color('textboxbg'))
        self.bgpreference.set_color(parse_color('background'))
        self.borderpreference.set_color(parse_color('border'))
        self.paddingpreference.set_value(float(
            self.graphical.theme['padding'])
        )
        self.widthpreference.set_value(
            float(self.graphical.theme['width']) * 100
        )
        self.heightpreference.set_value(
            float(self.graphical.theme['height']) * 100
        )

    def presetchanged(self, widget, mode=None):
        """some presets have changed, apply those"""
        active_theme_id = self.presetscombobox.get_active()
        for key, value in self.stylesvalues.iteritems():
            if value == active_theme_id:
                active_theme = key
        if active_theme_id == 0:
            custom_theme = Theme('custom')
            custom_theme['name'] = 'custom'
            custom_theme.update(self.get_custom_data())
            config.set("visual", "theme", str(active_theme))
            self.graphical.theme = custom_theme
            self.save_custom_button.set_sensitive(True)
        else:
            new_theme = Theme(active_theme)
            self.graphical.theme = new_theme
            parse_color = lambda x: gtk.gdk.color_parse(
                self.graphical.theme[x]
            )
            self.colorpreference.set_color(parse_color('foreground'))
            self.textboxbgpreference.set_color(parse_color('textboxbg'))
            self.bgpreference.set_color(parse_color('background'))
            self.borderpreference.set_color(parse_color('border'))
            self.paddingpreference.set_value(float(
                self.graphical.theme['padding'])
            )
            self.widthpreference.set_value(
                float(self.graphical.theme['width']) * 100
            )
            self.heightpreference.set_value(
                float(self.graphical.theme['height']) * 100
            )
            config.set("visual", "theme", str(active_theme))
            self.presetscombobox.set_active(active_theme_id)
            self.save_custom_button.set_sensitive(False)

        self.graphical.apply_theme()
        self.graphical.status.set_text(_('Style Changed to %s') %
                                        (active_theme))

    def show(self):
        """display the preferences dialog"""
        self.dlg = self.wTree.get_widget("dialog-preferences")
        self.dlg.show()

    def toggle_indent(self, widget):
        """toggle textbox indent"""
        if config.get('visual', 'indent') == '1':
            config.set('visual', 'indent', '0')
        else:
            config.set('visual', 'indent', '1')
        self.graphical.apply_theme()

    def toggleborder(self, widget):
        """toggle border display"""
        borderstate = config.getint('visual', 'showborder')
        if borderstate:
            opposite = 0
        else:
            opposite = 1
        config.set('visual', 'showborder', str(opposite))
        self.graphical.apply_theme()

    def changelinespacing(self, widget):
        """Change line spacing"""
        linespacing = self.linespacing_spinbutton.get_value()
        config.set("visual", "linespacing", str(int(linespacing)))
        self.graphical.apply_theme()

    def toggleautosave(self, widget):
        """enable or disable autosave"""
        if self.autosave.get_active():
            self.autosave_spinbutton.set_sensitive(True)
            autosave_time = self.autosave_spinbutton.get_value_as_int()
            config.set('editor', 'autosavee', '1')
        else:
            self.autosave_spinbutton.set_sensitive(False)
            autosave_time = 0
            config.set('editor', 'autosave', '0')
        config.set('editor', 'autosavetime', str(autosave_time))

    def QuitEvent(self, widget, data=None):
        """quit our app"""
        gtk.main_quit()
        return False

    def kill_preferences(self, widget, data=None):
        """hide the preferences window"""
        self.dlg.hide()
        return True
