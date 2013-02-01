#Commented out and wip because I have to fucking finish the game
#class Keymap(object):
    #"""Maps keys to virtual keys, allowing for easy rebinding,
     #binding multiple keys to one virtual key, as well as creating
     #direction pads.
    #"""
    #def __init__(self):
        #self.defaults = {}

        #self.keys = defaultdict(lambda: set()) #virtual keys to keys
        #self.reverse_keys = defaultdict(lambda: set()) #keys to virtual keys
        ##self.keypads = [] #

    #def __check_binding(self, binding):
        #if   isinstance(binding, list ): return set(binding)
        #elif isinstance(binding, set  ): return binding
        #elif isinstance(binding, str  ): return set([binding])
        #else:
            #raise ValueError, "Binding must be a list, a set or a string"

    #def add_key(self, vkey, default_binding): pass

    #def set(self, vkey, binding):
        #"""Set virtual key 'vkey' to binding or bindings if 'binding' is a list"""
        #binding = self.__check_binding(binding)
        #self.keys[vkey] = binding
        #for b in binding:
            #self.reverse_keys[b].add(vkey)

    #def bind(self, vkey, binding):
        #binding = self.__check_binding(binding)
        #self.keys[vkey].update(binding)
        #for b in binding:
            #self.reverse_keys[b].remove(vkey)

    #def clear(self, vkey):
        #self.keys[vkey] = []
        #for l in self.reverse_keys:
            #l.

    #def name_to_code(self, key_name):
        #"""Converts a character or name of a key into a pygame keycode"""
        #if type(key_name) == str:
            #return self._keycode_map[key_name.lower()]
        #else:
            #return key_name #Not a key name but pygame code - this should work too

    #def code_to_name(self, keycode):
        #"""Converts pygame keycode to a character or string representing its name"""
        #if type(keycode) == int:
            #return self._key_name_map[keycode]
        #else:
            #return keycode #Already a key name

    ##Keyboard state functions
    #def just_pressed(self, keycode):
        #"""Return True if specified key was just pressed this frame"""
        #keycode = self.name_to_code(keycode)

        #if keycode not in self.changed_key_status:
            #return False
        #return self.changed_key_status[keycode] == True

    #def just_lifted(self, keycode):
        #"""Return True if specified key was just lifted this frame"""
        #keycode = self.name_to_code(keycode)

        #if keycode not in self.changed_key_status:
            #return False
        #return self.changed_key_status[keycode] == False

    #def pressed(self, keycode):
        #"""Return True if specified key is being held down"""
        #keycode = self.name_to_code(keycode)
        ##Make sure it's registered as pressed for at least one frame
        ## in case the press was too quick
        #if keycode in self.changed_key_status:
            #if self.changed_key_status[keycode] == True:
                #return True
        #return self.key_status[keycode]