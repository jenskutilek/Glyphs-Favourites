from AppKit import NSDragOperationCopy, NSFilenamesPboardType, NSNoBorder
from pathlib import Path
from GlyphsApp import Glyphs

from vanilla import (
    FloatingWindow,
    Group,
    LevelIndicatorListCell,
    List,
    Window,
)

libkey = "de.kutilek.GlyphsFavs.%s"


class FavouritesUI:
    def __init__(self, plugin):
        self.plugin = plugin
        self._setup_drop()
        s = (500, 100)
        self.w = FloatingWindow(
            s,
            self.plugin.name,
            closable=True,
            minSize=s,
            # maxSize=(1000, 1000),
        )
        self.w.bind("close", self._callback_close)
        self.w.group = Group("auto")
        self.w.group.list = List(
            "auto",
            [],
            doubleClickCallback=self._callback_double_click,
            enableDelete=True,
            # selfApplicationDropSettings=self.selfAppDropDict,
            otherApplicationDropSettings=self.selfAppDropDict,
            columnDescriptions=[
                {
                    "title": "Relevance",
                    "width": 80,
                    "cell": LevelIndicatorListCell(style="relevancy"),
                },
                {
                    "title": "Path",
                    # "minWidth": 100,
                },
                {
                    "title": "Name",
                },
            ],
        )
        rules = [
            "H:|[list]|",
            "V:|[list]|",
        ]
        self.w.group.addAutoPosSizeRules(rules)
        self.w.addAutoPosSizeRules(
            [
                "H:|-0-[group]-0-|",
                "V:|-0-[group]-0-|",
            ]
        )
        self.w.open()
        scrollView = self.w.group.list._nsObject
        scrollView.setBorderType_(NSNoBorder)
        self._load_data()

    def _setup_drop(self):
        self.selfAppDropDict = {
            "type": NSFilenamesPboardType,
            # "operation": NSDragOperationCopy,
            # "allowDropBetweenRows": True,
            # "allowDropOnRow": True,
            "callback": self._callback_drop,
        }

    def _callback_double_click(self, sender):
        items = sender.get()
        for i in sender.getSelection():
            entry = items[i]
            filepath = Path(entry["Path"]) / entry["Name"]
            Glyphs.open(str(filepath))

    def _callback_drop(self, sender, dropInfo):
        if dropInfo["data"] and dropInfo["isProposal"]:
            return True

        for entry in dropInfo["data"]:
            if entry in self.plugin.data:
                continue

            path = Path(entry)
            if path.suffix not in (
                ".glyphs",
                ".glyphspackage",
                ".glyphsproject",
            ):
                continue

            self.w.group.list.append(
                {
                    "Name": path.name,
                    "Path": str(path.parent),
                    "Relevance": 0,
                }
            )
            self.plugin.add_entry(entry)
        self.plugin.save_data()
        return True

    def _callback_close(self, sender):
        # print("_callback_close")
        self.save_window()
        self.plugin.window = None

    def _load_data(self):
        # Load data for the vanilla list from the parent plugin
        time_total = self.plugin.time_total
        for path, entry in self.plugin.data.items():
            p = Path(path)
            if time_total == 0:
                rel = 0
            else:
                rel = 100 * entry["total"] // time_total
            self.w.group.list.append(
                {
                    "Name": p.name,
                    "Path": str(p.parent),
                    "Relevance": rel,
                }
            )

    def save_window(self):
        # FIXME: Save column widths?
        # Glyphs.defaults[libkey % "widthName"] = self.w.group.list.get()
        self.plugin.save_data()
