import pygame

from bitmap import Bitmap

class Camera(object):
    def __init__(self, scene = None, width = None, height = None):
        """Camera that holds a surface onto which objects render
        themselves. If no width or height is given, it is assumed to be
        the size of screen.
        If no scene is given, the camera will display a black surface.
        """

        self.x = 0
        self.y = 0
        self.zoom = 1.0

        self.bg_color = (0, 0, 0)

        self.scene = scene
        if width is None or height is None:
            surf = pygame.display.get_surface()

            self.width = surf.get_width()
            self.height = surf.get_height()
        else:
            self.width = width
            self.height = height

        self.surface = pygame.Surface((self.width, self.height))
        self.surface.fill(self.bg_color)

    def set_scene(self, scene):
        self.scene = scene
        self.x, self.y = 0, 0

    def resize(self, new_width, new_height):
        self.width = new_width
        self.height = new_height
        pygame.Surface((self.width, self.height))
        self.surface.fill(self.bg_color)

    def render(self):
        #TODO: Direct rendering
        #TODO: Render only once per frame, for multiple viewports
        if self.scene is None: return
        self.surface.fill(self.bg_color)
        offset = (-self.x, -self.y)
        self.scene.render_onto(self, offset)
