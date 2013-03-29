import utils

from resource_manager import resman

class Spritesheet(object):
    def __init__(self, path, sprite_width=None, sprite_height=None, x_offset=0, y_offset=0, x_border=0, y_border=0):
        """Creates a spritesheet from a bitmap file, if sprite_width or sprite_height
        are not given, the whole image is assumed to be one sprite.
        """
        self.path = path
        #self.bitmap = utils.load_image(path)
        self.bitmap = resman.get_bitmap(path)

        if sprite_width is None or sprite_height is None:
            self.sprite_width = self.bitmap.width
            self.sprite_height = self.bitmap.height
        else:
            self.sprite_width = sprite_width
            self.sprite_height = sprite_height
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_border = x_border
        self.y_border = y_border


        self.width_in_tiles  = self.bitmap.get_width() // self.sprite_width
        self.height_in_tiles = self.bitmap.get_width() // self.sprite_height

    def get_sprite_rect(self, i):
        tx = i % self.width_in_tiles
        ty = i // self.width_in_tiles

        x = self.x_border + tx * (self.sprite_width  + self.x_offset)
        y = self.y_border + ty * (self.sprite_height + self.y_offset)

        return (x, y, self.sprite_width, self.sprite_height)

    def get_sprite_rect_xy(self, x, y):
        return self.get_sprite_rect(x + y * self.width_in_tiles)