import random as ran
import datetime as dt
import zlib
import pickle


DECK_DIR = 'C:/Users/ralph/Desktop/spidersol/decks/'
LOGGER_DIR = 'C:/Users/ralph/Desktop/spidersol/movelogs/'
DEAL_SEQ = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
RANKLIST = 'KQJT98765432A'
SUITLIST = 'SHDC'
COLUMNIDS = '0123456789ABCDEFGHIJ'
STANDARD_DECK = [rank + suit for rank in RANKLIST for suit in SUITLIST]

class MoveLogger:

    def __init__(self):
        self.log = []
        self.backtrack_ndx = 0
        now = dt.datetime.now()
        logfile_name = LOGGER_DIR + now.strftime("%d-%H-%M-%S") +'.txt'
        self.logfile = open(logfile_name,'w')

    def add_move(self,move):
        if self.backtrack_ndx != len(self.log) - 1:
            self.backtrack_ndx = len(self.log)
        self.log.append(move)

    def backtrack(self):
        if self.backtrack_ndx == len(self.log) - 1:
            self.log.append(self.log[self.backtrack_ndx] + '*')
            self.backtrack_ndx -= 1

    def save(self):
        for item in self.log:
            self.logfile.write(item + '\n')
        self.logfile.close()
        self.log = []
        self.backtrack_ndx = 0

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
        self.logger = MoveLogger()
        self.mq = {}
        self.score = None
        self.full_suits = []

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
        pass


    def redeal(self):

        for n in range(10):
            card = self.deck.pop()
            self.tableau[2 * n + 1].append(card)
        self.logger.add_move('***')

    def undo_deal(self):

        for n in range(10):
            card = self.tableau[2 * n + 1].pop()
            self.deck.append(card)
        self.logger.backtrack()




    def suited_seq(self,card1,card2):

        return card1[0] + card2[0] in RANKLIST and card1[1] == card2[1]

    @staticmethod
    def sequential(card1,card2):

        return card1[0] + card2[0] in RANKLIST

    def score_tableau(self):
        for lst in self.tableau:
            upcards = [self.tableau[2*i+1] for i in range(10) ]
            upcardsall = []
            for item in upcards:
                for subitem in item:
                    upcardsall.append(subitem)
        ziplist = list(zip(upcardsall,upcardsall[1:]))
        relations = []
        for item in ziplist:
            if self.suited_seq(item[0],item[1]):
                relations.append('*')
            elif self.sequential(item[0],item[1]):
                relations.append('#')
            else:
                relations.append('-')
        sscount = sum([item == '*' for item in relations])
        sccount = sum([item == '#' for item in relations])
        emptycolumncnt = sum([len(lst) == 0 for lst in upcards])
        self.score = 2*sscount + sccount
        if emptycolumncnt == 1:
            self.score += 3
        elif emptycolumncnt == 2:
            self.score += 10
        elif emptycolumncnt > 2:
            self.score += 20

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
                for chrc in inv:
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


        for i,seqto in enumerate(sequences):
            for j,seqfrom in enumerate(sequences):
                if seqfrom and seqto:
                    if self.suited_seq(sequences[i][-1],sequences[j][0]):
                        if i < j:
                            moves.append(COLUMNIDS[2*j + 1] + COLUMNIDS[2*i+1] + COLUMNIDS[len(sequences[i])])
                        elif i > j:
                            moves.append(COLUMNIDS[2 * j + 1] + COLUMNIDS[2 * i + 1] + COLUMNIDS[len(sequences[j])])
                elif seqfrom:
                    moves.append(COLUMNIDS[2*j + 1] + COLUMNIDS[2*i+1] + COLUMNIDS[len(seqfrom)])


        if moves == []:
            for i,seqto in enumerate(sequences):
                for j,seqfrom in enumerate(sequences):
                    if seqfrom and seqto:
                        if self.sequential(sequences[i][-1], sequences[j][0]):
                            if i < j:
                                moves.append(COLUMNIDS[2 * j + 1] + COLUMNIDS[2 * i + 1] + COLUMNIDS[len(sequences[i])])
                            elif i > j:
                                moves.append(COLUMNIDS[2*j + 1] + COLUMNIDS[2*i+1] + COLUMNIDS[len(sequences[j])])
                    elif seqfrom:
                        moves.append(COLUMNIDS[2*j + 1] + COLUMNIDS[2*i+1] + COLUMNIDS[len(seqfrom)])

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
        flat = []
        for item in self.tableau:
            for subitem in item:
                flat.append(subitem)
        ba = bytearray([STANDARD_DECK.index(card) for card in flat])
        crc = zlib.crc32(ba)
        crchex = hex(crc)[2:]
        if crchex not in self.mq:
            self.mq[crchex] = 1
        else:
            self.mq[crchex] += 1
        self.score = self.score_tableau()

    def scan_for_full(self):
        for i in range(10):
            if len(self.tableau[2*i + 1]) >= 13:
                suit_std = self.tableau[2*i+1][-1][1]
                suitcount = sum([item[1] == suit_std for item in self.tableau[2*i+1]])
                rankcount = 0
                for k,rank in enumerate(RANKLIST):
                    if rank == self.tableau[2*i+1][k][0]:
                        rankcount += 1
                if suitcount == 13 and rankcount == 13:
                    self.full_suits.append(suit_std)
                del self.tableau[2*i+1][-13:]
                if self.tableau[2*i+1] == [] and len(self.tableau[2*i]) > 0:
                    self.tableau[2*i+1].append(self.tableau[2*i].pop())




    def execute(self):

        self.game_setup('87654321') #'1361ec2b')
        self.spidertree.add(SpiderNode())
        while True:
            moves = self.getmoves()
            cycle_error = False
            for value in self.mq.values():
                if value >= 10:
                    cycle_error = True
                    break
            if len(list(self.mq)) > 20:
                self.mq = {}
            if (not moves or cycle_error) and self.deck:
                self.redeal()
                self.mq = {}
                continue
            elif not moves:
                break

            for move in moves:
                self.spidertree.nodes[self.current_node].children[move] = None
            chosen = ran.choice(moves)

            self.spidertree.nodes[self.current_node].children[chosen] = len(self.spidertree.nodes)
            self.spidertree.add(SpiderNode())
            self.spidertree.connect(self.current_node,len(self.spidertree.nodes) - 1,chosen)
            self.do_move(chosen)
            upcards = [self.tableau[2*i+1] for i in range(10) ]
            print(f"From: {(COLUMNIDS.index(chosen[0]) - 1)//2}, To: {(COLUMNIDS.index(chosen[1]) - 1)//2}, Num: {COLUMNIDS.index(chosen[2])}\n UP: {upcards}")
            self.scan_for_full()
            self.logger.add_move(chosen)
            self.current_node = self.spidertree.nodes[self.current_node].children[chosen]
        if len(self.full_suits) == 8:
            print('CONGRATULATIONS - you won.')
        else:
            print('Sorry, better luck next time - you lost.')


def save_state(data):
    with open('pickles/spider_state.pickle','wb') as f:
        pickle.dump(data,f,pickle.HIGHEST_PROTOCOL)

def load_state():
    with open('pickles/spider_state.pickle','rb') as f:
        data = pickle.load(f)
    return data



if __name__ == "__main__":
    sg = SpiderGame()
    sg.execute()
    save_state(sg.spidertree.nodes)
    data = load_state()
    pass









