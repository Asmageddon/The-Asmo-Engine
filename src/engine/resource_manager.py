RESOURCE_TYPES = ["bitmap"]

from singleton_decorator import singleton

import utils
from bitmap import Bitmap

import time, os

@singleton
class ResourceManager(object):
    def __init__(self):
        self.resources = { }
        for r in RESOURCE_TYPES:
            self.resources[r] = {}

        self.time_tree = {}
        self.update_times = {}

        self.update_frequency = 3.0 #seconds

        self.last_update = time.time()

    def get_bitmap(self, path):
        _bitmap = utils.load_image(path)
        self.update_times[path] = time.time()
        bitmap = Bitmap()
        bitmap._pixels = _bitmap
        bitmap._source = path
        bitmap._resman = self

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
                self.parent.systems.logging.notice("Reloading resource '%s'" % resname)
                self.resources["bitmap"][resname]._pixels = utils.load_image(resname)
                self.resources["bitmap"][resname]._changed = True
                self.update_times[resname] = mtime

resman = ResourceManager()