import random as ran
import datetime as dt
import zlib
import pickle
import copy as cpy

DECK_DIR = 'decks/'
RESULTS_DIR = 'resultslogs/'
PICKLE_DIR = 'pickles/'
DEAL_SEQ = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
RANKLIST = 'KQJT98765432A'
SUITLIST = 'SHDC'
COLUMNIDS = '0123456789ABCDEFGHIJ'
STANDARD_DECK = [rank + suit for rank in RANKLIST for suit in SUITLIST]

class Checkpoint:
    def __init__(self, tableau, full_suits, score, mq):
        self.tableau = tableau
        self.full_suits = full_suits
        self.score = score
        self.mq = mq



class SpiderNode:

    def __init__(self):
        self.parent = None
        self.children = {}
        self.hash = None


class SpiderTree:

    def __init__(self):
        self.nodes = []
        self.current_node = 0
        


    def add(self,node):
        self.nodes.append(node)


    def connect(self,nodenum1,nodenum2, move):
        self.nodes[nodenum1].children[move] = nodenum2
        self.nodes[nodenum2].parent = nodenum1

    def move_down(self,move):
        self.current_node = self.nodes[self.current_node].children[move]

    def move_up(self):
        self.current_node = self.nodes[self.current_node].parent

    def modify_key(self,node, old_key, new_key):
        self.nodes[node].children[new_key] = \
            self.nodes[node].children.pop(old_key)

    def initialize_nodes(self, moves):
        for move in moves:
            self.nodes[self.current_node].children[move] = None

    def get_parent_to_current_move(self, node):
        parent_node = self.nodes[node].parent
        keys = self.nodes[parent_node].children.keys()
        for key in keys:
            if self.nodes[parent_node].children[key] == node:
                return key
        return None


class SpiderGame:
    def __init__(self, deck_crc, resfile_name, major = 1, minor = 1, ):

        self.deck = []
        self.tableau = []
        self.spidertree = SpiderTree()
        self.mq = []
        self.score = 0
        self.full_suits = []
        self.deck_crc = deck_crc
        self.checkpoints = []
        self.resultsfile = open(RESULTS_DIR + resfile_name,'a')
        self.starttime = dt.datetime.now()
        self.best_score = 0
        self.major = major
        self.minor = minor


    def update_results(self,rep):
        self.score_tableau()
        if self.score > self.best_score:
            self.best_score = self.score
            self.resultsfile.write('\n' + 50*'*' + '\n')
            self.resultsfile.write(f'Repetition: {rep}\n')
            self.resultsfile.write(f'Best Score: {self.best_score}\n')
            self.resultsfile.write(f'Node Number: {self.spidertree.current_node}\n')
            self.resultsfile.write(f'Elapsed Time: {dt.datetime.now() - self.starttime}\n')
            self.resultsfile.write(f'Self Full Suits: {self.full_suits}\n')
            for i in range(10):
                self.resultsfile.write(f'{2*i + 1}: {str(self.tableau[2*i+1])} \n')
            self.resultsfile.flush()


    def game_setup(self):
        with open(DECK_DIR + self.deck_crc + '.txt','r') as f:
            self.deck = eval(f.read())
        build = []
        for num in DEAL_SEQ:
            while len(build) != num:
                card = self.deck.pop()
                build.append(card)
            self.tableau.append(build)
            build = []



    @staticmethod
    def suited_seq(card1,card2):
        return card1[0] + card2[0] in RANKLIST and card1[1] == card2[1]


    @staticmethod
    def sequential(card1,card2):
        return card1[0] + card2[0] in RANKLIST


    def score_tableau(self):
        upcards = [self.tableau[2 * i + 1] for i in range(10)]
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
        self.score += 26 * len(self.full_suits)


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

    def get_tableau_crc(self):
        flat = []
        for item in self.tableau:
            for subitem in item:
                flat.append(subitem)
        ba = bytearray([STANDARD_DECK.index(card) for card in flat])
        crc = zlib.crc32(ba)
        crchex = hex(crc)[2:]
        return crchex

    def move_cleanup(self):
        crchex= self.get_tableau_crc()
        self.mq.append(crchex)
        self.spidertree.nodes[self.spidertree.current_node].hash = crchex
        self.score_tableau()

    def do_move(self,move, backtrack = False):
        if move == '***':
            if backtrack:
                for n in range(10):
                    card = self.tableau[2 * n + 1].pop()
                    self.deck.append(card)
            else:
                for n in range(10):
                    card = self.deck.pop()
                    self.tableau[2 * n + 1].append(card)
        else:
            if backtrack:
                from_ = COLUMNIDS.index(move[1])
                to_ = COLUMNIDS.index(move[0])
            else:
                from_ = COLUMNIDS.index(move[0])
                to_ = COLUMNIDS.index(move[1])
            flip = move[-1] == '+'
            num = int(move[2:3],16)
            if backtrack and flip:
                self.tableau[to_ - 1].append(self.tableau[to_].pop())

            self.tableau[to_] += self.tableau[from_][-num:]
            self.tableau[from_] = self.tableau[from_][:-num]
            if not backtrack:
                if len(self.tableau[from_]) == 0:
                    if self.tableau[from_ - 1] != []:
                        self.tableau[from_] = self.tableau[from_ - 1][-1:]
                        self.tableau[from_ - 1] = self.tableau[from_ - 1][:-1]
                        parent_node =   self.spidertree.nodes[self.spidertree.current_node].parent
                        self.spidertree.modify_key(parent_node,move,move+'+')
            self.move_cleanup()



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

    def restore_last_checkpoint(self):
        cp = self.checkpoints.pop()
        import copy
        self.tableau = copy.deepcopy(cp.tableau)
        self.full_suits = cp.full_suits[:]
        self.score = cp.score
        self.mq = cp.mq[:]

    def update_nodes(self, move):
        # Save checkpoint BEFORE making a move

        cp = Checkpoint(
            tableau=cpy.deepcopy(self.tableau),
            full_suits=self.full_suits[:],
            score=self.score,
            mq=self.mq[:],
        )
        self.checkpoints.append(cp)

        # (Now do your normal stuff)
        self.spidertree.nodes[self.spidertree.current_node].children[move] = len(self.spidertree.nodes)
        self.spidertree.add(SpiderNode())
        self.spidertree.connect(self.spidertree.current_node, len(self.spidertree.nodes) - 1, move)
        self.spidertree.move_down(move)
        self.do_move(move)


    def execute(self):

        rep = 0
        while rep < self.major:
            self.game_setup()
            self.spidertree.add(SpiderNode())
            while True:
                redeal_flag = False
                cycle_error = len(self.mq) - len(set(self.mq)) > 2
    
                moves = self.getmoves()
                if not moves or cycle_error:
                    if self.deck:
                        redeal_flag = True
                        self.mq = []
                    elif not moves:
                        break
                    elif cycle_error:
                        break
                if not redeal_flag:
                    self.spidertree.initialize_nodes(moves)
                    chosen = ran.choice(moves)
                    self.update_nodes(chosen)
                    self.scan_for_full()
                else:
                    self.update_nodes('***')
            self.post_process(self.minor,rep)
            rep += 1



    def count_leaves(self):
        count = 0
        for i, node in enumerate(self.spidertree.nodes):
            if not self.spidertree.nodes[i].children:
                count += 1
        return count
    def print_tableau(self):
        for i,item in enumerate(self.tableau):
            print(i,item)

    def post_process(self,minor,rep):

        while True:  # Outer loop: repeat until limit hit
            # Step 1: Find a leaf node
            leaf = None
            for i, node in enumerate(self.spidertree.nodes):
                if not node.children:
                    leaf = i
                    break
            if leaf is None:
                return

            self.spidertree.current_node = leaf

            # Step 2: Walk up the tree until finding unexplored moves
            while True:
                move = self.spidertree.get_parent_to_current_move(self.spidertree.current_node)
                if move:
                    self.restore_last_checkpoint()
                    self.spidertree.move_up()
                else:
                    break

                parent_node = self.spidertree.nodes[self.spidertree.current_node]
                unexplored = [key for key, child in parent_node.children.items() if child is None]
                if not unexplored:
                    continue



                # Step 3: Pick and play an unexplored move

                move = ran.choice(unexplored)
                self.update_nodes(move)

                # Step 4: Expand forward until dead-end
                while True:
                    if len(self.spidertree.nodes) >= minor:
                        return

                    moves = self.getmoves()
                    if not moves or len(self.mq[-3:]) != len(set(self.mq[-3:])):
                        self.update_results(rep)
                        break
                    self.spidertree.initialize_nodes(moves)
                    move = ran.choice(moves)
                    self.update_nodes(move)
                    self.scan_for_full()


def run_process(major,minor, deck_crc = '7e3f0d41',):
    now = dt.datetime.now()
    resfile_name = now.strftime("%d-%H-%M-%S") + '-' + deck_crc + '.txt'
    sg = SpiderGame(deck_crc,resfile_name,major,minor)
    sg.execute()



if __name__ == "__main__":
    run_process(40,10000,'7e3f0d41')
