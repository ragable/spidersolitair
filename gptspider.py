import pygame
import os
import numpy as np
import random
import zlib
from spider_engine import SpiderEngine
import spider_constants as sc
import datetime as dt
import time

class Diagnostics:
    def __init__(self):
        self.max_suited_run_length = 0
        self.max_unsuited_run_length = 0
        self.single_empty_columns_in_effect = False
        self.multi_empty_columns_in_effect = False
        self.mode = sc.NORMAL


    def count(self,lists):
        connecteds = []
        for lst in lists:
            if len(lst) == 0:
                connecteds.append('')
            elif len(lst) == 1:
                connecteds.append(lst[0])
            else:
                ziplist = list(zip(lst,lst[1:]))
                relations = []
                for item in ziplist:
                    if item[0][1] == item[1][1] and sc.RANKS.index(item[0][0]) == sc.RANKS.index(item[1][0]) + 1:
                        relations.append('*')
                    elif sc.RANKS.index(item[0][0]) == sc.RANKS.index(item[1][0]) + 1:
                        relations.append('#')
                    else:
                        relations.append('-')
                strng = ''
                for i,item in enumerate(lst):
                    strng += item
                    if i >= len(relations):
                        break
                    strng += relations[i]
                connecteds.append(strng)

        suited = []
        unsuited = []
        for connected in connecteds:
            split1 = connected.split('-')
            for item in split1:
                if '*' in item:
                    suited.append(len(item.split('*')))
                elif '#' in item:
                    unsuited.append(len(item.split('#')))
        largest = 0
        for item in suited:
            if item > largest:
                largest = item
        if largest > self.max_suited_run_length:
            self.max_suited_run_length = largest
        largest = 0
        for item in unsuited:
            if item > largest:
                largest = item
        if largest > self.max_unsuited_run_length:
            self.max_unsuited_run_length = largest


    def collect(self, lists):
        relevant_lists = []
        for i in range(10):
            relevant_lists.append(lists[2*i+1])

        lengths = [len(lst) for lst in relevant_lists]
        empties = sum([item == 0 for item in lengths])
        if empties == 0:
            self.single_empty_columns_in_effect = False
            self.multi_empty_columns_in_effect = False
            self.mode = sc.NORMAL
        elif empties == 1:
            self.single_empty_columns_in_effect = True
            self.multi_empty_columns_in_effect = False
            self.mode = sc.SINGLE
        else:
            self.single_empty_columns_in_effect = False
            self.multi_empty_columns_in_effect = True
            self.mode = sc.MULTI
        self.count(relevant_lists)
        pass

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
        self.dfilename = None
        self.move_list = []
        self.game_state = sc.FORWARD
        self.game_strategy = sc.NORMAL
        self.moveno = 1
        self.diags = Diagnostics()


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
            for _ in piles[2 * col]:
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

    @staticmethod
    def delay_play():
        time.sleep(0.05)

    @staticmethod
    def quit():
        pygame.quit()
        #sys.exit()



    def create_initial_deal(self,deckname):
    
    
        if deckname is None:
            full_deck = sc.STANDARD_DECK * 2
            random.shuffle(full_deck)
            ba = bytearray([sc.STANDARD_DECK.index(card) for card in full_deck])
            crc = zlib.crc32(ba)
            self.dfilename = 'decks/' + hex(crc)[2:] + '.txt'
            with open(self.dfilename, 'w') as f:
                f.write(str(full_deck))
        else:
            self.dfilename = 'decks/' + deckname + '.txt'
            with open(self.dfilename, 'r') as f:
                full_deck = eval(f.read())
    
        piles = []

        sequence = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
        build = []
        for num in sequence:
            while len(build) != num:
                card = full_deck.pop()
                build.append(card)

            piles.append(build)
            build = []
        return [np.array(pile) for pile in piles], full_deck


    def xeqt(self,deck=None):
        piles, stock = self.create_initial_deal(deck)
        engine = SpiderEngine(piles)
        display = SpiderDisplay()
        mq = []
    
        display.draw_piles([list(p) for p in engine.piles])
        display.delay_play()
        while True:

            moves = engine.get_all_possible_moves()
            if not moves or len(mq) != len(set(mq)):
                self.move_list.append('K')
                if len(stock) >= 10:
                    for i in range(10):
                        card = stock.pop()
                        engine.piles[2*i + 1] = np.append(engine.piles[2*i + 1], card)
                    display.draw_piles(engine.piles)
                    mq =[]
                    continue
                else:

                    print("Stock empty — no more possible moves.")
                    print(f"MAX SUITED: {self.diags.max_suited_run_length}")
                    print(f"MAX UNSUITED:{self.diags.max_unsuited_run_length}")
                    dealpart = self.dfilename.split('/')[1].split('.')[0]
                    fname = 'movefiles/' +    str(int((dt.datetime.now() - sc.BASE_DATE).microseconds))+ '-' + dealpart + '.txt'
                    print("Move file saved to " + fname)
                    with open(fname, 'w') as f:
                        f.write(str(self.move_list))
                    pilesz = [len(item) for item in engine.piles]
                    pcount = sum(pilesz)
                    if sum(pilesz) == 0:
                        print('CONGRATULATIONS - YOU WON A SPIDER GAME!')
                    else:
                        print(f'Sorry - you lost - there were {pcount} cards left on the table.')
                    break
            move_ranks = []
            for move in moves:
                move_ranks.append(engine.rate_move(move))
            high = 0
            for rate in move_ranks:
                if rate > high:
                    high = rate
            results = []
            for i,rate in enumerate(move_ranks):
                if rate == high:
                    results.append(moves[i])


            while True:
                move = random.choice(results)
                if move not in mq:
                    mq.append(engine.calc_pile_hash([list(pile) for pile in engine.piles]))
                    break
            if len(mq) > 5:
                mq = mq[-5:]
            self.move_list.append(move)
            print(self.moveno,mq)
            self.moveno+=1
            engine.move_sequence(move)

    

            from_idx = sc.COLNUM.index(move[0])
            if len(engine.piles[from_idx]) == 0 and len(engine.piles[from_idx - 1]) != 0:
                engine.piles[from_idx] = np.append(engine.piles[from_idx],engine.piles[from_idx - 1][-1])
                engine.piles[from_idx-1] = engine.piles[from_idx - 1][:-1]

            self.diags.collect([list(pile) for pile in engine.piles])
            display.draw_piles(engine.piles)

            display.delay_play()

        display.quit()


if __name__ == "__main__":

    for i in range(100):
        sd = SpiderDisplay()
        sd.xeqt('faab0829')
