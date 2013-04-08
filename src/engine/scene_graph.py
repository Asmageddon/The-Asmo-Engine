class SceneGraphNode(object):
    def __init__(self):
        self.children_set = set()
        self.children = []
        self.parent = None
        self.x = 0
        self.y = 0

    def _attach_parent(self, parent):
        """Attach a parent to this scene node. Do not call manually"""
        if self.parent is not None:
            raise KeyError, "Given node already is a child of another node"
        self.parent = parent

    def _detach_parent(self, parent):
        """Detach the parent of this scene node. Do not call manually"""
        if self.parent is not parent:
            raise KeyError, "Given node is not a child of this node"
        self.parent = None

    def add_child(self, node):
        if node not in self.children_set:
            self.children.append(node)
            self.children_set.add(node)
            node._attach_parent(self)
        else:
            raise KeyError, "Given node already is a child of this node"

    def remove_child(self, node):
        if node not in self.children_set:
            raise KeyError, "Given node not a child of this node"
        else:
            self.children_set.remove(node)
            self.children.remove(node)
            node._detach_parent(self)

    def render_onto(self, camera, offset=(0, 0)):
        """Render entity and all its children, override _render for rendering"""

        offset = (
            offset[0] + self.x,
            offset[1] + self.y
        )

        self._render(camera, offset)

        for c in self.children:
            c.render_onto(camera, offset)

    def _render(self, camera, offset): pass

    def update(self, delta_time):
        self._update(delta_time)
        for c in self.children:
            c.update(delta_time)

    def _update(self, delta_time): pass

    def absolute_pos(self):
        if self.parent:
            p = self.parent.absolute_pos()
            return (self.x + p[0], self.y + p[1])
        else:
            return (self.x, self.y)

class Scene(SceneGraphNode): pass
