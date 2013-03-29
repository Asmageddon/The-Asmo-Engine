import os, sys
import pygame

def load_image(path, color_key = None):
    full_path = join_path("data", path)

    try:
        image = pygame.image.load(full_path)
    except pygame.error, message:
        raise SystemExit, message


    if color_key != None:
        image = image.convert()
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()


    return image

def join_path(directory, resource):
    """Contencate project directory, 'directory' and resource"""
    root = sys.path[0]

    #Strip parent dir elements
    directory = directory.replace("../", "").replace("..\\", "")
    resource = resource.replace("../", "").replace("..\\", "")

    path = os.path.join(root, directory, resource)

    return os.path.normpath(path)

color_dict = {
    "default": (220, 65, 160)
}

def convert_color(color):
    """Converts a color name or hex code into an (r, g, b) tuple"""
    if   isinstance(color, tuple): return color
    elif isinstance(color, str):
        if color[0] == "#":
            i = int(color[1:], 16)
            r = i & 255
            g = i >> 8 & 255
            b = i >> 16 & 255
            return (r, g, b)
        else:
            try:
                return color_dict[color]
            except:
                return (0, 0, 0)