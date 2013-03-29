from entity import Entity

from resource_manager import resman

class Image(Entity):
    def __init__(self, bitmap_or_path = None):
        Entity.__init__(self)

        if bitmap_or_path is None:
            self.bitmap = None
        elif isinstance(bitmap_or_path, basestring):
            self.load_bitmap(bitmap_or_path)
        else:
            self.set_bitmap(bitmap_or_path)

    def set_bitmap(self, bitmap):
        self.bitmap = bitmap

    def load_bitmap(self, path):
        self.bitmap = resman.get_bitmap(path)

    def _render(self, camera, offset):
        camera.surface.blit(self.bitmap.get_surface(), offset)
        #print "Rendering at %i, %i" % offset