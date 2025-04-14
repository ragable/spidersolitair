# spider_engine.py
import spider_constants as sc
import zlib
import copy as cpy

class SpiderEngine:
    def __init__(self, piles):
        self.piles = piles
        self.finished_suits_pds = []
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
        local_piles = cpy.deepcopy(self.piles)
        try:
            from_idx = sc.COLNUM.index(mv_string[0])
        except:
            pass
        to_idx = sc.COLNUM.index(mv_string[1])
        howmany = sc.HEXNUM.index(mv_string[2])
        pile_from = local_piles[from_idx]
        visible = local_piles[from_idx]
        move_cards = visible[-howmany:]
        local_piles[from_idx] = pile_from[:-howmany]
        for card in move_cards:
            local_piles[to_idx].append(card)
        if len(local_piles[from_idx]) == 0:
            if len(local_piles[from_idx - 1]) != 0:
                local_piles[from_idx].append(local_piles[from_idx - 1].pop())
        return local_piles



    def calculate_moves(self):
        # isolate the up cards
        upcards = [self.piles[2*i+1] for i in range(10)]
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
                    if len(to_tail) > 0:
                        target_to = to_tail[-1][0]
                        value = sc.RANKS.index(target_to) - sc.RANKS.index(target_from)
                        if value == 1:
                            move = sc.COLNUM[2*i+1] + sc.COLNUM[2*j+1] + sc.HEXNUM[len(tails[i])]
                            moves.append(move)

                    else:
                        move = sc.COLNUM[2 * i + 1] + sc.COLNUM[2 * j + 1] + sc.HEXNUM[len(tails[i])]
                        moves.append(move)
        return moves





