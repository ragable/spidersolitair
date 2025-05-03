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
    def __init__(self, tableau, full_suits, deck, mq):
        self.tableau = tableau
        self.full_suits = full_suits
        self.deck = deck
        self.mq = mq




class SpiderGame:
    def __init__(self,deck_crc = None):
        self.deck = []
        self.tableau = []
        self.mq = []
        self.score = 0
        self.full_suits = []
        self.deck_crc = deck_crc
        self.checkpoints = []
        with open(sdc.DT_FILENAME,'r') as f:
            fdate = eval(f.read()).strftime("%d-%H-%M-%S")
        self.resultsfile = open(sdc.RESULTS_DIR + fdate + '-'+self.deck_crc + '.txt','a')
        self.starttime = dt.datetime.now()
        self.trialtree = TrialTree()
        self.working_node = SavedRun(
            tableau= [],
            full_suits= [],
            deck= [],
            mq= [],
        )




    def game_setup(self):
        with open(sdc.DECK_DIR + self.deck_crc + '.txt','r') as f:
            self.working_node.deck = eval(f.read())
        build = []
        for num in sdc.DEAL_SEQ:
            while len(build) != num:
                card = self.working_node.deck.pop()
                build.append(card)
            self.working_node.tableau.append(build)
            build = []
        pass




    @staticmethod
    def suited_seq(card1,card2):
        return card1[0] + card2[0] in sdc.RANKLIST and card1[1] == card2[1]


    @staticmethod
    def sequential(card1,card2):
        return card1[0] + card2[0] in sdc.RANKLIST


    def score_tableau(self):
        upcards = [self.working_node.state.tableau[2 * i + 1] for i in range(10)]
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
        upcards = [self.working_node.state.tableau[2*i+1] for i in range(10)]
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
        if not moves:
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
        for item in self.working_node.state.tableau:
            for subitem in item:
                flat.append(subitem)
        ba = bytearray([sdc.STANDARD_DECK.index(card) for card in flat])
        crc = zlib.crc32(ba)
        crchex = hex(crc)[2:]
        return crchex


    def do_move(self,move):
        if move == '***':
            for n in range(10):
                card = self.working_node.state.deck.pop()
                self.working_node.state.tableau[2 * n + 1].append(card)
        else:
            from_ = sdc.COLUMNIDS.index(move[0])
            to_ = sdc.COLUMNIDS.index(move[1])
            num = int(move[2:3],16)
            self.working_node.state.tableau[to_] += self.working_node.state.tableau[from_][-num:]
            self.working_node.state.tableau[from_] = self.working_node.state.tableau[from_][:-num]
            if len(self.working_node.state.tableau[from_]) == 0:
                if self.working_node.state.tableau[from_ - 1]:
                    self.working_node.state.tableau[from_] = self.working_node.state.tableau[from_ - 1][-1:]
                    self.working_node.state.tableau[from_ - 1] = self.working_node.state.tableau[from_ - 1][:-1]

            crchex= self.get_tableau_crc()
            self.mq.append(crchex)
            self.score_tableau()


    def scan_for_full(self):
        for i in range(10):
            if len(self.working_node.state.tableau[2*i + 1]) >= 13:
                suit_std = self.working_node.state.tableau[2*i+1][-1][1]
                suitcount = sum([item[1] == suit_std for item in self.working_node.state.tableau[2*i+1]])
                rankcount = 0
                for k,rank in enumerate(sdc.RANKLIST):
                    if rank == self.working_node.state.tableau[2*i+1][k][0]:
                        rankcount += 1
                if suitcount == 13 and rankcount == 13:
                    self.full_suits.append(suit_std)
                del self.working_node.state.tableau[2*i+1][-13:]
                if not self.working_node.state.tableau[2*i+1] and len(self.working_node.state.tableau[2*i]) > 0:
                    self.working_node.state.tableau[2*i+1].append(self.working_node.state.tableau[2*i].pop())


    def execute(self):
        cycle_error = len(self.mq) - len(set(self.mq)) > 2
        moves = self.getmoves()
        if (not moves or cycle_error) and self.working_node.state.deck:
            self.mq = []
            self.do_move('***')
        else:
            chosen = ran.choice(moves)
            self.do_move(chosen)
            self.scan_for_full()



    def restart(self,restart_snap):
        self.tableau = restart_snap.tableau
        self.full_suits = restart_snap.full_suits
        self.deck = restart_snap.deck
        self.mq = restart_snap.mq

    def tree_run(self):
        self.trialtree = TrialTree()
        self.game_setup()
        saved = SavedRun(
            tableau=cpy.deepcopy(self.working_node.tableau),
            full_suits=cpy.deepcopy(self.working_node.full_suits[:]),
            deck=cpy.deepcopy(self.working_node.deck[:]),
            mq=cpy.deepcopy(self.working_node.mq[:]),
        )
        self.trialtree.add_node(TrialNode(saved))
        this_node = 0
        self.working_node = saved
        while len(self.trialtree.nodes) < 1092:

            for i in range(3):
                self.working_node = cpy.deepcopy(self.trialtree.nodes[this_node])
                self.execute()
                saved = SavedRun(
                    tableau=cpy.deepcopy(self.working_node.state.tableau),
                    full_suits=cpy.deepcopy(self.working_node.state.full_suits[:]),
                    deck=cpy.deepcopy(self.working_node.state.deck[:]),
                    mq=cpy.deepcopy(self.working_node.state.mq[:]),
                )
                self.trialtree.add_node(TrialNode(saved))

            for i in range(3):
                self.trialtree.connect(this_node, len(self.trialtree.nodes) - 3 + i)
            this_node += 1

        scores = []
        for node in self.trialtree.nodes[-729:]:
            scores.append(node.state.score)
        biggest = 0
        for score in scores:
            if score > biggest:
                biggest = score

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

