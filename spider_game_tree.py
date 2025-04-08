import copy
import zlib
import spider_constants as sc


class TreeNode:
    def __init__(self, state, parent=None, move=None, crc_id= None):
        self.state = copy.deepcopy(state)  # Deep copy of [np.array, ..., np.array]
        self.parent = parent               # Parent TreeNode
        self.children = []                 # List of TreeNode
        self.move = move                   # Move taken to reach this state (from parent)
        flatdisp = []
        for item in state:
            for subitem in item:
                flatdisp.append(sc.STANDARD_DECK.index(subitem))
        ba = bytearray([crd for crd in flatdisp])
        self.crc_id = hex(zlib.crc32(ba))[2:]


    def add_child(self, child_node):
        self.children.append(child_node)


class GameTree:
    def __init__(self, initial_state):
        self.nodes = []
        root = TreeNode(initial_state)
        self.nodes.append(root)
        self.root = root
        self.current = root

    def expand_with_move(self, move, new_state):
        new_node = TreeNode(state=new_state, parent=self.current, move=move,crc_id = None)
        self.current.add_child(new_node)
        self.nodes.append(new_node)
        self.current = new_node
        return new_node

    def reset_to_node(self, node):
        self.current = node

    def to_pickle(self, path):
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self, f)


