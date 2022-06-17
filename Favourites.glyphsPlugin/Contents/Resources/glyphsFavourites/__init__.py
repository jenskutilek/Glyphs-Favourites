from AppKit import NSDragOperationCopy, NSFilenamesPboardType
from pathlib import Path
from time import time
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
		self._setup_drop()
		s = (500, 300)
		self.w = Window(
			s,
			plugin.name,
			closable=True,
			minSize=s,
			# maxSize=(1000, 1000),
		)
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
					"title": "Name",
					"minWidth": 100,
				},
				{
					"title": "Relevancy",
					"width": 80,
					"cell": LevelIndicatorListCell(style="relevancy")
				},
				{
					"title": "Path",
					# "minWidth": 100,
				},
			],
		)
		rules = [
			"H:|[list]|",
			"V:|[list]|",
		]
		self.w.group.addAutoPosSizeRules(rules)
		self.w.addAutoPosSizeRules([
			"H:|-8-[group]-8-|",
			"V:|-8-[group]-8-|",
		])
		self.w.open()
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
		print("_callback_double_click")
		items = sender.get()
		print(sender.getSelection())
		for i in sender.getSelection():
			entry = items[i]
			filepath = Path(entry["Path"]) / entry["Name"]
			print(filepath)
			Glyphs.open(str(filepath))
	
	def _callback_drop(self, sender, dropInfo):
		if dropInfo["data"] and dropInfo["isProposal"]:
			return True

		for entry in dropInfo["data"]:
			path = Path(entry)
			if path.suffix not in ("glyphs", "glyphspackage", "glyphsproject"):
				continue

			self.w.group.list.append({
				"Name": path.name,
				"Path": str(path.parent),
				"Relevancy": 0,
			})
		self._save_data()
		return True
	
	def _load_data(self):
		data = Glyphs.defaults[libkey % "data"]
		if data is not None:
			for entry in data:
				self.w.group.list.append(entry)
		print("Load data:", data)
	
	def _save_data(self):
		# Save the list
		Glyphs.defaults[libkey % "data"] = self.w.group.list.get()
	
	def save_window(self):
		# FIXME: Save column widths?
		# Glyphs.defaults[libkey % "widthName"] = self.w.group.list.get()
		self._save_data()

if __name__ == "__main__":
	class Plugin:
		pass

	p = Plugin()
	p.name = "Favoriten"
	FavouritesUI(p)
