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

CHARGE_OBSTACLE = 3
CHARGE_FLOOR = 5

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
        if self.parent.key_just_pressed("1"):
            self.parent.set_mode(PegLocalMode())
        elif self.parent.key_just_pressed("2"):
            self.parent.set_mode(LobbyMode(host = True))
        elif self.parent.key_just_pressed("3"):
            self.parent.set_mode(LobbyMode(host = False))
        elif self.parent.key_just_pressed("4"):
            self.parent.set_mode(InstructionsMode())
        elif self.parent.key_just_pressed("5"):
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
            "3. Every %i turns you can place an obstacle anywhere on the map" % CHARGE_OBSTACLE,
            "4. Every %i turns you can remove an obstacle from anywhere on the map" % CHARGE_FLOOR,
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

class PegMode(Mode):
    def start(self):
        self.tileset = Tilesheet("tileset.png", 24, 24) #Tileset
        self.tilemap = Tilemap(self.tileset, 32, 32) #On-screen tiles

        self._generate_map()

        self.turn = 0
        self.turn_player = 0

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

                if oldmap[x][y] == T_OBSTACLE:
                    if random.randint(0, floor_count + 0) <= 1:
                        tiles[x][y] = T_FLOOR
                elif oldmap[x][y] == T_FLOOR:
                    if random.randint(0, obstacle_count + 4) == 0:
                        tiles[x][y] = T_OBSTACLE

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
                if self.tilemap.get_tile(x, y) in [T_BLU_BASE, T_BLU_PEG]:
                    #Holy mother of god what is this black voodoo
                    for direction in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        x2 = x + direction[0]
                        y2 = y + direction[1]
                        f_PASSABLE_TILES = lambda x, y: self.tilemap.get_tile(x2, y2) in PASSABLE_TILES
                        while (x2 >= 0) and (x2 < 32) and (y2 >= 0) and (y2 < 32) and f_PASSABLE_TILES(x2, y2):
                            if   self.tilemap.get_tile(x2, y2) in [T_RED_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                            elif self.tilemap.get_tile(x2, y2) in [T_RED_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_FLOOR2: ttype = T_BLU_PATH2
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
                        f_PASSABLE_TILES = lambda x, y: self.tilemap.get_tile(x2, y2) in PASSABLE_TILES
                        while (x2 >= 0) and (x2 < 32) and (y2 >= 0) and (y2 < 32) and f_PASSABLE_TILES(x2, y2):
                            if   self.tilemap.get_tile(x2, y2) in [T_BLU_PATH, T_MIX_PATH]: ttype = T_MIX_PATH
                            elif self.tilemap.get_tile(x2, y2) in [T_BLU_PATH2, T_MIX_PATH2]: ttype = T_MIX_PATH2
                            elif self.tilemap.get_tile(x2, y2) == T_FLOOR2: ttype = T_RED_PATH2
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
            self.red_charge_wall  = min(self.red_charge_wall  + 1, CHARGE_OBSTACLE )
            self.red_charge_floor = min(self.red_charge_floor + 1, CHARGE_FLOOR)

            self.blu_charge_wall  = min(self.blu_charge_wall  + 1, CHARGE_OBSTACLE )
            self.blu_charge_floor = min(self.blu_charge_floor + 1, CHARGE_FLOOR)

        self._cast_paths()
        self._update_status()

    def _handle_input(self):
        pass

    def run(self, delta_time):
        if self.quit_popup:
            if   self.parent.key_just_pressed("escape"): self.quit_popup = False
            elif self.parent.key_just_pressed("y"): self.parent.set_mode(MenuMode())
            #elif self.parent.key_just_pressed("y"): self.parent.running = False
            return

        if self.parent.key_just_pressed("escape"):
            self.quit_popup = True
            return

        self._handle_input()

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

class PegLocalMode(PegMode):
    def _handle_input(self):
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

        if self.turn_player == 0:
            rc = self.red_cursor
            if self.parent.key_just_pressed("c"):
                if self.tilemap.get_tile(rc[0], rc[1]) in [T_RED_PATH, T_RED_PATH2]:
                    self.tilemap.set_tile(rc[0], rc[1], T_RED_PEG)
                    self._end_turn()

            if self.parent.key_just_pressed("v"):
                if self.red_charge_wall == CHARGE_OBSTACLE:
                    if self.tilemap.get_tile(rc[0], rc[1]) not in IMMUTABLE_TILES:
                        self.tilemap.set_tile(rc[0], rc[1], T_OBSTACLE2)
                        self.red_charge_wall = -1
                        self._end_turn()

            if self.parent.key_just_pressed("b"):
                if self.red_charge_floor == CHARGE_FLOOR:
                    if self.tilemap.get_tile(rc[0], rc[1]) not in IMMUTABLE_TILES:
                        self.tilemap.set_tile(rc[0], rc[1], T_FLOOR2)
                        self.red_charge_floor = -1
                        self._end_turn()


        if self.turn_player == 1:
            bc = self.blu_cursor
            if self.parent.key_just_pressed("KP1"):
                if self.tilemap.get_tile(bc[0], bc[1]) in [T_BLU_PATH, T_BLU_PATH2]:
                    self.tilemap.set_tile(bc[0], bc[1], T_BLU_PEG)
                    self._end_turn()

            if self.parent.key_just_pressed("KP2"):
                if self.blu_charge_wall == CHARGE_OBSTACLE:
                    if self.tilemap.get_tile(bc[0], bc[1]) not in IMMUTABLE_TILES:
                        self.tilemap.set_tile(bc[0], bc[1], T_OBSTACLE2)
                        self.blu_charge_wall = -1
                        self._end_turn()

            if self.parent.key_just_pressed("KP3"):
                if self.blu_charge_floor == CHARGE_FLOOR:
                    if self.tilemap.get_tile(bc[0], bc[1]) not in IMMUTABLE_TILES:
                        self.tilemap.set_tile(bc[0], bc[1], T_FLOOR2)
                        self.blu_charge_floor = -1
                        self._end_turn()

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
            self.server_socket.bind((socket.gethostname(), 39612))
            #Allow reusing the socket immediately (on Linux at least)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket = None
        else:
            self.server_socket = None
            self.socket = None

    def connect(self, host_ip):
        if self.host: return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((host_ip, GAME_PORT))

        print "Connected to server"

    def run(self):
        running = True

        if self.host:
            self.server_socket.listen(5)
            while self.socket is None and running:
                client, address = self.server_socket.accept()
                self.socket = client
                print "Client connected"

        while running:
            if self.socket is None:
                time.sleep(0.25) #Don't waste CPU cycles
                continue

            #Accept incoming data and push it onto the queue
            data = self.socket.recv(4096)
            if data:
                self.data_in.append(data)
            else:
                self.socket.close()
                running = False

    def connected(self):
        return self.socket is not None

    def close(self):
        self.running = False

        if self.server_socket is not None:
            self.server_socket.close()
            print "Closed server socket"

        if self.socket is not None:
            self.socket.close()
            print "Closed client socket"

    def receive(self):
        """Usage: for data in connection.receive(): blah blah"""
        while len(self.data_in) > 0:
            data = self.data_in[0]
            self.data_in = self.data_in[1:]
            yield data

    def send(self, data):
        self.socket.send(data)

class LobbyMode(Mode):
    def __init__(self, host = False):
        Mode.__init__(self)
        self.host = host

        self.ip_input = ""

        self.connection = NetworkConnection(host)
        self.connection.start()

    def run(self, delta_time):
        if self.parent.key_just_pressed("escape"):
            self.parent.set_mode(MenuMode())
            self.connection.close()

        if self.host:
            if self.connection.connected():
                print "Maaaaagic is happeneing to me"
                self.parent.set_mode(PegMultiplayerMode(self.connection, 0))
            return #Ain't anything more an host can do

        for char in self.parent.key_input:
            if char == pygame.K_BACKSPACE:
                if self.ip_input != "":
                    self.ip_input = self.ip_input[:-1]
            elif char == 13:
                try:
                    print "Performing maaaagic"
                    self.connection.connect(self.ip_input)
                    self.parent.set_mode(PegMultiplayerMode(self.connection, 1))
                except:
                    self.ip_input = ""
            elif char in range(ord('a'), ord('z')) + range(ord('0'), ord('9')) + [ord('.')]:
                self.ip_input += chr(char)

            print char

    def render(self, surface):
        font = pygame.font.Font(None, 32)

        surface.fill((0, 0, 0))

        if self.host:
            text = font.render("Waiting for a connection(Esc to cancel)...", 1, (230, 230, 50))
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

    def _handle_input(self):
        for data in self.connection.receive():
            command, _, params = data.partition(" ")
            params = params.split(" ")
            if command.startswith("PLACE_"):
                if command == "PLACE_PEG":
                    tile = T_RED_PEG if self.side == 1 else T_BLU_PEG
                elif command == "PLACE_OBSTACLE":
                    tile = T_OBSTACLE2
                elif command == "PLACE_FLOOR":
                    tile = T_FLOOR2

                x = int(params[0])
                y = int(params[1])

                self.tilemap.set_tile(x, y, tile)
            elif command == "END_TURN":
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
                self.parent.set_mode(MenuMode())

        if self.turn == 0 and self.parent.key_just_pressed("r"):
            self._generate_map()
            self.send_map()

        if self.side == 0:
            old_cursor = self.red_cursor[:]
            if self.parent.key_pressed('w'): self.red_cursor[1] -= 1
            if self.parent.key_pressed('s'): self.red_cursor[1] += 1
            if self.parent.key_pressed('a'): self.red_cursor[0] -= 1
            if self.parent.key_pressed('d'): self.red_cursor[0] += 1
            if self.red_cursor[1] < 0: self.red_cursor[1] = 0
            if self.red_cursor[1] > 31: self.red_cursor[1] = 31
            if self.red_cursor[0] < 0: self.red_cursor[0] = 0
            if self.red_cursor[0] > 31: self.red_cursor[0] = 31

            if self.red_cursor != old_cursor:
                rc = self.red_cursor
                self.connection.send("MOVE_CURSOR %i %i %i" % (rc[0], rc[1], self.frame))

            if self.turn_player == self.side:
                rc = self.red_cursor
                if self.parent.key_just_pressed("c"):
                    if self.tilemap.get_tile(rc[0], rc[1]) in [T_RED_PATH, T_RED_PATH2]:
                        self.tilemap.set_tile(rc[0], rc[1], T_RED_PEG)
                        self.connection.send("PLACE_PEG %i %i" % (rc[0], rc[1]))
                        self.connection.send("END_TURN")
                        self._end_turn()

                if self.parent.key_just_pressed("v"):
                    if self.red_charge_wall == CHARGE_OBSTACLE:
                        if self.tilemap.get_tile(rc[0], rc[1]) not in IMMUTABLE_TILES:
                            self.tilemap.set_tile(rc[0], rc[1], T_OBSTACLE2)
                            self.connection.send("PLACE_OBSTACLE %i %i" % (rc[0], rc[1]))
                            self.connection.send("END_TURN")
                            self.red_charge_wall = -1
                            self._end_turn()

                if self.parent.key_just_pressed("b"):
                    if self.red_charge_floor == CHARGE_FLOOR:
                        if self.tilemap.get_tile(rc[0], rc[1]) not in IMMUTABLE_TILES:
                            self.tilemap.set_tile(rc[0], rc[1], T_FLOOR2)
                            self.connection.send("PLACE_FLOOR %i %i" % (rc[0], rc[1]))
                            self.connection.send("END_TURN")
                            self.red_charge_floor = -1
                            self._end_turn()
        else:
            old_cursor = self.blu_cursor[:]
            if self.parent.key_pressed('w'): self.blu_cursor[1] -= 1
            if self.parent.key_pressed('s'): self.blu_cursor[1] += 1
            if self.parent.key_pressed('a'): self.blu_cursor[0] -= 1
            if self.parent.key_pressed('d'): self.blu_cursor[0] += 1
            if self.blu_cursor[1] < 0: self.blu_cursor[1] = 0
            if self.blu_cursor[1] > 31: self.blu_cursor[1] = 31
            if self.blu_cursor[0] < 0: self.blu_cursor[0] = 0
            if self.blu_cursor[0] > 31: self.blu_cursor[0] = 31

            if self.blu_cursor != old_cursor:
                bc = self.blu_cursor
                self.connection.send("MOVE_CURSOR %i %i %i" % (bc[0], bc[1], self.frame))

            if self.turn_player == self.side:
                bc = self.blu_cursor
                if self.parent.key_just_pressed("c"):
                    if self.tilemap.get_tile(bc[0], bc[1]) in [T_BLU_PATH, T_BLU_PATH2]:
                        self.tilemap.set_tile(bc[0], bc[1], T_BLU_PEG)
                        self.connection.send("PLACE_PEG %i %i" % (bc[0], bc[1]))
                        self.connection.send("END_TURN")
                        self._end_turn()

                if self.parent.key_just_pressed("v"):
                    if self.blu_charge_wall == CHARGE_OBSTACLE:
                        if self.tilemap.get_tile(bc[0], bc[1]) not in IMMUTABLE_TILES:
                            self.tilemap.set_tile(bc[0], bc[1], T_OBSTACLE2)
                            self.connection.send("PLACE_OBSTACLE %i %i" % (bc[0], bc[1]))
                            self.connection.send("END_TURN")
                            self.blu_charge_wall = -1
                            self._end_turn()

                if self.parent.key_just_pressed("b"):
                    if self.blu_charge_floor == CHARGE_FLOOR:
                        if self.tilemap.get_tile(bc[0], bc[1]) not in IMMUTABLE_TILES:
                            self.tilemap.set_tile(bc[0], bc[1], T_FLOOR2)
                            self.connection.send("PLACE_FLOOR %i %i" % (bc[0], bc[1]))
                            self.connection.send("END_TURN")
                            self.blu_charge_floor = -1
                            self._end_turn()

    def stop(self):
        if self.connection.connected():
            self.connection.send("DISCONNECT")
        self.connection.close()

class PegGame(Game):
    def start(self):
        self.set_mode(MenuMode())

if __name__ == '__main__':
    game = PegGame()
    game.run()
