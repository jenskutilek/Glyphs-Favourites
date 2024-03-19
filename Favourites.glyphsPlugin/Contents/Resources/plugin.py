from pathlib import Path
from time import time
import objc
from AppKit import (
    NSApplicationDidBecomeActiveNotification,
    NSApplicationWillResignActiveNotification,
    NSMenuItem,
    NSNotificationCenter,
    NSWindowDidBecomeMainNotification,
    NSWindowDidResignMainNotification,
)
from GlyphsApp import Glyphs, WINDOW_MENU
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
        self.launch_time = int(time())
        self.became_active_time = self.launch_time
        print(f"Glyphs launched at {self.became_active_time}")

        # Initialize the time counter
        for key in ("TimeSession", "TimeTotal"):
            if Glyphs.defaults[libkey % key] is None:
                Glyphs.defaults[libkey % key] = 0

        # Add any time from last session to the total time
        Glyphs.defaults[libkey % "TimeTotal"] += Glyphs.defaults[libkey % "TimeSession"]
        # print(f"Usage: {Glyphs.defaults[libkey % 'TimeTotal']} seconds")
        self.time_total = Glyphs.defaults[libkey % "TimeTotal"]

        data = Glyphs.defaults[libkey % "Data"]
        self.data = {}
        if data is not None:
            for path, total, session in data:
                self.data[path] = {"total": total + session, "session": 0}
        print("Loaded:", self.data)
        # Session data for opened files
        # {path, open_time, session_time}
        self.session = {}

    @objc.python_method
    def add_entry(self, path):
        if path in self.data:
            print("File is already in favourites")
            return

        self.data[path] = {"total": 0, "session": 0}

    @objc.python_method
    def save_data(self):
        # print("save_data")
        # print(self.data)
        Glyphs.defaults[libkey % "Data"] = [
            (path, entry["total"], entry["session"])
            for path, entry in self.data.items()
        ]

    def showWindow_(self, sender):
        """
        Show the window
        """
        if not self.hasNotification:
            self.center = NSNotificationCenter.defaultCenter()
            self.center.addObserver_selector_name_object_(
                self,
                objc.selector(self.docActivated_, signature=b"v@:"),
                NSWindowDidBecomeMainNotification,
                None,
            )
            self.center.addObserver_selector_name_object_(
                self,
                objc.selector(self.docDeactivated_, signature=b"v@:"),
                NSWindowDidResignMainNotification,
                None,
            )
            self.center.addObserver_selector_name_object_(
                self,
                objc.selector(self.appActivated_, signature=b"v@:"),
                NSApplicationDidBecomeActiveNotification,
                None,
            )
            self.center.addObserver_selector_name_object_(
                self,
                objc.selector(self.appDeactivated_, signature=b"v@:"),
                NSApplicationWillResignActiveNotification,
                None,
            )
            self.hasNotification = True
        if self.window is None:
            self.window = FavouritesUI(self)

    def appActivated_(self, info):
        self.became_active_time = int(time())
        print(f"Glyphs became active at {self.became_active_time}")

    def appDeactivated_(self, info):
        # Save time in seconds
        became_inactive_time = int(time())
        print(f"Glyphs became inactive at {became_inactive_time}")
        if self.became_active_time < self.launch_time:
            print(
                "Time of becoming active is before app launch time, something is wrong."
            )
            print(f"Launch {self.launch_time} vs. activation {self.became_active_time}")
            return

        session_time = became_inactive_time - self.became_active_time
        Glyphs.defaults[libkey % "TimeSession"] += session_time
        print(
            f"Log session: +{session_time} (total session {Glyphs.defaults[libkey % 'TimeSession']}) seconds"
        )

    @objc.python_method
    def getPath(self, info):
        """Extract the file path from the info object (GSWindow)

        Returns:
            str | None: The path if it could be extracted; otherwise None
        """
        obj = info.object()
        print(f"getPath: {obj}")
        try:
            doc = obj.windowController().glyphsDocument()
        except:  # noqa: E722
            try:
                doc = obj.windowController().document()
                print(f"obj.windowController().document(): {doc}")
            except:  # noqa: E722
                return

        if not hasattr(doc, "filePath"):
            return

        path = doc.filePath
        if path not in self.data:
            return

        return path

    def docActivated_(self, info):
        path = self.getPath(info)
        if path is None:
            return

        print(f"docActivated_: {path}")
        # We should watch this file
        self.session[path] = int(time())
        print(f"Resume watching {Path(path).name}.")
        print(f"  Session: {self.data[path]['session']}")
        print(f"  Total: {self.data[path]['total']}")

    def docDeactivated_(self, info):
        path = self.getPath(info)
        if path is None:
            return

        print(f"docDectivated_: {path}")
        if path not in self.session:
            print(f"ERROR: Path not found in current session: '{path}' in")
            print(self.session)
            return

        # We should watch this file
        active_time = int(time()) - self.session[path]
        del self.session[path]
        self.data[path]["session"] += active_time
        print(f"Deactivated {Path(path).name} after {active_time} seconds.")
        print(f"  Session: {self.data[path]['session']}")
        print(f"  Total: {self.data[path]['total']}")

    @objc.python_method
    def __del__(self):
        if self.hasNotification:
            self.hasNotification = False

    def logTime_(self, info=None):
        # Save time in seconds
        if self.became_active_time < self.launch_time:
            print(
                "Time of becoming active is before app launch time, something is wrong."
            )
            print(f"Launch {self.launch_time} vs. activation {self.became_active_time}")
            return

        session_time = int(time() - self.became_active_time)
        Glyphs.defaults[libkey % "TimeSession"] += session_time
        print("Log session:", Glyphs.defaults[libkey % "TimeSession"], "seconds")

    @objc.python_method
    def __file__(self):
        """
        Please leave this method unchanged
        """
        return __file__
