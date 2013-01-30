
class Mode(object):
    #To be executed on mode switch, don't call manually
    def __init__(self):
        self.frame = 0

    def _attach_parent(self, parent):
        self.parent = parent

    def start(self): pass
    def run(self, time_delta): pass
    def stop(self): pass

    def render(self, surface): pass