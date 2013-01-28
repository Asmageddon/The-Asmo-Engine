#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import pygame

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

import math
import random
from collections import defaultdict


import utils


def gen_list2d(width, height, fill=0):
    return [[fill for y in range(width)] for x in range(height)]

def deg2rad(degrees):
    return degrees / 180.0 * math.pi

class Map(object):
    def __init__(self):
        self.tiles = gen_list2d(32, 32)

class Mode(object):
    #To be executed on mode switch, don't call manually
    def _attach_parent(self, parent):
        self.parent = parent

    def start(self): pass
    def run(self, time_delta): pass
    def stop(self): pass

    def render(self, surface): pass

class TestMode(Mode):
    def start(self):
        self.t = 0
        self.direction = 1
    def run(self, time_delta):
        if self.parent.key_just_pressed("r"):
            self.t -= 10

        if self.parent.key_pressed("r"):
            self.direction = -1
        else:
            self.direction = 1

        if self.parent.mouse_pressed("right"):
            self.direction *= 0.5

        if self.parent.mouse_pressed("left"):
            self.direction *= 2.0

        self.t += self.direction
    def render(self, surface):
        surface.fill((0, 0, 85))

        color = (255, 175 , 85)

        center = (surface.get_width() // 2, surface.get_height() // 2)
        arm_end = (
            center[0] + math.sin(deg2rad(self.t)) * 240,
            center[1] + math.cos(deg2rad(self.t)) * 240,
        )

        pygame.draw.line(surface, color, center, arm_end, 3)

class Game(object):
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(1) #Set mouse to visible

        self.clock = pygame.time.Clock()
        self.running=0
        self.current_mode = None

        self.width=768; self.height=768
        self.screen=pygame.display.set_mode((self.width,self.height))

        #Key code map for internal use:
        names = filter(lambda name: name.startswith("K_"), dir(pygame))
        keycode_map = { name[2:].lower(): eval("pygame.%s" % name) for name in names }
        self.keycode_map = defaultdict(lambda: 0) #0 for unknown keys
        self.keycode_map.update(keycode_map)

        #Key status dictionaries
        self.key_status = defaultdict(lambda: False)
        self.changed_key_status = {}

        #Mouse status variables
        self.mouse_status = defaultdict(lambda: False)
        self.changed_mouse_status = {}
        self.mouse_pos = (0, 0)

        pygame.display.set_caption("TGWACAFT")

    def start(self): pass
    def stop(self): pass

    def set_mode(self, mode):
        mode._attach_parent(self)
        self.current_mode = mode

    def run(self):
        self.start()

        if self.current_mode == None: return

        self.current_mode.start()
        self.running = 1

        while(self.running):
            self.clock.tick(60)

            self.check_events()

            #Run a frame of the current mode and render
            self.current_mode.run(1.0 / 60) #For now let's just pretend the fps is perfect
            self.current_mode.render(self.screen)
            pygame.display.flip()

        self.current_mode.stop()
        self.stop()

        pygame.quit()

    def __convert_keycode(self, keycode):
        if type(keycode) == str:
            if len(keycode) == 1:
                return ord(keycode) #Convert characters into key codes
            else:
                return self.keycode_map[lower(keycode)]
        else:
            return keycode

    def __convert_mouse_code(self, mouse_button):
        if type(mouse_button) == str:
            mouse_button = mouse_button.lower().replace(" ", "_")
            d = {
                "left": 1,
                "middle": 2,
                "right": 3,
                "wheel_up": 4,
                "wheel_down": 5,
                "extra1": 8,
                "extra2": 9,
                "extra3": 10,
                #And if you think you need more then go commit suicide
                # (or just fix this code if you actually have a good reason)
            }

            return d[mouse_button]
        else:
            return mouse_button #It's just a number unless it's something else which will break stuff anyway.

    def key_just_pressed(self, keycode):
        """Return True if specified key was just pressed this frame"""
        keycode = self.__convert_keycode(keycode)

        if keycode not in self.changed_key_status:
            return False
        return self.changed_key_status[keycode] == True

    def key_just_lifted(self, keycode):
        """Return True if specified key was just lifted this frame"""
        keycode = self.__convert_keycode(keycode)

        if keycode not in self.changed_key_status:
            return False
        return self.changed_key_status[keycode] == False

    def key_pressed(self, keycode):
        """Return True if specified key is being held down"""
        keycode = self.__convert_keycode(keycode)
        return self.key_status[keycode]

    def mouse_just_pressed(self, mouse_button):
        """Return True if specified mouse button was just pressed this frame"""
        mouse_button = self.__convert_mouse_code(mouse_button)

        if mouse_button not in self.changed_mouse_status:
            return False
        return self.changed_mouse_status[mouse_button] == True

    def mouse_just_lifted(self, mouse_button):
        """Return True if specified mouse button was just lifted this frame"""
        mouse_button = self.__convert_mouse_code(mouse_button)

        if mouse_button not in self.changed_mouse_status:
            return False
        return self.changed_mouse_status[mouse_button] == False

    def mouse_pressed(self, mouse_button):
        """Return True if specified mouse button is being held down"""
        mouse_button = self.__convert_mouse_code(mouse_button)
        return self.mouse_status[mouse_button]

    def check_events(self):
        self.changed_key_status = {}
        self.changed_mouse_status = {}

        for event in pygame.event.get():
            if   event.type == pygame.QUIT:
                self.running = False #No arguing

            elif event.type == pygame.KEYDOWN:
                #Update the key status dictionaries
                self.changed_key_status[event.key] = True
                self.key_status[event.key] = True

                #Some alt+key special hotkeys
                if pygame.key.get_mods() & pygame.KMOD_ALT:
                    if event.key == pygame.K_ESCAPE:
                        self.running = 0
                    if event.key == pygame.K_F12:
                        pygame.image.save(self.screen, utils.join_path("user", "screenshot.png"))

            elif event.type == pygame.KEYUP:
                #Update the key status dictionaries
                self.changed_key_status[event.key] = False
                self.key_status[event.key] = False

            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_status[event.button] = True
                self.changed_mouse_status[event.button] = True
                self.mouse_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_status[event.button] = False
                self.changed_mouse_status[event.button] = False
                self.mouse_pos = event.pos

class TestGame(Game):
    def start(self):
        self.set_mode(TestMode())

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

class Tilemap(object):
    def __init__(self, tileset, width, height):
        self.tileset = tileset
        self.width = width
        self.height = height

        self.tiles = gen_list2d(width, height)

        size = (
            width * self.tileset.tile_width,
            height * self.tileset.tile_height,
        )

        self.image = pygame.Surface(size)

        self.render_all()

    def render_tile(self, x, y):
        rect = self.tileset.get_tile_rect(self.tiles[x][y])

        tw = self.tileset.tile_width
        th = self.tileset.tile_height

        self.image.blit(self.tileset.image, (x * tw, y * th), rect)

    def render_all(self):
        for x in range(self.width):
            for y in range(self.height):
                self.render_tile(x, y)

    def get_tile(self, x, y):
        return self.tiles[x][y]

    def set_tile(self, x, y, tile):
        self.tiles[x][y] = tile
        self.render_tile(x, y)

    def __on_new_data(self):
        self.width = len(self.tiles[0])
        self.height = len(self.tiles)

        size = (
            self.width * self.tileset.tile_width,
            self.height * self.tileset.tile_height,
        )
        self.image = pygame.Surface(size)

    def from_list(self, list_):
        self.tiles = []
        for row in list_:
            self.tiles.append(row[:])

        self.__on_new_data()

        self.render_all();

###Here starts the game

T_GROUND   = 0
T_OBSTACLE = 1
T_OBSTACLE2= 6
T_GOAL     = 4

T_RED_BASE = 2
T_BLU_BASE = 3
T_RED_PEG  = 7
T_BLU_PEG  = 8

T_RED_PATH = 5
T_BLU_PATH = 10
T_MIX_PATH = 11


class PegGameMode(Mode):
    def start(self):
        self.tiles = gen_list2d(32, 32) #Game tiles
        self.tileset = Tilesheet("tileset.png", 24, 24) #Tileset
        self.tilemap = Tilemap(self.tileset, 32, 32) #On-screen tiles

        self._generate_map()

    def _generate_map(self):
        for x in range(32):
            for y in range(32):
                if (x + y <= 15) or ((32-x) + (32-y) <= 15):
                    self.tiles[x][y] = T_OBSTACLE
                elif (x + (32-y) <= 5):
                    self.tiles[x][y] = T_OBSTACLE
                elif (x == 0) and (y == 19):
                    self.tiles[x][y] = T_RED_BASE
                elif (x == 32 - 19) and (y == 31):
                    self.tiles[x][y] = T_BLU_BASE
                elif (x == 30) and (y == 1):
                    self.tiles[x][y] = T_GOAL
                elif (x > 1) and (y < 30):
                    if random.randint(0, 2) == 0:
                        self.tiles[x][y] = T_OBSTACLE
                    else:
                        self.tiles[x][y] = T_GROUND

        self.tilemap.from_list(self.tiles)

    def run(self, delta_time):
        tx = self.parent.mouse_pos[0] // 24
        ty = self.parent.mouse_pos[1] // 24
        if self.parent.mouse_pressed("left"):
            self.tilemap.set_tile(tx, ty, T_OBSTACLE2)
        if self.parent.mouse_pressed("right"):
            self.tilemap.set_tile(tx, ty, T_GROUND)

    def render(self, surface):
        surface.blit(self.tilemap.image, (0, 0))


class PegGame(Game):
    def start(self):
        self.set_mode(PegGameMode())

if __name__ == '__main__':
    #game = TestGame()
    #game.run()

    game = PegGame()
    game.run()
