from scene_graph import SceneGraphNode

class Entity(SceneGraphNode):
    def __init__(self):
        SceneGraphNode.__init__(self)

        self.x = 0
        self.y = 0

