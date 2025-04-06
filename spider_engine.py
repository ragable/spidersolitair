# spider_engine.py
import numpy as np
import spider_constants as sc

class SpiderEngine:
    def __init__(self, piles):
        self.piles = piles


    def get_visible_cards(self, pile_idx):
        pile = self.piles[pile_idx]
        visible = []
        for card in reversed(pile):
            if card == "XX":
                break
            visible.append(card)
        return list(reversed(visible))

    def find_suited_tail(self, cards):
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

    def rate_move(self, move):
        orig = sc.COLNUM.index(move[0])
        dest = sc.COLNUM.index(move[1])
        howmany = sc.HEXNUM.index(move[2])
        rating = 0
        orig_visible = self.get_visible_cards(orig)
        orig_tail = self.find_suited_tail(orig_visible)

        dest_visible = self.get_visible_cards(dest)
        if len(dest_visible) == 0:
            rating += 4
        elif dest_visible[-1][1] == orig_tail[0][1]:
            # extending run
            rating += 2
        else:
            rating += 1
        all_visible = [len(self.get_visible_cards(2*i + 1)) for i in range(10)]
        all_cards = [len(self.piles[2*i]) + len(self.piles[2*i+1]) for i in range(10)]
        num_blank_cols = sum([all_visible[i] == 0 for i in range(10)])
        if howmany == len(self.piles[orig]):
            if num_blank_cols == 0:
                rating += 3
            elif num_blank_cols > 0:
                rating += 5
        return rating




    def move_sequence(self, mv_string):
        from_idx = sc.COLNUM.index(mv_string[0])
        to_idx = sc.COLNUM.index(mv_string[1])
        howmany = sc.HEXNUM.index(mv_string[2])
        pile_from = self.piles[from_idx]
        pile_to = self.piles[to_idx]
        visible = self.get_visible_cards(from_idx)

        if len(visible) < howmany:
            return False

        move_cards = visible[-howmany:]
        # Double-check the cards being moved are suited and descending
        if not self.is_suited_descending_sequence(move_cards):
            return False

        self.piles[from_idx] = np.array(list(pile_from[:-howmany]))
        self.piles[to_idx] = np.append(pile_to, move_cards)

        return True

    def is_suited_descending_sequence(self, seq):
        if len(seq) < 2:
            return True
        try:
            suits = [sc.SUITS.index(c[1]) for c in seq]
            values = [sc.RANKS.index(c[0]) for c in seq]
        except (KeyError, IndexError, ValueError):
            return False
        return all(s == suits[0] for s in suits) and all(values[i] == values[i+1] + 1 for i in range(len(values) - 1))
