from __future__ import annotations

import objc

from AppKit import (
    NSApplicationDidBecomeActiveNotification,
    NSApplicationWillResignActiveNotification,
    NSApplicationWillTerminateNotification,
    NSCommandKeyMask,
    NSControlKeyMask,
    NSMenuItem,
    NSNotificationCenter,
    NSWindowDidBecomeMainNotification,
    NSWindowDidResignMainNotification,
    NSWindowWillCloseNotification,
)
from datetime import datetime
from GlyphsApp import Glyphs, WINDOW_MENU
from GlyphsApp.plugins import GeneralPlugin
from glyphsFavourites import FavouritesUI, libkey
from pathlib import Path
from time import time


DEBUG = False
SUMMARIZE = False  # Print a summary of loaded items at startup?


def print_time(action: str, timestamp: int) -> None:
    t = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
    print(f"Glyphs {action} at {t}")


class Favourites(GeneralPlugin):
    @objc.python_method
    def settings(self) -> None:
        self.hasNotification = False
        self.name = Glyphs.localize(
            {
                "ar": "المفضلة",
                "cs": "Oblíbené",
                "de": "Favoriten",
                "en": "Favourites",
                "es": "Favoritos",
                "fr": "Favoris",
                "it": "Preferiti",
                "ja": "お気に入り",
                "ko": "즐겨찾기",
                "pt": "Favoritos",
                "ru": "Избранное",
                "tr": "Favoriler",
                "zh-Hans": "收藏",
                "zh-Hant": "收藏",
            }
        )
        self.keyboardShortcut = "d"
        self.keyboardShortcutModifier = NSControlKeyMask
        self.menuItem = NSMenuItem(self.name, self.showWindow_)
        self.menuItem.setTitle_(self.name)
        self.menuItem.setAction_(self.showWindow_)
        self.menuItem.setTarget_(self)
        self.menuItem.setKeyEquivalent_(self.keyboardShortcut)
        self.menuItem.setKeyEquivalentModifierMask_(self.keyboardShortcutModifier)

    @objc.python_method
    def start(self) -> None:
        Glyphs.menu[WINDOW_MENU].append(self.menuItem)
        self.window = None
        self.launch_time = int(time())
        self.became_active_time = self.launch_time
        if DEBUG:
            print_time("launched", self.became_active_time)

        # Initialize the time counter
        for key in ("TimeSession", "TimeTotal"):
            if Glyphs.defaults[libkey % key] is None:
                Glyphs.defaults[libkey % key] = 0

        # Add any time from last session to the total time
        Glyphs.defaults[libkey % "TimeTotal"] += Glyphs.defaults[libkey % "TimeSession"]
        # print(f"Usage: {Glyphs.defaults[libkey % 'TimeTotal']} seconds")
        self.time_total = Glyphs.defaults[libkey % "TimeTotal"]
        Glyphs.defaults[libkey % "TimeSession"] = 0

        data = Glyphs.defaults[libkey % "Data"]
        self.data = {}
        if data is not None:
            for path, total, session in data:
                self.data[path] = {"total": total + session, "session": 0}
        if SUMMARIZE:
            print(
                f"Loaded favourites with total time spent: "
                f"{self.time_total / 3600:0.2f} hours ({self.time_total} seconds)"
            )
        path_total = 0
        for path, times in self.data.items():
            path_time = times["total"]
            path_total += path_time
            if SUMMARIZE:
                print(
                    f"Spent {path_time}s ({100 * path_time / self.time_total:0.2f}%) "
                    f"on {Path(path).name}"
                )
        if self.time_total < path_total:
            if DEBUG:
                print(f"Resetting total time to {path_total} seconds")
            self.time_total = path_total
        # Session data for opened files
        # {path, open_time, session_time}
        self.session = {}

        self.center = None
        self.add_notifications()

    @objc.python_method
    def add_notifications(self) -> None:
        if self.hasNotification:
            return

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
            objc.selector(self.docClosed_, signature=b"v@:"),
            NSWindowWillCloseNotification,
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
        self.center.addObserver_selector_name_object_(
            self,
            objc.selector(self.appWillTerminate_, signature=b"v@:"),
            NSApplicationWillTerminateNotification,
            None,
        )
        self.hasNotification = True

    @objc.python_method
    def add_entry(self, path) -> None:
        if path in self.data:
            if DEBUG:
                print("File is already in favourites")
            return

        self.data[path] = {"total": 0, "session": 0}

    @objc.python_method
    def save_data(self) -> None:
        Glyphs.defaults[libkey % "Data"] = [
            (path, entry["total"], entry["session"])
            for path, entry in self.data.items()
        ]

    def showWindow_(self, sender) -> None:
        """
        Show the window, or close it if it is already open.
        """
        if self.window is None:
            self.window = FavouritesUI(self)
        else:
            self.window.w.close()

    def appActivated_(self, info) -> None:
        self.became_active_time = int(time())
        if DEBUG:
            print_time("became active", self.became_active_time)

    def appDeactivated_(self, info) -> None:
        # Save time in seconds
        became_inactive_time = int(time())
        if DEBUG:
            print_time("became inactive", became_inactive_time)
        if self.became_active_time < self.launch_time:
            if DEBUG:
                print(
                    "Time of becoming active is before app launch time, "
                    "something is wrong."
                )
                print(
                    f"Launch {self.launch_time} vs. activation "
                    f"{self.became_active_time}"
                )
            return

        session_time = became_inactive_time - self.became_active_time
        Glyphs.defaults[libkey % "TimeSession"] += session_time
        if DEBUG:
            print(
                f"Log session: +{session_time} (total session "
                f"{Glyphs.defaults[libkey % 'TimeSession']}) seconds"
            )

    def appWillTerminate_(self, info) -> None:
        terminate_time = int(time())
        session_time = terminate_time - self.became_active_time
        Glyphs.defaults[libkey % "TimeSession"] += session_time
        self.save_data()

    @objc.python_method
    def getPath(self, info) -> None | str:
        """Extract the file path from the info object (GSWindow)

        Returns:
            str | None: The path if it could be extracted; otherwise None
        """
        if info is None:
            return

        obj = info.object()
        if DEBUG:
            pass
            # print(f"getPath: {obj}")
        try:
            doc = obj.windowController().glyphsDocument()
        except:  # noqa: E722
            try:
                doc = obj.windowController().document()
                if DEBUG:
                    print(f"  obj.windowController().document(): {doc}")
                # if doc is None:
                #     if DEBUG:
                #         print("  Falling back to Glyphs.currentFontDocument()")
                #         # FIXME: Stop timer when there is no document
                #     doc = Glyphs.currentFontDocument()
            except:  # noqa: E722
                return

        if not hasattr(doc, "filePath"):
            return

        path = doc.filePath
        if path not in self.data:
            return

        return path

    def docActivated_(self, info) -> None:
        path = self.getPath(info)
        if path is None:
            return

        if DEBUG:
            print(f"docActivated_: {path}")
        # We should watch this file
        self.session[path] = int(time())
        if DEBUG:
            print(f"Resume watching {Path(path).name}.")
            print(f"  Session: {self.data[path]['session']}")
            print(f"  Total: {self.data[path]['total']}")

    def docDeactivated_(self, info) -> None:
        path = self.getPath(info)
        if path is None:
            return

        if DEBUG:
            print(f"docDectivated_: {path}")
        if path not in self.session:
            # print(f"ERROR: Path not found in current session: '{path}' in")
            # print(self.session)
            return

        # We should watch this file
        active_time = int(time()) - self.session[path]
        del self.session[path]
        self.data[path]["session"] += active_time
        if DEBUG:
            print(f"Deactivated {Path(path).name} after {active_time} seconds.")
            print(f"  Session: {self.data[path]['session']}")
            print(f"  Total: {self.data[path]['total']}")

    def docClosed_(self, info) -> None:
        # FIXME: Is also called on the export sheet, and will close the session erroneously
        path = self.getPath(info)
        if path is None:
            return

        if DEBUG:
            print(f"docClosed_: {path}")
        if path not in self.session:
            # print(f"ERROR: Path not found in current session: '{path}' in")
            # print(self.session)
            return

        # We should watch this file
        active_time = int(time()) - self.session[path]
        del self.session[path]
        self.data[path]["session"] += active_time
        if DEBUG:
            print(f"Closed {Path(path).name} after {active_time} seconds.")
            print(f"  Session: {self.data[path]['session']}")
            print(f"  Total: {self.data[path]['total']}")
        self.save_data()

    @objc.python_method
    def __file__(self) -> str:
        """
        Please leave this method unchanged
        """
        return __file__
