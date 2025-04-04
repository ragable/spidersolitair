import pygame
import os
import sys
import numpy as np
import random
import time
from spider_engine import SpiderEngine

CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_SPACING_Y = 30
PILE_SPACING_X = 100
MARGIN = 20
HEXNUM = '0123456789ABCDEF'
class SpiderDisplay:
    def __init__(self, card_folder="img/cards/"):
        pygame.init()
        self.card_folder = card_folder

        window_width = MARGIN * 2 + PILE_SPACING_X * 10
        window_height = MARGIN * 2 + CARD_SPACING_Y * 20 + CARD_HEIGHT
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Spider Solitaire Display")

        self.clock = pygame.time.Clock()
        self.card_images = self.load_card_images()

        # Support for a renamed back image
        if "XX" not in self.card_images and "BACK-SIDE" in self.card_images:
            self.card_images["XX"] = self.card_images["BACK-SIDE"]
        self.moveq = []

    def load_card_images(self):
        card_images = {}
        for filename in os.listdir(self.card_folder):
            if filename.endswith(".png"):
                name = filename[:-4]  # Remove .png
                path = os.path.join(self.card_folder, filename)
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
                card_images[name.upper()] = image
        return card_images

    def draw_piles(self, piles):
        self.screen.fill((0, 128, 0))  # green background like a card table

        for i, pile in enumerate(piles):
            x = MARGIN + i * PILE_SPACING_X
            for j, card in enumerate(pile):
                y = MARGIN + j * CARD_SPACING_Y
                card_str = card.upper()
                if card_str in self.card_images:
                    self.screen.blit(self.card_images[card_str], (x, y))
                else:
                    pygame.draw.rect(self.screen, (255, 0, 0), (x, y, CARD_WIDTH, CARD_HEIGHT))
                    print(f"Missing image for card: {card_str}")

        pygame.display.flip()
        self.clock.tick(30)

    def wait_for_key(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    return

    def quit(self):
        pygame.quit()
        sys.exit()

def create_initial_deal():
    suits = ["S", "H", "D", "C"]  # All four suits
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]

    # Build a full 2-deck Spider game with 4 suits (13 ranks × 4 suits × 2 decks = 104 cards)
    full_deck = [rank + suit for suit in suits for rank in ranks] * 2  # 104 cards
    random.shuffle(full_deck)

    piles = [[] for _ in range(10)]

    for i in range(10):
        num_cards = 6 if i < 4 else 5
        for j in range(num_cards):
            card = full_deck.pop()
            if j == num_cards - 1:
                piles[i].append(card)  # Face-up
            else:
                piles[i].append("XX")  # Face-down

    return [np.array(pile) for pile in piles], full_deck

if __name__ == "__main__":
    piles, stock = create_initial_deal()
    engine = SpiderEngine(piles)
    display = SpiderDisplay()

    # Initial display
    display.draw_piles([list(p) for p in engine.piles])
    display.wait_for_key()


    while True:
        moves = engine.get_all_possible_moves()
        if not moves:
            print("No more possible moves.")
            break

        move = random.choice(moves)
        #print(f"Random move: from {move[0]} to {move[1]}, length {move[2]}")
        if engine.move_sequence(move):
            display.moveq.append(move)
            if len(display.moveq) > 10:
                display.moveq = display.moveq[1:]


        # Flip card if needed
        from_idx = HEXNUM.index(move[0])

        pile = engine.piles[from_idx]
        if len(pile) > 0 and pile[-1] == "XX":
            for i in range(len(pile) - 1, -1, -1):
                if pile[i] == "XX":
                    if stock:
                        pile[i] = stock.pop()
                    else:
                        pile[i] = "??"  # Unknown card fallback
                    break

        display.draw_piles(engine.piles)
        display.wait_for_key()

    display.quit()
