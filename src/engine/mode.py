from scene_graph import Scene

from camera import Camera

class Mode(object):
    def __init__(self):
        self.frame = 0
        self.scene = Scene()
        self.camera = Camera(self.scene)

    def _attach_parent(self, parent):
        self.parent = parent

    def start(self): pass
    def run(self, time_delta): pass
    def stop(self): pass