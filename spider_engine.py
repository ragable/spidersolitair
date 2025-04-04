# spider_engine.py
HEXNUM = '0123456789ABCDEF'
import numpy as np

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
        if not cards:
            return []
        tail = [cards[-1]]
        for i in range(len(cards) - 2, -1, -1):
            prev = cards[i]
            curr = tail[-1]
            if self.suit(prev) != self.suit(curr):
                break
            if self.rank_value(self.rank(prev)) != self.rank_value(self.rank(curr)) + 1:
                break
            tail.append(prev)
        return list(reversed(tail))

    def get_all_possible_moves(self):
        moves = []
        for from_idx in range(10):
            visible = self.get_visible_cards(from_idx)
            tail = self.find_suited_tail(visible)
            if not tail:
                continue
            for to_idx in range(10):
                if from_idx == to_idx:
                    continue
                dest_pile = self.piles[to_idx]
                if len(dest_pile) == 0:
                    moves.append( HEXNUM[from_idx] + HEXNUM[to_idx] + HEXNUM[len(tail)])
                else:
                    top_card = dest_pile[-1]
                    if top_card != "XX" and self.rank_value(self.rank(top_card)) == self.rank_value(self.rank(tail[0])) + 1:
                        moves.append(HEXNUM[from_idx] + HEXNUM[to_idx] + HEXNUM[len(tail)])
        return moves

    def rank(self, card):
        return card[:-1]

    def suit(self, card):
        return card[-1]

    def rank_value(self, r):
        return {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                "6": 6, "7": 7, "8": 8, "9": 9, "T": 10,
                "J": 11, "Q": 12, "K": 13}[r]

    def move_sequence(self, mv_string):
        from_idx = HEXNUM.index(mv_string[0])
        to_idx = HEXNUM.index(mv_string[1])
        howmany = HEXNUM.index(mv_string[2])
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
            suits = [self.suit(c) for c in seq]
            values = [self.rank_value(self.rank(c)) for c in seq]
        except (KeyError, IndexError, ValueError):
            return False
        return all(s == suits[0] for s in suits) and all(values[i] == values[i+1] + 1 for i in range(len(values) - 1))
