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
from engine._math import rad2deg

from engine.input import mouse, keyboard

def gen_list2d(width, height, fill=0):
    return [[fill for y in range(width)] for x in range(height)]

###Here starts the game

T_FLOOR   = 0
T_FLOOR2  = 12
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
T_ICON_FLOOR = 12


IMMUTABLE_TILES = [
    T_RED_BASE, T_RED_PEG,
    T_BLU_BASE, T_BLU_PEG,
    T_OBSTACLE2, T_FLOOR2,
    T_GOAL,
]

PASSABLE_TILES = [
    T_FLOOR, T_FLOOR2,
    T_BLU_PATH, T_RED_PATH, T_MIX_PATH,
    T_BLU_PATH2, T_RED_PATH2, T_MIX_PATH2,
]

CHARGE_OBSTACLE = 5
CHARGE_FLOOR = 3

P_RED = 0
P_BLU = 1

RED_RED = (206, 60, 60)
BLU_BLUE = (60, 60, 206)

PROTECTED_RADIUS = 3

class MenuMode(Mode):
    def start(self):
        self.visuals = pygame.Surface((768, 768))
        self.visuals.fill((0, 0, 0))

        font = pygame.font.Font(None, 32)

        lines = ["1. Local Play", "2. Multiplayer (host)", "3. Multiplayer (join)", "4. Instructions", "5. Quit"]

        for i, line in enumerate(lines):
            text = font.render(line, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 - len(lines) * 18 + i * 36))
            self.visuals.blit(text, textpos)

    def run(self, delta_time):
        if keyboard.just_pressed("1"):
            self.parent.set_mode(PegLocalMode())
        elif keyboard.just_pressed("2"):
            self.parent.set_mode(LobbyMode(host = True))
        elif keyboard.just_pressed("3"):
            self.parent.set_mode(LobbyMode(host = False))
        elif keyboard.just_pressed("4"):
            self.parent.set_mode(InstructionsMode())
        elif keyboard.just_pressed("5"):
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
            "while preventing the enemy from doing so her- or him- self",
            "",
            "Rules:",
            "1. You can only place your pegs in direct line of sight from one of your pegs",
            "2. Every %i turns you can place an obstacle anywhere on the map" % CHARGE_OBSTACLE,
            "3. Every %i turns you can remove an obstacle from anywhere on the map" % CHARGE_FLOOR,
            "4. You can not modify already modified terrain",
            "5. You can not place obstacles next to enemy pegs",
            "6. You can not place obstacles in %i tile radius around the goal" % PROTECTED_RADIUS,
            "",
            "Red player controls(also multiplayer controls):",
            "W/S/A/D - move cursor",
            "C/V/B - place peg/obstacle/floor respectively, if charged",
            "",
            "Blue player controls:",
            "Up/Down/Left/Right - move cursor",
            "Num1/Num2/Num3 - place peg/obstacle/floor respectively, if charged",
            "",
            "Other controls:",
            "r - generate a new map, only works on the first turn, for balancing purposes",
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

    def run(self, delta_time):
        if keyboard.just_pressed("escape"):
            self.parent.set_mode(MenuMode())

    def render(self, surface):
        surface.blit(self.visuals, (0, 0))

class PegMode(Mode):
    def start(self):
        self.tileset = Tilesheet("tileset.png", 24, 24) #Tileset
        self.tilemap = Tilemap(self.tileset, 32, 32) #On-screen tiles

        self._generate_map()

        self.turn = 0
        self.turn_player = 0
        self.victorious_side = None
        self.quit_popup = False

        self.red_cursor = [ 0, 19]
        self.blu_cursor = [13, 31]

        self.red_charge_wall = 0
        self.red_charge_floor = 0
        self.blu_charge_wall = 0
        self.blu_charge_floor = 0

        self.red_image = pygame.Surface((8 * 24 + 3, 4 * 24 + 3))
        self.blu_image = pygame.Surface((8 * 24 + 3, 4 * 24 + 3))

        self._prerender_popups()

        self._update_status()

    def _prerender_popups(self):
        font = pygame.font.Font(None, 32)

        text = font.render("Really quit (Y/Esc)?", 1, (230, 230, 50))
        textpos = text.get_rect()
        self.quit_image = pygame.Surface((textpos[2], textpos[3]))
        self.quit_image.blit(text, textpos)

        text1 = font.render("Red player wins!", 1, RED_RED )
        text2 = font.render("Blue player wins!", 1, BLU_BLUE)
        textpos = text1.get_rect(left=3, top=3)
        self.victory_image_red = pygame.Surface((textpos[2] + 6, textpos[3] + 6))
        self.victory_image_blu = pygame.Surface((textpos[2] + 6, textpos[3] + 6))
        self.victory_image_red.fill(RED_RED)
        self.victory_image_red.fill((0,0,0), textpos)
        self.victory_image_red.blit(text1, textpos)

        self.victory_image_blu.fill(BLU_BLUE)
        self.victory_image_blu.fill((0,0,0), textpos)
        self.victory_image_blu.blit(text2, textpos)

    def _generate_map(self):
        tiles = gen_list2d(32, 32)

        density_sectors = [
            [10, 10, 10,  9,  6,  4,  3,  1],
            [10, 10,  9,  6,  8,  3,  2],
            [10,  9,  3,  5,  2,  3],
            [ 9,  7,  8,  3,  2],
            [ 4,  3,  2,  1],
            [ 0,  1,  2],
            [ 1,  4],
            [ 8]
        ]
        for y, row in enumerate(density_sectors):
            for x in range(len(row), 8):
                d = density_sectors[7-x][7-y]
                density_sectors[y] += [d]

        for x in range(32):
            for y in range(32):
                if (x + y <= 15) or ((32-x) + (32-y) <= 15):
                    tiles[x][y] = T_OBSTACLE
                elif (x + (32-y) <= 5):
                    tiles[x][y] = T_OBSTACLE
                elif (x == 0) and (y == 21):
                    tiles[x][y] = T_RED_BASE
                elif (x == 31 - 21) and (y == 31):
                    tiles[x][y] = T_BLU_BASE
                elif (x == 30) and (y == 1):
                    tiles[x][y] = T_GOAL
                elif (x > 1) and (y < 30):
                    d = density_sectors[y // 4][x // 4]
                    if random.randint(0, 15) <= d:
                        tiles[x][y] = T_OBSTACLE
                    else:
                        tiles[x][y] = T_FLOOR

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

                d = density_sectors[y // 4][x // 4]

                if oldmap[x][y] == T_OBSTACLE:
                    if random.randint(0, max(0, floor_count + d)) <= 3:
                        tiles[x][y] = T_FLOOR
                elif oldmap[x][y] == T_FLOOR:
                    if random.randint(0, obstacle_count + 10 - d) == 0:
                        tiles[x][y] = T_OBSTACLE

        for x in range(0, 32):
            for y in range(0, 32 - x):
                if tiles[x][y] in [T_OBSTACLE, T_FLOOR]:
                    tiles[31 - y][31 - x] = tiles[x][y]

        self.tilemap.from_list(tiles)

        self._cast_paths()

    def _cast_paths(self):
        #Clear paths
        for x in range(32):
            for y in range(32):
                if self.tilemap.get_tile(x, y) in [T_BLU_PATH, T_RED_PATH, T_MIX_PATH]:
                    self.tilemap.set_tile(x, y, T_FLOOR)
                if self.tilemap.get_tile(x, y) in [T_BLU_PATH2, T_RED_PATH2, T_MIX_PATH2]:
                    self.tilemap.set_tile(x, y, T_FLOOR2)
        #Recalculate paths
        for x in range(32):
            for y in range(32):
                d = [
                    {
                        "own_pegs":  [T_BLU_BASE, T_BLU_PEG],
                        "enemy_path":  [T_RED_PATH, T_MIX_PATH],
                        "enemy_path2": [T_RED_PATH2, T_MIX_PATH2],
                        "own_path": T_BLU_PATH,
                        "own_path2": T_BLU_PATH2,
                    },
                    {
                        "own_pegs":  [T_RED_BASE, T_RED_PEG],
                        "enemy_path":  [T_BLU_PATH, T_MIX_PATH],
                        "enemy_path2": [T_BLU_PATH2, T_MIX_PATH2],
                        "own_path": T_RED_PATH,
                        "own_path2": T_RED_PATH2,
                    }
                ]
                for dataset in d:
                    if self.tilemap.get_tile(x, y) in dataset["own_pegs"]:
                        for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            x2 = x + direction[0]
                            y2 = y + direction[1]
                            f_passable_tiles = lambda x, y: self.tilemap.get_tile(x2, y2) in PASSABLE_TILES
                            while (x2 >= 0) and (x2 < 32) and (y2 >= 0) and (y2 < 32) and f_passable_tiles(x2, y2):
                                if   self.tilemap.get_tile(x2, y2) in dataset["enemy_path"]:  ttype = T_MIX_PATH
                                elif self.tilemap.get_tile(x2, y2) in dataset["enemy_path2"]: ttype = T_MIX_PATH2
                                elif self.tilemap.get_tile(x2, y2) == T_FLOOR2: ttype = dataset["own_path2"]
                                elif self.tilemap.get_tile(x2, y2) == dataset["own_path2"]: ttype = dataset["own_path2"]
                                else: ttype = dataset["own_path"]

                                self.tilemap.set_tile(x2, y2, ttype)
                                x2 += direction[0]
                                y2 += direction[1]

    def place_peg(self, player, x, y):
        paths = (
            [T_RED_PATH, T_RED_PATH2],
            [T_BLU_PATH, T_BLU_PATH2]
        )[player] + [T_MIX_PATH, T_MIX_PATH2]
        peg = (T_RED_PEG, T_BLU_PEG)[player]

        if self.tilemap.get_tile(x, y) in paths:
            self.tilemap.set_tile(x, y, peg)
            self._end_turn()
            return True

        return False

    def place_obstacle(self, player, x, y):
        if x > (31 - PROTECTED_RADIUS) and y < PROTECTED_RADIUS:
            return False

        charge = (self.red_charge_wall, self.blu_charge_wall)[player]
        if charge == CHARGE_OBSTACLE:
            for d in [(-1, 0), ( 1, 0), ( 0,-1), ( 0, 1)]:
                x2, y2 = x + d[0], y + d[1]
                if x2 < 0 or x2 > 31 or y2 < 0 or y2 > 31: continue

                enemy_pegs = (
                    [T_RED_PEG, T_RED_BASE],
                    [T_BLU_PEG, T_BLU_BASE],
                )[player ^ 1]

                if self.tilemap.get_tile(x2, y2) in enemy_pegs:
                    return False

            if self.tilemap.get_tile(x, y) not in IMMUTABLE_TILES:
                self.tilemap.set_tile(x, y, T_OBSTACLE2)
                if player == P_RED: self.red_charge_wall = -1
                else: self.blu_charge_wall = -1

                self._end_turn()
                return True

        return False

    def place_floor(self, player, x, y):
        charge = (self.red_charge_floor, self.blu_charge_floor)[player]
        if charge == CHARGE_FLOOR:
            if self.tilemap.get_tile(x, y) not in IMMUTABLE_TILES:
                self.tilemap.set_tile(x, y, T_FLOOR2)
                if player == P_RED: self.red_charge_floor = -1
                else: self.blu_charge_floor = -1

                self._end_turn()
                return True

        return False

    def _update_status(self):
        icon_y = int(2.5 * 24)
        icon1pos = int(3.5 * 24)
        icon2pos = int(5.0 * 24)
        icon3pos = int(6.5 * 24)

        black = (0, 0, 0)
        gray75 = (192, 192, 192)
        green = (0, 192, 0)

        color = RED_RED if (self.turn_player == 0) else gray75
        self.red_image.fill(color)
        color = BLU_BLUE if (self.turn_player == 1) else gray75
        self.blu_image.fill(color)

        self.red_image.fill(black, (0, 0, 8*24, 4*24))
        self.blu_image.fill(black, (3, 3, 8*24, 4*24))

        icons = [
            [icon1pos, 1, 1, 1, T_ICON_RED_PEG, T_ICON_BLU_PEG],
            [icon2pos, self.red_charge_wall, self.blu_charge_wall, CHARGE_OBSTACLE, T_ICON_OBSTACLE, T_ICON_OBSTACLE],
            [icon3pos, self.red_charge_floor, self.blu_charge_floor, CHARGE_FLOOR, T_ICON_FLOOR, T_ICON_FLOOR],
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

        red_text = font.render("Player 1", 1, RED_RED)
        red_textpos = red_text.get_rect(left=10, top=10)

        blu_text = font.render("Player 2", 1, BLU_BLUE)
        blu_textpos = blu_text.get_rect(left=13, top=13)

        self.red_image.blit(red_text, red_textpos)
        self.blu_image.blit(blu_text, blu_textpos)

        #TODO: Add key captions

    def _end_turn(self):
        self.turn += 1
        self.turn_player ^= 1

        if self.turn_player == 0:
            self.red_charge_wall  = min(self.red_charge_wall  + 1, CHARGE_OBSTACLE )
            self.red_charge_floor = min(self.red_charge_floor + 1, CHARGE_FLOOR)

            self.blu_charge_wall  = min(self.blu_charge_wall  + 1, CHARGE_OBSTACLE )
            self.blu_charge_floor = min(self.blu_charge_floor + 1, CHARGE_FLOOR)

        self._cast_paths()
        self._update_status()

    def _handle_input(self):
        pass

    def run(self, delta_time):
        goal_pos = (31 - 1, 1)
        for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            x = goal_pos[0] + direction[0]
            y = goal_pos[1] + direction[1]
            tile = self.tilemap.get_tile(x, y)
            if   tile == T_RED_PEG: self.victorious_side = P_RED
            elif tile == T_BLU_PEG: self.victorious_side = P_BLU

        if self.victorious_side is not None:
            if keyboard.just_pressed("escape"): self.parent.set_mode(MenuMode())
            elif keyboard.just_pressed("enter"): self.parent.set_mode(MenuMode())
            return

        if self.quit_popup:
            if   keyboard.just_pressed("escape"): self.quit_popup = False
            elif keyboard.just_pressed("y"): self.parent.set_mode(MenuMode())
            #elif keyboard.just_pressed("y"): self.parent.running = False
            return

        if keyboard.just_pressed("escape"):
            self.quit_popup = True
            return



        self._handle_input()

    def render(self, surface):
        surface.blit(self.tilemap.image, (0, 0))

        color = (255, 0, 255)
        interval = 768 / 8

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

        if self.victorious_side is not None:
            pos = (
                (surface.get_width() - self.victory_image_red.get_width()) / 2,
                (surface.get_height() - self.victory_image_red.get_height()) / 2,
            )
            if self.victorious_side == P_RED:
                surface.blit(self.victory_image_red, pos)
            else:
                surface.blit(self.victory_image_blu, pos)
        elif self.quit_popup:
            pos = (
                (surface.get_width() - self.quit_image.get_width()) / 2,
                (surface.get_height() - self.quit_image.get_height()) / 2,
            )
            surface.blit(self.quit_image, pos)

class PegLocalMode(PegMode):
    def _handle_input(self):
        if keyboard.pressed("w"): self.red_cursor[1] -= 1
        if keyboard.pressed("s"): self.red_cursor[1] += 1
        if keyboard.pressed("a"): self.red_cursor[0] -= 1
        if keyboard.pressed("d"): self.red_cursor[0] += 1

        if self.red_cursor[1] < 0: self.red_cursor[1] = 0
        if self.red_cursor[1] > 31: self.red_cursor[1] = 31
        if self.red_cursor[0] < 0: self.red_cursor[0] = 0
        if self.red_cursor[0] > 31: self.red_cursor[0] = 31

        if keyboard.pressed("up"): self.blu_cursor[1] -= 1
        if keyboard.pressed("down"): self.blu_cursor[1] += 1
        if keyboard.pressed("left"): self.blu_cursor[0] -= 1
        if keyboard.pressed("right"): self.blu_cursor[0] += 1

        if self.blu_cursor[1] < 0: self.blu_cursor[1] = 0
        if self.blu_cursor[1] > 31: self.blu_cursor[1] = 31
        if self.blu_cursor[0] < 0: self.blu_cursor[0] = 0
        if self.blu_cursor[0] > 31: self.blu_cursor[0] = 31

        if keyboard.just_pressed("r") and self.turn == 0:
            self._generate_map()

        if keyboard.just_pressed("~"):
            t = raw_input(">>> ")
            exec(t)

        if self.turn_player == P_RED:
            rc = self.red_cursor
            if keyboard.just_pressed("c"):
                self.place_peg(P_RED, rc[0], rc[1])

            if keyboard.just_pressed("v"):
                self.place_obstacle(P_RED, rc[0], rc[1])

            if keyboard.just_pressed("b"):
                self.place_floor(P_RED, rc[0], rc[1])

        if self.turn_player == P_BLU:
            bc = self.blu_cursor
            if keyboard.just_pressed("KP1"):
                self.place_peg(P_BLU, bc[0], bc[1])

            if keyboard.just_pressed("KP2"):
                self.place_obstacle(P_BLU, bc[0], bc[1])

            if keyboard.just_pressed("KP3"):
                self.place_floor(P_BLU, bc[0], bc[1])

import threading
import socket, select
import time

GAME_PORT = 39612

class NetworkConnection(threading.Thread):
    def __init__(self, host = False):
        threading.Thread.__init__(self)
        self.host = host

        self.data_in = []
        self.data_out = []

        if self.host:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("0.0.0.0", 39612))
            #Allow reusing the socket immediately (on Linux at least)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket = None
        else:
            self.server_socket = None
            self.socket = None

        self.running = True

    def connect(self, host_ip):
        if self.host: return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((host_ip, GAME_PORT))

        print "Connected to server"

    def run(self):
        self.running = True

        if self.host:
            self.server_socket.listen(5)
            while self.socket is None and self.running:
                try:
                    client, address = self.server_socket.accept()
                    self.socket = client
                    print "Client connected"
                except:
                    print "Client not connected, connection shut down"


        prev_data = ""

        while self.running:
            if self.socket is None:
                time.sleep(0.25) #Don't waste CPU cycles
                continue

            #Accept incoming data and push it onto the queue
            data = self.socket.recv(4096)
            if not data:
                self.socket.close()
                self.running = False
                continue

            #Handle stuff that got broken into multiple parts
            # a.k.a. sending the map via one .send()
            if not data.endswith("\n"):
                prev_data += data
                continue
            elif prev_data != "":
                data = prev_data + data
                prev_data = ""

            if "\n" in data[:-1]:
                data = data.split("\n")
            else:
                data = [data]

            for d in data:
                if d:
                    self.data_in.append(d)

        print "Shutting down networking thread"

    def connected(self):
        return self.socket is not None

    def close(self):
        self.running = False

        if self.server_socket is not None:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
            self.server_socket = None
            print "Closed server socket"

        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass #Might be closed by the other endpoint already
            self.socket.close()
            self.socket = None
            print "Closed client socket"


    def receive(self):
        """Usage: for data in connection.receive(): blah blah"""
        while len(self.data_in) > 0:
            data = self.data_in[0]
            self.data_in = self.data_in[1:]
            yield data

    def send(self, data):
        try:
            self.socket.send(data + "\n")
        except:
            self.close()

class LobbyMode(Mode):
    def __init__(self, host = False):
        Mode.__init__(self)
        self.host = host

        self.ip_input = ""

        self.connection = NetworkConnection(host)
        self.connection.start()

    def run(self, delta_time):
        if keyboard.just_pressed("escape"):
            self.connection.close()
            self.parent.set_mode(MenuMode())

        if self.host:
            if self.connection.connected():
                print "Maaaaagic is happeneing to me"
                self.parent.set_mode(PegMultiplayerMode(self.connection, 0))
            return #Ain't anything more an host can do

        for char in keyboard.key_input:
            if char == pygame.K_BACKSPACE:
                if self.ip_input != "":
                    self.ip_input = self.ip_input[:-1]
            elif char == pygame.K_RETURN: #Enter
                try:
                    print "Performing maaaagic"
                    self.connection.connect(self.ip_input)
                    self.parent.set_mode(PegMultiplayerMode(self.connection, 1))
                except:
                    self.ip_input = ""
            elif char in range(ord('0'), ord('9')+1) + [ord('.')]: #Sowwy, IPv4 only
                self.ip_input += chr(char)

    def render(self, surface):
        font = pygame.font.Font(None, 32)

        surface.fill((0, 0, 0))

        if self.host:
            text = font.render("Waiting for a connection on port %i (Esc to cancel)..." % GAME_PORT, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384))
            surface.blit(text, textpos)
        else:
            text = font.render("Enter IP(Esc to cancel):", 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 - 16))
            surface.blit(text, textpos)

            text = font.render("%s_" % self.ip_input, 1, (230, 230, 50))
            textpos = text.get_rect(center=(384, 384 + 16))
            surface.blit(text, textpos)

class PegMultiplayerMode(PegMode):
    def __init__(self, connection, side):
        print "K, starting multiplayer game on %s" % ["RED", "BLU"][side]
        self.connection = connection
        self.side = side #0 for RED, 1 for BLU

        self.last_cursor_message = 0

    def start(self):
        PegMode.start(self)

        if self.side == 0:
            self.send_map()

    def send_map(self):
        flat_list = []
        for row in self.tilemap.tiles:
            flat_list.extend(row)

        map_data = " ".join(map(lambda i: str(i), flat_list))

        self.connection.send("MAP %s" % map_data)

    def place_peg(self, player, x, y):
        success = PegMode.place_peg(self, player, x, y)
        if success:
            self.connection.send("PLACE_PEG %i %i" % (x, y))
            self.connection.send("END_TURN")

    def place_floor(self, player, x, y):
        success = PegMode.place_floor(self, player, x, y)
        if success:
            self.connection.send("PLACE_FLOOR %i %i" % (x, y))
            self.connection.send("END_TURN")

    def place_obstacle(self, player, x, y):
        success = PegMode.place_obstacle(self, player, x, y)
        if success:
            self.connection.send("PLACE_OBSTACLE %i %i" % (x, y))
            self.connection.send("END_TURN")

    def _handle_input(self):
        for data in self.connection.receive():
            data = data.replace("\n", "")
            command, _, params = data.partition(" ")
            params = params.split(" ")
            if command.startswith("PLACE_"):
                if command == "PLACE_PEG":
                    tile = T_RED_PEG if self.side == 1 else T_BLU_PEG
                elif command == "PLACE_OBSTACLE":
                    tile = T_OBSTACLE2
                    if self.side == P_RED: self.blu_charge_wall = -1
                    else: self.red_charge_wall = -1
                elif command == "PLACE_FLOOR":
                    tile = T_FLOOR2
                    if self.side == P_RED: self.blu_charge_floor = -1
                    else: self.red_charge_floor = -1

                x = int(params[0])
                y = int(params[1])

                self.tilemap.set_tile(x, y, tile)
            elif command == "END_TURN":
                print "Ending turn"
                self._end_turn()
            elif command == "MOVE_CURSOR":
                x = int(params[0])
                y = int(params[1])
                timestamp = int(params[2])

                if timestamp > self.last_cursor_message:
                    self.last_cursor_message = timestamp
                    if self.side == 0:
                        self.blu_cursor = [x, y]
                    else:
                        self.red_cursor = [x, y]
            elif command == "MAP":
                tiles = []
                for y in range(32):
                    row = params[y * 32 : y * 32 + 32]
                    row = map(lambda s: int(s), row)
                    tiles.append(row)
                self.tilemap.from_list(tiles)
            elif command == "DISCONNECT":
                self.connection.close()
                self.parent.set_mode(MenuMode())

        if self.turn == 0 and keyboard.just_pressed("r"):
            self._generate_map()
            self.send_map()

        if self.side == 0:
            old_cursor = self.red_cursor[:]
            if keyboard.pressed('w'): self.red_cursor[1] -= 1
            if keyboard.pressed('s'): self.red_cursor[1] += 1
            if keyboard.pressed('a'): self.red_cursor[0] -= 1
            if keyboard.pressed('d'): self.red_cursor[0] += 1
            if self.red_cursor[1] < 0: self.red_cursor[1] = 0
            if self.red_cursor[1] > 31: self.red_cursor[1] = 31
            if self.red_cursor[0] < 0: self.red_cursor[0] = 0
            if self.red_cursor[0] > 31: self.red_cursor[0] = 31

            if self.red_cursor != old_cursor:
                rc = self.red_cursor
                self.connection.send("MOVE_CURSOR %i %i %i" % (rc[0], rc[1], self.frame))

            if self.turn_player == self.side:
                rc = self.red_cursor
                if keyboard.just_pressed("c"):
                    self.place_peg(P_RED, rc[0], rc[1])

                if keyboard.just_pressed("v"):
                    self.place_obstacle(P_RED, rc[0], rc[1])

                if keyboard.just_pressed("b"):
                    self.place_floor(P_RED, rc[0], rc[1])
        else:
            old_cursor = self.blu_cursor[:]
            if keyboard.pressed('w'): self.blu_cursor[1] -= 1
            if keyboard.pressed('s'): self.blu_cursor[1] += 1
            if keyboard.pressed('a'): self.blu_cursor[0] -= 1
            if keyboard.pressed('d'): self.blu_cursor[0] += 1
            if self.blu_cursor[1] < 0: self.blu_cursor[1] = 0
            if self.blu_cursor[1] > 31: self.blu_cursor[1] = 31
            if self.blu_cursor[0] < 0: self.blu_cursor[0] = 0
            if self.blu_cursor[0] > 31: self.blu_cursor[0] = 31

            if self.blu_cursor != old_cursor:
                bc = self.blu_cursor
                self.connection.send("MOVE_CURSOR %i %i %i" % (bc[0], bc[1], self.frame))

            if self.turn_player == self.side:
                bc = self.blu_cursor
                if keyboard.just_pressed("c"):
                    self.place_peg(P_BLU, bc[0], bc[1])

                if keyboard.just_pressed("v"):
                    self.place_obstacle(P_BLU, bc[0], bc[1])

                if keyboard.just_pressed("b"):
                    self.place_floor(P_BLU, bc[0], bc[1])

    def stop(self):
        #We're doing this in stop so it gets done correctly when game is quit via Esc, Y
        if self.connection.connected():
            print "Sending disconnect signal"
            self.connection.send("DISCONNECT")
            self.connection.close()

class PegGame(Game):
    def start(self):
        self.fps = 15 #Let's just make moving cursor slower with this...
        self.set_mode(MenuMode())
        self.set_title("A Game of Pegs for Two")

if __name__ == '__main__':
    game = PegGame()
    game.run()
