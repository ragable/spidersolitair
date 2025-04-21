
class SpiderNode:

    def __init__(self):
        self.parent = None
        self.children = {}
        self.hash = None



class SpiderTree:

    def __init__(self):
        self.nodes = []


    def add(self,node):
        self.nodes.append(node)

    def connect(self,nodenum1,nodenum2, move):
        self.nodes[nodenum1].children[move] = nodenum2
        self.nodes[nodenum2].parent = nodenum1

    def traverse_from_leaf(self, nodenum, movelist = []):
        while type(self.nodes[nodenum].parent) == int and self.nodes[nodenum].parent > -1:
            investigate = self.nodes[nodenum].parent
            for node in list(self.nodes[investigate].children):
                if self.nodes[investigate].children[node] == nodenum:
                    movelist.append(node)
            self.traverse_from_leaf(investigate,movelist)
            break


if __name__ == "__main__":
    pass




