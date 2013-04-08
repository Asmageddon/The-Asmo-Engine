try:
    import pygame
    if not pygame.font: raise ImportError
    if not pygame.mixer: raise ImportError
except ImportError:
    import tkMessageBox as box
    box.showerror("Error", "You need PyGame installed")
    exit()

from input import Keyboard, Mouse

from resource_manager import ResourceManager

from display_system import DisplaySystem, display

class Game(object):
    def __init__(self):

        self.clock = pygame.time.Clock()
        self.running = False
        self.current_mode = None

        self.fps = 30

        self.display = DisplaySystem()

        self.key = Keyboard()
        self.mouse = Mouse()
        self.resman = ResourceManager()


    def on_start(self): pass
    def on_stop(self): pass

    def start(self):
        self.run()

    def stop(self):
        self.running = False

    def set_mode(self, mode):
        mode._attach_parent(self)
        if self.running:
            self.current_mode.stop()

        self.current_mode = mode

        if self.running:
            self.current_mode.start()

    def run(self):
        self.on_start()

        if self.current_mode == None: return

        self.current_mode.start()
        self.running = True

        while(self.running):
            time_elapsed = self.clock.tick(self.fps)

            self.check_events()

            #Run a frame of the current mode
            self.current_mode.run(time_elapsed) #For now let's just pretend the fps is perfect
            self.current_mode.scene.update(time_elapsed)
            self.current_mode.frame += 1 #Increment frame count of active mode

            self.current_mode.camera.render()

            self.display.blit(self.current_mode.camera.surface)

        self.current_mode.stop()
        self.on_stop()

        pygame.quit()

    def check_events(self):
        self.key._on_enter_frame()
        self.mouse._on_enter_frame()
        self.resman._on_enter_frame()
        self.display._on_enter_frame()

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