#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import pygame

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

import math
import random
from collections import defaultdict

from engine import Game, Mode
from engine import Tilesheet, Tilemap

from engine import utils
from engine.math import rad2deg

def gen_list2d(width, height, fill=0):
    return [[fill for y in range(width)] for x in range(height)]

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
            "and prevent the enemy from doing so in subsequent 5 turns",
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
                elif (x == 0) and (y == 21):
                    tiles[x][y] = T_RED_BASE
                elif (x == 32 - 21) and (y == 31):
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

                obstacle_count = 0
                for (mx, my) in [(1, -1), (1, 0), (1, 1), (0, -1), (0, 1), (-1, -1), (-1, 0), (-1, 1)]:
                    obstacle_count += int(oldmap[x+mx][y+my] == T_OBSTACLE)
                floor_count = 8 - obstacle_count

                if oldmap[x][y] == T_OBSTACLE:
                    if random.randint(0, floor_count + 0) <= 1:
                        tiles[x][y] = T_GROUND
                elif oldmap[x][y] == T_GROUND:
                    if random.randint(0, obstacle_count + 4) == 0:
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
                    for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        x2 = x + direction[0]
                        y2 = y + direction[1]
                        f_passable = lambda x, y: self.tilemap.get_tile(x2, y2) in passable
                        while (x2 >= 0) and (x2 < 32) and (y2 >= 0) and (y2 < 32) and f_passable(x2, y2):
                            if   self.tilemap.get_tile(x2, y2) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                            elif self.tilemap.get_tile(x2, y2) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_GROUND2: ttype = T_BLU_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_BLU_PATH2: ttype = T_BLU_PATH2
                            else: ttype = T_BLU_PATH

                            self.tilemap.set_tile(x2, y2, ttype)
                            x2 += direction[0]
                            y2 += direction[1]

                if self.tilemap.get_tile(x, y) in [T_RED_BASE, T_RED_PEG]:
                    #Holy mother of god what is this white voodoo
                    for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        x2 = x + direction[0]
                        y2 = y + direction[1]
                        f_passable = lambda x, y: self.tilemap.get_tile(x2, y2) in passable
                        while (x2 >= 0) and (x2 < 32) and (y2 >= 0) and (y2 < 32) and f_passable(x2, y2):
                            if   self.tilemap.get_tile(x2, y2) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                            elif self.tilemap.get_tile(x2, y2) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_GROUND2: ttype = T_RED_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_RED_PATH2: ttype = T_RED_PATH2
                            else: ttype = T_RED_PATH

                            self.tilemap.set_tile(x2, y2, ttype)
                            x2 += direction[0]
                            y2 += direction[1]

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
            [icon1pos, 1, 1, 1, T_ICON_RED_PEG, T_ICON_BLU_PEG],
            [icon2pos, self.red_charge_wall, self.blu_charge_wall, self.CHARGE_WALL, T_ICON_OBSTACLE, T_ICON_OBSTACLE],
            [icon3pos, self.red_charge_floor, self.blu_charge_floor, self.CHARGE_FLOOR, T_ICON_GROUND, T_ICON_GROUND],
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

            rect = self.tileset.get_tile_rect(icon[4])
            self.red_image.blit(self.tileset.image, (icon[0], icon_y) , rect)
            rect = self.tileset.get_tile_rect(icon[5])
            self.blu_image.blit(self.tileset.image, (icon[0]+3, icon_y+3) , rect)

        font = pygame.font.Font(None, 32)

        red_text = font.render("Player 1", 1, red_red)
        red_textpos = red_text.get_rect(left=10, top=10)

        blu_text = font.render("Player 2", 1, blu_blue)
        blu_textpos = blu_text.get_rect(left=13, top=13)

        self.red_image.blit(red_text, red_textpos)
        self.blu_image.blit(blu_text, blu_textpos)

        #TODO: Add key captions

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

        if self.red_cursor[1] < 0: self.red_cursor[1] = 0
        if self.red_cursor[1] > 31: self.red_cursor[1] = 31
        if self.red_cursor[0] < 0: self.red_cursor[0] = 0
        if self.red_cursor[0] > 31: self.red_cursor[0] = 31

        if self.parent.key_pressed("up"): self.blu_cursor[1] -= 1
        if self.parent.key_pressed("down"): self.blu_cursor[1] += 1
        if self.parent.key_pressed("left"): self.blu_cursor[0] -= 1
        if self.parent.key_pressed("right"): self.blu_cursor[0] += 1

        if self.blu_cursor[1] < 0: self.blu_cursor[1] = 0
        if self.blu_cursor[1] > 31: self.blu_cursor[1] = 31
        if self.blu_cursor[0] < 0: self.blu_cursor[0] = 0
        if self.blu_cursor[0] > 31: self.blu_cursor[0] = 31

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
    game = PegGame()
    game.run()
