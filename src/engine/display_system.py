import pygame

from singleton_decorator import singleton

from resource_manager import resman

@singleton
class DisplaySystem(object):
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(1) #Set mouse to visible

        self.current_icon = None

        self.width=640
        self.height=480
        self.scaling = 1
        self.screen=pygame.display.set_mode((self.width, self.height))

        self.temp = pygame.Surface((self.width, self.height))

        pygame.display.set_caption("A game, a window, a plane of infinite possibility")

    def set_screen(self, width, height, scaling=1, fullscreen = False, resizable = False, frame = True):
        flags = 0
        flags += pygame.FULLSCREEN * fullscreen
        flags += pygame.RESIZABLE  * resizable
        flags += pygame.NOFRAME    * (not frame)

        self.screen = pygame.display.set_mode((width*scaling, height*scaling), flags)
        #self.temp = pygame.Surface((width, height))

        self.scaling = scaling

        self.width, self.height = width, height
        self.size = (width, height)

        return self.screen

    def set_title(self, caption):
        """Set window title to 'caption'"""
        pygame.display.set_caption(caption)

    def set_icon(self, icon_or_path):
        self.icon = resman.bitmap_or_path(icon_or_path)
        pygame.display.set_icon(self.icon.get_surface("game"))

    def blit(self, surface):
        if self.scaling == 1:
            self.screen.blit(surface, (0, 0))
        else:
            pygame.transform.scale(
                surface,
                (surface.get_width() * self.scaling, surface.get_height() * self.scaling),
                self.screen
            )

        pygame.display.flip()

    def _on_enter_frame(self):
        if self.icon.has_changed("game"):
            pygame.display.set_icon(self.icon.get_surface())

display = DisplaySystem()