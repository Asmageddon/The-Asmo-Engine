import utils

class Tilesheet(object):
    def __init__(self, path, tile_width, tile_height, x_offset=0, y_offset=0, x_border=0, y_border=0):
        self.path = path
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_border = x_border
        self.y_border = y_border

        self.image = utils.load_image(path)

        self.width_in_tiles  = self.image.get_width() // self.tile_width
        self.height_in_tiles = self.image.get_width() // self.tile_height

    def get_tile_rect(self, i):
        tx = i % self.width_in_tiles
        ty = i // self.width_in_tiles

        x = self.x_border + tx * (self.tile_width  + self.x_offset)
        y = self.y_border + ty * (self.tile_height + self.y_offset)

        return (x, y, self.tile_width, self.tile_height)

    def get_tile_rect_xy(self, x, y):
        return self.get_tile_rect(x + y * self.width_in_tiles)