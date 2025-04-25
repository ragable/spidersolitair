import random as ran
import datetime as dt
import zlib
import pickle

DECK_DIR = 'decks/'
LOGGER_DIR = 'movelogs/'
PICKLE_DIR = 'pickles/'
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
            self.log.append(self.log[self.backtrack_ndx] + '+')
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
    def __init__(self, deck_crc = None, state_filename = None):

        self.deck = []
        self.tableau = []
        self.spidertree = SpiderTree()
        self.logger = MoveLogger()
        self.mq = []
        self.score = None
        self.full_suits = []
        self.deck_crc = deck_crc
        self.state_filename = state_filename


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
        if self.state_filename:
            self.auto_start()


    def auto_start(self):
        working_tree = self.load_state()
        working_moves = []
        leaves = []
        for i,node in enumerate(working_tree.nodes):
            if working_tree.nodes[i].children == {}:
                leaves.append(i)

        if len(leaves) > 1:
            while True:
                answer = input('Which leaf file would you like to start from? \n' + str(leaves) + '\n')
                if int(answer) not in leaves:
                    print(f'{answer} not in leaves. Try again)')
                else:
                    break
            self.spidertree.current_node = int(answer)
        elif len(leaves) == 1:
            print(f'Only one leaf found {leaves[0]}. Will start from there')
            current_node = leaves[0]


        while working_tree.nodes[current_node].parent:
            parent_node_number = working_tree.nodes[current_node].parent
            moves = list(working_tree.nodes[parent_node_number].children)
            for move in moves:
                if working_tree.nodes[parent_node_number].children[move] == current_node:
                    working_moves.append(move)
                    break
            current_node = parent_node_number
        moves = list(working_tree.nodes[0].children)
        for move in moves:
            if working_tree.nodes[0].children[move] == 1:
                working_moves.append(move)
                break

        rev_working_moves = working_moves[::-1]
        for move in rev_working_moves:
            self.do_move(move)

    @staticmethod
    def suited_seq(card1,card2):
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

    def move_cleanup(self):
        flat = []
        for item in self.tableau:
            for subitem in item:
                flat.append(subitem)
        ba = bytearray([STANDARD_DECK.index(card) for card in flat])
        crc = zlib.crc32(ba)
        crchex = hex(crc)[2:]
        self.mq.append(crchex)
        self.score = self.score_tableau()

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
            num = int(move[2:],16)
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


    def update_nodes(self, move):

        self.spidertree.nodes[self.spidertree.current_node].children[move] = len(self.spidertree.nodes)
        self.spidertree.add(SpiderNode())
        self.spidertree.connect(self.spidertree.current_node, len(self.spidertree.nodes) - 1, move)
        self.current_node = self.spidertree.move_down(move)
        self.logger.add_move(move)
        self.do_move(move)

    def execute(self):
        self.game_setup()
        self.spidertree.add(SpiderNode())
        while True:
            redeal_flag = False
            cycle_error = len(self.mq) - len(set(self.mq)) > 3

            moves = self.getmoves()
            if (not moves or cycle_error):
                if self.deck:
                    redeal_flag = True
                    self.mq = []
                elif not moves:
                    break
                #elif cycle_error:
                #    break
            if not redeal_flag:
                self.spidertree.initialize_nodes(moves)
                chosen = ran.choice(moves)
                self.update_nodes(chosen)
                self.scan_for_full()
            else:
                self.update_nodes('***')
        if len(self.full_suits) == 8:
            print('CONGRATULATIONS - you won.')
        else:
            print('Sorry, better luck next time - you lost.')

    def post_process(self, adds):
        leaves = []
        goal = len(self.spidertree.nodes) + adds
        for i, node in enumerate(self.spidertree.nodes):
            if not self.spidertree.nodes[i].children:
                leaves.append(i)
        for leaf in leaves:
            this_node = leaf
            while len(self.spidertree.nodes) < goal:
                last_node = this_node
                parent_node = self.spidertree.nodes[this_node].parent
                keys = self.spidertree.nodes[parent_node].children.keys()
                values = self.spidertree.nodes[parent_node].children.values()
                num_not_defined = len(keys) - sum([value != None for value in values])
                if num_not_defined == 0:
                    move = self.spidertree.get_parent_to_current_move(last_node)
                    self.do_move(move, backtrack=True)
                    this_node = parent_node
                    continue
                for key in keys:
                    if not self.spidertree.nodes[parent_node].children[key]:
                        move = key
                        self.do_move(move)
                        break
                    else:
                        pass
                    self.update_nodes(move)


    def load_state(self):
        with open('pickles/'+ self.state_filename + '.pickle', 'rb') as f:
            data = pickle.load(f)
        return data


    @staticmethod
    def save_state(data):
        now = dt.datetime.now()
        pklfile_name = now.strftime("%d-%H-%M-%S") +'.txt'
        with open('pickles/'+pklfile_name +'.pickle','wb') as f:
            pickle.dump(data,f,pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    sg = SpiderGame('1361ec2b')
    sg.execute()
    sg.post_process(10)

    pass