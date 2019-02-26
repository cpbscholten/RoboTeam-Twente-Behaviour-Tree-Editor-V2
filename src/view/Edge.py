from PyQt5.QtWidgets import QGraphicsLineItem


class Edge(QGraphicsLineItem):

    def __init__(self, start_node, end_node):
        """
        The constructor for an ui edge
        :param start_node: Node on the start of the edge
        :param end_node: Node on the end of the edge
        """
        self.start_node = start_node
        self.end_node = end_node
        super(Edge, self).__init__(*self.get_position())
        end_node.setParentItem(self)

    def get_position(self):
        """
        Calculates the correct positions for both edge ends (keeps them connected to the nodes)
        :return: the start positions and end positions of the edge
        """
        # Position edge correctly, connecting the nodes
        start_x = self.start_node.rect().x() + (self.start_node.rect().width() / 2)
        start_y = self.start_node.rect().y() + self.start_node.rect().height()
        end_x = self.end_node.rect().x() + (self.end_node.rect().width() / 2) + self.end_node.pos().x()
        end_y = self.end_node.rect().y() + self.end_node.pos().y()
        return start_x, start_y, end_x, end_y

    def change_position(self):
        """
        Sets the edge to its correct position
        """
        self.setLine(*self.get_position())

    def xoffset(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the x offset of the parent
        """
        return self.parentItem().xoffset()

    def yoffset(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the y offset of the parent
        """
        return self.parentItem().yoffset()

    def xpos(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the x position of the parent
        """
        return self.parentItem().xpos()

    def ypos(self):
        """
        Function is recursively called by a connected node, passes call on to parent.
        :return: the y position of the parent
        """
        return self.parentItem().ypos()

