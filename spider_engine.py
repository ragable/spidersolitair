# spider_engine.py
import numpy as np
import spider_constants as sc
import zlib
import random



class SpiderEngine:
    def __init__(self, piles):
        self.piles = piles
        self.finished_suits_pds = []
        self.spider_goal_queue = []
        self.game_state = sc.FORWARD
        self.game_strategy = sc.NORMAL
        self.mq = []

    @staticmethod
    def find_suited_tail(cards):
        """
        Find the longest suited descending tail from the end of the visible cards.
        """
        if len(cards) == 0:
            return []
        tail = [cards[-1]]
        for i in range(len(cards) - 2, -1, -1):
            prev = cards[i]
            curr = tail[-1]
            if sc.SUITS.index(prev[1]) != sc.SUITS.index(curr[1]):
                break
            if sc.RANKS.index(prev[0]) != sc.RANKS.index(curr[0]) + 1:
                break
            tail.append(prev)
        return list(reversed(tail))

    def get_all_possible_moves(self):
        moves = []
        for from_idx in range(10):
            visible = self.piles[2*from_idx + 1] #self.get_visible_cards(from_idx)
            tail = self.find_suited_tail(visible)
            if not tail:
                continue
            if len(tail) == 13: # completed a suit
                suit = tail[-1][1]
                n = 2*from_idx + 1
                self.piles[n] = self.piles[n][:-13]
                self.finished_suits_pds.append([suit,2*from_idx + 1])
                continue

            for to_idx in range(10):
                if from_idx == to_idx:
                    continue
                dest_pile = self.piles[2*to_idx + 1]
                if len(dest_pile) == 0:
                    moves.append( sc.COLNUM[2*from_idx + 1] + sc.COLNUM[2*to_idx + 1] + sc.HEXNUM[len(tail)])
                else:
                    top_card = dest_pile[-1]
                    if top_card != "XX" and sc.RANKS.index(top_card[0]) == sc.RANKS.index(tail[0][0]) + 1:
                        moves.append(sc.COLNUM[2*from_idx + 1] + sc.COLNUM[2*to_idx + 1] + sc.HEXNUM[len(tail)])
        return moves

    def push_finished_suit(self, suit, pile):
        self.finished_suits_pds.append([suit, pile])

    def pop_finished_suit(self):
        return self.finished_suits_pds.pop()

    def rate_move(self, move):
        orig = sc.COLNUM.index(move[0])
        dest = sc.COLNUM.index(move[1])
        howmany = sc.HEXNUM.index(move[2])
        rating = 0
        orig_visible = self.piles[orig]
        orig_tail = self.find_suited_tail(orig_visible)

        dest_visible = self.piles[dest]
        if len(dest_visible) == 0:
            rating += 4
        elif dest_visible[-1][1] == orig_tail[0][1]:
            # extending run
            rating += 2
        else:
            rating += 1
        all_visible = [len(self.piles[2*i + 1]) for i in range(10)]
        num_blank_cols = sum([all_visible[i] == 0 for i in range(10)])
        if howmany == len(self.piles[orig]):
            if num_blank_cols == 0:
                rating += 3
            elif num_blank_cols > 0:
                rating += 5
        return rating

    @staticmethod
    def calc_pile_hash(piles):
        flat = []
        for lst in piles:
            for subelement in lst:
                flat.append(sc.STANDARD_DECK.index(subelement))
        ba = bytearray([item for item in flat])
        crc = hex(zlib.crc32(ba))
        return crc[2:]



    def move_sequence(self, mv_string):
        from_idx = sc.COLNUM.index(mv_string[0])
        to_idx = sc.COLNUM.index(mv_string[1])
        howmany = sc.HEXNUM.index(mv_string[2])
        pile_from = self.piles[from_idx]
        pile_to = self.piles[to_idx]
        visible = self.piles[from_idx]

        if len(visible) < howmany:
            return False

        move_cards = visible[-howmany:]
        # Double-check the cards being moved are suited and descending
        if not self.is_suited_descending_sequence(move_cards):
            return False

        self.piles[from_idx] = np.array(list(pile_from[:-howmany]))
        self.piles[to_idx] = np.append(pile_to, move_cards)

        return True

    @staticmethod
    def is_suited_descending_sequence(seq):
        if len(seq) < 2:
            return True
        try:
            suits = [sc.SUITS.index(c[1]) for c in seq]
            values = [sc.RANKS.index(c[0]) for c in seq]
        except (KeyError, IndexError, ValueError):
            return False
        return all(s == suits[0] for s in suits) and all(values[i] == values[i+1] + 1 for i in range(len(values) - 1))

    def calc_indices(self, card_ranks, standard):
        ndx_lists = []
        for rank in card_ranks:
            temp = [rank == item for item in standard]
            ndxes = list(zip(temp,range(10)))
            nlist = [item[1] for item in ndxes if item[0]]
            ndx_lists.append(nlist)
        return ndx_lists

    def calculate_goals(self,piles):
        upcards = [piles[2*i+1] for i in range(10)]
        tails = [self.find_suited_tail(ucards) for ucards in upcards]
        attached_to_targets = [item[0][0] if item else None for item in tails]
        atts = []
        for item in attached_to_targets:
            if item and item != 'A':
                target = sc.RANKS[sc.RANKS.index(item) - 1]
                for subitem in upcards:
                    subitem_ranks = [card[0] for card in subitem]
                    if target in subitem_ranks:
                        atts.append(target)
                        break
        predecessors = list(set(atts))
        predecessors.sort()
        successors = [sc.RANKS[sc.RANKS.index(item) + 1] for item in atts]
        successors.sort()
        succ_list_ndxes = self.calc_indices(successors,attached_to_targets)
        pred_list_ndxes = self.calc_indices(predecessors,attached_to_targets)

        movs = []
        for i in range(len(pred_list_ndxes)):
            for item in pred_list_ndxes[i]:
                for sub_item in succ_list_ndxes[i]:
                    movs.append([sc.COLNUM[2 * item + 1]+sc.COLNUM[2 * sub_item + 1] + sc.HEXNUM[len(tails[item])]])

        if self.game_strategy == sc.NORMAL:
            move_ranks = []
            for move in movs:
                move_ranks.append(self.rate_move(move))
            high = 0
            for rate in move_ranks:
                if rate > high:
                    high = rate
            results = []
            for i, rate in enumerate(move_ranks):
                if rate == high:
                    results.append(movs[i])

            while True:
                move = random.choice(results)
                if move not in self.mq:
                    self.mq.append(self.calc_pile_hash([list(pile) for pile in self.piles]))
                    break
            if len(self.mq) > 5:
                self.mq = self.mq[-5:]
            self.spider_goal_queue.append(move)
        elif self.game_strategy == sc.SINGLE:
            pass
        elif self.game_strategy == sc.MULTI:
            pass

