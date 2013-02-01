from singleton_decorator import singleton

from collections import defaultdict

import pygame

@singleton
class Keyboard(object):
    def __init__(self):
        #Create key name/code and code/name maps
        names = filter(lambda name: name.startswith("K_"), dir(pygame))
        keycode_map = { name[2:].lower(): eval("pygame.%s" % name) for name in names }

        #I bet there is stuff I'm still missing, but meh, for now this will be sufficient
        self._keycode_map = defaultdict(lambda: pygame.K_UNKNOWN)
        self._keycode_map.update(keycode_map)
        #Map chars to keycodes, even if some of them won't work :p
        for char in "`!@#$%^&*()-_=+[{]}\\|;:\"',<.>/?":
            self._keycode_map[char] = ord(char)

        self._keycode_map["~"] = ord("`") #Because most people will use ~ for console if making one
        self._keycode_map["enter"] = pygame.K_RETURN #Because doh, enter is more intuitive than return

        #Generate a key name to key code map
        self._key_name_map = { v:k for k, v in self._keycode_map.items()}

        #Key status dictionaries
        self.key_status = defaultdict(lambda: False)
        self.changed_key_status = {}

        #Keys pressed this frame, in order, for text input purposes
        self.key_input = []

    def name_to_code(self, key_name):
        """Converts a character or name of a key into a pygame keycode"""
        if type(key_name) == str:
            return self._keycode_map[key_name.lower()]
        else:
            return key_name #Not a key name but pygame code - this should work too

    def code_to_name(self, keycode):
        """Converts pygame keycode to a character or string representing its name"""
        if type(keycode) == int:
            return self._key_name_map[keycode]
        else:
            return keycode #Already a key name

    #Keyboard state functions
    def just_pressed(self, keycode):
        """Return True if specified key was just pressed this frame"""
        keycode = self.name_to_code(keycode)

        if keycode not in self.changed_key_status:
            return False
        return self.changed_key_status[keycode] == True

    def just_lifted(self, keycode):
        """Return True if specified key was just lifted this frame"""
        keycode = self.name_to_code(keycode)

        if keycode not in self.changed_key_status:
            return False
        return self.changed_key_status[keycode] == False

    def pressed(self, keycode):
        """Return True if specified key is being held down"""
        keycode = self.name_to_code(keycode)
        #Make sure it's registered as pressed for at least one frame
        # in case the press was too quick
        if keycode in self.changed_key_status:
            if self.changed_key_status[keycode] == True:
                return True
        return self.key_status[keycode]

    #Event receivers for events passed by the Game
    def _on_enter_frame(self):
        self.changed_key_status = {}
        self.key_input = []

    def _on_key_down(self, event):
        #Update the key status dictionaries
        self.changed_key_status[event.key] = True
        self.key_status[event.key] = True

        self.key_input.append(event.key)

    def _on_key_up(self, event):
        #Update the key status dictionaries
        self.changed_key_status[event.key] = False
        self.key_status[event.key] = False

keyboard = Keyboard()