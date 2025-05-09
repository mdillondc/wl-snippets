#!/usr/bin/env python3
# wl-snippets.py - A Wayland-compatible text snippet manager with dark mode and fuzzy search

import os
import subprocess
import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Pango

class WlSnippets(Gtk.Window):
    def __init__(self, snippets_dir):
        Gtk.Window.__init__(self, title="wl-snippets")
        self.set_default_size(350, 450)
        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)  # Remove window decorations (title bar, etc.)

        # Enable Nord theme (dark mode)
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Apply dark theme with CSS
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        .dark-mode {
            background-color: #2e3440;
            color: #d8dee9;
        }
        .dark-mode entry {
            background-color: #3b4252;
            color: #d8dee9;
            border-color: #4c566a;
        }
        .dark-mode treeview {
            background-color: #3b4252;
            color: #d8dee9;
        }
        .dark-mode treeview:selected {
            background-color: #5e81ac;
            color: #eceff4;
        }
        .highlighted-row {
            background-color: rgba(129, 161, 193, 0.7);
            color: #eceff4;
        }
        """)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Store snippets directory
        self.snippets_dir = os.path.expanduser(snippets_dir)

        # Setup UI
        self.setup_ui()

        # Load snippets
        self.load_snippets()

        # Connect key press event for keyboard shortcuts
        self.connect('key-press-event', self.on_key_press)

        # Show all widgets
        self.show_all()

        # Set focus to search entry
        self.search_entry.grab_focus()

    def setup_ui(self):
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Add dark mode style class
        self.get_style_context().add_class("dark-mode")

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Type to search snippets...")
        self.search_entry.connect("changed", self.on_search_changed)
        self.search_entry.connect("activate", self.on_select_snippet)
        vbox.pack_start(self.search_entry, False, False, 0)

        # Scrolled window for list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)

        # List store and view
        self.list_store = Gtk.ListStore(str, str)  # Path, Name
        self.filter_store = self.list_store.filter_new()
        self.filter_store.set_visible_func(self.filter_function)

        self.tree_view = Gtk.TreeView.new_with_model(self.filter_store)
        self.tree_view.set_headers_visible(False)
        self.tree_view.connect("row-activated", self.on_snippet_activated)

        # Add selection capability
        self.selection = self.tree_view.get_selection()
        self.selection.connect("changed", self.on_selection_changed)

        # Create text cell renderer
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Snippet", renderer, text=1)
        self.tree_view.append_column(column)

        scrolled.add(self.tree_view)

        # Status bar
        self.status_bar = Gtk.Statusbar()
        vbox.pack_start(self.status_bar, False, False, 0)
        self.status_context = self.status_bar.get_context_id("status")



    def load_snippets(self):
        self.list_store.clear()
        snippet_count = 0

        # Walk through directory and find all files
        for root, _, files in os.walk(self.snippets_dir):
            for file in sorted(files):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.snippets_dir)
                self.list_store.append([full_path, relative_path])
                snippet_count += 1

        # Update status
        self.status_bar.push(self.status_context, f"Loaded {snippet_count} snippets")

    def filter_function(self, model, iterator, data=None):
        search_text = self.search_entry.get_text().lower()

        # If search is empty, show all snippets
        if not search_text:
            return True

        snippet_name = model[iterator][1].lower()

        # Simple fuzzy search
        if search_text in snippet_name:  # Direct match
            return True

        # Fuzzy match - all characters appear in order but not necessarily adjacent
        i, j = 0, 0
        while i < len(search_text) and j < len(snippet_name):
            if search_text[i] == snippet_name[j]:
                i += 1
            j += 1
        return i == len(search_text)

    def on_search_changed(self, widget):
        # Force the filter to be reapplied
        self.filter_store.refilter()

        # Update status with filter info
        count = len(self.filter_store)
        if count > 0:
            # Select first item if exists
            self.tree_view.set_cursor(Gtk.TreePath.new_first())

            # Update status
            if self.search_entry.get_text():
                self.status_bar.push(self.status_context, f"Found {count} matching snippets")
        else:
            if self.search_entry.get_text():
                self.status_bar.push(self.status_context, "No matching snippets found")

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter:
            snippet_name = model[treeiter][1]
            self.status_bar.push(self.status_context, f"Selected: {snippet_name}")

    def on_snippet_activated(self, tree_view, path, column):
        self.copy_selected_snippet()

    def on_select_snippet(self, widget):
        self.copy_selected_snippet()
        
    def on_key_press(self, widget, event):
        # Handle keyboard shortcuts
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        
        # Close on Escape key
        if keyname == 'Escape':
            self.destroy()
            return True
            
        return False

    def provide_visual_feedback(self):
        # This method creates a brief highlight effect on the selected row
        # to provide visual confirmation that a snippet was successfully
        # copied to the clipboard

        # Get selected row
        model, treeiter = self.selection.get_selected()
        if not treeiter:
            return

        # Get the path of the selected row
        path = model.get_path(treeiter)

        # Get the row's TreeViewColumn (we'll use the first column)
        column = self.tree_view.get_column(0)

        # Get the renderer for the cell
        cell_area = self.tree_view.get_cell_area(path, column)

        # Create CSS provider for highlighting
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        treeview:selected {
            background-color: rgba(129, 161, 193, 0.7);
            color: #eceff4;
        }
        """)

        # Apply the style
        context = self.tree_view.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Force redraw
        self.tree_view.queue_draw()

        # Remove the style after a short delay
        def remove_style():
            context.remove_provider(css_provider)
            self.tree_view.queue_draw()
            return False

        GLib.timeout_add(300, remove_style)

    def copy_selected_snippet(self):
        model, treeiter = self.selection.get_selected()
        if treeiter:
            snippet_path = model[treeiter][0]
            snippet_name = model[treeiter][1]

            try:
                with open(snippet_path, 'r') as f:
                    content = f.read()

                # Track copy success
                copy_success = False

                # Try to copy to clipboard using wl-copy first
                try:
                    process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
                    process.communicate(input=content.encode())
                    copy_success = True
                except FileNotFoundError:
                    # Fallback to xclip if wl-copy is not available
                    try:
                        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                        process.communicate(input=content.encode())
                        copy_success = True
                    except FileNotFoundError:
                        self.status_bar.push(self.status_context, "Error: Neither wl-copy nor xclip is available")

                if copy_success:
                    # Show success message
                    self.status_bar.push(self.status_context, f"Copied: {snippet_name}")

                    # Flash background for visual feedback
                    self.provide_visual_feedback()

                # Always close the window after a short delay, regardless of copy success
                GLib.timeout_add(600, self.destroy)

            except Exception as e:
                self.status_bar.push(self.status_context, f"Error: {str(e)}")
                # Close the window even if an error occurs
                GLib.timeout_add(600, self.destroy)

def main():
    # Default snippets directory - modify as needed
    snippets_dir = os.path.expanduser("~/Sync/scripts/wl-snippets/snippets/")

    # Check if directory exists
    if not os.path.isdir(snippets_dir):
        print(f"Error: Snippets directory not found: {snippets_dir}")
        print("Please create this directory or modify the path in the script.")
        return 1

    # Create and run the application
    app = WlSnippets(snippets_dir)
    app.connect("destroy", Gtk.main_quit)

    # Ensure search field gets focus after the main loop starts
    GLib.idle_add(app.search_entry.grab_focus)

    Gtk.main()
    return 0

if __name__ == "__main__":
    exit(main())