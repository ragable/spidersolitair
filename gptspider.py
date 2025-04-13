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


    @staticmethod
    def get_piles_structure(lists):
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
                for n,item in enumerate(lst):
                    strng += item
                    if n >= len(relations):
                        break
                    strng += relations[i]
                connecteds.append(strng)
        return connecteds

    def count(self,lists):

        connecteds = self.get_piles_structure(lists)
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
        for n in range(10):
            relevant_lists.append(lists[2*n+1])

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

    def evaluate_piles(self,lists):
        structures = self.get_piles_structure(lists)
        ups = [structures[2*n+1] for n in range(10)]
        suited_count = 0
        unsuited_count = 0
        for up in ups:
            testrun = up.split('-')
            suited_seqs = []
            for item in testrun:
                if '*' in item:
                    suited_seqs.append(item)
            for item in suited_seqs:
                suited_count += len(item.split('*'))
            unsuited_seqs = []
            for item in testrun:
                if "#" in item:
                    unsuited_seqs.append(item)
            for item in unsuited_seqs:
                unsuited_count += len(item.split('#'))
        return 2*suited_count + unsuited_count





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

    def draw_piles(self, visual_piles):
        self.screen.fill((0, 128, 0))  # green background like a card table

        for col in range(len(visual_piles) // 2):  # 10 columns expected
            x = sc.MARGIN + col * sc.PILE_SPACING_X
            y = sc.MARGIN

            # Draw face-down cards from even index
            for _ in visual_piles[2 * col]:
                self.screen.blit(self.card_images['BACK-SIDE'], (x, y))
                y += sc.CARD_SPACING_Y

            # Draw face-up cards from odd index
            for card in visual_piles[2 * col + 1]:
                card_str = card.upper()
                if card_str in self.card_images:
                    self.screen.blit(self.card_images[card_str], (x, y))
                else:
                    print(f"Missing image for card {card_str}")
                y += sc.CARD_SPACING_Y

        pygame.display.flip()
        self.clock.tick(30)

    @staticmethod
    def delay_play(t):
        time.sleep(t)

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
    
        tableau_piles = []

        sequence = [5,1,5,1,5,1,5,1,4,1,4,1,4,1,4,1,4,1,4,1]
        build = []
        for num in sequence:
            while len(build) != num:
                card = full_deck.pop()
                build.append(card)

            tableau_piles.append(build)
            build = []
        return [np.array(pile) for pile in tableau_piles], full_deck


    def xeqt(self,deck=None):
        play_piles, stock = self.create_initial_deal(deck)
        engine = SpiderEngine(play_piles)
        display = SpiderDisplay()
        engine.mq = []
    
        display.draw_piles([list(p) for p in engine.piles])

        while True:
            engine.calculate_goals(engine.piles)
            if not engine.spider_goal_queue or len(engine.mq) != len(set(engine.mq)):
                engine.spider_goal_queue = []   # prevents problems when it's a cycle
                                                # that caused the redeal.
                self.move_list.append('L')
                if len(stock) >= 10:
                    for n in range(10):
                        card = stock.pop()
                        engine.piles[2*n + 1] = np.append(engine.piles[2*n + 1], card)
                    display.draw_piles(engine.piles)
                    engine.mq =[]
                    continue
                else:
                    print(50*'*')
                    print(f'No. of moves {self.moveno}')
                    print(f"MAX SUITED: {self.diags.max_suited_run_length}")
                    if self.diags.max_suited_run_length >= 9:
                        self.delay_play(10.0)
                    dealpart = self.dfilename.split('/')[1].split('.')[0]
                    fname = 'movefiles/' +    str(int((dt.datetime.now() - sc.BASE_DATE).microseconds))+ '-' + dealpart + '.txt'
                    print("Move file saved to " + fname)
                    with open(fname, 'w') as f:
                        f.write(str(self.move_list))
                    len_piles = [len(item) for item in engine.piles]
                    if sum(len_piles) == 0:
                        print('CONGRATULATIONS - YOU WON A SPIDER GAME!')
                    else:
                        score = self.diags.evaluate_piles(engine.piles) + 26 * len(engine.finished_suits_pds)
                        print(f'Sorry - you lost - your score was {score}/208.')
                    break


            self.moveno+=1
            if engine.spider_goal_queue:
                chosen_move = engine.spider_goal_queue.pop(0)

                engine.move_sequence(chosen_move)

                self.move_list.append(chosen_move)

                from_idx = sc.COLNUM.index(chosen_move[0])
                if len(engine.piles[from_idx]) == 0 and len(engine.piles[from_idx - 1]) != 0:
                    engine.piles[from_idx] = np.append(engine.piles[from_idx],engine.piles[from_idx - 1][-1])
                    engine.piles[from_idx-1] = engine.piles[from_idx - 1][:-1]

                self.diags.collect([list(pile) for pile in engine.piles])
                display.draw_piles(engine.piles)
                display.delay_play(0)
            else:
                continue

        display.quit()


if __name__ == "__main__":

    for i in range(100):
        sd = SpiderDisplay()
        sd.xeqt('65403372')
