import pygame

from collections import defaultdict

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