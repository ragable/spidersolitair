import random as ran

DECK_DIR = 'C:/Users/ralph/Desktop/spidersol/decks/'
DEAL_SEQ = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
RANKLIST = 'KQJT98765432A'
SUITLIST = 'SHDC'
COLUMNIDS = '0123456789ABCDEFGHIJ'


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

    def traverse_from_leaf(self, nodenum):
        movelist = []
        while type(self.nodes[nodenum].parent) == int and self.nodes[nodenum].parent > -1:
            investigate = self.nodes[nodenum].parent
            for node in list(self.nodes[investigate].children):
                if self.nodes[investigate].children[node] == nodenum:
                    movelist.append(node)
            nodenum = investigate
            #self.traverse_from_leaf(investigate,movelist)
            #break
        rptlist = movelist[::-1]
        print(rptlist)

    def general_traverse(self):
        for node in range(len(self.nodes)):
            if not self.nodes[node].children:
                self.traverse_from_leaf(node)

class SpiderGame:
    def __init__(self):
        self.deck = []
        self.tableau = []
        self.spidertree = SpiderTree()
        self.current_node = 0

    def game_setup(self, deckcrc):
        with open(DECK_DIR + deckcrc + '.txt','r') as f:
            self.deck = eval(f.read())
        build = []
        for num in DEAL_SEQ:
            while len(build) != num:
                card = self.deck.pop()
                build.append(card)

            self.tableau.append(build)
            build = []


    def redeal(self):
        for n in range(10):
            card = self.deck.pop()
            self.tableau[2 * n + 1].append(card)

    def suited_seq(self,card1,card2):
        return self.sequential(card1,card2) and card1[0][1] == card2[0][1]

    def sequential(self,card1,card2):
        return RANKLIST.index(card1[0][0]) - RANKLIST.index(card2[0][0]) == -1


    def seqs(self, upcards):
        outseqs = []
        for lst in upcards:
            if len(lst) == 0:
                outseqs.append([])
            elif len(lst) == 1:
                outseqs.append(lst)
            else:
                ziplist = list(zip(lst,lst[1:]))
                relations = []
                for item in ziplist:
                    if self.suited_seq(item[0],item[1]):
                        relations.append('*')
                    elif self.sequential(item[0],item[1]):
                        relations.append('#')
                    else:
                        relations.append('-')
                inv = relations[::-1]
                count = 0
                for chrc in relations:
                    if chrc == '*':
                        count += 1
                    else:
                        break
                if count == 0:
                    outseqs.append([lst[-1]])
                else:
                    outseqs.append(lst[-(count+1):])
        return outseqs




    def getmoves(self):
        upcards = [self.tableau[2*i+1] for i in range(10)]
        sequences = self.seqs(upcards)
        moves = []

        for i in range((len(sequences))):
            for j in range((len(sequences))):
                if i != j:
                    if self.sequential(sequences[i],sequences[j]):
                        moves.append(COLUMNIDS[2*i + 1] + COLUMNIDS[2*j+1] + hex(len(sequences[i]))[2:])
        return moves


    def do_move(self,move):
        from_ = COLUMNIDS.index(move[0])
        to_ = COLUMNIDS.index(move[1])
        num = int(move[2:],16)
        self.tableau[to_] += self.tableau[from_][-num:]
        self.tableau[from_] = self.tableau[from_][:-num]
        if len(self.tableau[from_]) == 0:
            if self.tableau[from_ - 1] != []:
                self.tableau[from_] = self.tableau[from_ - 1][-1:]
                self.tableau[from_ - 1] = self.tableau[from_ - 1][:-1]


    def execute(self):
        self.game_setup('1361ec2b')
        self.spidertree.add(SpiderNode())
        while True:
            moves = self.getmoves()
            for move in moves:
                self.spidertree.nodes[self.current_node].children[move] = None
            chosen = ran.choice(moves)
            self.spidertree.nodes[self.current_node].children[chosen] = len(self.spidertree.nodes)
            self.spidertree.add(SpiderNode())
            self.do_move(chosen)
            self.current_node = self.spidertree.nodes[self.current_node].children[chosen]
            pass

if __name__ == "__main__":
    sg = SpiderGame()
    sg.execute()





