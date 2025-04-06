import pygame
import os
import sys
import numpy as np
import random
import zlib
from spider_engine import SpiderEngine
from spider_game_tree import GameTree
import spider_constants as sc


class SpiderDisplay:
    def __init__(self):
        pygame.init()
        self.card_folder = "img/cards/"

        window_width = sc.MARGIN * 2 + sc.PILE_SPACING_X * 10
        window_height = sc.MARGIN * 2 + sc.CARD_SPACING_Y * 20 + sc.CARD_HEIGHT
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Spider Solitaire Display")

        self.clock = pygame.time.Clock()
        self.card_images = self.load_card_images()

        # Support for a renamed back image
        if "XX" not in self.card_images and "BACK-SIDE" in self.card_images:
            self.card_images["XX"] = self.card_images["BACK-SIDE"]


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

        for col in range(len(piles) // 2):  # 10 columns expected
            x = sc.MARGIN + col * sc.PILE_SPACING_X
            y = sc.MARGIN

            # Draw face-down cards from even index
            for card in piles[2 * col]:
                self.screen.blit(self.card_images['BACK-SIDE'], (x, y))
                y += sc.CARD_SPACING_Y

            # Draw face-up cards from odd index
            for card in piles[2 * col + 1]:
                card_str = card.upper()
                if card_str in self.card_images:
                    self.screen.blit(self.card_images[card_str], (x, y))
                else:
                    print(f"Missing image for card {card_str}")
                y += sc.CARD_SPACING_Y

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

    def create_initial_deal(self,deckname):
    
    
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
    
        piles = []
    
        i = 0
        sequence = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
        build = []
        for j in sequence:
            while len(build) != j:
                card = full_deck.pop()
                build.append(card)

            piles.append(build)
            build = []
        return [np.array(pile) for pile in piles], full_deck


    def xeqt(self,deck=None):
        piles, stock = self.create_initial_deal(deck)
        engine = SpiderEngine(piles)
        display = SpiderDisplay()
        #gt = GameTree([list(p) for p in piles_real])
        mq = []
    
        display.draw_piles([list(p) for p in engine.piles])
        display.wait_for_key()
    
        while True:
            moves = engine.get_all_possible_moves()
            if not moves or (len(mq) != len(set(mq))and (mq[-1] != mq[-2])):
                if len(stock) >= 10:
                    for i in range(10):
                        card = stock.pop()
                        engine.piles[2*i + 1] = np.append(engine.piles[2*i + 1], card)
                    display.draw_piles(engine.piles)
                    display.wait_for_key()
                    mq =[]
                    continue
                else:
                    print("Stock empty — no more possible moves.")
                    #gt.to_pickle("pckls/last_game_tree.pkl")
                    print("Game tree saved to last_game_tree.pkl")
                    break
            print(20*'*')
            print(f'Moves input: {moves}')
            move_ranks = []
            for move in moves:
                move_ranks.append(engine.rate_move(move))
            print(f'Move ranks: {move_ranks}')
            high = 0
            for rate in move_ranks:
                if rate > high:
                    high = rate
            results = []
            for i,rate in enumerate(move_ranks):
                if rate == high:
                    results.append(moves[i])
            print(f'Choices: {results}')

            move = random.choice(results)
            print(f'Chosen: {move}')
            mq.append(move)
            if len(mq) > 5:
                mq = mq[-5:]
            print(str(mq))
            engine.move_sequence(move)
    

            from_idx = sc.COLNUM.index(move[0])
            if len(engine.piles[from_idx]) == 0 and len(engine.piles[from_idx - 1]) != 0:
                engine.piles[from_idx] = np.append(engine.piles[from_idx],engine.piles[from_idx - 1][-1])
                engine.piles[from_idx-1] = engine.piles[from_idx - 1][:-1]


            display.draw_piles(engine.piles)
            # Save this move/state to game tree
            #gt.expand_with_move(move, [list(p) for p in piles_real])

            display.wait_for_key()
            pass

        display.quit()


if __name__ == "__main__":

    sd = SpiderDisplay()
    sd.xeqt('b1ef9451')
