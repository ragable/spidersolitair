import pygame
import os
import sys
import numpy as np
from spider_engine import SpiderEngine
from spider_game_tree import GameTree
from gptspider import SpiderDisplay
import spider_constants as sc
import datetime as dt
import time


class SpiderAnalyzer:

    def __init__(self, pfile):
        pname = 'pckls/' + pfile + '.pkl'
        self.gtree = self.from_pickle(pname)
        self.engine = SpiderEngine(self.gtree.root.state)
        self.display = SpiderDisplay()
        self.thisnode = self.gtree.root

    def process(self):
        while True:
            self.display.draw_piles(self.thisnode.state)
            time.sleep(3)
            self.thisnode = self.thisnode.children[0]








    @staticmethod
    def from_pickle(path):
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)


if __name__ == '__main__':
    sp = SpiderAnalyzer('516664-10696371')
    sp.process()
    pass