#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os

import math
import random
from collections import defaultdict

from engine import Game, Mode
from engine import Spritesheet, Tilemap

from engine import utils
from engine._math import rad2deg

from engine.input import mouse, keyboard
from engine import display

import pygame

from engine import Sprite, Image, Entity, Camera

def gen_list2d(width, height, fill=0):
    return [[fill for y in range(width)] for x in range(height)]

class Viewport(Entity):
    def __init__(self, *args):
        """Create a viewport entity that displays contents of a camera inside the world.
        Arguments are either (Camera, int, int) for a new camera or
        (Camera) for an existing one
        """
        Entity.__init__(self)
        if len(args) == 1:
            self.camera = args[0]
        elif len(args) == 3:
            scene = args[0]
            width = args[1]
            height = args[2]
            self.camera = Camera(scene, width, height)
        else:
            raise TypeError, "Viewport's constructor takes either 4 or 2 arguments, %i given" % len(args)+1

    width = property(lambda self: self.camera.width)
    height = property(lambda self: self.camera.height)

    def _render(self, camera, offset):
        #TODO: Recursion
        if camera == self.camera:
            rect = (
                self.x - offset[0],
                self.y - offset[1],
                self.width,
                self.height
            )
            #camera.surface.fill((0,0,0), rect)
            camera.surface.blit(self.camera.surface, offset)
            return
        self.camera.render()
        camera.surface.blit(self.camera.surface, offset)

class MovingGem(Image):
    def __init__(self):
        Image.__init__(self, "gem.png")

    def update(self, delta_time):
        self.x += random.randint(1,3) if random.random() <= 0.1 else 0
        self.y += random.randint(1,3) if random.random() <= 0.1 else 0

class ViewportFrame(Image):
    def __init__(self, viewport):
        Image.__init__(self, "frame256.png")
        self.viewport = viewport

    def update(self, delta_time):
        self.x = self.viewport.camera.x
        self.y = self.viewport.camera.y

class BaseMode(Mode):
    def start(self):

        tileset = Spritesheet("test_tileset_12.png", 12, 12)

        self.tilemap = Tilemap(tileset, 16, 16)
        self.tilemap.set_tile(6, 12, 1)
        self.scene.add_child(self.tilemap)

        self.scene.add_child(Image("gem.png"))

        v = Viewport(self.scene, 256, 256)
        v.x, v.y = 150, 150
        self.scene.add_child(v)

        #v.camera.bg_color = (200, 40, 210)

        self.viewport1 = v

        g = MovingGem()
        g.x, g.y = 50, 50
        self.scene.add_child(g)
        self.gem = g

        self.scene.add_child(ViewportFrame(v))

    def run(self, delta_time):
        if keyboard.just_pressed("escape"):
            self.parent.stop()

        if keyboard.pressed("up"): self.camera.y -= 5
        elif keyboard.pressed("down"): self.camera.y += 5

        if keyboard.pressed("left"): self.camera.x -= 5
        elif keyboard.pressed("right"): self.camera.x += 5

        if keyboard.pressed("w"): self.viewport1.camera.y -= 5
        elif keyboard.pressed("s"): self.viewport1.camera.y += 5

        if keyboard.pressed("a"): self.viewport1.camera.x -= 5
        elif keyboard.pressed("d"): self.viewport1.camera.x += 5

        if keyboard.just_pressed("f"):
            if self.camera.target is None:
                self.camera.follow(self.gem)
            else:
                self.camera.follow(None)


    def _render(self, surface):
        surface.blit(self.visuals, (0, 0))

class MyGame(Game):
    def on_start(self):
        self.fps = 30

        display.set_screen(600, 450, 2)
        display.set_icon("icon32px.png")
        display.set_title("A game with not a name")

        self.set_mode(BaseMode())


if __name__ == '__main__':
    game = PegGame()
    game.run()
