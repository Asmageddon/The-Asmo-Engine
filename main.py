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
        self.running = False
        self.current_mode = None

        self.fps = 15

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
        if self.running:
            self.current_mode.stop()

        self.current_mode = mode

        if self.running:
            self.current_mode.start()

    def run(self):
        self.start()

        if self.current_mode == None: return

        self.current_mode.start()
        self.running = True

        while(self.running):
            self.clock.tick(self.fps)

            self.check_events()

            #Run a frame of the current mode and render
            self.current_mode.run(1.0 / self.fps) #For now let's just pretend the fps is perfect
            self.current_mode.render(self.screen)
            pygame.display.flip()

        self.current_mode.stop()
        self.stop()

        pygame.quit()

    def __convert_keycode(self, keycode):
        if type(keycode) == str:
            if len(keycode) == 1:
                if keycode == '~': keycode = '`' #Convert tilde to backtick
                return ord(keycode) #Convert characters into key codes
            else:
                return self.keycode_map[keycode.lower()]
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
        #Make sure it's registered as pressed for at least one frame
        # in case the press was too quick
        if keycode in self.changed_key_status:
            if self.changed_key_status[keycode] == True:
                return True
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
        #Make sure it's registered as pressed for at least one frame
        # in case the click was too quick
        if mouse_button in self.changed_mouse_status:
            if self.changed_mouse_status[mouse_button] == True:
                return True
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
                        self.running = False
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
T_GROUND2  = 12
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

T_RED_PATH2 = 15
T_BLU_PATH2 = 16
T_MIX_PATH2 = 17

T_CURSOR_RED = 20
T_CURSOR_BLU = 21
T_CURSOR_MIX = 22
T_ICON_RED_PEG = 23
T_ICON_BLU_PEG = 24
T_ICON_OBSTACLE = 19
T_ICON_GROUND = 12

class MenuMode(Mode):
    def start(self):
        self.visuals = pygame.Surface((768, 768))
        self.visuals.fill((0, 0, 0))

        font = pygame.font.Font(None, 32)

        lines = ["1. Start Game (local)", "2. Instructions", "3. Quit"]

        for i, line in enumerate(lines):
            text = font.render(line, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 - len(lines) * 18 + i * 36))
            self.visuals.blit(text, textpos)

    def run(self, delta_time):
        if self.parent.key_just_pressed("1"):
            self.parent.set_mode(PegGameMode())
        elif self.parent.key_just_pressed("2"):
            self.parent.set_mode(InstructionsMode())
        elif self.parent.key_just_pressed("3"):
            self.parent.running = False

    def render(self, surface):
        surface.blit(self.visuals, (0, 0))

class InstructionsMode(Mode):
    def start(self):
        self.visuals = pygame.Surface((768, 768))
        self.visuals.fill((0, 0, 0))

        font = pygame.font.Font(None, 24)

        lines = [
            "The goal of this game is to place a peg of your own as close to the goal as possible",
            "and prevent the enemy from doing so",
            "",
            "Rules:",
            "1. You can only place your pegs in direct line of sight from one of your pegs",
            "2. You cannot place your peg on a tile that is in enemy line of sight",
            "3. Every 3 turns you can place an obstacle anywhere on the map",
            "4. Every 5 turns you can remove an obstacle from anywhere on the map",
            "5. You can not modify obstacles or floors placed by you or your enemy",
            "6. You can not modify terrain directly next to one of enemy pegs (not implemented)",
            "",
            "Red player controls:",
            "W/S/A/D - move cursor",
            "C/V/B - place peg/obstacle/floor respectively, if charged",
            "Blue player controls:",
            "Up/Down/Left/Right - move cursor",
            "Num1/Num2/Num3 - place peg/obstacle/floor respectively, if charged",
            "Other controls:",
            "r - generate a new map, only works on the first turn, for balancing purposes",
            "Esc - quit, confirm with 'Y'",
        ]

        for i, line in enumerate(lines):
            text = font.render(line, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 - len(lines) * 12 + i * 24))
            self.visuals.blit(text, textpos)

        font = pygame.font.Font(None, 32)
        text = font.render("Press Esc to go back to menu", 1, (240, 30, 30))
        textpos = text.get_rect(bottom = 768 - 12, right = 768 - 24)
        self.visuals.blit(text, textpos)

    def run(self, delta_time):
        if self.parent.key_just_pressed("escape"):
            self.parent.set_mode(MenuMode())

    def render(self, surface):
        surface.blit(self.visuals, (0, 0))

class PegGameMode(Mode):
    def start(self):
        self.tileset = Tilesheet("tileset.png", 24, 24) #Tileset
        self.tilemap = Tilemap(self.tileset, 32, 32) #On-screen tiles

        self._generate_map()

        self.turn = 0
        self.turn_player = 0

        self.CHARGE_WALL = 3
        self.CHARGE_FLOOR = 5

        self.red_cursor = [ 0, 19]
        self.blu_cursor = [13, 31]

        self.red_charge_wall = 0
        self.red_charge_floor = 0
        self.blu_charge_wall = 0
        self.blu_charge_floor = 0

        self.red_image = pygame.Surface((8 * 24 + 3, 4 * 24 + 3))
        self.blu_image = pygame.Surface((8 * 24 + 3, 4 * 24 + 3))

        self.quit_image = None

        font = pygame.font.Font(None, 32)

        text = font.render("Really quit (Y/Esc)?", 1, (230, 230, 50))
        textpos = text.get_rect()#left=8,top=16*16)
        self.quit_image = pygame.Surface((textpos[2], textpos[3]))
        self.quit_image.blit(text, textpos)

        self.quit_popup = False

        self._update_status()

    def _generate_map(self):
        tiles = gen_list2d(32, 32)
        for x in range(32):
            for y in range(32):
                if (x + y <= 15) or ((32-x) + (32-y) <= 15):
                    tiles[x][y] = T_OBSTACLE
                elif (x + (32-y) <= 5):
                    tiles[x][y] = T_OBSTACLE
                elif (x == 0) and (y == 19):
                    tiles[x][y] = T_RED_BASE
                elif (x == 32 - 19) and (y == 31):
                    tiles[x][y] = T_BLU_BASE
                elif (x == 30) and (y == 1):
                    tiles[x][y] = T_GOAL
                elif (x > 1) and (y < 30):
                    if random.randint(0, 2) == 0:
                        tiles[x][y] = T_OBSTACLE
                    else:
                        tiles[x][y] = T_GROUND

        #Some simple cellular automata magic to hopefully make the map nicer
        oldmap = [x[:] for x in tiles]
        for x in range(1, 30):
            for y in range(1, 30):
                if (x + y <= 15) or ((32-x) + (32-y) <= 15): continue
                elif (x + (32-y) <= 5): continue

                c = 0
                for (mx, my) in [(1, -1), (1, 0), (1, 1), (0, -1), (0, 1), (-1, -1), (-1, 0), (-1, 1)]:
                    c += int(oldmap[x+mx][y+my] == T_OBSTACLE)
                c2 = 8 - c

                if oldmap[x][y] == T_OBSTACLE:
                    if random.randint(0, c2 + 0) <= 1:
                        tiles[x][y] = T_GROUND
                elif oldmap[x][y] == T_GROUND:
                    if random.randint(0, c + 4) == 0:
                        tiles[x][y] = T_OBSTACLE

        self.tilemap.from_list(tiles)

        self._cast_paths()

    def _cast_paths(self):
        passable = [
            T_GROUND, T_GROUND2,
            T_BLU_PATH, T_RED_PATH, T_MIX_PATH,
            T_BLU_PATH2, T_RED_PATH2, T_MIX_PATH2,
        ]
        #Clear paths
        for x in range(32):
            for y in range(32):
                if self.tilemap.get_tile(x, y) in [T_BLU_PATH, T_RED_PATH, T_MIX_PATH]:
                    self.tilemap.set_tile(x, y, T_GROUND)
                if self.tilemap.get_tile(x, y) in [T_BLU_PATH2, T_RED_PATH2, T_MIX_PATH2]:
                    self.tilemap.set_tile(x, y, T_GROUND2)
        #Recalculate paths
        for x in range(32):
            for y in range(32):
                if self.tilemap.get_tile(x, y) in [T_BLU_BASE, T_BLU_PEG]:
                    #Holy mother of god what is this black voodoo
                    x2 = x - 1
                    while (x2 > 0) and self.tilemap.get_tile(x2, y) in passable:
                        if   self.tilemap.get_tile(x2, y) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x2, y) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_GROUND2: ttype = T_BLU_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_BLU_PATH2: ttype = T_BLU_PATH2
                        else: ttype = T_BLU_PATH

                        self.tilemap.set_tile(x2, y, ttype)
                        x2 -= 1
                    x2 = x + 1
                    while (x2 < 32) and self.tilemap.get_tile(x2, y) in passable:
                        if   self.tilemap.get_tile(x2, y) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x2, y) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_GROUND2: ttype = T_BLU_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_BLU_PATH2: ttype = T_BLU_PATH2
                        else: ttype = T_BLU_PATH

                        self.tilemap.set_tile(x2, y, ttype)
                        x2 += 1
                    y2 = y - 1
                    while (y2 > 0) and self.tilemap.get_tile(x, y2) in passable:
                        if   self.tilemap.get_tile(x, y2) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x, y2) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_GROUND2: ttype = T_BLU_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_BLU_PATH2: ttype = T_BLU_PATH2
                        else: ttype = T_BLU_PATH

                        self.tilemap.set_tile(x, y2, ttype)
                        y2 -= 1
                    y2 = y + 1
                    while (y2 < 32) and self.tilemap.get_tile(x, y2) in passable:
                        if   self.tilemap.get_tile(x, y2) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x, y2) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_BLU_PATH2: ttype = T_BLU_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_GROUND2: ttype = T_BLU_PATH2
                        else: ttype = T_BLU_PATH

                        self.tilemap.set_tile(x, y2, ttype)
                        y2 += 1

                if self.tilemap.get_tile(x, y) in [T_RED_BASE, T_RED_PEG]:
                    x2 = x - 1
                    while (x2 > 0) and self.tilemap.get_tile(x2, y) in passable:
                        if   self.tilemap.get_tile(x2, y) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x2, y) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_RED_PATH2: ttype = T_RED_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_GROUND2: ttype = T_RED_PATH2
                        else: ttype = T_RED_PATH

                        self.tilemap.set_tile(x2, y, ttype)
                        x2 -= 1
                    x2 = x + 1
                    while (x2 < 32) and self.tilemap.get_tile(x2, y) in passable:
                        if   self.tilemap.get_tile(x2, y) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x2, y) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_RED_PATH2: ttype = T_RED_PATH2
                        elif self.tilemap.get_tile(x2, y) == T_GROUND2: ttype = T_RED_PATH2
                        else: ttype = T_RED_PATH

                        self.tilemap.set_tile(x2, y, ttype)
                        x2 += 1
                    y2 = y - 1
                    while (y2 > 0) and self.tilemap.get_tile(x, y2) in passable:
                        if   self.tilemap.get_tile(x, y2) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x, y2) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_RED_PATH2: ttype = T_RED_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_GROUND2: ttype = T_RED_PATH2
                        else: ttype = T_RED_PATH

                        self.tilemap.set_tile(x, y2, ttype)
                        y2 -= 1
                    y2 = y + 1
                    while (y2 < 32) and self.tilemap.get_tile(x, y2) in passable:
                        if   self.tilemap.get_tile(x, y2) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                        elif self.tilemap.get_tile(x, y2) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_RED_PATH2: ttype = T_RED_PATH2
                        elif self.tilemap.get_tile(x, y2) == T_GROUND2: ttype = T_RED_PATH2
                        else: ttype = T_RED_PATH

                        self.tilemap.set_tile(x, y2, ttype)
                        y2 += 1

    def _update_status(self):
        icon_y = int(2.5 * 24)
        icon1pos = int(3.5 * 24)
        icon2pos = int(5.0 * 24)
        icon3pos = int(6.5 * 24)

        red_red = (206, 60, 60)
        blu_blue = (60, 60, 206)

        black = (0, 0, 0)
        gray75 = (192, 192, 192)
        green = (0, 192, 0)

        color = red_red if (self.turn_player == 0) else gray75
        self.red_image.fill(color)
        color = blu_blue if (self.turn_player == 1) else gray75
        self.blu_image.fill(color)

        self.red_image.fill(black, (0, 0, 8*24, 4*24))
        self.blu_image.fill(black, (3, 3, 8*24, 4*24))

        icons = [
            [icon1pos, 1, 1, 1],
            [icon2pos, self.red_charge_wall, self.blu_charge_wall, self.CHARGE_WALL],
            [icon3pos, self.red_charge_floor, self.blu_charge_floor, self.CHARGE_FLOOR],
        ]

        for icon in icons:
            red_charge = 1.0 - 1.0 * icon[1] / icon[3]
            blu_charge = 1.0 - 1.0 * icon[2] / icon[3]

            red_color = green if (self.turn_player == 0) else gray75
            blu_color = green if (self.turn_player == 1) else gray75

            red_y = icon_y - 2 + int(red_charge * 28)
            red_h = 28 - int(red_charge * 28)

            blu_y = icon_y - 2 + int(blu_charge * 28)
            blu_h = 28 - int(blu_charge * 28)

            self.red_image.fill(red_color, (icon[0] - 2, red_y, 28, red_h))
            self.red_image.fill(black, (icon[0], icon_y, 24, 24))
            self.blu_image.fill(blu_color, (icon[0] - 2 + 3, blu_y + 3, 28, blu_h))
            self.blu_image.fill(black, (icon[0] + 3, icon_y + 3, 24, 24))

        rect = self.tileset.get_tile_rect(T_ICON_RED_PEG)
        self.red_image.blit(self.tileset.image, (icon1pos, icon_y) , rect)
        rect = self.tileset.get_tile_rect(T_ICON_BLU_PEG)
        self.blu_image.blit(self.tileset.image, (icon1pos+3, icon_y+3) , rect)

        rect = self.tileset.get_tile_rect(T_ICON_OBSTACLE)
        self.red_image.blit(self.tileset.image, (icon2pos, icon_y) , rect)
        self.blu_image.blit(self.tileset.image, (icon2pos+3, icon_y+3) , rect)

        rect = self.tileset.get_tile_rect(T_ICON_GROUND)
        self.red_image.blit(self.tileset.image, (icon3pos, icon_y) , rect)
        self.blu_image.blit(self.tileset.image, (icon3pos+3, icon_y+3) , rect)

        #TODO: Add text

    def _end_turn(self):
        self.turn += 1
        self.turn_player ^= 1

        if self.turn_player == 0:
            self.red_charge_wall  = min(self.red_charge_wall  + 1, self.CHARGE_WALL )
            self.red_charge_floor = min(self.red_charge_floor + 1, self.CHARGE_FLOOR)

            self.blu_charge_wall  = min(self.blu_charge_wall  + 1, self.CHARGE_WALL )
            self.blu_charge_floor = min(self.blu_charge_floor + 1, self.CHARGE_FLOOR)

        self._cast_paths()
        self._update_status()

    def run(self, delta_time):
        if self.quit_popup:
            if   self.parent.key_just_pressed("escape"): self.quit_popup = False
            elif self.parent.key_just_pressed("y"): self.parent.set_mode(MenuMode())
            #elif self.parent.key_just_pressed("y"): self.parent.running = False
            return

        if self.parent.key_just_pressed("escape"):
            self.quit_popup = True
            return

        tx = self.parent.mouse_pos[0] // 24
        ty = self.parent.mouse_pos[1] // 24
        if self.parent.mouse_pressed("left"):
            self.tilemap.set_tile(tx, ty, T_OBSTACLE2)
            self._cast_paths()
        if self.parent.mouse_pressed("right"):
            self.tilemap.set_tile(tx, ty, T_GROUND2)
            self._cast_paths()

        if self.parent.key_pressed("w"): self.red_cursor[1] -= 1
        if self.parent.key_pressed("s"): self.red_cursor[1] += 1
        if self.parent.key_pressed("a"): self.red_cursor[0] -= 1
        if self.parent.key_pressed("d"): self.red_cursor[0] += 1

        if self.parent.key_pressed("up"): self.blu_cursor[1] -= 1
        if self.parent.key_pressed("down"): self.blu_cursor[1] += 1
        if self.parent.key_pressed("left"): self.blu_cursor[0] -= 1
        if self.parent.key_pressed("right"): self.blu_cursor[0] += 1

        if self.parent.key_just_pressed("r") and self.turn == 0:
            self._generate_map()

        if self.parent.key_just_pressed("~"):
            t = raw_input(">>> ")
            exec(t)

        immutable_tiles = [
            T_RED_BASE, T_RED_PEG,
            T_BLU_BASE, T_BLU_PEG,
            T_OBSTACLE2, T_GROUND2,
            T_GOAL,
        ]

        if self.turn_player == 0:
            rc = self.red_cursor
            if self.parent.key_just_pressed("c"):
                if self.tilemap.get_tile(rc[0], rc[1]) in [T_RED_PATH, T_RED_PATH2]:
                    self.tilemap.set_tile(rc[0], rc[1], T_RED_PEG)
                    self._end_turn()

            if self.parent.key_just_pressed("v"):
                if self.red_charge_wall == self.CHARGE_WALL:
                    if self.tilemap.get_tile(rc[0], rc[1]) not in immutable_tiles:
                        self.tilemap.set_tile(rc[0], rc[1], T_OBSTACLE2)
                        self.red_charge_wall = -1
                        self._end_turn()

            if self.parent.key_just_pressed("b"):
                if self.red_charge_floor == self.CHARGE_FLOOR:
                    if self.tilemap.get_tile(rc[0], rc[1]) not in immutable_tiles:
                        self.tilemap.set_tile(rc[0], rc[1], T_GROUND2)
                        self.red_charge_floor = -1
                        self._end_turn()


        if self.turn_player == 1:
            bc = self.blu_cursor
            if self.parent.key_just_pressed("KP1"):
                if self.tilemap.get_tile(bc[0], bc[1]) in [T_BLU_PATH, T_BLU_PATH2]:
                    self.tilemap.set_tile(bc[0], bc[1], T_BLU_PEG)
                    self._end_turn()

            if self.parent.key_just_pressed("KP2"):
                if self.blu_charge_wall == self.CHARGE_WALL:
                    if self.tilemap.get_tile(bc[0], bc[1]) not in immutable_tiles:
                        self.tilemap.set_tile(bc[0], bc[1], T_OBSTACLE2)
                        self.blu_charge_wall = -1
                        self._end_turn()

            if self.parent.key_just_pressed("KP3"):
                if self.blu_charge_floor == self.CHARGE_FLOOR:
                    if self.tilemap.get_tile(bc[0], bc[1]) not in immutable_tiles:
                        self.tilemap.set_tile(bc[0], bc[1], T_GROUND2)
                        self.blu_charge_floor = -1
                        self._end_turn()

    def render(self, surface):
        surface.blit(self.tilemap.image, (0, 0))

        #Render cursors
        pos1 = (self.red_cursor[0] * 24, self.red_cursor[1] * 24)
        pos2 = (self.blu_cursor[0] * 24, self.blu_cursor[1] * 24)
        rect1 = self.tileset.get_tile_rect(T_CURSOR_RED)
        rect2 = self.tileset.get_tile_rect(T_CURSOR_BLU)
        rect3 = self.tileset.get_tile_rect(T_CURSOR_MIX)
        if pos1 == pos2:
            surface.blit(self.tileset.image, pos1, rect3)
        else:
            #Render RED cursor
            surface.blit(self.tileset.image, pos1, rect1)
            #Render BLU cursor
            surface.blit(self.tileset.image, pos2, rect2)

        surface.blit(self.red_image, (0, 0))
        blu_status_pos = (
            768 - self.blu_image.get_width(),
            768 - self.blu_image.get_height()
        )
        surface.blit(self.blu_image, blu_status_pos)

        if self.quit_popup:
            pos = (
                (surface.get_width() - self.quit_image.get_width()) / 2,
                (surface.get_height() - self.quit_image.get_height()) / 2,
            )
            surface.blit(self.quit_image, pos)

class PegGame(Game):
    def start(self):
        self.set_mode(MenuMode())

if __name__ == '__main__':
    #game = TestGame()
    #game.run()

    game = PegGame()
    game.run()
