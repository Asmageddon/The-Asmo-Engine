import pygame

from game import Game
from mode import Mode

from _math import deg2rad
from math import sin, cos

from input import Keyboard
from input import Mouse

Keyboard = Keyboard()
Mouse = Mouse()

class TestMode(Mode):
    def start(self):
        self.t = 0
        self.direction = 1
        self.parent.fps = 60

    def run(self, time_delta):
        if Keyboard.just_pressed("escape"):
            self.parent.running = False

        if Keyboard.just_pressed("r"):
            self.t -= 10

        if Keyboard.pressed("r"):
            self.direction = -1
        else:
            self.direction = 1

        if Mouse.pressed("right"):
            self.direction *= 0.5

        if Mouse.pressed("left"):
            self.direction *= 2.0

        self.t += self.direction
    def render(self, surface):
        surface.fill((0, 0, 85))

        color = (255, 175 , 85)

        center = (surface.get_width() // 2, surface.get_height() // 2)
        arm_end = (
            center[0] + sin(deg2rad(self.t)) * 240,
            center[1] + cos(deg2rad(self.t)) * 240,
        )

        pygame.draw.line(surface, color, center, arm_end, 3)

class TestGame(Game):
    def start(self):
        self.set_mode(TestMode())

if __name__ == "__main__":
    TestGame().run()