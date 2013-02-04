try:
    import pygame
    if not pygame.font: raise ImportError
    if not pygame.mixer: raise ImportError
except ImportError:
    import tkMessageBox as box
    box.showerror("Error", "You need PyGame installed")
    exit()

from collections import defaultdict

#TODO: Make these into proper components once January's 1GAM is done.... I shouldn't even be "cleaning" this up now ;_;
from input import Keyboard, Mouse

class Game(object):
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(1) #Set mouse to visible

        self.clock = pygame.time.Clock()
        self.running = False
        self.current_mode = None

        self.fps = 30

        self.width=768; self.height=768
        self.screen=pygame.display.set_mode((self.width,self.height))

        pygame.display.set_caption("A game")

        self.key = Keyboard()
        self.mouse = Mouse()

    def set_title(self, caption):
        """Set window title to 'caption'"""
        pygame.display.set_caption(caption)

    def start(self): pass
    def stop(self): pass

    def set_mode(self, mode):
        mode._attach_parent(self)
        if self.running:
            self.current_mode.stop()

        self.current_mode = mode

        #Initialize frame variable of given mode so users don't have to call Mode.__init__ (don't like this ugly Python inheritance :<)
        if "frame" not in self.current_mode.__dict__:
            self.current_mode.frame = 0

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
            self.current_mode.frame += 1 #Increment frame count of active mode
            self.current_mode.render(self.screen)
            pygame.display.flip()

        self.current_mode.stop()
        self.stop()

        pygame.quit()

    def check_events(self):
        self.key._on_enter_frame()
        self.mouse._on_enter_frame()

        for event in pygame.event.get():
            if   event.type == pygame.QUIT:
                self.running = False #No arguing

            elif event.type == pygame.KEYDOWN:
                #Some alt+key special hotkeys. TODO: Move this elsewhere
                if pygame.key.get_mods() & pygame.KMOD_ALT:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_F12:
                        pygame.image.save(self.screen, utils.join_path("user", "screenshot.png"))

                self.key._on_key_down(event)

            elif event.type == pygame.KEYUP:
                self.key._on_key_up(event)

            elif event.type == pygame.MOUSEMOTION:
                self.mouse._on_mouse_motion(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse._on_mouse_button_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse._on_mouse_button_up(event)