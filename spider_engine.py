# spider_engine.py
import numpy as np
import spider_constants as sc
import zlib
import random
import copy as cp


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
    @staticmethod
    def calc_indices(card_ranks, standard):
        ndx_lists = []
        for rank in card_ranks:
            temp = [rank == item for item in standard]
            ndxes = list(zip(temp,range(10)))
            nlist = [item[1] for item in ndxes if item[0]]
            ndx_lists.append(nlist)
        return ndx_lists



    def calculate_goals(self,piles):
        # isolate the up cards
        upcards = [piles[2*i+1] for i in range(10)]
        tails = [self.find_suited_tail(ucards) for ucards in upcards]
        moves = []
        for i in range(len(tails)):
            from_tail = tails[i]
            if len(from_tail) == 0:
                continue
            target_from = from_tail[0][0]
            for j in range(len(tails)):
                if i != j:
                    to_tail = tails[j]
                    strng = ''
                    if len(to_tail) > 0:
                        target_to = to_tail[-1][0]
                        value = sc.RANKS.index(target_to) - sc.RANKS.index(target_from)
                        if value == 1:
                            move = sc.COLNUM[2*i+1] + sc.COLNUM[2*j+1] + sc.HEXNUM[len(tails[i])]
                            moves.append(move)
                    else:
                        move = sc.COLNUM[2 * i + 1] + sc.COLNUM[2 * j + 1] + sc.HEXNUM[len(tails[i])]
                        moves.append(move)
        if self.game_strategy == sc.NORMAL and len(moves) > 0:
            move_ranks = []
            for move in moves:
                move_ranks.append(self.rate_move(move))
            high = 0
            for rate in move_ranks:
                if rate > high:
                    high = rate
            results = []
            for i, rate in enumerate(move_ranks):
                if rate == high:
                    results.append(moves[i])
            move = random.choice(results)
            self.mq.append(self.calc_pile_hash([list(pile) for pile in piles]))

            if len(self.mq) > 5:
                self.mq = self.mq[-5:]
            self.spider_goal_queue.append(move)
        elif self.game_strategy == sc.SINGLE:
            pass
        elif self.game_strategy == sc.MULTI:
            pass

