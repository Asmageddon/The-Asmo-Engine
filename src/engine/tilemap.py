import pygame

from tilesheet import Tilesheet

from entity import Entity

class Tilemap(Entity):
    def __init__(self, tileset, width, height):
        Entity.__init__(self)
        self.tileset = tileset
        self.width = width
        self.height = height

        self.tiles = [[0 for y in range(width)] for x in range(height)]

        size = (
            width * self.tileset.sprite_width,
            height * self.tileset.sprite_height,
        )

        #TODO: Do not preallocate the whole thing
        self.image = pygame.Surface(size)

        self.render_all()

    def render_tile(self, x, y):
        rect = self.tileset.get_sprite_rect(self.tiles[x][y])

        tw = self.tileset.sprite_width
        th = self.tileset.sprite_height

        self.image.blit(self.tileset.bitmap.get_surface(), (x * tw, y * th), rect)

    def render_all(self):
        for x in range(self.width):
            for y in range(self.height):
                self.render_tile(x, y)

    def get_tile(self, x, y):
        return self.tiles[x][y]

    def set_tile(self, x, y, tile):
        self.tiles[x][y] = tile
        self.render_tile(x, y)

    def _on_new_data(self):
        self.width = len(self.tiles[0])
        self.height = len(self.tiles)

        size = (
            self.width * self.tileset.sprite_width,
            self.height * self.tileset.sprite_height,
        )
        self.image = pygame.Surface(size)

    def from_list(self, list_):
        self.tiles = []
        for row in list_:
            self.tiles.append(row[:])

        self._on_new_data()

        self.render_all()

    def _render(self, camera, offset):
        camera.surface.blit(self.image, offset)
        #print "Rendering at %i, %i" % offset