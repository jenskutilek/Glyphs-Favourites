from time import time
import objc
from AppKit import NSMenuItem, NSTimer
from GlyphsApp import Glyphs, WINDOW_MENU, DOCUMENTDIDCLOSE, DOCUMENTOPENED
from GlyphsApp.plugins import GeneralPlugin

from glyphsFavourites import FavouritesUI, libkey


class Favourites(GeneralPlugin):
    @objc.python_method
    def settings(self):
        self.hasNotification = False
        self.name = Glyphs.localize({"de": "Favoriten", "en": "Favourites"})

    @objc.python_method
    def start(self):
        newMenuItem = NSMenuItem(self.name, self.showWindow_)
        Glyphs.menu[WINDOW_MENU].append(newMenuItem)
        self.window = None
        self.launch_time = time()

        # Initialize the time counter
        for key in ("time_session", "time_total"):
            if Glyphs.defaults[libkey % key] is None:
                Glyphs.defaults[libkey % key] = 0
        
        # Add any time from last session to the total time
        Glyphs.defaults[libkey % "time_total"] += (
            Glyphs.defaults[libkey % "time_session"]
        )
        # print(f"Usage: {Glyphs.defaults[libkey % 'time_total']} minutes")

        # Record the session time every 10 seconds
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            29.0, self, self.logTime_, None, True
        )

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

    def logTime_(self, info):
        # Save time in minutes
        session_time = int(time() - self.launch_time) // 60
        Glyphs.defaults[libkey % "time_session"] = session_time
        # print("Session:", Glyphs.defaults[libkey % "time_session"], "minutes")

    @objc.python_method
    def __file__(self):
        """
        Please leave this method unchanged
        """
        return __file__
