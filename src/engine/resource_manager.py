RESOURCE_TYPES = ["bitmap"]

from singleton_decorator import singleton

import utils
from bitmap import Bitmap

import time, os

from logging import logging

@singleton
class ResourceManager(object):
    def __init__(self):
        self.resources = { }
        self.just_changed_resources = {}
        for r in RESOURCE_TYPES:
            self.resources[r] = {}

        self.time_tree = {}
        self.update_times = {}

        self.update_frequency = 3.0 #seconds

        self.last_update = time.time()


    def bitmap_or_path(self, bitmap_or_path):
        "A helper function for flexibly passing bitmaps either directly or via resource paths"
        if isinstance(bitmap_or_path, basestring):
            return self.get_bitmap(bitmap_or_path)
        else:
            return bitmap_or_path

    def get_bitmap(self, path):
        if path in self.resources["bitmap"]:
            return self.resources["bitmap"][path]

        self.update_times[path] = time.time()

        bitmap = Bitmap()
        bitmap._load(path)

        self.resources["bitmap"][path] = bitmap

        return bitmap

    def _on_enter_frame(self):
        delta = time.time() - self.last_update
        if delta > self.update_frequency:
            self.last_update = time.time()
            self.check_updates()

    def check_updates(self, path = None):
        if path is None:
            path = utils.join_path("", "data")

        if os.path.isdir(path):
            for f in os.listdir(path):
                self.check_updates(os.path.join(path, f))
        else:
            resname = path.partition("/data/")[2]
            mtime = os.stat(path).st_mtime

            if resname not in self.update_times: return

            if self.update_times[resname] < mtime:
                logging.notice("Reloading resource '%s'" % resname)
                self.resources["bitmap"][resname]._reload()
                self.update_times[resname] = mtime

resman = ResourceManager()