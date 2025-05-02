import random as ran
import datetime as dt
import zlib
import copy as cpy
import sd_constants as sdc


class TrialNode:

    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []


class TrialTree:

    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def connect(self, nodenum1, nodenum2):
        self.nodes[nodenum1].children.append(nodenum2)
        self.nodes[nodenum2].parent = nodenum1


class SavedRun:
    def __init__(self, tableau, full_suits, deck, mq, score, spider_tree):
        self.tableau = tableau
        self.full_suits = full_suits
        self.deck = deck
        self.mq = mq
        self.score = score
        self.spider_tree = spider_tree

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
    def __init__(self,deck_crc = None):
        self.deck = []
        self.tableau = []
        self.spidertree = SpiderTree()
        self.mq = []
        self.score = 0
        self.full_suits = []
        self.deck_crc = deck_crc
        self.checkpoints = []
        with open(sdc.DT_FILENAME,'r') as f:
            fdate = eval(f.read()).strftime("%d-%H-%M-%S")
        self.resultsfile = open(sdc.RESULTS_DIR + fdate + '-'+self.deck_crc + '.txt','a')
        self.starttime = dt.datetime.now()
        self.best_score = 0
        self.trialtree = TrialTree()
        self.snap_count = 0


    def update_results(self):
        self.score_tableau()
        if self.score >= 75:
            self.best_score = self.score
            self.resultsfile.write('\n' + 50*'*' + '\n')
            self.resultsfile.write(f'Best Score: {self.best_score}\n')
            self.resultsfile.write(f'Node Number: {self.spidertree.current_node}\n')
            self.resultsfile.write(f'Elapsed Time: {dt.datetime.now() - self.starttime}\n')
            self.resultsfile.write(f'Self Full Suits: {self.full_suits}\n')
            for i in range(10):
                self.resultsfile.write(f'{2*i + 1}: {str(self.tableau[2*i+1])} \n')
            self.resultsfile.flush()


    def game_setup(self):
        with open(sdc.DECK_DIR + self.deck_crc + '.txt','r') as f:
            self.deck = eval(f.read())
        build = []
        for num in sdc.DEAL_SEQ:
            while len(build) != num:
                card = self.deck.pop()
                build.append(card)
            self.tableau.append(build)
            build = []




    @staticmethod
    def suited_seq(card1,card2):
        return card1[0] + card2[0] in sdc.RANKLIST and card1[1] == card2[1]


    @staticmethod
    def sequential(card1,card2):
        return card1[0] + card2[0] in sdc.RANKLIST


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
                            moves.append(sdc.COLUMNIDS[2*j + 1] + sdc.COLUMNIDS[2*i+1] + sdc.COLUMNIDS[len(sequences[i])])
                        elif i > j:
                            moves.append(sdc.COLUMNIDS[2 * j + 1] + sdc.COLUMNIDS[2 * i + 1] + sdc.COLUMNIDS[len(sequences[j])])
                elif seqfrom:
                    moves.append(sdc.COLUMNIDS[2*j + 1] + sdc.COLUMNIDS[2*i+1] + sdc.COLUMNIDS[len(seqfrom)])
        if moves == []:
            for i,seqto in enumerate(sequences):
                for j,seqfrom in enumerate(sequences):
                    if seqfrom and seqto:
                        if self.sequential(sequences[i][-1], sequences[j][0]):
                            if i < j:
                                moves.append(sdc.COLUMNIDS[2 * j + 1] + sdc.COLUMNIDS[2 * i + 1] + sdc.COLUMNIDS[len(sequences[i])])
                            elif i > j:
                                moves.append(sdc.COLUMNIDS[2*j + 1] + sdc.COLUMNIDS[2*i+1] + sdc.COLUMNIDS[len(sequences[j])])
                    elif seqfrom:
                        moves.append(sdc.COLUMNIDS[2*j + 1] + sdc.COLUMNIDS[2*i+1] + sdc.COLUMNIDS[len(seqfrom)])
        return moves

    def get_tableau_crc(self):
        flat = []
        for item in self.tableau:
            for subitem in item:
                flat.append(subitem)
        ba = bytearray([sdc.STANDARD_DECK.index(card) for card in flat])
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
                from_ = sdc.COLUMNIDS.index(move[1])
                to_ = sdc.COLUMNIDS.index(move[0])
            else:
                from_ = sdc.COLUMNIDS.index(move[0])
                to_ = sdc.COLUMNIDS.index(move[1])
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
                for k,rank in enumerate(sdc.RANKLIST):
                    if rank == self.tableau[2*i+1][k][0]:
                        rankcount += 1
                if suitcount == 13 and rankcount == 13:
                    self.full_suits.append(suit_std)
                del self.tableau[2*i+1][-13:]
                if self.tableau[2*i+1] == [] and len(self.tableau[2*i]) > 0:
                    self.tableau[2*i+1].append(self.tableau[2*i].pop())

    def restore_last_checkpoint(self):
        cp = self.checkpoints.pop()
        self.tableau = cpy.deepcopy(cp.tableau)
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




    def execute(self,move):
        self.spidertree.add(SpiderNode())
        cycle_error = len(self.mq) - len(set(self.mq)) > 2
        if (not move or cycle_error) and self.deck:
            self.mq = []
            self.update_nodes('***')
        else:
            self.spidertree.initialize_nodes(move)
            self.update_nodes(move)
            self.scan_for_full()



    def restart(self,restart_snap):
        self.tableau = restart_snap.tableau
        self.full_suits = restart_snap.full_suits
        self.deck = restart_snap.deck
        self.mq = restart_snap.mq
        self.spidertree = restart_snap.spider_tree

    def tree_run(self):
        self.trialtree = TrialTree()
        self.game_setup()
        saved = SavedRun(
            tableau=cpy.deepcopy(self.tableau),
            full_suits=cpy.deepcopy(self.full_suits[:]),
            deck=cpy.deepcopy(self.deck[:]),
            mq=cpy.deepcopy(self.mq[:]),
            score=cpy.deepcopy(self.best_score),
            spider_tree=cpy.deepcopy(self.spidertree)
        )
        self.trialtree.add_node(TrialNode(saved))
        this_node = 0
        count = 1
        while len(self.trialtree.nodes) < 1092:
            self.restart(self.trialtree.nodes[this_node].state)
            moves = self.getmoves()
            for i in range(3):
                if len(moves) == 0:
                    self.execute(None)
                elif len(moves) == 1:
                    self.execute(moves[0])
                elif len(moves) == 2:
                    if i == 0:
                        self.execute(moves[0])
                    else:
                        self.execute(moves[1])
                else: # len(moves) > 2
                    move = ran.choice(moves)
                    moves.remove(move)
                self.execute(move)
                saved = SavedRun(
                    tableau=cpy.deepcopy(self.tableau),
                    full_suits=cpy.deepcopy(self.full_suits[:]),
                    deck=cpy.deepcopy(self.deck[:]),
                    mq=cpy.deepcopy(self.mq[:]),
                    score=cpy.deepcopy(self.best_score),
                    spider_tree=cpy.deepcopy(self.spidertree)
                )
                self.trialtree.add_node(TrialNode(saved))
                count += 1
            for i in range(3):
                self.trialtree.connect(this_node, len(self.trialtree.nodes) - 3 + i)
            this_node += 1
        # do a new deal
        scores = []
        for node in self.trialtree.nodes[-729:]:
            scores.append(node.state.score)
        biggest = 0
        for score in scores:
            if score > biggest:
                biggest = score
        filter = [score == biggest for score in scores]
        pass




    def count_leaves(self):
        count = 0
        for i, node in enumerate(self.spidertree.nodes):
            if not self.spidertree.nodes[i].children:
                count += 1
        return count
    def print_tableau(self):
        for i,item in enumerate(self.tableau):
            print(i,item)

def get_deck():
    full_deck = sdc.STANDARD_DECK * 2
    ran.shuffle(full_deck)
    ba = bytearray([sdc.STANDARD_DECK.index(card) for card in full_deck])
    crc = zlib.crc32(ba)

    dfilename = 'decks/' + hex(crc)[2:] + '.txt'
    with open(dfilename, 'w') as f:
        f.write(str(full_deck))
    return hex(crc)[2:]

if __name__ == "__main__":
    if __name__ == '__main__':
        sg= SpiderGame('1f5734a7')
        sg.tree_run()

