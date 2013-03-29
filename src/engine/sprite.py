from entity import Entity

from resource_manager import resman

from spritesheet import Spritesheet

class Sprite(Entity):
    def __init__(self, spritesheet_or_path = None):
        Entity.__init__(self)


        if spritesheet_or_path is None:
            self.spritesheet = None
        elif isinstance(spritesheet_or_path, basestring):
            self.load_spritesheet(spritesheet_or_path)
        else:
            self.set_spritesheet(spritesheet_or_path)

        self.sprite_n = 0

    def set_spritesheet(self, spritesheet):
        self.spritesheet = spritesheet

    def load_spritesheet(self, path, sprite_width, sprite_height):
        b = resman.get_bitmap(path)
        self.spritesheet = Spritesheet(b, sprite_width, sprite_height)

    def _render(self, camera, offset):
        #camera.surface
        #camera.position
        pass