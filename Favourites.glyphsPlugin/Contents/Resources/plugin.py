from time import time
import objc
from AppKit import NSControlKeyMask, NSMenuItem, NSShiftKeyMask
from GlyphsApp import Glyphs, WINDOW_MENU, DOCUMENTDIDCLOSE, DOCUMENTOPENED
from GlyphsApp.plugins import GeneralPlugin

from glyphsFavourites import FavouritesUI, libkey


class Favourites(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.hasNotification = False
        self.name = Glyphs.localize({"de": "Favoriten", "en": "Favourites"})
        # A keyboard shortcut for activating/deactivating the plug-in
        # (together with Control + Shift)
        self.keyboardShortcut = "f"
        self.keyboardShortcutModifier = NSControlKeyMask | NSShiftKeyMask

    @objc.python_method
    def start(self):
        newMenuItem = NSMenuItem(self.name, self.showWindow_)
        Glyphs.menu[WINDOW_MENU].append(newMenuItem)
        self.window = None
        self.launch_time = time()
        print(f"Launch: {self.launch_time}")
        if Glyphs.defaults[libkey % "time"] is None:
            Glyphs.defaults[libkey % "time"] = 0

    def showWindow_(self, sender):
        """
        Show the window
        """
        if not self.hasNotification:
            Glyphs.addCallback(self.docOpened, DOCUMENTOPENED)
            Glyphs.addCallback(self.docClosed, DOCUMENTDIDCLOSE)
            self.hasNotification = True
        if self.window is None:
            self.window = FavouritesUI(self)

    @objc.python_method
    def docClosed(self, info):
        obj = info.object()  # GSDocument
        if hasattr(obj, "filePath"):
            path = obj.filePath
            # log end edit

    @objc.python_method
    def docOpened(self, info):
        obj = info.object()  # GSDocument
        if hasattr(obj, "filePath"):
            path = obj.filePath
            # log begin edit

    @objc.python_method
    def __del__(self):
        if self.hasNotification:
            Glyphs.removeCallback(self.docClosed)
            Glyphs.removeCallback(self.docOpened)
            self.hasNotification = False
        quit_time = time()
        # Save time in minutes
        Glyphs.defaults[libkey % "time"] += (
            int(quit_time - self.launch_time) // 60
        )
        # if self.window is not None:
        #     self.window.save_window()

    @objc.python_method
    def __file__(self):
        """
        Please leave this method unchanged
        """
        return __file__
