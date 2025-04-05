import pygame
import os
import sys
import numpy as np
import random
import zlib
from spider_engine import SpiderEngine
import spider_game_tree as sgt
import spider_constants as sc


class SpiderDisplay:
    def __init__(self, card_folder="img/cards/"):
        pygame.init()
        self.card_folder = card_folder

        window_width = sc.MARGIN * 2 + sc.PILE_SPACING_X * 10
        window_height = sc.MARGIN * 2 + sc.CARD_SPACING_Y * 20 + sc.CARD_HEIGHT
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
                image = pygame.transform.scale(image, (sc.CARD_WIDTH, sc.CARD_HEIGHT))
                card_images[name.upper()] = image
        return card_images

    def draw_piles(self, piles):
        self.screen.fill((0, 128, 0))  # green background like a card table

        for i, pile in enumerate(piles):
            x = sc.MARGIN + i * sc.PILE_SPACING_X
            for j, card in enumerate(pile):
                y = sc.MARGIN + j * sc.CARD_SPACING_Y
                card_str = card.upper()
                if card_str in self.card_images:
                    self.screen.blit(self.card_images[card_str], (x, y))
                else:
                    pygame.draw.rect(self.screen, (255, 0, 0), (x, y, sc.CARD_WIDTH, sc.CARD_HEIGHT))
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

def create_initial_deal(deckname):


    if deckname is None:
        full_deck = sc.STANDARD_DECK * 2
        random.shuffle(full_deck)
        ba = bytearray([sc.STANDARD_DECK.index(card) for card in full_deck])
        crc = zlib.crc32(ba)
        dfilename = 'decks/' + hex(crc)[2:] + '.txt'
        with open(dfilename, 'w') as f:
            f.write(str(full_deck))
    else:
        dfilename = 'decks/' + deckname + '.txt'
        with open(dfilename, 'r') as f:
            full_deck = eval(f.read())

    piles_real = [[] for _ in range(10)]
    piles_display = [[] for _ in range(10)]

    for i in range(10):
        num_cards = 6 if i < 4 else 5
        for j in range(num_cards):
            card = full_deck.pop()
            piles_real[i].append(card)
            if j == num_cards - 1:
                piles_display[i].append(card)  # face-up
            else:
                piles_display[i].append("XX")  # face-down

    return [np.array(pile) for pile in piles_display], full_deck, piles_real

def main(deck=None):
    piles, stock, piles_real = create_initial_deal(deck)
    engine = SpiderEngine(piles)
    display = SpiderDisplay()
    gt = sgt.GameTree(piles_real)

    display.draw_piles([list(p) for p in engine.piles])
    display.wait_for_key()

    while True:
        moves = engine.get_all_possible_moves()
        if not moves:
            print("No more possible moves.")
            break

        move = random.choice(moves)
        if engine.move_sequence(move):
            display.moveq.append(move)
            if len(display.moveq) > 10:
                display.moveq = display.moveq[1:]

        from_idx = sc.HEXNUM.index(move[0])
        pile = engine.piles[from_idx]
        if len(pile) > 0 and pile[-1] == "XX":
            for i in range(len(pile) - 1, -1, -1):
                if pile[i] == "XX":
                    pile[i] = piles_real[from_idx][i]  # reveal the true card
                    break

        display.draw_piles(engine.piles)
        gt.expand_with_move(move, engine.piles)
        display.wait_for_key()

    display.quit()

if __name__ == "__main__":
    main('f1f01170')
