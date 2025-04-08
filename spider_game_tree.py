import copy
import zlib
import spider_constants as sc


class TreeNode:
    def __init__(self, state = None, parent=None):
        if state:
            self.state = copy.deepcopy(state)
        else:
            self.state = None# Deep copy of [np.array, ..., np.array]
        self.parent = parent               # Parent TreeNode
        self.children = []                 # List of TreeNode
        self.move = None                  # Move taken to reach this state (from parent)
        if not self.state:
            self.crc = None
        else:
            flatdisp = []
            for item in state:
                for subitem in item:
                    flatdisp.append(sc.STANDARD_DECK.index(subitem))
            ba = bytearray([crd for crd in flatdisp])
            self.crc_id = hex(zlib.crc32(ba))[2:]

    def define_state(self, state):
        self.state = copy.deepcopy(state)
        flatdisp = []
        for item in state:
            for subitem in item:
                flatdisp.append(sc.STANDARD_DECK.index(subitem))
        ba = bytearray([crd for crd in flatdisp])
        self.crc_id = hex(zlib.crc32(ba))[2:]


class GameTree:
    def __init__(self, initial_state):
        self.nodes = []
        self.current = None

    def add_node(self, node):
        self.nodes.append(node)

    def expand_with_move(self, move, new_state):
        if self.current is None:
            self.add_node(TreeNode(state=new_state, parent=None))
            self.current = 0
        else:
            self.add_node(TreeNode(state=new_state, parent=self.current))
            self.nodes[self.current].move = move
            self.nodes[self.current].children.append(self.current + 1)
            self.current += 1



    def to_pickle(self, path):
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self, f)


