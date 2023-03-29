# preferences.py
#
# Copyright 2022-2023 kramo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gi.repository import Adw, Gio, GLib, Gtk

from .create_dialog import create_dialog


class ImportPreferences:
    def __init__(
        self,
        source_id,
        name,
        key,
        paths,
        expander_row,
        file_chooser_button,
        window,
        config=False,
    ):
        def set_dir(_source, result, _unused):
            try:
                path = window.file_chooser.select_folder_finish(result).get_path()

                def response(widget, response):
                    if response == "choose_folder":
                        window.choose_folder(widget, set_dir)

                if not any(
                    os.path.exists(os.path.join(path, current_path))
                    for current_path in paths
                ):
                    create_dialog(
                        window.parent_widget,
                        _("Installation Not Found"),
                        # The variable is the name of the game launcher
                        _(f"Select the {name} configuration directory.") if config
                        # The variable is the name of the game launcher
                        else _(f"Select the {name} data directory."),
                        "choose_folder",
                        _("Set Location"),
                    ).connect("response", response)
                else:
                    window.schema.set_string(
                        key,
                        path,
                    )
            except GLib.GError:
                pass

        window.schema.bind(
            source_id,
            expander_row,
            "enable-expansion",
            Gio.SettingsBindFlags.DEFAULT,
        )

        file_chooser_button.connect("clicked", window.choose_folder, set_dir)


@Gtk.Template(resource_path="/hu/kramo/Cartridges/gtk/preferences.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"

    general_page = Gtk.Template.Child()
    import_page = Gtk.Template.Child()

    sources_group = Gtk.Template.Child()

    exit_after_launch_switch = Gtk.Template.Child()
    cover_launches_game_switch = Gtk.Template.Child()
    high_quality_images_switch = Gtk.Template.Child()

    steam_expander_row = Gtk.Template.Child()
    steam_file_chooser_button = Gtk.Template.Child()
    steam_extra_file_chooser_button = Gtk.Template.Child()
    steam_clear_button_revealer = Gtk.Template.Child()
    steam_clear_button = Gtk.Template.Child()

    heroic_expander_row = Gtk.Template.Child()
    heroic_file_chooser_button = Gtk.Template.Child()
    heroic_epic_switch = Gtk.Template.Child()
    heroic_gog_switch = Gtk.Template.Child()
    heroic_sideloaded_switch = Gtk.Template.Child()

    bottles_expander_row = Gtk.Template.Child()
    bottles_file_chooser_button = Gtk.Template.Child()

    def __init__(self, parent_widget, **kwargs):
        super().__init__(**kwargs)
        self.schema = parent_widget.schema
        self.parent_widget = parent_widget
        self.file_chooser = Gtk.FileDialog()

        self.set_transient_for(parent_widget)
        self.schema.bind(
            "exit-after-launch",
            self.exit_after_launch_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.schema.bind(
            "cover-launches-game",
            self.cover_launches_game_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.schema.bind(
            "high-quality-images",
            self.high_quality_images_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.schema.bind(
            "heroic-import-epic",
            self.heroic_epic_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.schema.bind(
            "heroic-import-gog",
            self.heroic_gog_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.schema.bind(
            "heroic-import-sideload",
            self.heroic_sideloaded_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

        def update_revealer():
            if self.schema.get_strv("steam-extra-dirs"):
                self.steam_clear_button_revealer.set_reveal_child(True)
            else:
                self.steam_clear_button_revealer.set_reveal_child(False)

        def add_steam_dir(_source, result, _unused):
            try:
                value = self.schema.get_strv("steam-extra-dirs")
                value.append(self.file_chooser.select_folder_finish(result).get_path())
                self.schema.set_strv("steam-extra-dirs", value)
            except GLib.GError:
                pass
            update_revealer()

        def clear_steam_dirs(*_unused):
            self.schema.set_strv("steam-extra-dirs", [])
            update_revealer()

        update_revealer()

        self.steam_extra_file_chooser_button.connect(
            "clicked", self.choose_folder, add_steam_dir
        )
        self.steam_clear_button.connect("clicked", clear_steam_dirs)

        ImportPreferences(
            "steam",
            "Steam",
            "steam-location",
            [
                "steamapps",
                os.path.join("steam", "steamapps"),
                os.path.join("Steam", "steamapps"),
            ],
            self.steam_expander_row,
            self.steam_file_chooser_button,
            self,
        )

        ImportPreferences(
            "heroic",
            "Heroic",
            "heroic-location",
            ["config.json"],
            self.heroic_expander_row,
            self.heroic_file_chooser_button,
            self,
            True,
        )

        ImportPreferences(
            "bottles",
            "Bottles",
            "bottles-location",
            ["library.yml"],
            self.bottles_expander_row,
            self.bottles_file_chooser_button,
            self,
        )

        if os.name == "nt":
            self.sources_group.remove(self.bottles_expander_row)

    def choose_folder(self, _widget, function):
        self.file_chooser.select_folder(self.parent_widget, None, function, None)
