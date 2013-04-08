import pygame

import time
from collections import defaultdict

import utils

class Bitmap(object):
    def __init__(self, size = None):
        if size is not None:
            self._pixels = pygame.Surface((width, height))
        else:
            self._pixels = None

        self._source = None

        self._changed = defaultdict()
        self._change_time = time.time()


    def fill(self, color, rect = None):
        color = utils.convert_color(color)
        self._pixels.fill(color, rect)

    def draw_line(self, p1, p2, color, thickness = 1):
        color = utils.convert_color(color)
        pygame.draw.line(p1, p2, color, thickness)

    def draw_rect(self, p1, p2, color, border = 0):
        """
        Draw rectangle between p1 and p2 of color.
        If border parameter is equal to 0, the rectangle will be filled.
        If not, the border will be placed inside enclosing rectangle
        """
        x = p1[0]
        y = p1[1]
        w = x - p2[0]
        h = y - p2[1]
        if border == 0:
            self.fill(color, (x, y, w, h))
        else:
            self.fill(color, (x, y, border, h))
            self.fill(color, (x + w - border, y, border, h))
            self.fill(color, (x, y, w, border))
            self.fill(color, (x, y + h - border, w, border))

    def get_bitmap(self, path):
        if path in self.resources["bitmap"]:
            return self.resources["bitmap"][path]

        _bitmap = utils.load_image(path)
        self.update_times[path] = time.time()
        bitmap = Bitmap()
        bitmap._pixels = _bitmap
        bitmap._source = path

        self.resources["bitmap"][path] = bitmap
        return bitmap

    def _load(self, path):
        if self._pixels is not None: raise RuntimeError, "Already loaded"

        self._pixels = utils.load_image(path)
        self._source = path
        self._changed_time = time.time()

    def _reload(self):
        if self._source == None: return
        self._pixels = utils.load_image(self._source)
        self._on_update()

    def _on_update(self):
        self._changed_time = time.time()
        for key in self._changed:
            self._changed[key] = True

    def has_changed_since(self, time):
        if self._change_time > time: return True
        return False

    def has_changed(self, user=""):
        """Either use has_changed_since, or ask with your own user ID"""
        result = self._changed[user]
        self._changed[user] = False
        return result

    def get_surface(self, user = None):
        """Returns the object for internal representation of the image
            If user is not None, it will update the access time
        """
        if user is not None: self._changed[user] = False
        return self._pixels

    width = property(lambda self: self._pixels.get_width())
    height = property(lambda self: self._pixels.get_height())

    #TODO: Rest
        #pygame.draw.polygon - draw a shape with any number of sides	draw a shape with any number of sides
        #pygame.draw.circle - draw a circle around a point	draw a circle around a point
        #pygame.draw.ellipse - draw a round shape inside a rectangle	draw a round shape inside a rectangle
        #pygame.draw.arc - draw a partial section of an ellipse	draw a partial section of an ellipse
        #pygame.draw.line - draw a straight line segment	draw a straight line segment
        #pygame.draw.lines - draw multiple contiguous line segments	draw multiple contiguous line segments
        #pygame.draw.aaline - draw fine antialiased lines	draw fine antialiased lines
        #pygame.draw.aalines - pygame.draw.aalines(Surface, color, closed, pointlist, blend=1): return Rect	pygame.draw.aalines(Surface, color, closed, pointlist, blend=1): return Rect
