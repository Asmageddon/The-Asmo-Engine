from singleton_decorator import singleton

from collections import defaultdict

import pygame

@singleton
class Mouse(object):
    def __init__(self):

        self._mb_code_map = {
            "left": 1,
            "middle": 2,
            "right": 3,
            "wheel_up": 4,
            "wheel_down": 5,
            "extra1": 8,
            "extra2": 9,
            "extra3": 10,
            "extra4": 11,
            "extra5": 12,
            #Let's hope nobody will need more(in fact let's hope nobody will even use extra5)
        }
        self._mb_name_map = {v: k for k, v in self._mb_code_map.items()}

        #Mouse status variables
        self.mouse_status = defaultdict(lambda: False)
        self.changed_mouse_status = {}
        self.mouse_pos = (0, 0)

    def name_to_code(self, mb_name):
        """Convert button name to pygame button code"""
        if type(mb_name) == str:
            mb_name = mb_name.lower().replace(" ", "_")

            return self._mb_code_map[mb_name]
        else:
            return mb_name #It's just a number unless it's something else in which case it will break stuff. Proper design ftw, moahahaha

    def code_to_name(self, mb_code):
        """Convert pygame button code to a readable name"""
        if type(mb_code) == int:
            return self._mb_name_map[mb_code]
        else:
            return mb_code #Probably already a string... I shouldn't be doing this, ehhh...

    #Mouse state function
    def just_pressed(self, mouse_button):
        """Return True if specified mouse button was just pressed this frame"""
        mouse_button = self.name_to_code(mouse_button)

        if mouse_button not in self.changed_mouse_status:
            return False
        return self.changed_mouse_status[mouse_button] == True

    def just_lifted(self, mouse_button):
        """Return True if specified mouse button was just lifted this frame"""
        mouse_button = self.name_to_code(mouse_button)

        if mouse_button not in self.changed_mouse_status:
            return False
        return self.changed_mouse_status[mouse_button] == False

    def pressed(self, mouse_button):
        """Return True if specified mouse button is being held down"""
        mouse_button = self.name_to_code(mouse_button)
        #Make sure it's registered as pressed for at least one frame
        # in case the click was too quick
        if mouse_button in self.changed_mouse_status:
            if self.changed_mouse_status[mouse_button] == True:
                return True
        return self.mouse_status[mouse_button]

    def _on_enter_frame(self):
        self.changed_mouse_status = {}

    def _on_mouse_motion(self, event):
        self.mouse_pos = event.pos

    def _on_mouse_button_down(self, event):
        self.mouse_status[event.button] = True
        self.changed_mouse_status[event.button] = True
        self.mouse_pos = event.pos

    def _on_mouse_button_up(self, event):
        self.mouse_status[event.button] = False
        self.changed_mouse_status[event.button] = False
        self.mouse_pos = event.pos

mouse = Mouse()