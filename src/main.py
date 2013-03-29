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
            return
        self.camera.render()
        camera.surface.blit(self.camera.surface, offset)

class MovingGem(Image):
    def __init__(self):
        Image.__init__(self, "gem.png")

    def update(self, delta_time):
        self.x += random.randint(1,3) if random.random() <= 0.1 else 0
        self.y += random.randint(1,3) if random.random() <= 0.1 else 0

class BaseMode(Mode):
    def start(self):
        self.visuals = pygame.Surface((768, 768))
        self.visuals.fill((0, 0, 0))

        font = pygame.font.Font(None, 24)

        lines = [
            "The goal of this game is to place your pegs next to 4 different goals(yellow tiles)",
            "and prevent your enemy from doing so",
            "",
            "Rules:",
            "1. Spam",
            "2. SPAM!",
            "3. SPAM SPAM SPAM!",
            "4. SPAMSPAMSPAMSPAMSPAMSPAM!!!!!11",
            "Other controls:",
            "R - generate a new map, only works on the first turn",
            "T - generate a new, symmetric map",
            "Esc - quit the game, confirm with 'Y'",
        ]

        for i, line in enumerate(lines):
            text = font.render(line, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 - len(lines) * 12 + i * 24))
            self.visuals.blit(text, textpos)

        font = pygame.font.Font(None, 32)
        text = font.render("Press Esc to go back to menu", 1, (240, 30, 30))
        textpos = text.get_rect(bottom = 768 - 12, right = 768 - 24)
        self.visuals.blit(text, textpos)

        self.scene.add_child(Image("gem.png"))
        g = MovingGem()
        g.x, g.y = 50, 50
        self.scene.add_child(g)

        v = Viewport(self.scene, 256, 256)
        v.x, v.y = 150, 150
        self.scene.add_child(v)

        v.camera.bg_color = (200, 40, 210)

        self.viewport1 = v

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


    def _render(self, surface):
        surface.blit(self.visuals, (0, 0))

class MyGame(Game):
    def on_start(self):
        self.fps = 30
        self.set_mode(BaseMode())
        pygame.display.set_icon(utils.load_image("icon32px.png"))
        self.set_title("A game with not a name")

if __name__ == '__main__':
    game = PegGame()
    game.run()
