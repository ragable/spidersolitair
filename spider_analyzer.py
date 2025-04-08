from spider_engine import SpiderEngine
from gptspider import SpiderDisplay
import time


class SpiderAnalyzer:

    def __init__(self, pfile):
        pname = 'pckls/' + pfile + '.pkl'
        self.gtree = self.from_pickle(pname)
        self.current_node = 0
        self.engine = SpiderEngine(self.gtree.nodes[self.current_node].state)
        self.display = SpiderDisplay()

    def process(self):
        while True:
            self.display.draw_piles(self.gtree.nodes[self.current_node].state)
            time.sleep(3)
            self.current_node = self.gtree.nodes[self.current_node].children[0]


    @staticmethod
    def from_pickle(path):
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)


if __name__ == '__main__':
    sp = SpiderAnalyzer('257835-8f982524')
    sp.process()