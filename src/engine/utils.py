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
