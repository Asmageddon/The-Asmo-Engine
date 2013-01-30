#import Game, Mode

from game import Game
from mode import Mode

from math import rad2deg

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

class TestGame(Game):
    def start(self):
        self.set_mode(TestMode())